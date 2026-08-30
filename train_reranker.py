"""Optional domain adaptation for the reranker.
Training JSONL fields: query, positive, negative. This is intentionally separate
from the default package so the shipped system works without training.
"""
import argparse,json
from sentence_transformers import CrossEncoder, InputExample
from torch.utils.data import DataLoader

def main(path,out_dir):
    rows=[json.loads(x) for x in open(path,encoding='utf-8') if x.strip()]
    examples=[]
    for r in rows:
        examples.append(InputExample(texts=[r['query'],r['positive']],label=1.0))
        for n in r.get('negative',[]): examples.append(InputExample(texts=[r['query'],n],label=0.0))
    model=CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2',num_labels=1)
    loader=DataLoader(examples,shuffle=True,batch_size=8)
    model.fit(train_dataloader=loader,epochs=1,warmup_steps=max(1,len(loader)//10),show_progress_bar=True,output_path=out_dir)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='./models/medical_reranker'); a=ap.parse_args(); main(a.data,a.output)
