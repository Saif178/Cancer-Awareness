"""Build the Cancer Awareness knowledge graph in the supplied template structure.

Usage:
    python knowledge_graph/knowledge_graph_builder.py

Outputs:
    local_chroma_db_v2/medical_graph_v3.json
    local_chroma_db_v2/cancer_early_detection_template.dot
    local_chroma_db_v2/cancer_early_detection_template.png  (when Graphviz is installed)

The graph has two layers:
1. Evidence layer: transcript-backed entities/relations with provenance.
2. Template layer: the user's five-module visual scaffold and relationship labels.
Template-only edges are presentation metadata and are NOT used as medical evidence.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from config import SETTINGS
from medical_chunker import build_records
from .graph_store import MedicalKnowledgeGraph
from .graph_viz import template_to_dot

def load_records(input_path):
    data=json.loads(Path(input_path).read_text(encoding="utf-8"))
    if not isinstance(data,list):
        raise ValueError("Transcript dataset must be a JSON list.")
    records=[]
    for video in data:
        records.extend(build_records(video, SETTINGS.chunk_tokens, SETTINGS.chunk_overlap_tokens))
    return records

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input", default=SETTINGS.input_path)
    parser.add_argument("--output", default=SETTINGS.graph_path)
    parser.add_argument("--png", default=None)
    args=parser.parse_args()

    records=load_records(args.input)
    graph=MedicalKnowledgeGraph(args.output)
    entities, relations=graph.build_from_records(records)

    dot_path=Path(args.output).with_name("cancer_early_detection_template.dot")
    dot_path.write_text(template_to_dot(graph.template), encoding="utf-8")

    png_path=Path(args.png) if args.png else Path(args.output).with_name("cancer_early_detection_template.png")
    try:
        subprocess.run(
            ["dot","-Tpng",str(dot_path),"-o",str(png_path)],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        rendered=f"PNG: {png_path}"
    except (FileNotFoundError, subprocess.CalledProcessError):
        rendered="PNG not rendered (Graphviz 'dot' executable is unavailable); DOT was created."

    print(f"Input videos: {len({r['metadata'].get('video_id') for r in records})}")
    print(f"Chunks: {len(records)}")
    print(f"Evidence entities: {len(graph.nodes)}")
    print(f"Evidence relations: {len(graph.edges)}")
    print(f"Template nodes: {len(graph.template.get('nodes',{}))}")
    print(f"Template edges: {len(graph.template.get('edges',[]))}")
    print(f"Graph JSON: {args.output}")
    print(f"DOT: {dot_path}")
    print(rendered)

if __name__=="__main__":
    main()
