"""Evaluate retrieval using a gold JSON file.
Gold format: [{"query":"...","relevant_ids":["video_chunk_0001", ...]}]
Reports Recall@k, MRR@k and nDCG@k for hybrid and reranked retrieval.
"""
from __future__ import annotations
import argparse,json,math
from rag_engine import MedicalRAG

def mrr(ids, rel,k):
    rel=set(rel)
    for i,c in enumerate(ids[:k],1):
        if c in rel:return 1/i
    return 0

def recall(ids,rel,k): return 1.0 if set(ids[:k]) & set(rel) else 0.0

def ndcg(ids,rel,k):
    rel=set(rel); dcg=sum((1/math.log2(i+2)) for i,c in enumerate(ids[:k]) if c in rel); ideal=sum(1/math.log2(i+2) for i in range(min(len(rel),k))); return dcg/ideal if ideal else 0.0

def run(path):
    data=json.load(open(path,encoding='utf-8')); rag=MedicalRAG(); rows=[]
    for q in data:
        candidates=rag.retriever.search(q['query']); reranked=rag.reranker.rerank(q['query'],candidates)
        rows.append((q['relevant_ids'],[x['id'] for x in candidates],[x['id'] for x in reranked]))
    out={}
    for name,pos in [('hybrid',1),('reranked',2)]:
        for k in (1,3,5,10):
            vals=[]
            for rel,d,r in rows: vals.append((recall((d,r)[pos-1],rel,k),mrr((d,r)[pos-1],rel,k),ndcg((d,r)[pos-1],rel,k)))
            out[f'{name}@{k}']={"Recall":sum(x[0] for x in vals)/len(vals),"MRR":sum(x[1] for x in vals)/len(vals),"nDCG":sum(x[2] for x in vals)/len(vals)}
    print(json.dumps(out,indent=2)); return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--gold',default='evaluation/gold_questions.json'); run(ap.parse_args().gold)
