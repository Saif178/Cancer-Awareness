# RAG Evaluation

Populate `gold_questions.json` with queries and the chunk IDs that should be retrieved.

Example:
```json
[{"query":"What symptoms are discussed for pancreatic cancer?","relevant_ids":["S3CegUhEd7Y_chunk_0000"]}]
```

Run:
```bash
python evaluate_rag.py --gold evaluation/gold_questions.json
```

The evaluator reports Recall@K, MRR@K and nDCG@K for the hybrid first stage and the reranked stage. These metrics measure retrieval quality; they should be complemented with manual/LLM evaluation of faithfulness, citation correctness and answer relevance.
