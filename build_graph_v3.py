"""Standalone GraphRAG v3 graph builder from the bundled transcript dataset."""
import argparse
import json
from pathlib import Path
from medical_chunker import build_records
from knowledge_graph.graph_store import MedicalKnowledgeGraph
from config import SETTINGS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=SETTINGS.input_path)
    parser.add_argument("--output", default=SETTINGS.graph_path)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    records = []
    for video in data:
        records.extend(build_records(video, SETTINGS.chunk_tokens, SETTINGS.chunk_overlap_tokens))
    graph = MedicalKnowledgeGraph(args.output)
    entities, relations = graph.build_from_records(records)
    print(f"Graph written to {args.output}")
    print(f"Recognized entity occurrences: {entities}")
    print(f"Relations: {relations}")
    print(f"Unique entities: {len(graph.nodes)}")


if __name__ == "__main__":
    main()
