import os
import json
import chromadb
import ollama  # Official local Ollama Python connector
from chromadb.utils import embedding_functions

class OfflineMedicalRAGEngine:
    def __init__(self, db_path: str = "./local_chroma_db", collection_name: str = "cancer_treatment_rag", model_name: str = "llama3"):
        """
        Initializes a completely offline local RAG execution environment.
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"❌ Database not found at '{db_path}'. Please run your ingestion script first!")

        # 1. Connect to the local open-source Chroma instance
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.chroma_client.get_collection(name=collection_name, embedding_function=self.embedding_function)
        
        # 2. Assign the target local LLM name hosted on Ollama
        self.model_name = model_name
        print(f"🌲 Connected to local vector DB collection: '{collection_name}'")
        print(f"🧠 Generation Engine bound to local Ollama model: '{self.model_name}'\n")

    def retrieve_context(self, user_query: str, top_k: int = 3) -> str:
        """ Queries the local DB and joins matching chunks into a single text block. """
        results = self.collection.query(query_texts=[user_query], n_results=top_k)
        
        context_fragments = []
        if results and 'documents' in results and results['documents'][0]:
            for idx, doc in enumerate(results['documents'][0]):
                video_title = results['metadatas'][0][idx].get('title', 'Unknown Video')
                context_fragments.append(f"--- [Fragment #{idx+1} from: {video_title}] ---\n{doc}")
                
        return "\n\n".join(context_fragments)

    def generate_answer(self, user_query: str) -> dict:
        """
        Retrieves context, formats a medical guardrail prompt, and invokes Ollama locally.
        """
        # 1. Fetch relevant transcript fragments locally
        context = self.retrieve_context(user_query, top_k=3)
        
        if not context:
            context = "No relevant transcript information found in the local knowledge database."

        # 2. Construct a strict system prompt to completely block LLM hallucinations
        system_instructions = (
            "You are an expert medical AI assistant specialized in oncology. Your goal is to synthesize answers "
            "using exclusively the provided source text from clinical video transcripts. "
            "CRITICAL DIRECTIVES:\n"
            "1. Rely ONLY on the clear facts explicitly stated in the context text below.\n"
            "2. Do NOT extrapolate or assume anything not mentioned.\n"
            "3. If the context does not contain the information needed to answer, state clearly: "
            "'I cannot find the answer within the current local video transcripts database.'\n"
            "4. Provide a clear, factual, objective response without conversational fluff."
        )
        
        user_prompt = f"CONTEXT FRAGMENTS FROM TRANSCRIPTS:\n\n{context}\n\nUSER QUESTION: {user_query}"

        print(f"🤖 Generation: Invoking local {self.model_name} processing loop...")
        
        try:
            # 3. Call the offline Ollama client engine
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,  # Low temperature forces predictable, factual output
                    "top_p": 0.9
                }
            )
            
            return {
                "query": user_query,
                "answer": response['message']['content'],
                "context_used": context
            }
            
        except Exception as e:
            return {
                "query": user_query,
                "answer": f"❌ Ollama Local Engine Error: {e}",
                "context_used": context
            }

# ==========================================
# Application Runner Loop
# ==========================================
if __name__ == "__main__":
    # Ensure you have executed 'ollama run llama3' in your terminal before running this script
    try:
        # Initialize the fully offline engine
        rag_engine = OfflineMedicalRAGEngine(db_path="./local_chroma_db", model_name="llama3")
        
        # Define your research/medical query
        query = "What specific clinical trials outcomes or adverse side effects are discussed regarding immunotherapy?"
        
        # Execute RAG generation loop
        result = rag_engine.generate_answer(user_query=query)
        
        # Print structured outputs
        print("\n" + "="*70)
        print(f"❓ QUESTION: {result['query']}")
        print("="*70)
        print(f"📖 OFFLINE LLM RESPONSE:\n\n{result['answer']}")
        print("="*70)
        
    except FileNotFoundError as e:
        print(e)
