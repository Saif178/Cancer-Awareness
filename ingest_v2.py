"""Build and validate the Chroma + BM25 medical RAG index.

This module is safe for Streamlit Cloud: if the collection or BM25 sidecar is
missing/corrupt/out of sync, ``ensure_index`` rebuilds it from the bundled
transcript dataset before the retriever is created.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import shutil
from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

from config import SETTINGS
from medical_chunker import build_records
from knowledge_graph.graph_store import MedicalKnowledgeGraph


def tokenize(text: str):
    return re.findall(r"(?u)\b\w+\b", str(text).lower())


def _embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=SETTINGS.embedding_model
    )


def _client(db_path: str):
    Path(db_path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=db_path)


def _bm25_path(db_path: str) -> Path:
    return Path(db_path) / "bm25.pkl"


def _graph_path(db_path: str) -> Path:
    if str(db_path) == str(SETTINGS.db_path):
        return Path(SETTINGS.graph_path)
    return Path(db_path) / "medical_graph_v3.json"


def _write_bm25(db_path: str, records: list[dict]) -> None:
    tokenized = [tokenize(r["text"]) for r in records]
    payload = {
        "version": 2,
        "ids": [r["id"] for r in records],
        "texts": [r["text"] for r in records],
        "metadatas": [r["metadata"] for r in records],
        "tokenized": tokenized,
        "bm25": BM25Okapi(tokenized) if tokenized else None,
    }
    with open(_bm25_path(db_path), "wb") as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)


def _records_from_collection(collection) -> list[dict]:
    total = collection.count()
    if total == 0:
        return []
    result = collection.get(include=["documents", "metadatas"], limit=total)
    ids = result.get("ids") or []
    docs = result.get("documents") or []
    metas = result.get("metadatas") or []
    return [
        {"id": i, "text": d or "", "metadata": m or {}}
        for i, d, m in zip(ids, docs, metas)
    ]


def get_collection(db_path=None, collection_name=None, create=True):
    db_path = str(db_path or SETTINGS.db_path)
    collection_name = collection_name or SETTINGS.collection_name
    client = _client(db_path)
    ef = _embedding_function()
    if create:
        return client.get_or_create_collection(
            name=collection_name,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return client.get_collection(collection_name, embedding_function=ef)


def build(input_path, db_path=None, collection_name=None, rebuild=True):
    """Build the complete index from the transcript JSON."""
    db_path = str(db_path or SETTINGS.db_path)
    collection_name = collection_name or SETTINGS.collection_name
    input_path = str(input_path or SETTINGS.input_path)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Transcript dataset not found: {input_path}")

    if rebuild and os.path.exists(db_path):
        shutil.rmtree(db_path, ignore_errors=True)

    collection = get_collection(db_path, collection_name, create=True)

    with open(input_path, encoding="utf-8") as fh:
        videos = json.load(fh)

    if not isinstance(videos, list):
        raise ValueError("Transcript dataset must contain a JSON list of videos.")

    records: list[dict] = []
    for video in videos:
        records.extend(build_records(video, SETTINGS.chunk_tokens, SETTINGS.chunk_overlap_tokens))

    if records:
        collection.upsert(
            ids=[r["id"] for r in records],
            documents=[r["text"] for r in records],
            metadatas=[r["metadata"] for r in records],
        )

    _write_bm25(db_path, records)
    graph = MedicalKnowledgeGraph(str(_graph_path(db_path)))
    graph.build_from_records(records)
    return len(records)


def index_is_valid(db_path=None, collection_name=None) -> tuple[bool, str]:
    """Validate Chroma, BM25, and their shared chunk IDs."""
    db_path = str(db_path or SETTINGS.db_path)
    collection_name = collection_name or SETTINGS.collection_name
    if not os.path.isdir(db_path):
        return False, f"Database directory not found: {db_path}"

    try:
        collection = get_collection(db_path, collection_name, create=False)
    except Exception as exc:
        return False, f"Collection '{collection_name}' is unavailable: {exc}"

    try:
        count = collection.count()
        if count <= 0:
            return False, "Chroma collection is empty"

        bm25_file = _bm25_path(db_path)
        if not bm25_file.exists():
            return False, "BM25 index file is missing"

        with open(bm25_file, "rb") as fh:
            lex = pickle.load(fh)
        ids = lex.get("ids") or []
        texts = lex.get("texts") or []
        metas = lex.get("metadatas") or []
        bm25 = lex.get("bm25")
        if len(ids) != count:
            return False, f"BM25/Chroma count mismatch: {len(ids)} vs {count}"
        if len(texts) != count or len(metas) != count or bm25 is None:
            return False, "BM25 index is incomplete"

        chroma_ids = collection.get(limit=count, include=["metadatas"]).get("ids", [])
        if set(ids) != set(chroma_ids):
            return False, "BM25/Chroma chunk IDs are out of sync"
    except Exception as exc:
        return False, f"Index validation failed: {exc}"

    graph_path = _graph_path(db_path)
    try:
        graph = MedicalKnowledgeGraph(str(graph_path))
        graph_ok, graph_reason = graph.validate()
        if not graph_ok:
            return False, f"Knowledge graph invalid: {graph_reason}"
        graph_chunk_ids = {e.get("chunk_id") for e in graph.edges if e.get("chunk_id")}
        if not graph_chunk_ids.issubset(set(ids)):
            return False, "Knowledge graph contains provenance IDs absent from Chroma/BM25"
    except Exception as exc:
        return False, f"Knowledge graph validation failed: {exc}"

    return True, f"{count} chunks + graph"


def ensure_index(input_path=None, db_path=None, collection_name=None):
    """Return a valid collection, rebuilding automatically if necessary."""
    db_path = str(db_path or SETTINGS.db_path)
    collection_name = collection_name or SETTINGS.collection_name
    input_path = str(input_path or SETTINGS.input_path)

    valid, reason = index_is_valid(db_path, collection_name)
    if valid:
        return get_collection(db_path, collection_name, create=False), False, reason

    if not os.path.exists(input_path):
        raise RuntimeError(
            f"RAG index is unavailable ({reason}) and source dataset was not found: {input_path}"
        )

    try:
        count = build(input_path, db_path=db_path, collection_name=collection_name, rebuild=True)
    except Exception as exc:
        raise RuntimeError(
            f"Automatic RAG index build failed. Reason before rebuild: {reason}. "
            f"Build error: {exc}"
        ) from exc

    valid, reason = index_is_valid(db_path, collection_name)
    if not valid:
        raise RuntimeError(f"RAG index build failed validation after indexing {count} chunks: {reason}")

    return get_collection(db_path, collection_name, create=False), True, reason


def add_records(records: Iterable[dict], db_path=None, collection_name=None):
    """Upsert transcript chunks and rebuild BM25 to keep indexes synchronized."""
    db_path = str(db_path or SETTINGS.db_path)
    collection_name = collection_name or SETTINGS.collection_name
    collection, _, _ = ensure_index(db_path=db_path, collection_name=collection_name)
    records = list(records)
    if not records:
        return 0

    video_ids = {str(r.get("metadata", {}).get("video_id", "")) for r in records}
    video_ids.discard("")
    for video_id in video_ids:
        try:
            existing = collection.get(where={"video_id": video_id}, include=["metadatas"])
            old_ids = existing.get("ids") or []
            if old_ids:
                collection.delete(ids=old_ids)
        except Exception:
            pass

    collection.upsert(
        ids=[r["id"] for r in records],
        documents=[r["text"] for r in records],
        metadatas=[r["metadata"] for r in records],
    )
    all_records = _records_from_collection(collection)
    _write_bm25(db_path, all_records)
    graph = MedicalKnowledgeGraph(str(_graph_path(db_path)))
    graph.build_from_records(all_records)
    return len(records)


def build_index(input_path=None, db_path=None, collection_name=None):
    """Public alias used by deployment/bootstrap code."""
    return build(input_path or SETTINGS.input_path, db_path, collection_name, rebuild=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=SETTINGS.input_path)
    parser.add_argument("--db", default=None)
    parser.add_argument("--no-rebuild", action="store_true")
    args = parser.parse_args()
    count = build(args.input, args.db, rebuild=not args.no_rebuild)
    print(f"Indexed {count} chunks into {args.db or SETTINGS.db_path}/{SETTINGS.collection_name}")
