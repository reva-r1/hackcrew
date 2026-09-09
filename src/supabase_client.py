import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://wqqzhndzoiajrpzxpnsq.supabase.co")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndxcXpobmR6b2lhanJwenhwbnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg5MzkyOTUsImV4cCI6MjEwNDUxNTI5NX0.RpeD7DEEpbx58cpznWHBUcpQ0gc1w9VcDxd0VdGspTY"
)

_SUPABASE_CLIENT: Optional[Client] = None

def get_supabase() -> Optional[Client]:
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is None:
        try:
            if SUPABASE_URL and SUPABASE_KEY:
                _SUPABASE_CLIENT = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Warning: Could not initialize Supabase client: {e}")
            _SUPABASE_CLIENT = None
    return _SUPABASE_CLIENT

def sync_chunks_to_supabase(chunks: List[Dict[str, Any]]) -> bool:
    """Upserts chunk records into Supabase chunks table."""
    client = get_supabase()
    if not client or not chunks:
        return False

    try:
        # Prepare records matching schema
        records = []
        for c in chunks:
            records.append({
                "chunk_id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "doc_name": c["doc_name"],
                "page_num": c.get("page_num"),
                "chunk_text": c["chunk_text"],
                "doc_summary": c.get("doc_summary"),
                "role_tags": c.get("role_tags")
            })

        # Upsert in batches of 50
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            client.table("chunks").upsert(batch, on_conflict="chunk_id").execute()
        return True
    except Exception as e:
        print(f"Warning: Failed to sync chunks to Supabase: {e}")
        return False

def log_query_to_supabase(
    query: str,
    role: str = "employee",
    status: str = "answered",
    confidence: Optional[float] = None,
    answer: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    reason: Optional[str] = None
):
    """Logs query interactions and refusal metrics into Supabase cloud table."""
    client = get_supabase()
    if not client:
        return

    try:
        record = {
            "query": query,
            "role": role or "employee",
            "status": status,
            "confidence": confidence,
            "answer": answer,
            "sources": sources or [],
            "reason": reason
        }
        client.table("query_logs").insert(record).execute()
    except Exception as e:
        print(f"Warning: Failed to log query to Supabase: {e}")
