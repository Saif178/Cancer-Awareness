"""Question-to-entity linking and bounded multi-hop graph retrieval."""
from __future__ import annotations
import re
from .schema import LEXICON

class GraphRetriever:
    def __init__(self, graph, max_hops=2, max_paths=12):
        self.graph = graph
        self.max_hops = max_hops
        self.max_paths = max_paths

    def link_entities(self, query):
        q = query.lower()
        found = []
        for terms in LEXICON.values():
            for term in sorted(terms, key=len, reverse=True):
                if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", q):
                    if term in self.graph.nodes and term not in found:
                        found.append(term)
        return found

    def search(self, query):
        seeds = self.link_entities(query)
        paths = self.graph.paths(seeds, self.max_hops, self.max_paths)
        evidence = []
        for p in paths:
            for edge in p["edges"]:
                evidence.append({
                    "type": "graph",
                    "source": edge["source"],
                    "relation": edge["relation"],
                    "target": edge["target"],
                    "path": p["nodes"],
                    "text": edge["sentence"],
                    "metadata": {
                        "chunk_id": edge["chunk_id"],
                        "video_id": edge["video_id"],
                        "title": edge["title"],
                        "link": edge["link"],
                        "graph_confidence": edge["confidence"],
                    },
                    "graph_score": edge["confidence"] / max(1, len(p["nodes"])-1),
                })
        # Deduplicate while retaining the strongest provenance.
        best = {}
        for x in evidence:
            key = (x["source"], x["relation"], x["target"], x["metadata"]["chunk_id"])
            if key not in best or x["graph_score"] > best[key]["graph_score"]:
                best[key] = x
        return sorted(best.values(), key=lambda x: x["graph_score"], reverse=True)
