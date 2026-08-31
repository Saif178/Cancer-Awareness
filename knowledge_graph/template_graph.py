"""Template-aligned oncology knowledge graph.

The visual organization follows the user-supplied template:
Early Detection of Cancer at the center, five method modules around it,
a General Diagnostic Tests bridge, and Better Outcomes at the end.

Important: template scaffold nodes/edges are presentation metadata. Only
transcript-backed `edges` are used as medical evidence by GraphRetriever.
"""
from __future__ import annotations
import re
from collections import defaultdict
from pathlib import Path
from .schema import TEMPLATE_MODULES

CENTRAL = {
    "id": "early_detection_of_cancer",
    "label": "Early Detection of Cancer",
    "type": "CENTRAL",
    "description": "Improves treatment outcomes, survival rates and quality of life",
    "color": "purple",
}

OUTCOME = {
    "id": "better_outcomes",
    "label": "Better Outcomes",
    "type": "OUTCOME",
    "description": "Early treatment, higher survival rates, improved quality of life",
    "color": "green",
}

# Exact high-level relationship wording from the template.
MODULE_RELATIONS = {
    "blood_biomarkers": "ACHIEVED_THROUGH",
    "mammography": "ACHIEVED_THROUGH",
    "prostate": "ACHIEVED_THROUGH",
    "colorectal": "ACHIEVED_THROUGH",
    "diagnostics": "OFTEN_FOLLOWED_BY",
}

COLOR_HEX = {
    "green": "#2E7D32",
    "blue": "#1565C0",
    "purple": "#512DA8",
    "orange": "#EF6C00",
    "teal": "#00838F",
}

def _norm(s):
    return re.sub(r"\s+", " ", str(s).lower().strip())

def _text_contains(text, term):
    return bool(re.search(r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)", text.lower()))

def _supporting_chunks(records, terms, limit=6):
    out=[]
    for r in records:
        text = r.get("text","")
        if any(_text_contains(text, t) for t in terms):
            out.append({
                "chunk_id": r["id"],
                "video_id": r.get("metadata",{}).get("video_id",""),
                "title": r.get("metadata",{}).get("title",""),
                "link": r.get("metadata",{}).get("link",""),
            })
            if len(out)>=limit:
                break
    return out

def build_template_layer(records, extracted_edges=None):
    """Return a deterministic visual/semantic scaffold aligned to the template.

    `records` are transcript chunks. `extracted_edges` are evidence-backed
    relations. The returned template edges may have supporting_chunks, but
    are never treated as authoritative evidence unless a transcript supports
    the relationship.
    """
    extracted_edges = extracted_edges or []
    nodes = {
        CENTRAL["id"]: dict(CENTRAL),
        OUTCOME["id"]: dict(OUTCOME),
    }
    edges=[]
    sources=[]

    # Central -> outcome is the visual end-state.
    edges.append({
        "source": CENTRAL["id"], "relation": "LEADS_TO",
        "target": OUTCOME["id"], "template": True,
        "supporting_chunks": _supporting_chunks(
            records, ["early detection", "survival", "treatment outcomes"], limit=8
        )
    })

    for key, module in TEMPLATE_MODULES.items():
        mid = f"module_{key}"
        nodes[mid] = {
            "id": mid, "label": module["title"], "type": "METHOD_MODULE",
            "color": module["color"],
            "description": "Template-aligned knowledge domain",
        }
        support = _supporting_chunks(records, module["evidence_hint"], limit=8)
        edges.append({
            "source": mid,
            "relation": MODULE_RELATIONS[key],
            "target": CENTRAL["id"],
            "template": True,
            "supporting_chunks": support,
        })

        for subgroup, terms in module["subgroups"].items():
            sid = f"{mid}__{re.sub(r'[^a-z0-9]+','_', subgroup.lower()).strip('_')}"
            nodes[sid] = {
                "id": sid, "label": subgroup, "type": "SUBGROUP",
                "module": mid, "color": module["color"],
            }
            edges.append({
                "source": mid, "relation": "HAS_COMPONENT",
                "target": sid, "template": True,
                "supporting_chunks": _supporting_chunks(records, terms, limit=6),
            })

            # Link actual ontology entities to the subgroup where possible.
            terms_norm = {_norm(t) for t in terms}
            matched=set()
            for e in extracted_edges:
                for side in ("source","target"):
                    val=_norm(e.get(side,""))
                    if any(t in val or val in t for t in terms_norm):
                        key_sig=(val, e.get(f"{side}_type","OTHER"))
                        if key_sig in matched: continue
                        matched.add(key_sig)
                        nid=f"entity__{re.sub(r'[^a-z0-9]+','_',val).strip('_')}"
                        if nid not in nodes:
                            nodes[nid]={
                                "id": nid, "label": val, "type": e.get(f"{side}_type","OTHER"),
                                "color": module["color"],
                            }
                        edges.append({
                            "source": sid, "relation": "INCLUDES",
                            "target": nid, "template": True,
                            "supporting_chunks": [{
                                "chunk_id": e.get("chunk_id",""),
                                "video_id": e.get("video_id",""),
                                "title": e.get("title",""),
                                "link": e.get("link",""),
                            }] if e.get("chunk_id") else [],
                        })

    # General diagnostics are often downstream of screening.
    for key in ("mammography","prostate","colorectal"):
        edges.append({
            "source": f"module_{key}", "relation": "OFTEN_FOLLOWED_BY",
            "target": "module_diagnostics", "template": True,
            "supporting_chunks": _supporting_chunks(records, TEMPLATE_MODULES[key]["evidence_hint"], limit=4),
        })

    # Template relationship guide: semantic labels used in visualization.
    relationship_guide = [
        ("ACHIEVED_THROUGH", "How each method contributes to early detection"),
        ("USED_TO_DETECT", "How tests identify biomarkers or abnormalities"),
        ("IDENTIFIES", "How imaging detects early signs"),
        ("DETECTS", "How screening finds abnormalities"),
        ("OFTEN_FOLLOWED_BY", "Diagnostic tests after initial screening"),
        ("LEADS_TO", "Path toward better outcomes"),
    ]

    # Evidence source cards modeled on the six-source footer of the template.
    source_candidates = [
        ("E1", "Detecting cancer in real-time with machine learning",
         ["biomarker","diagnos","tumor"]),
        ("E2", "How To Catch Breast Cancer Early: Stanford Doctors Explain Mammography Options",
         ["mammography","mammogram","breast cancer"]),
        ("E3", "Prostate cancer symptoms - detecting them early",
         ["prostate cancer","psa","mri"]),
        ("E4", "Bowel cancer symptoms: how to spot the warning signs | NHS",
         ["colorectal cancer","colon cancer","stool","bowel"]),
        ("E5", "Cancer Diagnosis Tests - How do Doctors Diagnose Cancer",
         ["diagnosis","biopsy","mammography","scan"]),
        ("E6", "New nanotech to detect cancer early | Joshua Smith",
         ["early detection","survival","cancer"]),
    ]
    for eid, title, terms in source_candidates:
        matches=_supporting_chunks(records, terms, limit=1)
        if matches:
            sources.append({"id":eid,"title":title,"support":matches[0]})

    return {
        "central": CENTRAL,
        "outcome": OUTCOME,
        "nodes": nodes,
        "edges": edges,
        "relationship_guide": relationship_guide,
        "sources": sources,
    }
