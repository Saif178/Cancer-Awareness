"""End-to-end GraphRAG pipeline.

Dense + BM25 -> graph entity linking/multi-hop -> Cross-Encoder -> evidence
validation -> OpenAI/Ollama. Graph facts always retain provenance to original
transcript chunks so citations remain deterministic.
"""
from __future__ import annotations

from config import SETTINGS
from hybrid_retriever import HybridRetriever
from reranker import Reranker
from evidence import grade_evidence, make_evidence, citation_catalog
from llm import generate
from knowledge_graph.graph_store import MedicalKnowledgeGraph
from knowledge_graph.graph_retriever import GraphRetriever


class MedicalRAG:
    def __init__(self):
        self.retriever = HybridRetriever(auto_build=True)
        self.reranker = Reranker()
        self.graph = MedicalKnowledgeGraph(str(SETTINGS.graph_path))
        ok, reason = self.graph.validate()
        if not ok:
            # This should only happen for an externally modified index. Rebuild
            # from the synchronized Chroma records without touching the vectors.
            records = []
            total = self.retriever.collection.count()
            if total:
                result = self.retriever.collection.get(
                    limit=total, include=["documents", "metadatas"]
                )
                for cid, text, meta in zip(
                    result.get("ids", []),
                    result.get("documents", []),
                    result.get("metadatas", []),
                ):
                    records.append({"id": cid, "text": text or "", "metadata": meta or {}})
            self.graph.build_from_records(records)
            ok, reason = self.graph.validate()
        if not ok:
            raise RuntimeError(f"Knowledge graph is unavailable: {reason}")
        self.graph_retriever = GraphRetriever(
            self.graph,
            max_hops=SETTINGS.graph_max_hops,
            max_paths=SETTINGS.graph_max_paths,
        )

    @property
    def index_status(self):
        return self.retriever.index_status

    @property
    def index_built(self):
        return self.retriever.index_built

    @property
    def graph_stats(self):
        return {"entities": len(self.graph.nodes), "relations": len(self.graph.edges)}

    def retrieve(self, query):
        text_candidates = self.retriever.search(query)
        graph_candidates = self.graph_retriever.search(query)

        # Convert graph findings into rerankable evidence. The source sentence
        # is the original transcript sentence, never generated graph text.
        graph_as_candidates = []
        for g in graph_candidates:
            graph_as_candidates.append({
                "id": g["metadata"].get("chunk_id", ""),
                "text": g["text"],
                "metadata": {
                    **g["metadata"],
                    "graph_source": g["source"],
                    "graph_relation": g["relation"],
                    "graph_target": g["target"],
                },
                "hybrid_score": g.get("graph_score", 0.0),
                "graph_score": g.get("graph_score", 0.0),
            })

        # Deduplicate by chunk ID while retaining the strongest graph signal.
        merged = {}
        for item in text_candidates + graph_as_candidates:
            cid = str(item.get("id", ""))
            if not cid:
                continue
            if cid not in merged:
                merged[cid] = item
            else:
                merged[cid]["graph_score"] = max(
                    float(merged[cid].get("graph_score", 0.0)),
                    float(item.get("graph_score", 0.0)),
                )
                if item.get("graph_relation"):
                    merged[cid].setdefault("graph_relations", []).append({
                        "source": item["metadata"].get("graph_source"),
                        "relation": item["metadata"].get("graph_relation"),
                        "target": item["metadata"].get("graph_target"),
                    })

        ranked = self.reranker.rerank(query, list(merged.values()), SETTINGS.final_k)
        return ranked, graph_candidates

    def answer(self, query, provider=None, model=None):
        ranked, graph_candidates = self.retrieve(query)
        level, confidence = grade_evidence(ranked, SETTINGS.min_rerank_score)
        if graph_candidates and level == "INSUFFICIENT":
            level, confidence = "SYNTHESIZED", max(confidence, 0.55)

        evidence = make_evidence(ranked)
        catalog = citation_catalog(evidence)
        texts = []
        for e in evidence:
            graph_note = ""
            m = e.get("metadata", {})
            if m.get("graph_relation"):
                graph_note = (
                    f"\nGraph relation discovered from this source: "
                    f"{m.get('graph_source')} --{m.get('graph_relation')}--> "
                    f"{m.get('graph_target')}"
                )
            texts.append(f"[{e['evidence_id']}] {e['text']}{graph_note}")

        graph_paths = []
        for g in graph_candidates[:SETTINGS.graph_max_paths]:
            graph_paths.append({
                "path": g["path"],
                "source": g["source"],
                "relation": g["relation"],
                "target": g["target"],
                "chunk_id": g["metadata"].get("chunk_id", ""),
                "title": g["metadata"].get("title", ""),
                "link": g["metadata"].get("link", ""),
                "confidence": g.get("graph_score", 0.0),
            })

        graph_text = "\n".join(
            f"- {' -> '.join(p['path'])} "
            f"[{p['relation']}; source chunk {p['chunk_id']}]"
            for p in graph_paths
        ) or "No graph path was found."

        evidence_text = "\n\n".join(texts)
        prompt = (
            f"Question: {query}\n\n"
            f"Evidence level: {level}\n"
            f"Evidence confidence: {confidence:.2f}\n\n"
            f"Evidence catalog:\n{catalog}\n\n"
            f"Transcript evidence:\n{evidence_text}\n\n"
            f"Knowledge-graph paths (derived only from transcript evidence):\n{graph_text}\n\n"
            "Answer using only the supplied transcript evidence. A graph path is "
            "a retrieval aid, not independent medical authority. Every factual "
            "claim must cite one or more immutable evidence IDs such as [E1]. "
            "For a multi-hop graph inference, explicitly say it is a synthesis "
            "and cite the source chunks supporting the path. Never create IDs. "
            "If evidence is insufficient, say so."
        )

        if level == "INSUFFICIENT":
            answer = "The retrieved evidence is insufficient to answer this question reliably."
        else:
            answer = generate(prompt, provider, model)

        return {
            "answer": answer,
            "evidence_level": level,
            "confidence": confidence,
            "evidence": evidence,
            "retrieved": ranked,
            "graph_evidence": graph_paths,
            "graph_stats": self.graph_stats,
            "index_status": self.index_status,
        }
