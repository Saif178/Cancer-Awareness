"""Dense + BM25 hybrid retrieval with automatic index bootstrap."""
from __future__ import annotations

import os
import pickle
import re

from config import SETTINGS
from ingest_v2 import ensure_index, get_collection


def tokenize(text):
    return re.findall(r"(?u)\b\w+\b", str(text).lower())


def rrf(rank, k=60):
    return 1.0 / (k + rank + 1)


class HybridRetriever:
    def __init__(self, db_path=None, collection_name=None, auto_build=True):
        self.db_path = str(db_path or SETTINGS.db_path)
        self.collection_name = collection_name or SETTINGS.collection_name
        self.index_built = False

        if auto_build:
            collection, built, status = ensure_index(
                input_path=SETTINGS.input_path,
                db_path=self.db_path,
                collection_name=self.collection_name,
            )
            self.index_built = built
            self.index_status = status
            self.collection = collection
        else:
            self.collection = get_collection(self.db_path, self.collection_name, create=False)
            self.index_status = "existing"

        bm25_path = os.path.join(self.db_path, "bm25.pkl")
        try:
            with open(bm25_path, "rb") as fh:
                self.lex = pickle.load(fh)
        except Exception as exc:
            raise RuntimeError(f"BM25 index could not be loaded from '{bm25_path}': {exc}") from exc

        self.id_to_idx = {x: i for i, x in enumerate(self.lex.get("ids", []))}
        chroma_count = self.collection.count()
        if chroma_count != len(self.id_to_idx):
            raise RuntimeError(
                "Hybrid index validation failed: Chroma and BM25 contain "
                f"different numbers of chunks ({chroma_count} vs {len(self.id_to_idx)})."
            )

    def search(self, query, dense_k=None, lexical_k=None, candidate_k=None):
        dense_k = dense_k or SETTINGS.dense_k
        lexical_k = lexical_k or SETTINGS.lexical_k
        candidate_k = candidate_k or SETTINGS.candidate_k
        total = self.collection.count()
        if total == 0:
            return []

        d = self.collection.query(
            query_texts=[query],
            n_results=min(dense_k, total),
            include=["documents", "metadatas", "distances"],
        )
        docs = (d.get("documents") or [[]])[0]
        metas = (d.get("metadatas") or [[]])[0]
        distances = (d.get("distances") or [[]])[0]
        ids = (d.get("ids") or [[]])[0]

        dense = []
        for rank, (cid, text, meta, distance) in enumerate(zip(ids, docs, metas, distances)):
            meta = meta or {}
            cid = str(cid)
            dense.append({
                "id": cid,
                "text": text or "",
                "metadata": meta,
                "dense_distance": float(distance),
                "dense_rank": rank,
            })

        scores, byid = {}, {}
        for item in dense:
            cid = item["id"]
            scores[cid] = scores.get(cid, 0.0) + rrf(item["dense_rank"])
            byid[cid] = item

        bm25 = self.lex.get("bm25")
        lexical_ids = self.lex.get("ids") or []
        lexical_texts = self.lex.get("texts") or []
        lexical_metas = self.lex.get("metadatas") or []
        if bm25 is not None and lexical_ids:
            lexical_scores = bm25.get_scores(tokenize(query))
            order = sorted(range(len(lexical_scores)), key=lambda i: lexical_scores[i], reverse=True)[:min(lexical_k, len(lexical_scores))]
            for rank, i in enumerate(order):
                cid = str(lexical_ids[i])
                scores[cid] = scores.get(cid, 0.0) + rrf(rank)
                byid.setdefault(cid, {
                    "id": cid,
                    "text": lexical_texts[i],
                    "metadata": lexical_metas[i] or {},
                })
                byid[cid]["bm25_score"] = float(lexical_scores[i])
                byid[cid]["lexical_rank"] = rank

        return [
            dict(byid[cid], hybrid_score=float(score))
            for cid, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:candidate_k]
        ]
