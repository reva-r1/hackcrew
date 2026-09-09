import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import config first to ensure BLAS thread limits are set before library imports
import src.config
from src.ingestion import ingest_document
from src.database import get_all_chunks, get_total_chunks_count
from src.vector_store import VectorStore
from src.bm25_index import BM25Index

def run_step1_tests():
    print("=" * 60)
    print("STEP 1 TEST: INGESTION PIPELINE VERIFICATION")
    print("=" * 60)

    pdf_path = "data/docs/HR_Policy_2026.pdf"
    doc_name = "HR_Policy_2026.pdf"

    print(f"Testing ingestion with file: {pdf_path}")
    result = ingest_document(file_path=pdf_path, doc_name=doc_name)
    print(f"Ingestion result: {result}")

    assert result["status"] == "success", f"Ingestion failed: {result}"
    assert result["chunks_created"] > 0, "No chunks created"
    assert len(result["doc_id"]) > 0, "doc_id is empty"

    # Verify SQLite metadata storage
    total_db_chunks = get_total_chunks_count()
    all_chunks = get_all_chunks()
    print(f"SQLite chunks count: {total_db_chunks}")
    assert total_db_chunks >= result["chunks_created"], f"DB count mismatch: {total_db_chunks}"

    # Verify fields of sample chunk
    first_chunk = all_chunks[0]
    print(f"\nSample Chunk Record in SQLite:")
    print(f" - chunk_id: {first_chunk['chunk_id']}")
    print(f" - doc_name: {first_chunk['doc_name']}")
    print(f" - page_num: {first_chunk['page_num']}")
    print(f" - chunk_text length: {len(first_chunk['chunk_text'])} chars")
    print(f" - preview: {first_chunk['chunk_text'][:120]}...")

    assert first_chunk["doc_name"] == doc_name
    assert first_chunk["page_num"] is not None
    assert len(first_chunk["chunk_text"]) > 0

    # Verify Vector Store (Chroma)
    v_store = VectorStore()
    v_count = v_store.count()
    print(f"\nVector Store (Chroma) count: {v_count}")
    assert v_count >= result["chunks_created"], f"Vector store count mismatch: {v_count}"

    # Verify BM25 Index
    bm25 = BM25Index()
    bm25_count = bm25.count()
    print(f"BM25 Index count: {bm25_count}")
    assert bm25_count >= result["chunks_created"], f"BM25 index count mismatch: {bm25_count}"

    # Check that a specific keyword can be searched in BM25
    bm25_results = bm25.search("internet allowance", top_k=3)
    print(f"\nBM25 quick sanity search for 'internet allowance': {len(bm25_results)} matches")
    assert len(bm25_results) > 0, "BM25 failed to find 'internet allowance'"
    print(f"Top BM25 hit chunk: {bm25_results[0]['chunk_id']} (score: {bm25_results[0]['score']:.4f})")
    print(f"Snippet: {bm25_results[0]['text'][:120]}...")

    print("\n" + "=" * 60)
    print("STEP 1 VERIFICATION: ALL ASSERTIONS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_step1_tests()
