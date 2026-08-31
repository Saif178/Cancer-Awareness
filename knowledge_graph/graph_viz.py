"""Template-style Graphviz renderers for the Cancer Awareness GraphRAG."""
from html import escape
import re
from .template_graph import COLOR_HEX

def _q(s):
    return str(s).replace("\\","\\\\").replace('"','\\"').replace("\n"," ")

def _node_id(s):
    return "n_" + "".join(ch if ch.isalnum() else "_" for ch in str(s))

def to_dot(graph_evidence, max_edges=20):
    """Compact query-specific evidence graph."""
    lines=[
        "digraph G {",
        'graph [rankdir=LR, bgcolor="white", overlap=false, splines=true, nodesep=0.5, ranksep=0.8];',
        'node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10, fillcolor="white", color="#777777"];',
        'edge [fontname="Arial", fontsize=8, color="#666666", arrowsize=0.7];'
    ]
    seen=set()
    for item in graph_evidence[:max_edges]:
        a,b=item["source"],item["target"]
        na,nb=_node_id(a),_node_id(b)
        if a not in seen:
            lines.append(f'{na} [label="{_q(a)}"];'); seen.add(a)
        if b not in seen:
            lines.append(f'{nb} [label="{_q(b)}"];'); seen.add(b)
        lines.append(f'{na} -> {nb} [label="{_q(item["relation"].replace("_"," ").lower())}"];')
    lines.append("}")
    return "\n".join(lines)

def template_to_dot(template_graph, show_entity_details=False):
    """Render the supplied five-module template reliably in Streamlit.

    Uses the standard Graphviz `dot` layout rather than fixed `neato` coordinates.
    The template structure is deterministic, while transcript evidence remains
    available in the underlying graph/provenance data.
    """
    tg = template_graph or {}
    nodes = tg.get("nodes") or {}
    sources = tg.get("sources") or []

    def q(value):
        return (str(value).replace("\\", "\\\\").replace('"', '\\"')
                .replace("\r", "").replace("\n", "\\n"))

    def nid(value):
        return "n_" + re.sub(r"[^A-Za-z0-9_]+", "_", str(value)).strip("_")

    modules = [
        ("module_blood_biomarkers", "Blood Tests & Biomarkers", "E1", "#2E7D32",
         ["Sample Types: Blood, Urine, Saliva", "Key Features: Biomarkers, rapid/non-invasive potential", "Benefits: Accessible, efficient, early detection"]),
        ("module_mammography", "Mammography for Breast Cancer", "E2", "#1565C0",
         ["Method: Mammography (2-D), 3-D/tomosynthesis", "Detects: Microcalcifications, small tumors, early signs", "Benefits: Higher detection, useful for dense tissue"]),
        ("module_prostate", "Prostate Cancer Detection", "E3", "#512DA8",
         ["Who: Age/risk-based screening", "Methods: PSA, digital rectal exam, MRI/imaging", "Benefits: Early detection and treatment planning"]),
        ("module_colorectal", "Colorectal Cancer Screening", "E4", "#EF6C00",
         ["Methods: Colonoscopy, FIT, DNA stool tests, CT colonography", "Who & When: Age/risk-based screening", "Benefits: Detects polyps and early cancer"]),
    ]
    diagnostics = ("module_diagnostics", "General Diagnostic Tests", "E5", "#00838F",
                   ["Imaging: Ultrasound, X-ray, CT, MRI, PET", "Laboratory: Blood, urine, tumor markers", "Tissue: Biopsy, fine needle aspiration", "Purpose: Confirm diagnosis, type and stage", "Outcome: Treatment planning and monitoring"])

    # Use ordinary DOT layout; this avoids blank output caused by neato/pin/pos.
    lines = [
        "digraph CancerAwarenessTemplate {",
        'graph [rankdir=TB, bgcolor="white", pad=0.35, nodesep=0.45, ranksep=0.75, splines=ortho];',
        'node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10, margin="0.10,0.06", fillcolor="white"];',
        'edge [fontname="Arial", fontsize=8, arrowsize=0.6, color="#777777"];',
        'title [shape=plaintext, label="CANCER EARLY DETECTION KNOWLEDGE GRAPH\\nFrom Screening to Better Outcomes", fontsize=18, fontname="Arial"];',
        'early_detection_of_cancer [shape=ellipse, style="filled", fillcolor="#F4EEFF", color="#512DA8", penwidth=2.4, fontcolor="#2F1B69", fontsize=13, label="EARLY DETECTION OF CANCER\\n\\nImproves treatment outcomes, survival rates\\nand quality of life"];',
        'better_outcomes [shape=box, style="rounded,filled", fillcolor="#EEF8EE", color="#2E7D32", penwidth=2.0, fontcolor="#1B5E20", fontsize=12, label="BETTER OUTCOMES\\n\\nEarly treatment\\nHigher survival rates\\nImproved quality of life\\nReduced healthcare costs"];',
    ]

    # Keep title above the central node without affecting the template flow.
    lines.append('title -> early_detection_of_cancer [style=invis];')

    for mid, fallback, eid, color, bullets in modules:
        data = nodes.get(mid) or {}
        label = data.get("label") or fallback
        lines.append(f'{nid(mid)} [color="{color}", fontcolor="{color}", penwidth=2, label="{q(label)} [{eid}]\\n{q("\\n".join(bullets))}"];')

    data = nodes.get(diagnostics[0]) or {}
    label = data.get("label") or diagnostics[1]
    lines.append(f'{nid(diagnostics[0])} [color="{diagnostics[3]}", fontcolor="{diagnostics[3]}", penwidth=2, label="{q(label)} [{diagnostics[2]}]\\n{q("\\n".join(diagnostics[4]))}"];')

    # Four screening/detection modules feed the central early-detection node.
    for mid, _, _, color, _ in modules:
        lines.append(f'{nid(mid)} -> early_detection_of_cancer [label="achieved through", color="{color}", fontcolor="{color}"];')

    # Diagnostics follow early detection in the template.
    lines.append(f'early_detection_of_cancer -> {nid(diagnostics[0])} [label="often followed by", color="#512DA8", fontcolor="#512DA8"];')
    lines.append(f'{nid(diagnostics[0])} -> better_outcomes [label="leads to", color="#2E7D32", fontcolor="#2E7D32", penwidth=1.8];')

    # Keep source footer compact and safe.
    source_lines = []
    for src in sources:
        if isinstance(src, dict) and src.get("id") and src.get("title"):
            source_lines.append(f'[{src["id"]}] {src["title"]}')
    if not source_lines:
        source_lines = [
            "[E1] Detecting cancer in real-time with machine learning",
            "[E2] Mammography for breast cancer",
            "[E3] Prostate cancer detection",
            "[E4] Colorectal cancer screening",
            "[E5] Cancer diagnosis tests",
            "[E6] New nanotech to detect cancer early",
        ]
    lines.append(f'evidence_sources [shape=box, style="rounded,filled", color="#999999", fontcolor="#333333", fontsize=8, label="EVIDENCE SOURCES\\n{q(chr(10).join(source_lines))}"];')
    lines.append('better_outcomes -> evidence_sources [style=invis];')

    lines.append("}")
    return "\n".join(lines)
