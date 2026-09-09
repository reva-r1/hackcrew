import sys
import requests
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_URL = "http://127.0.0.1:8000"

def _get_client():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=0.5)
        if r.status_code == 200:
            return requests.Session()
    except Exception:
        pass
    from fastapi.testclient import TestClient
    from src.app import app
    return TestClient(app)

client = _get_client()

def test_all():
    print("==================================================")
    print("RUNNING COMPREHENSIVE UNIVERSAL OCR & RAG TEST")
    print("==================================================")

    # 0. Health check
    res = client.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Backend health check OK.")

    # 1. Test PNG OCR Upload
    png_path = Path("data/test_assets/it_security_policy.png")
    print(f"\n1. Uploading & OCR processing PNG: {png_path}...")
    with open(png_path, "rb") as f:
        res = client.post(f"{BASE_URL}/upload", files={"file": ("it_security_policy.png", f, "image/png")})
    assert res.status_code == 200, f"Upload error: {res.text}"
    data = res.json()
    print("Response:", json.dumps(data, indent=2))
    assert data["status"] == "success", f"PNG upload failed: {data}"
    assert data["chunks_created"] > 0, "No chunks created"
    assert data["confidence"] > 0.70, f"Confidence too low: {data['confidence']}"
    assert "macbook" in data["preview_text"].lower() or "laptop" in data["preview_text"].lower() or "policy" in data["preview_text"].lower()
    print(f"[PASS] PNG OCR succeeded with {data['confidence']*100:.1f}% confidence. Chunks: {data['chunks_created']}")

    # 2. Test JPG OCR Upload
    jpg_path = Path("data/test_assets/corporate_travel_stipend.jpg")
    print(f"\n2. Uploading & OCR processing JPG: {jpg_path}...")
    with open(jpg_path, "rb") as f:
        res = client.post(f"{BASE_URL}/upload", files={"file": ("corporate_travel_stipend.jpg", f, "image/jpeg")})
    assert res.status_code == 200, f"Upload error: {res.text}"
    data = res.json()
    print("Response:", json.dumps(data, indent=2))
    assert data["status"] == "success", f"JPG upload failed: {data}"
    assert data["chunks_created"] > 0
    assert data["confidence"] > 0.70
    assert "$85" in data["preview_text"] or "diem" in data["preview_text"].lower() or "travel" in data["preview_text"].lower()
    print(f"[PASS] JPG OCR succeeded with {data['confidence']*100:.1f}% confidence. Chunks: {data['chunks_created']}")

    # 3. Test WEBP OCR Upload
    webp_path = Path("data/test_assets/campus_cafeteria_perks.webp")
    print(f"\n3. Uploading & OCR processing WEBP: {webp_path}...")
    with open(webp_path, "rb") as f:
        res = client.post(f"{BASE_URL}/upload", files={"file": ("campus_cafeteria_perks.webp", f, "image/webp")})
    assert res.status_code == 200, f"Upload error: {res.text}"
    data = res.json()
    print("Response:", json.dumps(data, indent=2))
    assert data["status"] == "success", f"WEBP upload failed: {data}"
    assert data["chunks_created"] > 0
    assert data["confidence"] > 0.70
    assert "lunch" in data["preview_text"].lower() or "breakfast" in data["preview_text"].lower() or "catering" in data["preview_text"].lower()
    print(f"[PASS] WEBP OCR succeeded with {data['confidence']*100:.1f}% confidence. Chunks: {data['chunks_created']}")

    # 4. Check GET /uploaded-files
    print("\n4. Checking GET /uploaded-files...")
    res = client.get(f"{BASE_URL}/uploaded-files")
    assert res.status_code == 200
    file_list = res.json().get("files", [])
    names = [f["name"] for f in file_list]
    print(f"Uploaded files in library ({len(file_list)} total): {names}")
    assert "it_security_policy.png" in names
    assert "corporate_travel_stipend.jpg" in names
    assert "campus_cafeteria_perks.webp" in names
    print("[PASS] All uploaded images found in file library.")

    # 5. Query chatbot on PNG contents
    print("\n5. Querying knowledge extracted from PNG: 'How often are engineering laptops replaced?'")
    res = client.post(f"{BASE_URL}/query", json={"query": "How often are engineering laptops replaced and what model do they get?"})
    data = res.json()
    print("RAG Response:", json.dumps(data, indent=2))
    assert data["status"] == "answered", f"Query was not answered: {data}"
    assert "24" in data["answer"] or "macbook" in data["answer"].lower()
    assert any("it_security_policy.png" in s["doc_name"] for s in data["sources"])
    print("[PASS] Chatbot correctly answered query from PNG OCR with proper citation!")

    # 6. Query chatbot on JPG contents
    print("\n6. Querying knowledge extracted from JPG: 'What is the domestic daily meal per diem stipend?'")
    res = client.post(f"{BASE_URL}/query", json={"query": "What is the domestic daily meal per diem rate?"})
    data = res.json()
    print("RAG Response:", json.dumps(data, indent=2))
    assert data["status"] == "answered", f"Query was not answered: {data}"
    assert "85" in data["answer"]
    assert any("corporate_travel_stipend.jpg" in s["doc_name"] for s in data["sources"])
    print("[PASS] Chatbot correctly answered query from JPG OCR with proper citation!")

    # 7. Query chatbot on WEBP contents
    print("\n7. Querying knowledge extracted from WEBP: 'What time is the buffet lunch served?'")
    res = client.post(f"{BASE_URL}/query", json={"query": "What time is the free catered artisan buffet lunch served?"})
    data = res.json()
    print("RAG Response:", json.dumps(data, indent=2))
    assert data["status"] == "answered", f"Query was not answered: {data}"
    assert "12:30" in data["answer"] or "lunch" in data["answer"].lower()
    assert any("campus_cafeteria_perks.webp" in s["doc_name"] for s in data["sources"])
    print("[PASS] Chatbot correctly answered query from WEBP OCR with proper citation!")

    # 8. Deterministic Refusal Check
    print("\n8. Checking deterministic refusal on out-of-scope question...")
    res = client.post(f"{BASE_URL}/query", json={"query": "What is the CEO's personal home address and secret phone number?"})
    data = res.json()
    print("Refusal Response:", json.dumps(data, indent=2))
    assert data["status"] == "refused", f"Expected refusal, got: {data['status']}"
    assert data["confidence"] < 0.40
    print("[PASS] Deterministic refusal correctly triggered for hallucination prevention.")

    print("\n==================================================")
    print("ALL UNIVERSAL OCR & MULTI-FORMAT TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_all()
