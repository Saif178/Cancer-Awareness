"""Streamlit Cloud entrypoint for Cancer Awareness GraphRAG v3.

Preserves the existing RAG/YouTube workspace while adding ontology extraction,
multi-hop graph retrieval, provenance, and an interactive graph view.
"""
from __future__ import annotations

import os
import re
import streamlit as st

from config import SETTINGS
from rag_engine import MedicalRAG
from medical_chunker import build_records
from ingest_v2 import add_records
from knowledge_graph.graph_viz import to_dot, template_to_dot

try:
    import yt_dlp
except ImportError:
    yt_dlp = None
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
except ImportError:
    YouTubeTranscriptApi = None
    TranscriptsDisabled = NoTranscriptFound = Exception

try:
    import ollama
except ImportError:
    ollama = None
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(page_title="Medical Workspace GraphRAG Pro", page_icon="🧬", layout="wide")


def get_config(name, default=None):
    try:
        value = st.secrets.get(name)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return os.getenv(name, default)


DEFAULT_PROVIDER = str(get_config("LLM_PROVIDER", SETTINGS.llm_provider)).lower().strip()
OLLAMA_MODEL = str(get_config("OLLAMA_MODEL", SETTINGS.ollama_model)).strip()
OLLAMA_BASE_URL = str(get_config("OLLAMA_BASE_URL", SETTINGS.ollama_base_url)).rstrip("/")
OPENAI_MODEL = str(get_config("OPENAI_MODEL", SETTINGS.openai_model)).strip()


@st.cache_resource(show_spinner=False)
def get_rag():
    return MedicalRAG()


try:
    rag = get_rag()
    rag_error = None
except Exception as exc:
    rag = None
    rag_error = exc

st.title("🧬 Private Medical GraphRAG Platform with Inline Citations")
st.caption("Dense + BM25 retrieval → Cross-Encoder reranking → oncology knowledge graph → evidence validation → OpenAI/Ollama")

if rag_error:
    st.error(f"RAG initialization failed: {rag_error}")
    st.info("The application automatically rebuilds Chroma, BM25, and the knowledge graph from the bundled transcript dataset when an index is missing or invalid.")
    st.stop()

with st.sidebar:
    st.header("⚙️ RAG Configuration")
    provider = st.radio("LLM Provider", ["ollama", "openai"], index=0 if DEFAULT_PROVIDER == "ollama" else 1)
    selected_model = st.text_input("Model", OLLAMA_MODEL if provider == "ollama" else OPENAI_MODEL)
    graph_hops = st.slider("Graph hops", 1, 3, SETTINGS.graph_max_hops)
    st.caption(f"Index: {rag.index_status}")
    stats = rag.graph_stats
    c1, c2 = st.columns(2)
    c1.metric("Chunks", rag.retriever.collection.count())
    c2.metric("Graph entities", stats["entities"])
    st.metric("Graph relations", stats["relations"])

    if provider == "openai":
        st.caption("☁️ OpenAI credentials are read only when OpenAI is selected.")
    else:
        st.caption("🦙 Ollama mode does not require OPENAI_API_KEY.")


def generate_with_openai(system_instructions, user_prompt):
    if OpenAI is None:
        raise RuntimeError("OpenAI package is not installed.")
    key = get_config("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured in Streamlit Secrets.")
    client = OpenAI(api_key=key, timeout=180, max_retries=2)
    if hasattr(client, "responses"):
        response = client.responses.create(model=selected_model, instructions=system_instructions, input=user_prompt)
        if getattr(response, "output_text", None):
            return response.output_text.strip()
    response = client.chat.completions.create(
        model=selected_model, temperature=0.1,
        messages=[{"role": "system", "content": system_instructions}, {"role": "user", "content": user_prompt}],
    )
    return (response.choices[0].message.content or "").strip()


def generate_with_ollama(system_instructions, user_prompt):
    if ollama is None:
        raise RuntimeError("Ollama package is not installed.")
    client = ollama.Client(host=OLLAMA_BASE_URL)
    response = client.chat(model=selected_model, messages=[
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_prompt},
    ], options={"temperature": 0.1})
    return response["message"]["content"].strip()


def test_llm():
    system = "You are a concise test assistant. Return only: LLM connection OK."
    user = "Test the configured model connection."
    return generate_with_openai(system, user) if provider == "openai" else generate_with_ollama(system, user)


if st.sidebar.button("🧪 Test Selected LLM"):
    try:
        st.sidebar.success(test_llm())
    except Exception as exc:
        st.sidebar.error(str(exc))

st.markdown("---")

# --------------------------- YouTube ingestion ---------------------------
st.subheader("📥 Add a YouTube medical source")
with st.expander("Index a new transcript", expanded=False):
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    if st.button("Add to GraphRAG index"):
        if not url.strip():
            st.warning("Enter a YouTube URL first.")
        elif yt_dlp is None or YouTubeTranscriptApi is None:
            st.error("YouTube ingestion dependencies are not installed.")
        else:
            try:
                with st.spinner("Fetching transcript, chunking, and updating Chroma + BM25 + knowledge graph..."):
                    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                        info = ydl.extract_info(url.strip(), download=False)
                    video_id = info.get("id")
                    title = info.get("title", "Untitled Video")
                    if not video_id:
                        raise RuntimeError("Could not determine the YouTube video ID.")
                    transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
                    full_text = re.sub(r"\s+", " ", " ".join(x.text for x in transcript)).strip()
                    if not full_text:
                        raise RuntimeError("Transcript is empty.")
                    video = {"video_id": video_id, "title": title, "link": f"https://www.youtube.com/watch?v={video_id}", "transcript": full_text}
                    records = build_records(video, SETTINGS.chunk_tokens, SETTINGS.chunk_overlap_tokens)
                    count = add_records(records)
                st.success(f"Indexed {count} chunks from '{title}'. The graph was rebuilt with provenance to the new transcript chunks.")
                st.cache_resource.clear()
                st.rerun()
            except (TranscriptsDisabled, NoTranscriptFound):
                st.error("English captions/transcript are missing for this video.")
            except Exception as exc:
                st.error(f"Ingestion failed: {exc}")

# --------------------------- Query --------------------------------------
user_query = st.text_input(
    "Enter clinical research query:",
    placeholder="Ask about treatments, biomarkers, symptoms, diagnostics, or relationships between them...",
)

if user_query:
    with st.spinner("⏳ Running hybrid retrieval, graph traversal, reranking, and evidence synthesis..."):
        try:
            # Update hop setting for this query without mutating global config.
            rag.graph_retriever.max_hops = graph_hops
            result = rag.answer(user_query, provider=provider, model=selected_model)
            answer = result["answer"]
            evidence = result.get("evidence", [])
            graph_evidence = result.get("graph_evidence", [])

            col_main, col_sources = st.columns([3, 1])
            with col_main:
                st.subheader("🤖 Verified Sentence Synthesis")
                st.markdown(answer)
                badge = result.get("evidence_level", "UNKNOWN")
                st.info(f"Evidence level: **{badge}** · confidence: **{result.get('confidence', 0):.2f}**")

                st.subheader("🕸️ Knowledge Graph — Template View")
                # The full ontology follows the supplied five-module template.
                st.graphviz_chart(
                    template_to_dot(rag.graph.template),
                    use_container_width=True,
                )
                with st.expander("Question-specific graph paths and provenance", expanded=bool(graph_evidence)):
                    if graph_evidence:
                        st.graphviz_chart(to_dot(graph_evidence), use_container_width=True)
                        for p in graph_evidence:
                            path = " → ".join(p["path"])
                            st.markdown(f"**{path}**")
                            st.caption(
                                f"{p['relation']} · chunk `{p['chunk_id']}` · {p['title']}"
                            )
                            if p.get("link"):
                                st.markdown(f"[🎥 Original source]({p['link']})")
                    else:
                        st.caption("No transcript-backed oncology entity path was found for this question.")
                with st.expander("Template evidence sources", expanded=False):
                    for s in rag.graph.template.get("sources", []):
                        support=s.get("support", {})
                        st.markdown(f"**[{s['id']}] {s['title']}**")
                        if support.get("link"):
                            st.markdown(f"[🎥 Source video]({support['link']})")

            with col_sources:
                st.subheader("📑 Evidence")
                if not evidence:
                    st.warning("No sufficiently relevant evidence was retrieved.")
                for e in evidence:
                    m = e.get("metadata", {})
                    label = f"[{e['evidence_id']}] {e.get('title', 'Source')[:42]}"
                    with st.expander(label):
                        st.caption(e["text"])
                        if e.get("rerank_score") is not None:
                            st.caption(f"Rerank score: {float(e['rerank_score']):.4f}")
                        if m.get("graph_relation"):
                            st.caption(f"Graph: {m.get('graph_source')} —{m.get('graph_relation')}→ {m.get('graph_target')}")
                        if e.get("link"):
                            st.markdown(f"[🎥 Watch Original Video]({e['link']})")
        except Exception as exc:
            st.error(f"RAG query failed: {exc}")
            with st.expander("Technical diagnostic details"):
                st.exception(exc)
