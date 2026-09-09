import sqlite3
from typing import List, Dict, Any, Optional
from src.config import SQLITE_DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database with the exact schema from ingestion-pipeline-spec.md"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            doc_name TEXT NOT NULL,
            page_num INTEGER,
            chunk_text TEXT NOT NULL,
            doc_summary TEXT,
            role_tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def insert_chunks(chunks_data: List[Dict[str, Any]]):
    """
    Inserts multiple chunk records into SQLite metadata store.
    Each item must contain: chunk_id, doc_id, doc_name, page_num, chunk_text, doc_summary, role_tags
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
        INSERT OR REPLACE INTO chunks (
            chunk_id, doc_id, doc_name, page_num, chunk_text, doc_summary, role_tags
        ) VALUES (
            :chunk_id, :doc_id, :doc_name, :page_num, :chunk_text, :doc_summary, :role_tags
        )
        """, chunks_data)
        conn.commit()

def get_chunk(chunk_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_chunks() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chunks ORDER BY created_at ASC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_total_chunks_count() -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        return cursor.fetchone()[0]

def delete_chunks_by_doc_name(doc_name: str):
    """Purges existing chunks for a doc_name to prevent duplicate accumulation upon re-ingestion."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks WHERE doc_name = ?", (doc_name,))
        conn.commit()

