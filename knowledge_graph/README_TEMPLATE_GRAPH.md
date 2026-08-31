# Cancer Awareness GraphRAG v3 — Template-Aligned Knowledge Graph

This version reorganizes the oncology knowledge graph around the user-supplied
visual template:

1. Blood Tests & Biomarkers
2. Mammography for Breast Cancer
3. Prostate Cancer Detection
4. Colorectal Cancer Screening
5. General Diagnostic Tests
6. Better Outcomes

The graph has two layers:

- **Evidence layer:** entities and relations extracted from transcript chunks.
  Every evidence relation has `chunk_id`, video ID, title, URL, sentence and
  confidence.
- **Template layer:** a deterministic visual/semantic scaffold matching the
  supplied infographic. Template-only edges are not used as medical evidence.

## Build

From the project root:

```bash
python knowledge_graph/knowledge_graph_builder.py
```

Outputs:

- `local_chroma_db_v2/medical_graph_v3.json`
- `local_chroma_db_v2/cancer_early_detection_template.dot`
- `local_chroma_db_v2/cancer_early_detection_template.png` when Graphviz is installed

The regular `ingest_v2.py` pipeline also rebuilds the template layer whenever
the Chroma/BM25 index is rebuilt.

## Streamlit

The Streamlit application renders:

- the full template-aligned knowledge graph
- question-specific multi-hop graph paths
- provenance for graph relationships
- the six evidence-source cards

The graph is a retrieval aid. Final medical answers must still cite the
underlying transcript evidence.
