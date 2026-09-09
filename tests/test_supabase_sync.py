import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import src.config
from fastapi.testclient import TestClient
from src.app import app
from src.supabase_client import get_supabase

client = TestClient(app)

print("1. Sending in-scope query...")
r1 = client.post("/query", json={"query": "What is the WFH internet allowance?"})
print("Result 1 status:", r1.json().get("status"))

print("\n2. Sending out-of-scope query...")
r2 = client.post("/query", json={"query": "What is the weather today?"})
print("Result 2 status:", r2.json().get("status"))

print("\n3. Querying Supabase 'query_logs' table...")
supabase = get_supabase()
logs = supabase.table("query_logs").select("*").order("created_at", desc=True).limit(5).execute()

print(f"\nFound {len(logs.data)} logs in Supabase:")
for row in logs.data:
    print(f" - [{row['status'].upper()}] Conf: {row['confidence']} | Query: '{row['query']}' | Answer: {str(row['answer'])[:60]}...")
