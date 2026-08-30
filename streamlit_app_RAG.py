import os
import re
import json
import streamlit as st
import chromadb
import yt_dlp
import ollama
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Configures the webpage container options
st.set_page_config(
    page_title="Medical Workspace RAG Pro",
    page_icon="🧬",
    layout="wide"
)

# Caches database connections across stream shifts
@st.cache_resource
def initialize_chroma_connection():
    db_path = "./local_chroma_db"
    collection_name = "cancer_treatment_rag"
    
    # Initialize the local persistent client directory if missing
    chroma_client = chromadb.PersistentClient(path=db_path)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_collection(name=collection_name, embedding_function=embedding_function)
    return collection

# Functional helper to convert bracket source tokens into live clickable markdown links
def inject_clickable_citations(llm_text: str, matched_chunks: list) -> str:
    def replace_tag(match):
        index_val = int(match.group(1)) - 1
        if 0 <= index_val < len(matched_chunks):
            v_title = matched_chunks[index_val]["title"]
            v_link = matched_chunks[index_val]["link"]
            safe_title = v_title[:25] + "..." if len(v_title) > 25 else v_title
            return f" **[{safe_title}]({v_link})**"
        return ""
    pattern = r"\[(?:Source\s*#?|Fragment\s*#?)(\d+)\]"
    return re.sub(pattern, replace_tag, llm_text)

# Extends the yt-dlp pipeline to isolate metadata and process transcription fetches smoothly
def process_and_index_url(url: str, collection):
    ydl_opts = {'quiet': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')
            title = info.get('title', 'Untitled Video')
        
        # Pull text tokens using the instance fetch layout framework
        transcript_obj = YouTubeTranscriptApi().fetch(video_id, languages=['en'])
        text_fragments = [segment.text for segment in transcript_obj]
        full_text = re.sub(r'\s+', ' ', " ".join(text_fragments)).strip()
        
        # Split using standard clinical chunk guidelines
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
        chunks = text_splitter.split_text(full_text)
        
        documents, metadatas, ids = [], [], []
        for index, chunk_text in enumerate(chunks):
            vector_id = f"{video_id}_chunk_{index}"
            enriched_text = f"Source Video: {title} | Content: {chunk_text}"
            
            documents.append(enriched_text)
            metadatas.append({
                "video_id": video_id,
                "title": title,
                "link": f"https://youtube.com{video_id}",
                "chunk_index": index,
                "medical_domain": "oncology"
            })
            ids.append(vector_id)
            
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return True, f"✨ Successfully indexed '{title}' into {len(chunks)} searchable vector nodes!"
    except (TranscriptsDisabled, NoTranscriptFound):
        return False, "⚠️ Ingestion Cancelled: English caption logs or transcripts are missing for this video link."
    except Exception as e:
        return False, f"❌ Ingestion Error: {str(e)}"

# Initialize DB connection safely
collection = initialize_chroma_connection()

# ==========================================
# 🔧 SIDEBAR CONFIGURATION (REMAINING INTACT)
# ==========================================
st.sidebar.header("🔧 Engine Settings")

selected_model = st.sidebar.selectbox(
    "Target Ollama Model",
    ["llama3", "llama3.1", "llama3.2", "mistral"],
    index=0,
    help="Select the local model running on your Ollama server instance."
)

top_k_chunks = st.sidebar.slider(
    "Context Sample Size (Top-K)",
    min_value=1,
    max_value=5,
    value=3,
    help="The number of highly relevant transcript chunks to feed to the LLM."
)

st.sidebar.markdown("---")

# --- NEW ADDITION INTEGRATED UNDER THE UNTOUCHED SETTINGS CONTROLS ---
st.sidebar.subheader("📥 Quick-Ingest YouTube URL")
st.sidebar.caption("Provide a new oncology/medical lecture link to append it instantly to your local vector memory space.")
new_video_url = st.sidebar.text_input("Paste YouTube Link:", placeholder="https://youtube.com...", key="ingest_url")

if st.sidebar.button("Process & Vectorize Document", use_container_width=True):
    if new_video_url:
        with st.sidebar.spinner("⏳ Extracting video telemetry and building structural matrices..."):
            success, feedback_message = process_and_index_url(new_video_url, collection)
            if success:
                st.sidebar.success(feedback_message)
                st.cache_resource.clear()  # Triggers a metric count update smoothly
            else:
                st.sidebar.error(feedback_message)
    else:
        st.sidebar.warning("Please provide a valid URL string.")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Local Database Metadata")
st.sidebar.metric(label="Total Vectors Indexed", value=f"{collection.count()} chunks")
st.sidebar.caption("🔒 Status: Secured Offline. Data will not leak to external APIs.")

# ==========================================
# Main Dashboard Application Area
# ==========================================
st.title("🧬 Private Medical RAG Platform with Inline Citations")
st.markdown("Securely evaluate cancer research transcripts utilizing local Llama 3 processing logic pipelines.")
st.markdown("---")

user_query = st.text_input("Enter clinical research query:", placeholder="Ask about immunotherapy targets, safety bounds, clinical timelines, etc...")

if user_query:
    with st.spinner("⏳ Running semantic comparison array lookup loops..."):
        results = collection.query(query_texts=[user_query], n_results=top_k_chunks)
        
        matched_chunks = []
        context_string_builder = []
        
        if results and 'documents' in results and results['documents']:

            # ChromaDB query results are commonly returned as nested lists:
            # documents  -> [[doc1, doc2, doc3, ...]]
            # metadatas  -> [[metadata1, metadata2, metadata3, ...]]
            #
            # Flatten the outer query-result layer when present.

            documents = results.get('documents', [])
            metadatas = results.get('metadatas', [])

            if documents and isinstance(documents[0], list):
                documents = documents[0]

            if metadatas and isinstance(metadatas[0], list):
                metadatas = metadatas[0]

            for idx, doc in enumerate(documents):

                # Safely obtain metadata corresponding to this document
                metadata = {}

                if idx < len(metadatas):
                    candidate_metadata = metadatas[idx]

                if isinstance(candidate_metadata, dict):
                    metadata = candidate_metadata

                # Safely extract metadata fields
                v_title = metadata.get('title', 'Unknown Video')
                v_link = metadata.get('link', '#')

                # Store matched result
            matched_chunks.append({
                "text": doc,
                "title": v_title,
                "link": v_link
            })

            # Build context for the RAG prompt
            context_string_builder.append(
                f"--- [Source #{idx + 1} | Video: {v_title}] ---\n{doc}"
            )

        full_context_block = (
        "\n\n".join(context_string_builder)
        if context_string_builder
        else "No context loaded."
        )      

        system_instructions = (
            "You are an expert medical AI assistant specialized in oncology. Synthesize coherent answers "
            "using exclusively the factual tokens in the provided text sources. "
            "CRITICAL CITATION DIRECTIVE: You must append the corresponding source reference index in source tags "
            "at the immediate end of every sentence detailing a data claim (e.g., [Source 1] or [Source 2]). "
            "Never construct statements without specifying exactly where the datum originated."
        )
        user_prompt = f"CONTEXT TEXT:\n\n{full_context_block}\n\nQUESTION: {user_query}"

        try:
            response = ollama.chat(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_prompt}
                ],
                options={"temperature": 0.1}
            )
            raw_answer = response['message']['content']
            # Replaces bracket strings with bold, interactive hyperlinked pointers
            final_answer = inject_clickable_citations(raw_answer, matched_chunks)
        except Exception as e:
            final_answer = f"❌ Ollama Endpoint Disconnect: {str(e)}\n\nVerify that 'ollama run {selected_model}' is executing in your backend terminal node."

    # Render dashboard blocks
    col_gen, col_cite = st.columns(2)

    with col_gen:
        st.subheader("🤖 Verified Sentence Synthesis")
        st.markdown(final_answer)

    with col_cite:
        st.subheader("📑 Document Sources")
        if not matched_chunks:
            st.warning("No vectors intersected the semantic neighborhood bounds.")
        else:
            for i, chunk in enumerate(matched_chunks, start=1):
                with st.expander(f"Source #{i}: {chunk['title'][:40]}..."):
                    st.caption(f'"{chunk["text"]}"')
                    st.markdown(f"[🎥 Watch Original Video]({chunk['link']})")
