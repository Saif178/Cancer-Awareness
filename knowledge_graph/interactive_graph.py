"""Interactive GraphRAG explorer for the Cancer Awareness Project.

Click an oncology entity to inspect connected entities, relationship types,
and the transcript chunk/source supporting each relationship.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _pretty(value: str) -> str:
    s = str(value).replace("_", " ").strip()
    return s.title() if s else "Unknown"


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(value)).strip("_") or "node"


def _color(entity_type: str) -> str:
    return {
        "CANCER": "#E57373",
        "TREATMENT": "#64B5F6",
        "DRUG": "#42A5F5",
        "BIOMARKER": "#AB47BC",
        "GENE": "#7E57C2",
        "SYMPTOM": "#FFB74D",
        "RISK_FACTOR": "#FF8A65",
        "DIAGNOSTIC_TEST": "#26A69A",
        "SCREENING": "#26A69A",
        "ANATOMY": "#78909C",
        "SIDE_EFFECT": "#EF5350",
        "OUTCOME": "#66BB6A",
    }.get(str(entity_type).upper(), "#90A4AE")


def _chunk(collection, chunk_id: str) -> dict[str, Any]:
    if collection is None or not chunk_id:
        return {}
    try:
        result = collection.get(
            ids=[str(chunk_id)],
            include=["documents", "metadatas"],
        )
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        return {
            "text": docs[0] if docs else "",
            "metadata": metas[0] if metas else {},
        }
    except Exception:
        return {}


def build_nodes_edges(graph, max_nodes: int = 120, max_edges: int = 220):
    """Build streamlit-agraph objects from transcript-backed graph data."""
    from streamlit_agraph import Node, Edge

    raw_nodes = getattr(graph, "nodes", {}) or {}
    raw_edges = getattr(graph, "edges", []) or []

    # Keep the graph responsive while retaining the most useful/high-degree
    # entities. The examples requested by the user are preferentially retained.
    preferred = {"mammography", "psa", "biomarker", "colonoscopy"}
    ranked_keys = sorted(
        raw_nodes.keys(),
        key=lambda k: (0 if str(k).lower() in preferred else 1, str(k)),
    )
    allowed = set(ranked_keys[:max_nodes])

    nodes = []
    node_meta = {}
    for key in allowed:
        data = raw_nodes.get(key) or {}
        label = data.get("name") or key
        nid = f"entity__{key}"
        node_meta[nid] = {
            "key": key,
            "label": label,
            "type": data.get("type", "OTHER"),
        }
        nodes.append(
            Node(
                id=nid,
                label=str(label)[:42],
                size=28 if str(key).lower() in preferred else 22,
                color=_color(data.get("type", "OTHER")),
                title=f"{label} | {data.get('type', 'OTHER')} | click to inspect",
            )
        )

    edges = []
    seen = set()
    for e in raw_edges:
        a = e.get("source")
        b = e.get("target")
        if a not in allowed or b not in allowed:
            continue
        sig = (a, e.get("relation", ""), b)
        if sig in seen:
            continue
        seen.add(sig)
        edges.append(
            Edge(
                source=f"entity__{a}",
                target=f"entity__{b}",
                label=_pretty(e.get("relation", "RELATED_TO")),
                color="#777777",
            )
        )
        if len(edges) >= max_edges:
            break

    return nodes, edges, node_meta


def get_node_provenance(graph, selected_id: str, collection=None, limit: int = 20):
    """Return relationships plus exact source chunk metadata for a node."""
    if not selected_id or not selected_id.startswith("entity__"):
        return None

    key = selected_id[len("entity__"):]
    node = (getattr(graph, "nodes", {}) or {}).get(key, {})
    if not node:
        return None

    relationships = []
    for e in getattr(graph, "edges", []) or []:
        if e.get("source") != key and e.get("target") != key:
            continue

        outgoing = e.get("source") == key
        other = e.get("target") if outgoing else e.get("source")
        chunk_id = e.get("chunk_id", "")
        chunk = _chunk(collection, chunk_id)
        metadata = chunk.get("metadata", {}) or {}

        relationships.append(
            {
                "connected_entity": other,
                "relation": e.get("relation", "RELATED_TO"),
                "direction": "outgoing" if outgoing else "incoming",
                "confidence": e.get("confidence"),
                "sentence": e.get("sentence", ""),
                "chunk_id": chunk_id,
                "video_id": e.get("video_id") or metadata.get("video_id", ""),
                "title": e.get("title") or metadata.get("title", ""),
                "link": e.get("link") or metadata.get("link", ""),
                "chunk_text": chunk.get("text", ""),
            }
        )

    relationships.sort(
        key=lambda x: (
            -(float(x["confidence"]) if x.get("confidence") is not None else -1),
            str(x.get("relation", "")),
        )
    )

    return {
        "id": selected_id,
        "label": node.get("name") or key,
        "type": node.get("type", "OTHER"),
        "relationships": relationships[:limit],
    }


def render_interactive_graph(st, graph, collection=None, max_nodes: int = 120):
    """Render the interactive graph and the provenance inspector."""
    try:
        from streamlit_agraph import Config, agraph
    except ImportError:
        st.error(
            "Interactive graph is unavailable because `streamlit-agraph` "
            "is not installed. Add `streamlit-agraph` to requirements.txt."
        )
        return None

    nodes, edges, node_meta = build_nodes_edges(graph, max_nodes=max_nodes)

    st.caption(
        "Click an entity node to inspect its relationships and the exact "
        "transcript evidence behind each relationship."
    )

    config = Config(
        width="100%",
        height=650,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#1565C0",
        collapsible=False,
    )

    selected = agraph(nodes=nodes, edges=edges, config=config)

    if not selected:
        st.info("Select a node such as Mammography, PSA, Biomarker or Colonoscopy.")
        return None

    details = get_node_provenance(graph, selected, collection)
    if not details:
        st.warning("No transcript-backed details were found for the selected node.")
        return selected

    st.markdown("### 🔎 Selected Entity")
    st.markdown(
        f"**{details['label']}**  ·  `{details['type']}`"
    )

    relationships = details["relationships"]
    if not relationships:
        st.info("This entity has no transcript-backed relationships in the graph.")
        return selected

    st.markdown(f"**{len(relationships)} connected relationship(s)**")

    for i, rel in enumerate(relationships, 1):
        arrow = "→" if rel["direction"] == "outgoing" else "←"
        st.markdown(
            f"**{i}. {details['label']} {arrow} {rel['connected_entity']}**  "
            f"`{_pretty(rel['relation'])}`"
        )
        if rel.get("confidence") is not None:
            st.caption(f"Extraction confidence: {float(rel['confidence']):.3f}")
        if rel.get("sentence"):
            st.markdown(f"> {rel['sentence']}")

        with st.expander(
            f"📜 Transcript chunk: {rel.get('chunk_id') or 'not available'}"
        ):
            if rel.get("chunk_text"):
                st.write(rel["chunk_text"])
            else:
                st.warning(
                    "The graph contains provenance metadata, but the full "
                    "chunk is not currently available from ChromaDB."
                )

            cols = st.columns(2)
            with cols[0]:
                if rel.get("title"):
                    st.caption(f"Source: {rel['title']}")
                if rel.get("video_id"):
                    st.caption(f"Video ID: {rel['video_id']}")
            with cols[1]:
                if rel.get("link"):
                    st.markdown(f"[🎥 Open original video]({rel['link']})")

    return selected
