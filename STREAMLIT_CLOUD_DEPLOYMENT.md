# Streamlit Cloud deployment — RAG v2

## Main file

Use `streamlit_app_RAG_cloud_ready.py` (or `streamlit_app_RAG_v2.py`).

## Automatic index bootstrap

The app no longer assumes that `cancer_treatment_rag_v2` already exists. On startup it:

1. Checks the configured Chroma database and collection.
2. Checks `bm25.pkl`.
3. Verifies Chroma/BM25 chunk IDs match.
4. If anything is missing or inconsistent, rebuilds both indexes from `cancer_treatment_transcripts.json`.
5. Validates the rebuilt index before constructing the retriever.

On Streamlit Cloud the default generated index is under `/tmp/cancer_awareness_rag_v2`; it is ephemeral and can be rebuilt automatically after a restart. Set `RAG_DB_PATH` only if you have a persistent external/local storage strategy.

## Secrets

For OpenAI mode, configure in Streamlit Cloud Secrets:

```toml
LLM_PROVIDER = "openai"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = "..."
```

Ollama mode does not read `OPENAI_API_KEY`. It requires an Ollama endpoint reachable from the Streamlit Cloud runtime.

Never commit `.streamlit/secrets.toml`.

## GraphRAG v3 deployment

Use `streamlit_app_RAG_cloud_ready.py` as the main entrypoint. GraphRAG v3 builds and validates three synchronized artifacts at startup: Chroma collection `cancer_treatment_rag_v3`, `bm25.pkl`, and `medical_graph_v3.json`. If any artifact is absent or inconsistent, it rebuilds them from `cancer_treatment_transcripts.json`.

The graph is intentionally stored as a local JSON adjacency structure so no Neo4j service is required. The default Streamlit Cloud runtime path is `/tmp/cancer_awareness_rag_v2`; it is ephemeral and may be rebuilt after a cold start.

The UI includes graph-hop selection, graph statistics, multi-hop graph visualization, and provenance links back to the original transcript chunks.
