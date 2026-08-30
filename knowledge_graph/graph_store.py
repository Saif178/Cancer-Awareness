"""Persistent local oncology graph with provenance-preserving JSON storage."""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict
from .entity_relation_extractor import extract_from_chunk, relation_to_dict

class MedicalKnowledgeGraph:
    VERSION = 3
    def __init__(self, path: str):
        self.path = Path(path)
        self.nodes = {}
        self.edges = []
        self._adj = defaultdict(set)
        self.loaded = False
        if self.path.exists():
            self.load()

    def load(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.nodes = data.get("nodes", {})
        self.edges = data.get("edges", [])
        self._rebuild_adjacency()
        self.loaded = True

    def _rebuild_adjacency(self):
        self._adj = defaultdict(set)
        for e in self.edges:
            self._adj[e["source"]].add(e["target"])
            self._adj[e["target"]].add(e["source"])

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": self.VERSION, "nodes": self.nodes, "edges": self.edges}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def clear(self):
        self.nodes, self.edges = {}, []
        self._rebuild_adjacency()

    def add_chunk(self, text: str, chunk_id: str, metadata: dict):
        entities, relations = extract_from_chunk(text, chunk_id, metadata)
        for e in entities:
            self.nodes.setdefault(e.normalized, {"name": e.normalized, "type": e.entity_type})
        for r in relations:
            edge = relation_to_dict(r)
            # Exact duplicate extraction is ignored; provenance from distinct
            # chunks remains as separate edges.
            signature = (edge["source"], edge["relation"], edge["target"], edge["chunk_id"])
            if not any((x["source"], x["relation"], x["target"], x["chunk_id"]) == signature for x in self.edges):
                self.edges.append(edge)
        self._rebuild_adjacency()
        return len(entities), len(relations)

    def build_from_records(self, records):
        self.clear()
        ent_count = rel_count = 0
        for r in records:
            e, rel = self.add_chunk(r["text"], r["id"], r.get("metadata", {}))
            ent_count += e; rel_count += rel
        self.save()
        return ent_count, rel_count

    def validate(self):
        if not self.path.exists(): return False, "Graph file is missing"
        if not self.nodes: return False, "Graph contains no entities"
        if not self.edges: return False, "Graph contains no relations"
        required = {"source", "relation", "target", "sentence", "chunk_id", "video_id", "title", "link"}
        for e in self.edges:
            if not required.issubset(e):
                return False, "Graph relation is missing provenance fields"
            if not e.get("chunk_id"):
                return False, "Graph relation has empty chunk_id provenance"
        return True, f"{len(self.nodes)} entities / {len(self.edges)} relations"

    def neighbors(self, node):
        return sorted(self._adj.get(node, set()))

    def paths(self, seed_nodes, max_hops=2, max_paths=20):
        """Return bounded undirected multi-hop paths with original edge provenance."""
        seed_nodes = [s for s in seed_nodes if s in self.nodes]
        results = []
        for seed in seed_nodes:
            queue = [(seed, [seed])]
            seen = {(seed,)}
            while queue and len(results) < max_paths:
                current, path = queue.pop(0)
                if len(path) - 1 >= max_hops:
                    continue
                for nxt in self.neighbors(current):
                    if nxt in path:
                        continue
                    new_path = path + [nxt]
                    key = tuple(new_path)
                    if key in seen: continue
                    seen.add(key)
                    edges = []
                    for a, b in zip(new_path, new_path[1:]):
                        matches = [e for e in self.edges if {e["source"], e["target"]} == {a,b}]
                        if matches:
                            # Prefer strongest provenance edge.
                            edges.append(max(matches, key=lambda x: x.get("confidence",0)))
                    if edges:
                        results.append({"nodes": new_path, "edges": edges})
                    queue.append((nxt, new_path))
        return results[:max_paths]
