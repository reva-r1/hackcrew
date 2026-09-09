import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.config
from src.hybrid_search import hybrid_search

def run_step2_tests():
    print("=" * 60)
    print("STEP 2 TEST: HYBRID SEARCH (VECTOR + BM25 RRF) VERIFICATION")
    print("=" * 60)

    # Test 1: Exact keyword query (BM25 advantage)
    q_keyword = "EGT-POL-2026-V1.4"
    print(f"\nQuery 1 (Exact code): '{q_keyword}'")
    results1 = hybrid_search(q_keyword, top_k=5)
    
    assert len(results1) > 0, "No results returned for exact code query"
    top1 = results1[0]
    print(f"Top result: chunk_id={top1['chunk_id']}, score={top1['score']:.6f}")
    print(f"Snippet: {top1['text'][:120]}...")
    assert "EGT-POL-2026-V1.4" in top1["text"], "Top result does not contain exact code!"
    assert "metadata" in top1 and "doc_name" in top1["metadata"], "Missing metadata in result"

    # Test 2: Semantic paraphrase query (Vector search advantage)
    q_semantic = "Can I do remote work and get internet expenses reimbursed?"
    print(f"\nQuery 2 (Semantic paraphrase): '{q_semantic}'")
    results2 = hybrid_search(q_semantic, top_k=5)

    assert len(results2) > 0, "No results returned for semantic query"
    top2 = results2[0]
    print(f"Top result: chunk_id={top2['chunk_id']}, score={top2['score']:.6f}")
    print(f"Page: {top2['metadata'].get('page_num')}")
    print(f"Snippet: {top2['text'][:140]}...")
    assert ("internet allowance" in top2["text"].lower() or "remote" in top2["text"].lower()), \
        "Top result did not retrieve remote work or internet policy!"

    # Test 3: Contract verification
    print("\nVerifying Interface Contract:")
    for i, r in enumerate(results2):
        assert "chunk_id" in r, f"Result {i} missing chunk_id"
        assert "score" in r, f"Result {i} missing score"
        assert isinstance(r["score"], float), f"Score is not float: {type(r['score'])}"
        assert "text" in r, f"Result {i} missing text"
        assert len(r["text"]) > 0, f"Result {i} has empty text"
        assert "metadata" in r, f"Result {i} missing metadata"
        assert "doc_name" in r["metadata"], f"Result {i} metadata missing doc_name"
        assert "page_num" in r["metadata"], f"Result {i} metadata missing page_num"
    print("Contract verified: All results adhere to List[{chunk_id, score, text, metadata}]")

    print("\n" + "=" * 60)
    print("STEP 2 VERIFICATION: ALL HYBRID SEARCH TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_step2_tests()
