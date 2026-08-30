# RAG v2 Deployment Fixes

## Streamlit Cloud / GitHub fixes

- `streamlit_app_RAG_cloud_ready.py` no longer opens the legacy `cancer_treatment_rag` collection.
- The app uses the v2 `cancer_treatment_rag_v2` collection and `local_chroma_db_v2` path through `MedicalRAG`.
- A missing or invalid Chroma/BM25 index is automatically rebuilt from `cancer_treatment_transcripts.json`.
- Chroma and BM25 are validated for matching chunk counts and IDs before retrieval.
- YouTube ingestion updates both Chroma and BM25, preventing the hybrid retriever from using a stale lexical index.
- Existing video chunks are replaced during re-ingestion to avoid stale duplicate chunks.
- OpenAI credentials are read only when OpenAI is selected; Ollama does not require `OPENAI_API_KEY`.
- Streamlit Cloud secrets are supported without placing credentials in source code.
- Citations now use immutable `[E1]`, `[E2]`, ... evidence IDs and are resolved deterministically by the UI.
- The cloud-ready app consumes the `MedicalRAG.answer()` evidence payload instead of attempting to treat that result as a raw Chroma query response.
- The earlier CrossEncoder `activation_fn` constructor incompatibility is removed from `reranker.py`.
