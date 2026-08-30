"""Medical/transcript-aware chunking with stable source metadata."""
from __future__ import annotations
import re
from typing import Dict, List

_MEDICAL_BOUNDARIES = re.compile(r"(?i)(symptoms?|diagnos(?:is|tic)|treatment|therapy|immunotherapy|chemotherapy|radiation|surgery|screening|risk factors?|prevention|staging|prognosis|survival|side effects?|adverse effects?|clinical trial|biomarker|mutation|gene|medication|vaccine)")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")

def _words(text: str):
    return text.split()

def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text

def chunk_transcript(text: str, target_words: int = 450, overlap_words: int = 80) -> List[str]:
    """Create coherent chunks while preferring sentence/topic boundaries."""
    text = _clean(text)
    if not text:
        return []
    sentences = [s.strip() for s in _SENTENCE.split(text) if s.strip()]
    chunks, current = [], []
    current_words = 0
    for sent in sentences:
        n = len(_words(sent))
        boundary_hint = bool(_MEDICAL_BOUNDARIES.search(sent))
        if current and current_words + n > target_words:
            chunks.append(" ".join(current))
            tail=[]; tail_words=0
            for prev in reversed(current):
                pw=len(_words(prev))
                if tail_words + pw > overlap_words: break
                tail.insert(0, prev); tail_words += pw
            current=tail; current_words=tail_words
        if boundary_hint and current and current_words >= int(target_words*0.65):
            chunks.append(" ".join(current))
            current=[]; current_words=0
        current.append(sent); current_words += n
    if current: chunks.append(" ".join(current))
    return chunks

def build_records(video: Dict, target_words=450, overlap_words=80) -> List[Dict]:
    chunks=chunk_transcript(video.get("transcript", ""), target_words, overlap_words)
    records=[]
    for i, text in enumerate(chunks):
        cid=f"{video['video_id']}_chunk_{i:04d}"
        records.append({
            "id": cid,
            "text": text,
            "metadata": {
                "video_id": str(video.get("video_id", "")),
                "title": str(video.get("title", "Untitled")),
                "link": str(video.get("link", "")),
                "chunk_index": i,
                "medical_domain": "oncology",
                "source_type": "youtube_transcript",
            }
        })
    return records
