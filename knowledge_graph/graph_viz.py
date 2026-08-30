"""Dependency-light DOT rendering for Streamlit graph visualization."""
from html import escape

def to_dot(graph_evidence, max_edges=20):
    lines = ["graph G {", 'rankdir=LR;', 'overlap=false;', 'splines=true;']
    seen_nodes = set()
    for item in graph_evidence[:max_edges]:
        a, b = item["source"], item["target"]
        ra, rb = a.replace('"',''), b.replace('"','')
        if a not in seen_nodes:
            lines.append(f'"{ra}" [label="{escape(a)}"];'); seen_nodes.add(a)
        if b not in seen_nodes:
            lines.append(f'"{rb}" [label="{escape(b)}"];'); seen_nodes.add(b)
        rel = item["relation"].replace('"','')
        lines.append(f'"{ra}" -- "{rb}" [label="{rel}"];')
    lines.append("}")
    return "\n".join(lines)
