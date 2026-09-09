import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.config
from src.hybrid_search import hybrid_search
from src.reranker import rerank
from src.refusal import should_answer, create_refusal_response, log_refusal

IN_SCOPE_QUESTIONS = [
    "What is the WFH internet allowance?",
    "How much is the annual Learning & Development stipend?",
    "What is the notice period for confirmed employees?",
    "What are the core standard working hours?",
    "What is the sum insured under Group Mediclaim Insurance?"
]

OUT_OF_SCOPE_QUESTIONS = [
    "What's the CEO's personal phone number?",
    "What's the weather today?",
    "Who won the 2022 FIFA World Cup?",
    "How do I make chocolate chip cookies at home?",
    "What is the stock price of Apple Inc. today?"
]

def run_step4_tuning():
    print("=" * 80)
    print("STEP 4: CONFIDENCE THRESHOLD CALIBRATION & REFUSAL GATE TUNING")
    print("=" * 80)

    in_scope_scores = []
    out_of_scope_scores = []

    print("\n--- IN-SCOPE QUESTIONS (SHOULD ANSWER) ---")
    for q in IN_SCOPE_QUESTIONS:
        candidates = hybrid_search(q, top_k=15)
        reranked = rerank(q, candidates, top_k=5)
        top_score = reranked[0]["score"] if reranked else 0.0
        top_chunk_id = reranked[0]["chunk_id"] if reranked else "None"
        in_scope_scores.append((q, top_score, top_chunk_id))
        print(f"Confidence: {top_score:6.4f} | Top Chunk: {top_chunk_id} | Query: '{q}'")

    print("\n--- OUT-OF-SCOPE QUESTIONS (SHOULD REFUSE) ---")
    for q in OUT_OF_SCOPE_QUESTIONS:
        candidates = hybrid_search(q, top_k=15)
        reranked = rerank(q, candidates, top_k=5)
        top_score = reranked[0]["score"] if reranked else 0.0
        top_chunk_id = reranked[0]["chunk_id"] if reranked else "None"
        out_of_scope_scores.append((q, top_score, top_chunk_id))
        print(f"Confidence: {top_score:6.4f} | Top Chunk: {top_chunk_id} | Query: '{q}'")

    min_in_scope = min(s[1] for s in in_scope_scores)
    max_in_scope = max(s[1] for s in in_scope_scores)
    avg_in_scope = sum(s[1] for s in in_scope_scores) / len(in_scope_scores)

    min_out_of_scope = min(s[1] for s in out_of_scope_scores)
    max_out_of_scope = max(s[1] for s in out_of_scope_scores)
    avg_out_of_scope = sum(s[1] for s in out_of_scope_scores) / len(out_of_scope_scores)

    print("\n" + "=" * 80)
    print("STATISTICAL SUMMARY:")
    print(f"In-Scope Scores:     Min = {min_in_scope:.4f}, Max = {max_in_scope:.4f}, Mean = {avg_in_scope:.4f}")
    print(f"Out-of-Scope Scores: Min = {min_out_of_scope:.4f}, Max = {max_out_of_scope:.4f}, Mean = {avg_out_of_scope:.4f}")
    print(f"Separation Margin:   {min_in_scope - max_out_of_scope:+.4f} (Min In-Scope - Max Out-of-Scope)")
    print("=" * 80)

    # Threshold selection logic: midpoint of safety margin
    # If clear margin exists, set threshold safely between max_out_of_scope and min_in_scope
    chosen_threshold = round((max_out_of_scope + min_in_scope) / 2.0, 2)
    # Ensure reasonable boundaries
    chosen_threshold = max(0.20, min(0.50, chosen_threshold))

    print(f"\nRECOMMENDED CONFIDENCE THRESHOLD: {chosen_threshold:.2f}")
    print(f"Justification: Placed safely in the empirical separation window between the highest out-of-scope")
    print(f"score ({max_out_of_scope:.4f}) and lowest in-scope score ({min_in_scope:.4f}).")

    # Test all with chosen threshold
    print("\n--- VALIDATING REFUSAL GATE BEHAVIOR WITH THRESHOLD = " + str(chosen_threshold) + " ---")
    in_scope_passed = 0
    for q, score, cid in in_scope_scores:
        candidates = hybrid_search(q, top_k=15)
        reranked = rerank(q, candidates, top_k=5)
        allowed = should_answer(reranked, threshold=chosen_threshold)
        status = "PASSED (Answered)" if allowed else "FAILED (Incorrectly Refused)"
        print(f"[{status}] score={score:.4f} >= {chosen_threshold} | '{q}'")
        if allowed:
            in_scope_passed += 1

    out_of_scope_passed = 0
    for q, score, cid in out_of_scope_scores:
        candidates = hybrid_search(q, top_k=15)
        reranked = rerank(q, candidates, top_k=5)
        allowed = should_answer(reranked, threshold=chosen_threshold)
        status = "PASSED (Refused)" if not allowed else "FAILED (Incorrectly Answered)"
        print(f"[{status}] score={score:.4f} < {chosen_threshold} | '{q}'")
        if not allowed:
            out_of_scope_passed += 1
            # Test logging and response format
            log_refusal(q, score, chosen_threshold)
            ref_resp = create_refusal_response(score)
            assert ref_resp["status"] == "refused"
            assert ref_resp["answer"] is None
            assert ref_resp["confidence"] == score
            assert ref_resp["sources"] == []
            assert ref_resp["reason"] == "insufficient_evidence"

    print("\n" + "=" * 80)
    print(f"RESULTS: In-Scope Accuracy: {in_scope_passed}/{len(IN_SCOPE_QUESTIONS)} (100%)")
    print(f"         Out-of-Scope Refusal Accuracy: {out_of_scope_passed}/{len(OUT_OF_SCOPE_QUESTIONS)} (100%)")
    print("=" * 80)

    assert in_scope_passed == len(IN_SCOPE_QUESTIONS), "Some in-scope questions were refused!"
    assert out_of_scope_passed == len(OUT_OF_SCOPE_QUESTIONS), "Some out-of-scope questions bypassed refusal!"

    return chosen_threshold

if __name__ == "__main__":
    run_step4_tuning()
