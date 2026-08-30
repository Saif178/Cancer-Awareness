"""Configuration for the upgraded medical RAG pipeline.

Paths are resolved from the application directory so Streamlit Cloud does not
depend on its current working directory. On Streamlit Cloud, the generated
Chroma/BM25 index defaults to /tmp because the source checkout is ephemeral.
Set RAG_DB_PATH to override this behavior.
"""
from dataclasses import dataclass
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

def _is_streamlit_cloud() -> bool:
    return str(BASE_DIR).startswith("/mount/src/")

_DEFAULT_DB = (Path("/tmp") / "cancer_awareness_rag_v2") if _is_streamlit_cloud() else (BASE_DIR / "local_chroma_db_v2")

@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("RAG_DB_PATH", str(_DEFAULT_DB))
    input_path: str = os.getenv("RAG_INPUT_PATH", str(BASE_DIR / "cancer_treatment_transcripts.json"))
    collection_name: str = os.getenv("RAG_COLLECTION", "cancer_treatment_rag_v3")
    graph_path: str = os.getenv("RAG_GRAPH_PATH", str(Path(os.getenv("RAG_DB_PATH", str(_DEFAULT_DB))) / "medical_graph_v3.json"))
    graph_max_hops: int = int(os.getenv("RAG_GRAPH_MAX_HOPS", "2"))
    graph_max_paths: int = int(os.getenv("RAG_GRAPH_MAX_PATHS", "12"))
    embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
    reranker_model: str = os.getenv("RAG_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2")
    dense_k: int = int(os.getenv("RAG_DENSE_K", "12"))
    lexical_k: int = int(os.getenv("RAG_LEXICAL_K", "12"))
    candidate_k: int = int(os.getenv("RAG_CANDIDATE_K", "20"))
    final_k: int = int(os.getenv("RAG_FINAL_K", "6"))
    min_rerank_score: float = float(os.getenv("RAG_MIN_RERANK_SCORE", "0.10"))
    chunk_tokens: int = int(os.getenv("RAG_CHUNK_TOKENS", "450"))
    chunk_overlap_tokens: int = int(os.getenv("RAG_CHUNK_OVERLAP", "80"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama").lower()
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

SETTINGS = Settings()
