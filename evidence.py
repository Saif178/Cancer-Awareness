"""Evidence grading and deterministic citation IDs."""
from __future__ import annotations

def grade_evidence(results, min_score=0.10):
    if not results: return "INSUFFICIENT", 0.0
    scores=[r.get("rerank_score",-999.0) for r in results]
    best=max(scores)
    if best < min_score: return "INSUFFICIENT", max(0.0,min(1.0,(best+5)/10))
    if len(results)>=2 and scores[0] >= min_score: return "DIRECT", min(1.0,0.55+0.08*min(len(results),5))
    return "SYNTHESIZED", 0.60

def make_evidence(results):
    evidence=[]
    for i,r in enumerate(results,1):
        m=r.get("metadata",{})
        evidence.append({"evidence_id":f"E{i}","text":r["text"],"metadata":m,"title":m.get("title","Unknown source"),"link":m.get("link",""),"video_id":m.get("video_id",""),"chunk_index":m.get("chunk_index",i-1),"rerank_score":r.get("rerank_score"),"hybrid_score":r.get("hybrid_score")})
    return evidence

def citation_catalog(evidence):
    return "\n".join(f"[{e['evidence_id']}] {e['title']} | {e['link']} | chunk {e['chunk_index']}" for e in evidence)
