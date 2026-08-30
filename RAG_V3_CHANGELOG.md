# GraphRAG v3 Change Log

## Added
- Constrained oncology ontology and entity types.
- Provenance-preserving relation extraction from transcript chunks.
- Local persistent medical knowledge graph (`medical_graph_v3.json`).
- Query entity linking and bounded 1-3 hop graph traversal.
- Graph evidence mapped back to original transcript chunk IDs.
- Graph paths supplied to the same evidence/citation policy used by the RAG answerer.
- Streamlit graph visualization and provenance panel.
- Automatic validation/rebuild of Chroma + BM25 + graph as one synchronized index.
- YouTube ingestion now updates Chroma, BM25, and graph together.
- OpenAI remains provider-isolated; Ollama does not require an OpenAI key.

## Compatibility
- The existing `MedicalRAG`, hybrid retrieval, Cross-Encoder reranking, deterministic evidence IDs, and OpenAI/Ollama adapters are retained.
- No Neo4j server is required. The graph store is dependency-light for Streamlit Cloud deployment.
