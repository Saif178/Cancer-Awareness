"""Cross-encoder reranking stage."""
from sentence_transformers import CrossEncoder
from config import SETTINGS

class Reranker:
    def __init__(self, model_name=None):
        self.model_name=model_name or SETTINGS.reranker_model
        self.model=CrossEncoder(self.model_name)
    def rerank(self, query, candidates, top_k=None):
        top_k=top_k or SETTINGS.final_k
        if not candidates: return []
        pairs=[(query,c["text"]) for c in candidates]
        scores=self.model.predict(pairs, show_progress_bar=False)
        ranked=[]
        for c,s in zip(candidates,scores):
            x=c.copy(); x["rerank_score"]=float(s); ranked.append(x)
        ranked.sort(key=lambda x:x["rerank_score"],reverse=True)
        return ranked[:top_k]
