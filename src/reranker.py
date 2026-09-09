import math
from typing import List, Dict, Any, Optional
import src.config
from sentence_transformers import CrossEncoder
from src.config import RERANKER_MODEL_NAME, TOP_K_RERANK

_RERANKER: Optional[CrossEncoder] = None

def get_reranker() -> CrossEncoder:
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder(RERANKER_MODEL_NAME)
    return _RERANKER

def sigmoid(x: float) -> float:
    """Calculates sigmoid to map cross-encoder logits to [0.0, 1.0]."""
    try:
        if x < -700:
            return 0.0
        if x > 700:
            return 1.0
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0

def rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = TOP_K_RERANK
) -> List[Dict[str, Any]]:
    """
    Reranks candidate chunks using cross-encoder/ms-marco-MiniLM-L-6-v2.
    Computes joint cross-attention score for each (query, chunk_text) pair.
    
    Interface contract from rag-tier1-tier2-buildspec.md:
    rerank(query: str, candidates: List[chunk]) -> List[chunk] (same shape, reordered/truncated)
    """
    if not candidates or not query or not query.strip():
        return []

    reranker = get_reranker()
    
    # Prepare pairs: (query, chunk_text)
    pairs = [(str(query or ""), str(c.get("text") or "")) for c in candidates]
    
    # CrossEncoder returns raw logits (or probabilities if activation_fn is used)
    scores = reranker.predict(pairs, show_progress_bar=False)

    scored_candidates = []
    for candidate, raw_score in zip(candidates, scores):
        raw_val = float(raw_score)
        norm_score = sigmoid(raw_val)
        
        # Clone and update candidate dict with cross-encoder score
        updated = {
            "chunk_id": candidate["chunk_id"],
            "score": round(norm_score, 4),
            "raw_logit": round(raw_val, 4),
            "text": candidate.get("text", ""),
            "metadata": candidate.get("metadata", {})
        }
        scored_candidates.append(updated)

    # Sort descending by cross-encoder score
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)

    # Truncate to top_k
    return scored_candidates[:top_k]
