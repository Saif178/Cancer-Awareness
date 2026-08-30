"""One-command local setup and smoke test."""
import argparse, os
from ingest_v2 import build
from rag_engine import MedicalRAG
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--input',default='cancer_treatment_transcripts.json'); ap.add_argument('--query',default='What cancer warning signs are discussed?'); a=ap.parse_args()
    build(a.input)
    rag=MedicalRAG(); r=rag.answer(a.query); print(r['answer']); print('Evidence:',r['evidence_level'],r['confidence']);
    for e in r['evidence']: print(f"[{e['evidence_id']}] {e['title']} | {e['link']}")
