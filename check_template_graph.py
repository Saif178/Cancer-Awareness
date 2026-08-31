from knowledge_graph.graph_viz import template_to_dot
from knowledge_graph.template_graph import build_template_layer

try:
    import json
    from pathlib import Path
    p=Path("knowledge_graph/data/medical_graph_v3_template.json")
    if p.exists():
        data=json.loads(p.read_text(encoding="utf-8")); tg=data.get("template", data)
        print("template nodes:", len(tg.get("nodes",{})))
        print("template edges:", len(tg.get("edges",[])))
        dot=template_to_dot(tg)
        Path("template_debug.dot").write_text(dot, encoding="utf-8")
        print("DOT written to template_debug.dot")
    else:
        print("No persisted template graph found; it will be rebuilt from Chroma at startup.")
except Exception as e:
    print("Template diagnostic failed:", e)
