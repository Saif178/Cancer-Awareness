import os
import re
import json
from pathlib import Path
import streamlit as st
import chromadb
import yt_dlp
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# GraphRAG interactive knowledge graph
from knowledge_graph.graph_store import MedicalKnowledgeGraph
from knowledge_graph.interactive_graph import render_interactive_graph

# Optional local Ollama dependency. The cloud/OpenAI mode does not require it.
try:
    import ollama
except ImportError:
    ollama = None

# Optional OpenAI dependency for Streamlit Cloud deployment.
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Medical Workspace RAG Pro",
    page_icon="🧬",
    layout="wide",
)


# =========================================================
# LLM CONFIGURATION
#
# Local:
#   LLM_PROVIDER=ollama
#   OLLAMA_MODEL=llama3
#
# Streamlit Cloud:
#   LLM_PROVIDER=openai
#   OPENAI_MODEL=gpt-4o-mini
#   OPENAI_API_KEY=<stored in Streamlit Secrets>
# =========================================================
def get_config(name, default=None):
    """Read Streamlit Secrets first, then environment variables."""
    try:
        value = st.secrets.get(name)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return os.getenv(name, default)


LLM_PROVIDER = str(get_config("LLM_PROVIDER", "ollama")).strip().lower()
OLLAMA_MODEL = str(get_config("OLLAMA_MODEL", "llama3")).strip()
OLLAMA_BASE_URL = str(
    get_config("OLLAMA_BASE_URL", "http://localhost:11434")
).rstrip("/")
OPENAI_MODEL = str(get_config("OPENAI_MODEL", "gpt-4o-mini")).strip()


# =========================================================
# CHROMA CONFIGURATION
# =========================================================
@st.cache_resource
def initialize_chroma_connection():
    """Open the Chroma collection and build it automatically when missing/empty.

    The transcript JSON bundled with the project is the source of truth for the
    initial local index. OpenAI/Ollama are completely independent of indexing.
    """
    db_path = str(get_config("CHROMA_DB_PATH", "./local_chroma_db")).strip()
    collection_name = str(
        get_config("CHROMA_COLLECTION", "cancer_treatment_rag")
    ).strip()

    chroma_client = chromadb.PersistentClient(path=db_path)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

    # Missing collection is now handled by get_or_create_collection(). If the
    # newly-created/existing collection is empty, bootstrap it from the bundled
    # transcript corpus instead of leaving the RAG engine unusable.
    if collection.count() == 0:
        transcript_path = Path("cancer_treatment_transcripts.json")
        if not transcript_path.exists():
            raise RuntimeError(
                f"Chroma collection '{collection_name}' is empty and the bundled "
                f"transcript file '{transcript_path}' was not found."
            )

        with transcript_path.open("r", encoding="utf-8") as fh:
            raw_videos = json.load(fh)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""],
        )

        documents, metadatas, ids = [], [], []

        for video in raw_videos:
            transcript = str(video.get("transcript", "") or "").strip()
            if not transcript:
                continue

            video_id = str(video.get("video_id", "")).strip()
            title = str(video.get("title", "Untitled Video"))
            link = str(
                video.get("link")
                or f"https://www.youtube.com/watch?v={video_id}"
            )

            for index, chunk_text in enumerate(splitter.split_text(transcript)):
                documents.append(
                    f"Source Video: {title} | Content: {chunk_text}"
                )
                metadatas.append(
                    {
                        "video_id": video_id,
                        "title": title,
                        "link": link,
                        "chunk_index": index,
                        "medical_domain": "oncology",
                    }
                )
                ids.append(f"{video_id}_chunk_{index}")

        if ids:
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

    return collection

# =========================================================
# KNOWLEDGE GRAPH INITIALIZATION
# =========================================================
def _graph_path():
    configured = get_config("GRAPH_PATH", "")
    candidates = [
        configured,
        "./knowledge_graph/data/medical_graph_v3.json",
        "./knowledge_graph/data/medical_graph_v3_template.json",
        "./knowledge_graph/data/medical_knowledge_graph.json",
        "./medical_graph.json",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    # Default for a new local build.
    return "./knowledge_graph/data/medical_graph_v3.json"


def _records_from_collection(collection):
    total = collection.count()
    if not total:
        return []
    result = collection.get(
        limit=total,
        include=["documents", "metadatas"],
    )
    records = []
    for cid, text, meta in zip(
        result.get("ids", []),
        result.get("documents", []),
        result.get("metadatas", []),
    ):
        records.append({
            "id": cid,
            "text": text or "",
            "metadata": meta or {},
        })
    return records


@st.cache_resource
def initialize_knowledge_graph(_collection):
    path = _graph_path()
    graph = MedicalKnowledgeGraph(path)
    ok, reason = graph.validate()
    if not ok:
        records = _records_from_collection(_collection)
        if not records:
            return graph, False, reason
        graph.build_from_records(records)
        ok, reason = graph.validate()
    return graph, ok, reason


# =========================================================
# CITATION HANDLING
# =========================================================
def inject_clickable_citations(llm_text: str, matched_chunks: list) -> str:
    def replace_tag(match):
        index_val = int(match.group(1)) - 1

        if 0 <= index_val < len(matched_chunks):
            v_title = matched_chunks[index_val]["title"]
            v_link = matched_chunks[index_val]["link"]

            safe_title = (
                v_title[:25] + "..."
                if len(v_title) > 25
                else v_title
            )

            return f" **[{safe_title}]({v_link})**"

        return ""

    pattern = r"\[(?:Source\s*#?|Fragment\s*#?)(\d+)\]"
    return re.sub(pattern, replace_tag, llm_text)


# =========================================================
# YOUTUBE INGESTION
# =========================================================
def process_and_index_url(url: str, collection):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            video_id = info.get("id")
            title = info.get("title", "Untitled Video")

        if not video_id:
            return False, "❌ Could not determine the YouTube video ID."

        transcript_obj = YouTubeTranscriptApi().fetch(
            video_id,
            languages=["en"],
        )

        text_fragments = [segment.text for segment in transcript_obj]

        full_text = re.sub(
            r"\s+",
            " ",
            " ".join(text_fragments),
        ).strip()

        if not full_text:
            return False, "⚠️ The video transcript is empty."

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
        )

        chunks = text_splitter.split_text(full_text)

        documents = []
        metadatas = []
        ids = []

        for index, chunk_text in enumerate(chunks):
            vector_id = f"{video_id}_chunk_{index}"

            enriched_text = (
                f"Source Video: {title} | Content: {chunk_text}"
            )

            documents.append(enriched_text)

            metadatas.append(
                {
                    "video_id": video_id,
                    "title": title,
                    "link": f"https://www.youtube.com/watch?v={video_id}",
                    "chunk_index": index,
                    "medical_domain": "oncology",
                }
            )

            ids.append(vector_id)

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        return (
            True,
            f"✨ Successfully indexed '{title}' into "
            f"{len(chunks)} searchable vector nodes!",
        )

    except (TranscriptsDisabled, NoTranscriptFound):
        return (
            False,
            "⚠️ Ingestion cancelled: English captions/transcripts "
            "are missing for this video.",
        )

    except Exception as exc:
        return False, f"❌ Ingestion Error: {exc}"


# =========================================================
# CHROMA RESULT NORMALIZATION
# =========================================================
def normalize_query_results(results):
    """
    Chroma query() returns one outer list per query.

    Example:
        documents = [[doc1, doc2, doc3]]
        metadatas = [[meta1, meta2, meta3]]

    Convert those to:
        documents = [doc1, doc2, doc3]
        metadatas = [meta1, meta2, meta3]
    """
    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []
    distances = results.get("distances") or []
    ids = results.get("ids") or []

    if documents and isinstance(documents[0], list):
        documents = documents[0]

    if metadatas and isinstance(metadatas[0], list):
        metadatas = metadatas[0]

    if distances and isinstance(distances[0], list):
        distances = distances[0]

    if ids and isinstance(ids[0], list):
        ids = ids[0]

    return documents, metadatas, distances, ids


# =========================================================
# OPENAI CLOUD GENERATION
# =========================================================
def generate_with_openai(system_instructions, user_prompt):
    if OpenAI is None:
        raise RuntimeError(
            "The 'openai' package is not installed. "
            "Add openai to requirements.txt."
        )

    api_key = get_config("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing from Streamlit Secrets."
        )

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": system_instructions,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    return response.choices[0].message.content or ""


# =========================================================
# LOCAL OLLAMA GENERATION
# =========================================================
def generate_with_ollama(system_instructions, user_prompt, selected_model):
    if ollama is None:
        raise RuntimeError(
            "The 'ollama' Python package is not installed. "
            "Add ollama to requirements.txt for local mode."
        )

    # The Python Ollama client can be directed to a remote/local endpoint.
    client = ollama.Client(host=OLLAMA_BASE_URL)

    response = client.chat(
        model=selected_model,
        messages=[
            {
                "role": "system",
                "content": system_instructions,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        options={"temperature": 0.1},
    )

    return response["message"]["content"]


# =========================================================
# UNIFIED LLM GENERATION
# =========================================================
def generate_answer(system_instructions, user_prompt, selected_model):
    if selected_provider == "openai":
        return generate_with_openai(
            system_instructions,
            user_prompt,
        )

    if selected_provider == "ollama":
        return generate_with_ollama(
            system_instructions,
            user_prompt,
            selected_model,
        )

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER='{selected_provider}'. "
        "Use 'ollama' or 'openai'."
    )


# =========================================================
# INITIALIZE DATABASE
# =========================================================
try:
    collection = initialize_chroma_connection()
except Exception as exc:
    st.error("❌ ChromaDB initialization failed.")
    st.exception(exc)
    st.stop()

# Build/validate the transcript-backed knowledge graph once per session.
try:
    knowledge_graph, graph_ok, graph_status = initialize_knowledge_graph(collection)
except Exception as exc:
    knowledge_graph, graph_ok, graph_status = None, False, str(exc)


# =========================================================
# SIDEBAR CONFIGURATION
# =========================================================
st.sidebar.header("🔧 Engine Settings")

provider_options = ["ollama", "openai"]
default_provider_index = (
    provider_options.index(LLM_PROVIDER)
    if LLM_PROVIDER in provider_options else 0
)

selected_provider = st.sidebar.radio(
    "LLM Provider",
    provider_options,
    index=default_provider_index,
    help="Choose Ollama for local generation or OpenAI for API-based generation.",
)

if selected_provider == "ollama":
    selected_model = st.sidebar.text_input(
        "Ollama Model",
        value=OLLAMA_MODEL,
        help="Use the exact model name shown by `ollama list`.",
    ).strip() or OLLAMA_MODEL

    st.sidebar.caption(
        f"🟢 Ollama endpoint: {OLLAMA_BASE_URL}"
    )

elif selected_provider == "openai":
    selected_model = OPENAI_MODEL
    st.sidebar.caption(
        f"☁️ OpenAI model: {OPENAI_MODEL}"
    )

else:
    st.sidebar.error(f"Unsupported LLM provider: {selected_provider}")
    st.stop()


top_k_chunks = st.sidebar.slider(
    "Context Sample Size (Top-K)",
    min_value=1,
    max_value=5,
    value=3,
    help="Number of relevant transcript chunks supplied to the LLM.",
)


# =========================================================
# YOUTUBE INGESTION
# =========================================================
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Quick-Ingest YouTube URL")

st.sidebar.caption(
    "Provide a new oncology/medical lecture link to append "
    "it to the vector memory."
)

new_video_url = st.sidebar.text_input(
    "Paste YouTube Link:",
    placeholder="https://youtube.com/watch?v=...",
    key="ingest_url",
)

if st.sidebar.button(
    "Process & Vectorize Document",
    use_container_width=True,
):
    if new_video_url:
        with st.sidebar.spinner(
            "⏳ Extracting transcript and building vector nodes..."
        ):
            success, feedback_message = process_and_index_url(
                new_video_url,
                collection,
            )

        if success:
            st.sidebar.success(feedback_message)
            # Chroma changed; invalidate the transcript-backed graph so the new
            # video is incorporated on the next rerun.
            try:
                graph_file = _graph_path()
                if os.path.exists(graph_file):
                    os.remove(graph_file)
            except Exception:
                pass
            st.cache_resource.clear()
        else:
            st.sidebar.error(feedback_message)

    else:
        st.sidebar.warning(
            "Please provide a valid YouTube URL."
        )


# =========================================================
# DATABASE METADATA
# =========================================================
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Local Database Metadata")

st.sidebar.metric(
    label="Total Vectors Indexed",
    value=f"{collection.count()} chunks",
)

if selected_provider == "ollama":
    st.sidebar.caption(
        "🔒 LLM mode: local Ollama. "
        "The deployed app must have network access to the configured Ollama endpoint."
    )
else:
    st.sidebar.caption(
        "☁️ LLM mode: cloud API. "
        "API credentials are read from Streamlit Secrets."
    )


# =========================================================
# INTERACTIVE KNOWLEDGE GRAPH
# =========================================================
st.markdown("---")
st.subheader("🕸️ Interactive Oncology Knowledge Graph")

if knowledge_graph is None or not graph_ok:
    st.warning(
        "The interactive knowledge graph is not available. "
        f"Status: {graph_status}"
    )
else:
    graph_tab, template_tab = st.tabs([
        "🔎 Evidence Graph",
        "🧩 Template Overview",
    ])

    with graph_tab:
        render_interactive_graph(
            st,
            knowledge_graph,
            collection=collection,
            max_nodes=120,
        )

    with template_tab:
        # Keep the already-working template renderer as the overview.
        try:
            from knowledge_graph.graph_viz import template_to_dot
            st.graphviz_chart(
                template_to_dot(knowledge_graph.template),
                use_container_width=True,
            )
        except Exception as exc:
            st.warning(f"Template overview could not be rendered: {exc}")


# =========================================================
# MAIN DASHBOARD
# =========================================================
st.title("🧬 Private Medical RAG Platform with Inline Citations")

st.markdown(
    "Retrieve cancer research transcript evidence and generate "
    "source-linked answers."
)

st.markdown("---")

user_query = st.text_input(
    "Enter clinical research query:",
    placeholder=(
        "Ask about immunotherapy targets, safety bounds, "
        "clinical timelines, etc..."
    ),
)


if user_query:
    with st.spinner(
        "⏳ Running semantic retrieval and evidence synthesis..."
    ):
        results = collection.query(
            query_texts=[user_query],
            n_results=top_k_chunks,
        )

        matched_chunks = []
        context_string_builder = []

        documents, metadatas, distances, ids = (
            normalize_query_results(results)
        )

        for idx, doc in enumerate(documents):
            metadata = {}

            if idx < len(metadatas):
                candidate_metadata = metadatas[idx]

                if isinstance(candidate_metadata, dict):
                    metadata = candidate_metadata

            v_title = metadata.get(
                "title",
                "Unknown Video",
            )

            v_link = metadata.get(
                "link",
                "#",
            )

            matched_chunks.append(
                {
                    "text": doc,
                    "title": v_title,
                    "link": v_link,
                }
            )

            context_string_builder.append(
                f"--- [Source #{idx + 1} | Video: {v_title}] ---\n"
                f"{doc}"
            )

        full_context_block = (
            "\n\n".join(context_string_builder)
            if context_string_builder
            else "No context loaded."
        )

        system_instructions = (
            "You are an expert medical AI assistant specialized in oncology. "
            "Synthesize coherent answers using exclusively the factual tokens "
            "in the provided text sources. "
            "CRITICAL CITATION DIRECTIVE: append the corresponding source "
            "reference index in source tags at the immediate end of every "
            "sentence detailing a data claim, for example [Source 1] or "
            "[Source 2]. Never construct factual statements without specifying "
            "where the datum originated. If the supplied sources do not contain "
            "the answer, explicitly say that the retrieved sources do not "
            "provide sufficient evidence."
        )

        user_prompt = (
            f"CONTEXT TEXT:\n\n{full_context_block}\n\n"
            f"QUESTION: {user_query}"
        )

        try:
            raw_answer = generate_answer(
                system_instructions,
                user_prompt,
                selected_model,
            )

            final_answer = inject_clickable_citations(
                raw_answer,
                matched_chunks,
            )

        except Exception as exc:
            if selected_provider == "ollama":
                final_answer = (
                    "❌ Ollama connection failed.\n\n"
                    f"Endpoint: `{OLLAMA_BASE_URL}`\n\n"
                    f"Model: `{selected_model}`\n\n"
                    f"Details: {exc}\n\n"
                    "For Streamlit Cloud, do not use "
                    "`localhost:11434` unless Ollama is running inside "
                    "the same cloud environment. Use a cloud LLM provider "
                    "or a securely hosted remote Ollama endpoint."
                )
            else:
                final_answer = (
                    "❌ Cloud LLM request failed.\n\n"
                    f"Model: `{OPENAI_MODEL}`\n\n"
                    f"Details: {exc}\n\n"
                    "Check OPENAI_API_KEY and OPENAI_MODEL in Streamlit Secrets."
                )

    # =====================================================
    # RENDER DASHBOARD
    # =====================================================
    col_gen, col_cite = st.columns([3, 1])

    with col_gen:
        st.subheader("🤖 Verified Sentence Synthesis")
        st.markdown(final_answer)

    with col_cite:
        st.subheader("📑 Document Sources")

        if not matched_chunks:
            st.warning(
                "No vectors intersected the semantic neighborhood bounds."
            )
        else:
            for i, chunk in enumerate(
                matched_chunks,
                start=1,
            ):
                with st.expander(
                    f"Source #{i}: {chunk['title'][:40]}..."
                ):
                    st.caption(
                        f'"{chunk["text"]}"'
                    )

                    st.markdown(
                        f"[🎥 Watch Original Video]({chunk['link']})"
                    )
