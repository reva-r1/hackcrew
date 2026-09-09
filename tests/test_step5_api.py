import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import src.config
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_health_check():
    print("\n[TEST] Health Check (/health)...")
    res = client.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print(f"Response: {data}")
    assert data == {"status": "ok"}, f"Unexpected health response: {data}"
    print("Health check passed.")

def test_query_refused():
    print("\n[TEST] Query Refusal (/query - Out-of-Scope)...")
    payload = {
        "query": "What's the CEO's personal phone number?",
        "role": "employee"
    }
    res = client.post("/query", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print(f"Response: {data}")

    # Exact contract checks for refused case
    assert data["status"] == "refused"
    assert data["answer"] is None
    assert isinstance(data["confidence"], (int, float))
    assert data["confidence"] < 0.40
    assert data["sources"] == []
    assert data["reason"] == "insufficient_evidence"
    print("Refusal test passed with exact schema.")

def test_query_answered():
    print("\n[TEST] Query Answered (/query - In-Scope with mocked LLM)...")
    payload = {
        "query": "What is the WFH internet allowance?",
        "role": "employee"
    }

    mock_answer = "The WFH internet allowance is ₹1,500 per month, reimbursed quarterly upon submission of valid invoices."

    with patch("src.app.generate_answer", return_value=mock_answer):
        res = client.post("/query", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        print(f"Response: {data}")

        # Exact contract checks for answered case
        assert data["status"] == "answered"
        assert data["answer"] == mock_answer
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0
        
        for s in data["sources"]:
            assert "doc_name" in s
            assert "page_num" in s
            assert "snippet" in s
            assert isinstance(s["doc_name"], str)
            assert isinstance(s["snippet"], str)
            assert len(s["snippet"]) > 0
            print(f" - Source: {s['doc_name']} (Page {s['page_num']}): {s['snippet']}")

        # Reason should NOT be in answered response
        assert "reason" not in data or data["reason"] is None
        print("Answered test passed with exact schema.")

def test_query_error():
    print("\n[TEST] Query Error Case (/query - LLM Generation Failure)...")
    payload = {
        "query": "What is the WFH internet allowance?",
        "role": "employee"
    }

    with patch("src.app.generate_answer", return_value=None):
        res = client.post("/query", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        print(f"Response: {data}")

        # Exact contract checks for error case
        assert data["status"] == "error"
        assert data["answer"] is None
        assert data["confidence"] is None
        assert data["sources"] == []
        assert data["reason"] == "generation_failed"
        print("Error case test passed with exact schema.")

def test_upload_endpoint():
    print("\n[TEST] Document Upload (/upload)...")
    pdf_path = Path("data/docs/HR_Policy_2026.pdf")
    with open(pdf_path, "rb") as f:
        res = client.post("/upload", files={"file": ("HR_Policy_2026_reupload.pdf", f, "application/pdf")})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print(f"Upload Response: {data}")
    assert data["status"] == "success"
    assert data["chunks_created"] > 0
    assert len(data["doc_id"]) > 0
    print("Upload endpoint test passed.")

def run_step5_tests():
    print("=" * 60)
    print("STEP 5 TEST: API RESPONSE SCHEMA & FASTAPI ENDPOINTS VERIFICATION")
    print("=" * 60)

    test_health_check()
    test_query_refused()
    test_query_answered()
    test_query_error()
    test_upload_endpoint()

    print("\n" + "=" * 60)
    print("STEP 5 VERIFICATION: ALL API TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_step5_tests()
