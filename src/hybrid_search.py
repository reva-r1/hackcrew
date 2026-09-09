from typing import List, Dict, Any, Optional
import src.config
from src.config import RRF_K, TOP_K_HYBRID
from src.ingestion import get_embedder
from src.vector_store import VectorStore
from src.bm25_index import BM25Index
from src.database import get_chunk

def hybrid_search(query: str, top_k: int = TOP_K_HYBRID) -> List[Dict[str, Any]]:
    """
    Executes hybrid search combining dense vector retrieval and BM25 sparse keyword retrieval
    using Reciprocal Rank Fusion (RRF).
    
    Formula:
    RRF_score(chunk) = 1 / (k + rank_vector) + 1 / (k + rank_bm25)
    where k = 60 by default.

    Interface contract:
    hybrid_search(query: str, top_k: int) -> List[{chunk_id, score, text, metadata}]
    """
    if not query or not query.strip():
        return []

    # 1. Retrieve dense vector candidates
    embedder = get_embedder()
    query_vector = embedder.encode(query, show_progress_bar=False, normalize_embeddings=True).tolist()
    vector_store = VectorStore()
    
    # Retrieve wider pool for fusion
    pool_size = max(top_k * 2, 20)
    vector_results = vector_store.search(query_embedding=query_vector, top_k=pool_size)

    # 2. Retrieve BM25 keyword candidates
    bm25_index = BM25Index()
    bm25_results = bm25_index.search(query=query, top_k=pool_size)

    # 3. Reciprocal Rank Fusion (RRF)
    # Maps chunk_id -> dict with details and score
    chunk_map: Dict[str, Dict[str, Any]] = {}
    
    # Process vector rankings (1-indexed)
    for rank_v, item in enumerate(vector_results, start=1):
        cid = item["chunk_id"]
        rrf_contrib = 1.0 / (RRF_K + rank_v)
        chunk_map[cid] = {
            "chunk_id": cid,
            "score": rrf_contrib,
            "text": item.get("text", ""),
            "metadata": item.get("metadata", {}),
            "vector_rank": rank_v,
            "bm25_rank": None
        }

    # Process BM25 rankings (1-indexed)
    for rank_b, item in enumerate(bm25_results, start=1):
        cid = item["chunk_id"]
        rrf_contrib = 1.0 / (RRF_K + rank_b)
        if cid in chunk_map:
            chunk_map[cid]["score"] += rrf_contrib
            chunk_map[cid]["bm25_rank"] = rank_b
            if not chunk_map[cid]["text"] and item.get("text"):
                chunk_map[cid]["text"] = item["text"]
            if not chunk_map[cid]["metadata"] and item.get("metadata"):
                chunk_map[cid]["metadata"] = item["metadata"]
        else:
            chunk_map[cid] = {
                "chunk_id": cid,
                "score": rrf_contrib,
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
                "vector_rank": None,
                "bm25_rank": rank_b
            }

    # If any text or metadata is missing, hydrate from SQLite metadata store
    for cid, record in chunk_map.items():
        if not record["text"] or not record["metadata"]:
            db_row = get_chunk(cid)
            if db_row:
                if not record["text"]:
                    record["text"] = db_row["chunk_text"]
                if not record["metadata"]:
                    record["metadata"] = {
                        "doc_id": db_row["doc_id"],
                        "doc_name": db_row["doc_name"],
                        "page_num": db_row["page_num"]
                    }

    # 4. Sort descending by RRF score
    fused = sorted(chunk_map.values(), key=lambda x: x["score"], reverse=True)

    # Format output with content-level deduplication to guarantee diverse candidate chunks
    output = []
    seen_texts = set()
    for item in fused:
        # Normalized prefix of chunk text for content deduplication
        norm_key = " ".join(item["text"].split())[:120] if item["text"] else item["chunk_id"]
        if norm_key in seen_texts:
            continue
        seen_texts.add(norm_key)

        output.append({
            "chunk_id": item["chunk_id"],
            "score": round(item["score"], 6),
            "text": str(item.get("text") or ""),
            "metadata": item.get("metadata") or {}
        })
        if len(output) >= top_k:
            break

    return output

