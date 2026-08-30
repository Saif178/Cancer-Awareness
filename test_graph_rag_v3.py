"""Lightweight GraphRAG smoke test (does not require Chroma or an LLM)."""
import json
from pathlib import Path
from medical_chunker import build_records
from knowledge_graph.graph_store import MedicalKnowledgeGraph
from knowledge_graph.graph_retriever import GraphRetriever

root = Path(__file__).resolve().parent
data = json.loads((root / "cancer_treatment_transcripts.json").read_text(encoding="utf-8"))
records = []
for video in data:
    records.extend(build_records(video, 450, 80))
path = Path("/tmp/cancer_awareness_graph_smoke.json")
graph = MedicalKnowledgeGraph(str(path))
entities, relations = graph.build_from_records(records)
print(f"Built graph: {len(graph.nodes)} unique entities, {len(graph.edges)} relations")
retriever = GraphRetriever(graph, max_hops=2, max_paths=10)
for q in ["breast cancer symptoms", "breast cancer treatment and biomarkers", "colorectal cancer risk factors"]:
    results = retriever.search(q)
    print(f"\nQ: {q}\nSeeds: {retriever.link_entities(q)}\nPaths: {len(results)}")
    for r in results[:3]:
        print(" -", " -> ".join(r["path"]), "|", r["relation"], "|", r["metadata"]["chunk_id"])
