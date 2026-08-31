"""Smoke test for the template-aligned Cancer Awareness knowledge graph."""
from pathlib import Path
from config import SETTINGS
from knowledge_graph.graph_store import MedicalKnowledgeGraph

REQUIRED_MODULES = [
    "module_blood_biomarkers",
    "module_mammography",
    "module_prostate",
    "module_colorectal",
    "module_diagnostics",
]
REQUIRED_RELATIONS = {"ACHIEVED_THROUGH", "OFTEN_FOLLOWED_BY", "LEADS_TO"}

def main():
    graph = MedicalKnowledgeGraph(str(Path(__file__).resolve().parent / "knowledge_graph" / "data" / "medical_graph_v3_template.json"))
    ok, reason = graph.validate()
    assert ok, reason
    nodes = graph.template.get("nodes", {})
    edges = graph.template.get("edges", [])
    for m in REQUIRED_MODULES:
        assert m in nodes, f"Missing template module: {m}"
    rels={e.get("relation") for e in edges}
    missing=REQUIRED_RELATIONS-rels
    assert not missing, f"Missing template relationships: {missing}"
    print("Template GraphRAG smoke test: PASS")
    print(reason)

if __name__ == "__main__":
    main()
