import os
import chromadb
from chromadb.utils import embedding_functions

class MedicalRAGRetriever:
    def __init__(self, db_path: str = "./local_chroma_db", collection_name: str = "cancer_treatment_rag"):
        """
        Initializes the retriever targeting your local open-source Chroma database matrix.
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"❌ Local database directory '{db_path}' not found. Please run your ingestion pipeline first!")

        # 1. Connect to the local disk database instance
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        # 2. Re-instantiate the same local open-source embedding model used during ingestion
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # 3. Retrieve the target collection reference
        try:
            self.collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"🌲 Connected to local collection '{collection_name}' successfully.")
            print(f"📊 Total items indexed in collection: {self.collection.count()}\n")
        except Exception:
            raise ValueError(f"❌ Collection '{collection_name}' does not exist in this database. Verify ingestion completed successfully.")

    def query_medical_context(self, user_query: str, top_k: int = 3) -> list:
        """
        Vectorizes the incoming query and retrieves the top-K closest matching text chunks.
        """
        print(f"🔍 Searching local vector space for: '{user_query}'...")
        
        # Chroma automatically vectorizes the string via the local SentenceTransformer under the hood
        results = self.collection.query(
            query_texts=[user_query],
            n_results=top_k
        )
        
        formatted_results = []
        
        # Parse the nested list outputs returned by Chroma
        if results and 'documents' in results and results['documents'][0]:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0] if 'distances' in results else [0.0] * len(documents)
            
            for idx in range(len(documents)):
                # Convert cosine distance to a standard similarity confidence percentage metric
                similarity_score = 1.0 - distances[idx]
                
                formatted_results.append({
                    "text": documents[idx],
                    "metadata": metadatas[idx],
                    "similarity": similarity_score
                })
                
        return formatted_results

# ==========================================
# Query Execution Block
# ==========================================
if __name__ == "__main__":
    try:
        # 1. Spin up retriever pipeline
        retriever = MedicalRAGRetriever(db_path="./local_chroma_db", collection_name="cancer_treatment_rag")
        
        # 2. Define a clinical/medical question targeting your video transcripts data 
        test_query = "What are the latest survival rates and clinical outcomes for lung cancer immunotherapy?"
        
        # 3. Fetch top 3 matching transcript chunks
        matched_chunks = retriever.query_medical_context(user_query=test_query, top_k=3)
        
        # 4. Display the retrieved knowledge base blocks
        print(f"✨ Found {len(matched_chunks)} highly relevant context matches:\n" + "="*60)
        
        for i, chunk in enumerate(matched_chunks, start=1):
            print(f"\n[ MATCH #{i} ] - Confidence Score: {chunk['similarity']:.2%}")
            print(f"🎥 Video Title: {chunk['metadata'].get('title')}")
            print(f"🔗 Video URL: {chunk['metadata'].get('link')}")
            print(f"📑 Transcript Snippet:\n{chunk['text']}")
            print("-" * 60)
            
    except Exception as e:
        print(e)

