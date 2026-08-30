# GraphRAG v3

## What changed

GraphRAG v3 augments the working v2 hybrid RAG with a provenance-preserving oncology knowledge graph. It does **not** replace Chroma, BM25, or the Cross-Encoder.

### Retrieval pipeline

```text
Question
  ├── Dense retrieval ─┐
  ├── BM25 retrieval ──┼─> RRF candidates ─> Cross-Encoder
  └── Entity linking ─> 1-3 hop graph paths ─> source chunks
                                      │
                                      └────> evidence fusion
                                                 │
                                           OpenAI / Ollama
                                                 │
                                      answer + deterministic [E1] citations
```

## Oncology graph

The bundled ontology recognizes cancer types, treatments, drugs, genes, biomarkers, symptoms, risk factors, diagnostics, and anatomy. Relations are constrained to a small medical vocabulary such as `TREATED_BY`, `HAS_SYMPTOM`, `HAS_RISK_FACTOR`, `DIAGNOSED_BY`, `TARGETS`, `HAS_SIDE_EFFECT`, `BIOMARKER_FOR`, and `AFFECTS`.

The extractor is intentionally dependency-light and conservative. It creates a graph relationship only when recognized medical entities and a relation trigger occur in the same transcript sentence. This avoids requiring an API key to build the graph.

## Provenance

Every graph edge stores:

- source entity and target entity
- relation type
- original transcript sentence
- `chunk_id`
- `video_id`
- video title and URL
- extraction confidence

The LLM never treats a graph edge as independent medical authority. Graph paths are mapped back to transcript chunks before answer generation.

## Multi-hop retrieval

Questions containing recognized entities are linked to graph nodes. The graph retriever performs bounded traversal (default: 2 hops) and returns the supporting source sentence/chunk for each path. Streamlit lets the user select 1-3 hops.

## Storage

The graph is stored as `medical_graph_v3.json` next to the runtime RAG index. No Neo4j server is required. This is intentional for Streamlit Community Cloud portability. A Neo4j adapter can be added later if the graph grows beyond the bundled corpus.

## Automatic bootstrap

`ingest_v2.py` now builds:

1. medical-aware chunks
2. Chroma collection `cancer_treatment_rag_v3`
3. synchronized BM25 index
4. oncology knowledge graph

`HybridRetriever(auto_build=True)` validates all three artifacts and rebuilds from `cancer_treatment_transcripts.json` if any is missing, corrupt, or out of sync.

## Manual build

```bash
python ingest_v2.py --input cancer_treatment_transcripts.json
```

## Streamlit Cloud

Deploy `streamlit_app_RAG_cloud_ready.py` as the main file. On a cold start the app may spend additional time downloading the embedding/reranker models and building the local `/tmp` index. This is expected.

The app does not require OpenAI credentials when Ollama is selected. OpenAI is initialized only after the OpenAI provider is selected.

## Graph visualization

The Streamlit UI shows a DOT-based graph for paths retrieved for the current query, plus an expandable provenance panel linking every graph relation to the original YouTube source.
