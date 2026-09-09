import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import src.config
from src.config import CONFIDENCE_THRESHOLD, DATA_DIR

REFUSAL_LOG_PATH = DATA_DIR / "refusal_log.jsonl"

def should_answer(
    reranked_results: List[Dict[str, Any]],
    threshold: float = CONFIDENCE_THRESHOLD
) -> bool:
    """
    Determines whether retrieved evidence is strong enough to attempt answer generation.
    Deterministic, numerical thresholding based on top cross-encoder score.
    
    Interface contract:
    should_answer(reranked_results: List[chunk], threshold: float) -> bool
    """
    if not reranked_results:
        return False

    top_chunk = reranked_results[0]
    top_score = float(top_chunk.get("score", 0.0))
    return top_score >= threshold

def log_refusal(query: str, top_score: float, threshold: float, reason: str = "insufficient_evidence"):
    """Logs refusals for auditing and refusal-rate tracking."""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "top_score": round(top_score, 4),
        "threshold": threshold,
        "reason": reason
    }
    REFUSAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REFUSAL_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def create_refusal_response(
    confidence: Optional[float] = None,
    reason: str = "insufficient_evidence"
) -> Dict[str, Any]:
    """
    Creates exact response shape for refused queries per api-response-schema.md:
    {
      "status": "refused",
      "answer": null,
      "confidence": 0.18,
      "sources": [],
      "reason": "insufficient_evidence"
    }
    """
    return {
        "status": "refused",
        "answer": None,
        "confidence": round(confidence, 4) if confidence is not None else 0.0,
        "sources": [],
        "reason": reason
    }
