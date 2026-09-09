import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.config
from src.hybrid_search import hybrid_search
from src.reranker import rerank

def run_step3_tests():
    print("=" * 60)
    print("STEP 3 TEST: CROSS-ENCODER RERANKING VERIFICATION")
    print("=" * 60)

    # Test 1: In-scope query reranking
    q = "What is the WFH internet allowance?"
    print(f"\nQuery: '{q}'")
    
    # 1. Hybrid search shortlist
    candidates = hybrid_search(q, top_k=15)
    print(f"Hybrid search returned {len(candidates)} candidates.")
    print(f"Top hybrid candidate before reranking: {candidates[0]['chunk_id']} (RRF score: {candidates[0]['score']})")

    # 2. Cross-encoder rerank
    reranked = rerank(q, candidates, top_k=5)
    print(f"Reranked top {len(reranked)} candidates.")

    # 3. Contract check
    assert len(reranked) <= 5, "Reranked list exceeded top_k limit"
    assert len(reranked) > 0, "Reranked list is empty"
    
    for i, c in enumerate(reranked):
        assert "chunk_id" in c, f"Item {i} missing chunk_id"
        assert "score" in c, f"Item {i} missing score"
        assert "text" in c, f"Item {i} missing text"
        assert "metadata" in c, f"Item {i} missing metadata"
        assert 0.0 <= c["score"] <= 1.0, f"Score {c['score']} out of [0, 1] range"
        print(f"Rank {i+1}: chunk_id={c['chunk_id']}, score={c['score']:.4f}, raw_logit={c.get('raw_logit')}, page={c['metadata'].get('page_num')}")

    top_chunk = reranked[0]
    print(f"\nTop Reranked Chunk Snippet:\n{top_chunk['text'][:150]}...")
    assert "₹1,500" in top_chunk["text"] or "internet allowance" in top_chunk["text"].lower(), \
        "Top reranked chunk does not match internet allowance policy!"

    # Verify scores are monotonically non-increasing
    for i in range(len(reranked) - 1):
        assert reranked[i]["score"] >= reranked[i+1]["score"], "Reranked results are not sorted in descending order!"

    # Test 2: Irrelevant query score check
    q_irrelevant = "What is the weather today in Paris?"
    print(f"\nTesting irrelevant query: '{q_irrelevant}'")
    irr_candidates = hybrid_search(q_irrelevant, top_k=10)
    irr_reranked = rerank(q_irrelevant, irr_candidates, top_k=5)
    if irr_reranked:
        print(f"Top irrelevant score: {irr_reranked[0]['score']:.4f} (raw_logit: {irr_reranked[0].get('raw_logit')})")
        assert irr_reranked[0]["score"] < top_chunk["score"], "Irrelevant query scored higher than relevant query!"

    print("\n" + "=" * 60)
    print("STEP 3 VERIFICATION: ALL RERANKING TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_step3_tests()
