import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def _get_client():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=0.5)
        if r.status_code == 200:
            return "http"
    except Exception:
        pass
    from fastapi.testclient import TestClient
    from src.app import app
    return TestClient(app)

_CLIENT = _get_client()

def post_query(payload: dict) -> dict:
    if _CLIENT == "http":
        return requests.post(f"{BASE_URL}/query", json=payload, timeout=30).json()
    else:
        return _CLIENT.post("/query", json=payload).json()

def test_step4():
    print("=" * 80)
    print("STEP 4 (PART 1): TEST BROAD / SUMMARIZATION PATH")
    print("=" * 80)
    
    summary_query = "what is this policy about?"
    print(f"Query: \"{summary_query}\"\n")
    
    res = post_query({"query": summary_query})
    print("Response JSON:")
    print(f"Status:     {res.get('status')}")
    print(f"Confidence: {res.get('confidence')}")
    print(f"Sources:    {len(res.get('sources', []))} sections cited")
    for s in res.get("sources", []):
        print(f"  - [{s.get('doc_name')} | Page {s.get('page_num')}]: \"{s.get('snippet')}\"")
    
    print("\nSynthesized Document Executive Summary:")
    print("-" * 70)
    print(res.get("answer"))
    print("-" * 70)
    
    assert res.get("status") == "answered", "Summary query failed to answer"
    assert res.get("confidence") == 1.0, "Summary query did not receive 1.0 confidence"
    assert len(res.get("sources", [])) > 1, "Expected multiple section sources for summary"
    print("\n[PASS] Summarization path successfully synthesized across multi-section chunks!\n")

    print("=" * 80)
    print("STEP 4 (PART 2): TEST NORMAL SPECIFIC-FACT & CONFIDENCE GATE PATH")
    print("=" * 80)
    
    test_suite = [
        # In-Scope Specific Facts
        ("What is the WFH internet allowance?", "in-scope-fact"),
        ("How much is the annual Learning & Development stipend?", "in-scope-fact"),
        ("What is the notice period for confirmed employees?", "in-scope-fact"),
        ("What are the core standard working hours?", "in-scope-fact"),
        ("Who is the document owner of the shipping policy?", "in-scope-fact"),
        # Out-of-Scope (Deterministic Refusal)
        ("What is the CEO's personal phone number?", "out-of-scope"),
        ("What is the capital of France?", "out-of-scope"),
        ("Who won the 2022 FIFA World Cup?", "out-of-scope"),
        ("What is the secret recipe for chocolate chip cookies?", "out-of-scope")
    ]
    
    all_passed = True
    print(f"{'Question':<55} | {'Path Type':<15} | {'Status':<10} | {'Conf':<6} | Result")
    print("-" * 100)
    
    for q, qtype in test_suite:
        r = post_query({"query": q})
        status = r.get("status")
        conf = r.get("confidence") or 0.0
        
        if qtype == "in-scope-fact":
            passed = (status == "answered") and (conf >= 0.40)
        else:
            passed = (status == "refused") and (conf < 0.40)
            
        if not passed:
            all_passed = False
            
        print(f"{q[:53]:<55} | {qtype:<15} | {status:<10} | {conf:<6.2f} | [{'PASS' if passed else 'FAIL'}]")
        
    print("-" * 100)
    print(f"\nFinal Verification Status: {'ALL TESTS PASSED 100%' if all_passed else 'FAILURES DETECTED'}")
    assert all_passed, "Not all tests passed in Step 4"

if __name__ == "__main__":
    test_step4()
