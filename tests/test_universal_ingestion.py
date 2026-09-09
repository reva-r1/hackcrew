import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import src.config
from src.ingestion import ingest_document
from src.hybrid_search import hybrid_search
from src.reranker import rerank
from src.refusal import should_answer
from src.generator import generate_answer, format_sources

def run_universal_test():
    print("=" * 75)
    print("UNIVERSAL MULTI-FORMAT INGESTION & OCR TEST")
    print("=" * 75)

    # 1. Ingest Plain Text
    txt_path = "data/docs/cloud_security_guidelines.txt"
    print(f"\n1. Ingesting Plain Text: {txt_path} ...")
    res_txt = ingest_document(txt_path, "cloud_security_guidelines.txt")
    print(f"   Result: {res_txt}")
    assert res_txt["status"] == "success"
    assert res_txt["chunks_created"] > 0

    # 2. Ingest Word Document (.docx)
    docx_path = "data/docs/employee_wellness_policy.docx"
    print(f"\n2. Ingesting Word Doc (.docx): {docx_path} ...")
    res_docx = ingest_document(docx_path, "employee_wellness_policy.docx")
    print(f"   Result: {res_docx}")
    assert res_docx["status"] == "success"
    assert res_docx["chunks_created"] > 0

    # 3. Ingest Image with OCR (.png)
    img_path = "data/docs/office_catering_menu.png"
    print(f"\n3. Ingesting Image via OCR (.png): {img_path} ...")
    res_img = ingest_document(img_path, "office_catering_menu.png")
    print(f"   Result: {res_img}")
    assert res_img["status"] == "success"
    assert res_img["chunks_created"] > 0

    print("\n" + "-" * 75)
    print("TESTING RETRIEVAL & GROUNDING ACROSS INGESTED FORMATS:")
    print("-" * 75)

    queries = [
        ("Where must API keys and secrets be stored?", "cloud_security_guidelines.txt", "Vault"),
        ("How much is the annual gym and fitness reimbursement?", "employee_wellness_policy.docx", "18,000"),
        ("What time is cafeteria breakfast served?", "office_catering_menu.png", "breakfast")
    ]

    for q, expected_doc, expected_keyword in queries:
        print(f"\n👉 Query: '{q}'")
        candidates = hybrid_search(q, top_k=15)
        reranked = rerank(q, candidates, top_k=5)
        
        assert len(reranked) > 0, f"No results for query: {q}"
        top = reranked[0]
        score = top["score"]
        doc = top["metadata"].get("doc_name")
        print(f"   Top Hit Doc:   {doc}")
        print(f"   Confidence:    {score:.4f}")
        print(f"   Snippet:       {top['text'][:120]}...")

        assert expected_doc in doc, f"Expected {expected_doc}, got {doc}"
        assert should_answer(reranked, threshold=0.40) is True, f"Failed refusal gate on in-scope query: {q}"
        assert expected_keyword.lower() in top["text"].lower(), f"Keyword {expected_keyword} missing from top chunk!"

        # Generate answer
        answer = generate_answer(q, [top])
        print(f"   LLM Answer:    {answer}")
        assert answer is not None and len(answer) > 0

    print("\n" + "=" * 75)
    print("🎉 UNIVERSAL FILE INGESTION & OCR VERIFIED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    run_universal_test()
