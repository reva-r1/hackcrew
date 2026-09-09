import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import requests

BASE_URL = "http://127.0.0.1:8000"

class HttpClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        try:
            r = requests.get(f"{base_url}/health", timeout=0.5)
            self.use_http = (r.status_code == 200)
        except Exception:
            self.use_http = False
        if self.use_http:
            self.session = requests.Session()
        else:
            from fastapi.testclient import TestClient
            from src.app import app
            self.test_client = TestClient(app)
    
    def post(self, path: str, json: dict):
        if self.use_http:
            return self.session.post(f"{self.base_url}{path}", json=json, timeout=30)
        else:
            return self.test_client.post(path, json=json)

client = HttpClient(BASE_URL)

def test_preview_confidence_typing_simulation():
    print("\n" + "=" * 70)
    print("STEP 4: LIVE CONFIDENCE PREVIEW TEST — TYPING SIMULATION")
    print("=" * 70)

    # Progression 1: In-scope Leave Policy question simulated typing
    in_scope_typing_sequence = [
        "what is the le",
        "what is the leave",
        "what is the leave pol",
        "what is the leave policy",
        "what is the annual leave allowance for full time employees"
    ]

    print("\n[Sequence 1: In-Scope Policy Query Typing]")
    print(f"{'Partial Query Typed':<60} | {'Score':<6} | {'Status':<14} | {'Latency':<8}")
    print("-" * 96)

    # Pre-warm embedder to eliminate first-call weight loading from latency measurement
    client.post("/preview-confidence", json={"partial_query": "warmup"})

    scores = []
    for partial in in_scope_typing_sequence:
        t0 = time.perf_counter()
        resp = client.post("/preview-confidence", json={"partial_query": partial})
        latency_ms = (time.perf_counter() - t0) * 1000
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        score = data["score"]
        status = data["status"]
        scores.append(score)
        print(f"{partial:<60} | {score:>5.1f}  | {status:<14} | {latency_ms:>5.1f}ms")
        assert latency_ms < 200, f"Latency {latency_ms}ms exceeded 200ms threshold!"

    # Verify score trends upward sensibly as the query becomes more complete and specific
    print("\nVerification check: score increases as query becomes more specific:")
    print(f"Initial fragment ('{in_scope_typing_sequence[0]}') score: {scores[0]}")
    print(f"Complete query    ('{in_scope_typing_sequence[-1]}') score: {scores[-1]}")
    assert scores[-1] > scores[0], "Expected score to increase as query becomes more specific!"
    assert scores[0] < 40, f"Initial 14-char fragment should start low (<40), got {scores[0]}"
    assert scores[-1] >= 70, f"Fully qualified query should be strong_match (>=70), got {scores[-1]}"

    # Progression 2: Out-of-scope question simulated typing
    out_of_scope_typing_sequence = [
        "what's the wea",
        "what's the weather",
        "what's the weather to",
        "what's the weather today in tokyo"
    ]

    print("\n[Sequence 2: Out-of-Scope Query Typing]")
    print(f"{'Partial Query Typed':<60} | {'Score':<6} | {'Status':<14} | {'Latency':<8}")
    print("-" * 96)

    oos_scores = []
    for partial in out_of_scope_typing_sequence:
        t0 = time.perf_counter()
        resp = client.post("/preview-confidence", json={"partial_query": partial})
        latency_ms = (time.perf_counter() - t0) * 1000
        assert resp.status_code == 200
        data = resp.json()
        score = data["score"]
        status = data["status"]
        oos_scores.append(score)
        print(f"{partial:<60} | {score:>5.1f}  | {status:<14} | {latency_ms:>5.1f}ms")
        assert latency_ms < 200, f"Latency {latency_ms}ms exceeded 200ms threshold!"
        assert score < 40, f"Out-of-scope query score should remain <40 (no_match), got {score}"
        assert status == "no_match", f"Expected 'no_match', got {status}"

    # Performance / In-memory Cache Benchmark
    print("\n[Sequence 3: In-Memory Cache Latency Test]")
    test_q = "what is the leave policy"
    t0 = time.perf_counter()
    resp1 = client.post("/preview-confidence", json={"partial_query": test_q})
    first_latency = (time.perf_counter() - t0) * 1000
    
    t0 = time.perf_counter()
    resp2 = client.post("/preview-confidence", json={"partial_query": test_q})
    cache_latency = (time.perf_counter() - t0) * 1000
    print(f"First request latency: {first_latency:.2f}ms")
    print(f"Cached request latency: {cache_latency:.2f}ms (Speedup: {first_latency / max(0.001, cache_latency):.1f}x)")
    assert resp1.json() == resp2.json()

    print("\n" + "=" * 70)
    print("ALL PREVIEW CONFIDENCE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70 + "\n")

def test_company_policy_broad_question():
    print("\n" + "=" * 70)
    print("TEST: 'explain or what is the policy os this company' ANSWERS PROPERLY")
    print("=" * 70)

    query = "explain or what is the policy os this company"
    t0 = time.perf_counter()
    resp = client.post("/query", json={"query": query})
    dur = time.perf_counter() - t0
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    print(f"Query: '{query}'")
    print(f"Status: {data.get('status')}")
    print(f"Confidence: {data.get('confidence')}")
    print(f"Answer:\n{data.get('answer')}")
    print(f"Sources Count: {len(data.get('sources', []))}")
    print(f"Duration: {dur:.2f}s")
    
    assert data["status"] == "answered", f"Expected status 'answered', got: {data.get('status')} (Reason: {data.get('reason')})"
    assert data["answer"] and len(data["answer"]) > 50, "Expected a substantive, detailed policy answer!"
    assert data["confidence"] is not None and data["confidence"] > 0.5, "Expected high confidence for policy overview!"
    print("\nSUCCESS: The company policy question was answered thoroughly, NOT refused!")

if __name__ == "__main__":
    test_preview_confidence_typing_simulation()
    test_company_policy_broad_question()
