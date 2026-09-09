import sys
import requests
import json
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

def test_csv():
    print("========================================")
    print("TESTING CSV FILE UPLOAD & RAG RETRIEVAL")
    print("========================================")

    # 1. Health check
    res = client.get(f"{BASE_URL}/health")
    assert res.status_code == 200
    print("[PASS] Server online.")

    # 2. Upload CSV
    user_csv = Path("data/docs/_MConverter.eu_shit.csv")
    if not user_csv.exists():
        user_csv = Path("_MConverter.eu_shit.csv")
    assert user_csv.exists(), "User CSV file not found"
    print(f"\n1. Uploading user's CSV: {user_csv.name}...")
    with open(user_csv, "rb") as f:
        res = client.post(f"{BASE_URL}/upload", files={"file": (user_csv.name, f, "text/csv")})
    assert res.status_code == 200
    data = res.json()
    print("Upload response:", json.dumps(data, indent=2))
    assert data["status"] == "success"
    assert data["chunks_created"] > 0
    print(f"[PASS] User CSV uploaded and indexed successfully! ({data['chunks_created']} chunks)")

    # 3. Create & upload a tabular CSV
    tabular_csv = Path("data/test_assets/employee_shipping_matrix.csv")
    tabular_csv.parent.mkdir(parents=True, exist_ok=True)
    tabular_csv.write_text(
        "Region,Carrier,Delivery Speed,Signature Required,Insurance Cap\n"
        "North America,FedEx Ground,3-5 Days,Over $100,$5000\n"
        "Europe,DHL Express,2-4 Days,Always,$10000\n"
        "Asia Pacific,Yamato Global,4-7 Days,Always,$7500\n"
        "Latin America,Correos Priority,7-10 Days,Over $50,$2500\n",
        encoding="utf-8"
    )
    print(f"\n2. Uploading tabular CSV: {tabular_csv.name}...")
    with open(tabular_csv, "rb") as f:
        res = client.post(f"{BASE_URL}/upload", files={"file": (tabular_csv.name, f, "text/csv")})
    assert res.status_code == 200
    data = res.json()
    print("Upload response:", json.dumps(data, indent=2))
    assert data["status"] == "success"
    print("[PASS] Tabular CSV uploaded and structured records indexed!")

    # 4. Check /uploaded-files
    print("\n3. Checking /uploaded-files...")
    res = client.get(f"{BASE_URL}/uploaded-files")
    file_names = [f["name"] for f in res.json().get("files", [])]
    print(f"Files found: {file_names}")
    assert "_MConverter.eu_shit.csv" in file_names
    assert "employee_shipping_matrix.csv" in file_names
    print("[PASS] Both CSV files present in uploaded files library.")

    # 5. Query user CSV
    print("\n4. Querying user CSV: 'Who is the document owner of the shipping policy?'")
    res = client.post(f"{BASE_URL}/query", json={"query": "Who is the document owner of the shipping company policy?"})
    data = res.json()
    print("Answer:", json.dumps(data, indent=2))
    assert data["status"] == "answered"
    assert "shipping operations" in data["answer"].lower()
    assert any("_MConverter.eu_shit.csv" in s["doc_name"] for s in data["sources"])
    print("[PASS] Correctly answered from user's CSV!")

    # 6. Query tabular CSV
    print("\n5. Querying tabular CSV: 'What is the carrier and delivery speed for Europe?'")
    res = client.post(f"{BASE_URL}/query", json={"query": "What carrier and delivery speed are used for Europe in the shipping matrix?"})
    data = res.json()
    print("Answer:", json.dumps(data, indent=2))
    assert data["status"] == "answered"
    assert "dhl" in data["answer"].lower() or "2-4" in data["answer"]
    assert any("employee_shipping_matrix.csv" in s["doc_name"] for s in data["sources"])
    print("[PASS] Correctly answered from tabular CSV!")

    print("\n========================================")
    print("ALL CSV INGESTION & RETRIEVAL TESTS PASSED 100%!")
    print("========================================")

if __name__ == "__main__":
    test_csv()
