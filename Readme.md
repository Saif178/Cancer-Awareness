# Cancer Awareness — Upgraded RAG Package

This upgrade keeps the existing Streamlit/OpenAI/Ollama project but replaces the single-stage vector lookup with a production-oriented retrieve-and-rerank pipeline.

## Included
- Medical/transcript-aware semantic chunking
- Sentence-Transformer dense retrieval
- BM25 lexical retrieval
- Reciprocal Rank Fusion (hybrid retrieval)
- Cross-Encoder reranking
- Evidence levels: DIRECT / SYNTHESIZED / INSUFFICIENT
- Immutable evidence IDs (`E1`, `E2`, ...) for reliable citations
- OpenAI Responses API + Ollama adapters
- Retrieval evaluation: Recall@K, MRR@K, nDCG@K
- Optional reranker fine-tuning script
- Rebuildable Chroma + BM25 index

## Important
The existing `local_chroma_db` was built with the old embedding model and chunking strategy. **Do not reuse it for the v2 index.** Build `local_chroma_db_v2` with `ingest_v2.py`.

## Install
```bash
pip install -r requirements_upgrade.txt
```

## Build the new index
```bash
python ingest_v2.py --input cancer_treatment_transcripts.json
```

## Test retrieval + generation
```bash
# Ollama
set LLM_PROVIDER=ollama
set OLLAMA_MODEL=llama3.1
python run_upgrade.py

# OpenAI
set LLM_PROVIDER=openai
set OPENAI_API_KEY=YOUR_KEY
set OPENAI_MODEL=gpt-4o-mini
python run_upgrade.py
```

Linux/macOS users should use `export` instead of `set`. Streamlit users can place these values in `.streamlit/secrets.toml`.

## Integrate into Streamlit
Replace the old `collection.query(...)` call with:
```python
from rag_engine import MedicalRAG
rag = MedicalRAG()
result = rag.answer(user_query, provider=LLM_PROVIDER, model=selected_model)
answer = result["answer"]
evidence = result["evidence"]
```
Render citations from `evidence` rather than allowing the LLM to invent source numbers.

## Evaluate
Create `evaluation/gold_questions.json` with real questions and relevant chunk IDs, then:
```bash
python evaluate_rag.py --gold evaluation/gold_questions.json
```

## Optional reranker training
Create JSONL rows with `query`, `positive`, and `negative` text passages. Then:
```bash
python train_reranker.py --data evaluation/reranker_train.jsonl --output models/medical_reranker
```
Set `RAG_RERANKER_MODEL=./models/medical_reranker` afterwards.

## Medical safety
This project is an evidence retrieval/education system, not a diagnostic or treatment decision system. The generation policy intentionally refuses unsupported medical claims and avoids personalized clinical recommendations.

## Streamlit Cloud RAG v2 bootstrap

`streamlit_app_RAG_cloud_ready.py` and `streamlit_app_RAG_v2.py` now call `MedicalRAG`, whose `HybridRetriever` validates Chroma and BM25 before opening the collection. If `cancer_treatment_rag_v2` is missing, empty, corrupt, or out of sync with `bm25.pkl`, the application rebuilds both indexes automatically from `cancer_treatment_transcripts.json`.

On Streamlit Cloud the generated index defaults to `/tmp/cancer_awareness_rag_v2` so the app does not depend on a writable Git checkout. The index is ephemeral and is rebuilt after a cold restart when needed.

OpenAI credentials are read only when OpenAI is selected. Ollama mode does not require `OPENAI_API_KEY`.


# GraphRAG v3

This version augments the v2 hybrid RAG with a provenance-preserving oncology knowledge graph. The graph is built automatically from the same medical transcript chunks used by Chroma and BM25. It performs conservative ontology-based entity/relation extraction and bounded 1-3 hop retrieval. Every graph relation stores its originating transcript `chunk_id`, video metadata, source sentence, and extraction confidence.

## GraphRAG architecture

```text
Dense + BM25 -> RRF -> Cross-Encoder
                    +
             Entity linking
                    -> 1-3 hop graph traversal
                    -> source-chunk provenance
                    +
              Evidence fusion
                    -> OpenAI / Ollama
```

The graph is stored as `medical_graph_v3.json` beside the RAG index, so Streamlit Cloud can rebuild it automatically from `cancer_treatment_transcripts.json`. No Neo4j server is required for the bundled deployment.

## GraphRAG files

- `knowledge_graph/schema.py` — constrained oncology ontology
- `knowledge_graph/entity_relation_extractor.py` — dependency-light entity/relation extraction
- `knowledge_graph/graph_store.py` — persistent graph and bounded path traversal
- `knowledge_graph/graph_retriever.py` — query entity linking and multi-hop retrieval
- `knowledge_graph/graph_viz.py` — Streamlit DOT graph rendering

## Cloud deployment

Use `streamlit_app_RAG_cloud_ready.py` as the Streamlit entrypoint. On first startup, the application validates Chroma, BM25, and the graph. If any component is missing or out of sync, it rebuilds the synchronized index from the bundled transcript JSON.

The UI includes graph-hop control, graph entity/relation metrics, graph visualization, graph-path provenance, and the existing document evidence panel. OpenAI is initialized only when OpenAI is selected; Ollama does not require an OpenAI key.
