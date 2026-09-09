import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.ocr import (
    BlockSchema,
    BlockType,
    BoundingBox,
    OCRConfidenceCalculator,
    OCRLayoutBuilder,
    PageDetector,
    OCRStrategy,
    DocumentOCRPipeline,
)
from src.ocr.engines.fitz_engine import PyMuPDFEngine

def test_confidence_calculator():
    print("\n--- TEST 1: OCRConfidenceCalculator ---")
    
    # 1. Test word metadata
    words = [
        {"text": "Enterprise", "confidence": 0.95},
        {"text": "Policy", "confidence": 0.88},
        {"text": "LowQuality", "confidence": 0.55},
        {"text": "Medium", "confidence": 0.75}
    ]
    meta = OCRConfidenceCalculator.build_confidence_metadata(words, page_number=1)
    print(f"Confidence Metadata: {meta}")
    assert meta["page_number"] == 1
    assert meta["word_count"] == 4
    assert meta["confidence_distribution"]["high_greater_than_85"] == 2
    assert meta["confidence_distribution"]["medium_60_to_85"] == 1
    assert meta["confidence_distribution"]["low_less_than_60"] == 1

    # 2. Test block and document confidence
    b1 = BlockSchema(
        block_id="b1", page_number=1, reading_order=1, block_type=BlockType.PARAGRAPH,
        text="Sample text", bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=20),
        confidence=0.90, provenance="OCR"
    )
    b2 = BlockSchema(
        block_id="b2", page_number=1, reading_order=2, block_type=BlockType.PARAGRAPH,
        text="Another line", bounding_box=BoundingBox(x0=0, y0=25, x1=100, y1=45),
        confidence=0.80, provenance="OCR"
    )
    page_conf = OCRConfidenceCalculator.calculate_page_confidence([b1, b2])
    print(f"Calculated Page Confidence: {page_conf}")
    assert page_conf == 0.85

    doc_conf = OCRConfidenceCalculator.calculate_document_confidence([0.85, 0.95])
    print(f"Calculated Document Confidence: {doc_conf}")
    assert doc_conf == 0.90
    print("✅ Confidence Calculator assertions passed.")

def test_page_detector():
    print("\n--- TEST 2: PageDetector ---")
    detector = PageDetector(char_threshold=50)

    # Low character count block (needs OCR)
    sparse_blocks = [
        BlockSchema(
            block_id="s1", page_number=1, reading_order=1, text="Logo",
            bounding_box=BoundingBox(x0=0, y0=0, x1=50, y1=20)
        )
    ]
    assert detector.evaluate_page(1, sparse_blocks, OCRStrategy.AUTO) is True
    print(" - Sparse page detected as needing OCR (AUTO): PASS")

    # High character count block (does not need OCR)
    dense_blocks = [
        BlockSchema(
            block_id="d1", page_number=1, reading_order=1,
            text="This is a fully digital document page containing plenty of selectable digital text characters.",
            bounding_box=BoundingBox(x0=0, y0=0, x1=500, y1=100)
        )
    ]
    assert detector.evaluate_page(1, dense_blocks, OCRStrategy.AUTO) is False
    print(" - Dense page detected as digital (AUTO): PASS")

    # Strategy overrides
    assert detector.evaluate_page(1, dense_blocks, OCRStrategy.FORCE) is True
    assert detector.evaluate_page(1, sparse_blocks, OCRStrategy.SKIP) is False
    print(" - FORCE and SKIP strategy overrides: PASS")
    print("✅ Page Detector assertions passed.")

def test_layout_builder():
    print("\n--- TEST 3: OCRLayoutBuilder ---")
    builder = OCRLayoutBuilder()

    sample_words = [
        {"text": "1.", "bbox": (10, 10, 20, 25), "confidence": 0.98, "block_num": 1, "line_num": 1},
        {"text": "Code", "bbox": (25, 10, 55, 25), "confidence": 0.97, "block_num": 1, "line_num": 1},
        {"text": "of", "bbox": (60, 10, 75, 25), "confidence": 0.99, "block_num": 1, "line_num": 1},
        {"text": "Conduct", "bbox": (80, 10, 140, 25), "confidence": 0.95, "block_num": 1, "line_num": 1},
        {"text": "All", "bbox": (10, 40, 30, 55), "confidence": 0.96, "block_num": 2, "line_num": 1},
        {"text": "employees", "bbox": (35, 40, 100, 55), "confidence": 0.92, "block_num": 2, "line_num": 1},
        {"text": "must", "bbox": (105, 40, 140, 55), "confidence": 0.94, "block_num": 2, "line_num": 1},
        {"text": "adhere.", "bbox": (145, 40, 190, 55), "confidence": 0.95, "block_num": 2, "line_num": 1},
    ]

    blocks = builder.build_layout_blocks(
        words=sample_words,
        page_number=1,
        img_size=(800, 1000),
        pdf_size=(612.0, 792.0)
    )

    print(f"Generated {len(blocks)} layout blocks from word coordinates:")
    for b in blocks:
        print(f" - [{b.block_type}] (conf: {b.confidence}, font: {b.font_size:.1f}pt) Text: '{b.text}'")

    assert len(blocks) == 2
    assert blocks[0].text == "1. Code of Conduct"
    assert blocks[1].text == "All employees must adhere."
    print("✅ Layout Builder assertions passed.")

def test_pipeline_on_document():
    print("\n--- TEST 4: End-to-End DocumentOCRPipeline ---")
    pipeline = DocumentOCRPipeline()
    pdf_path = "data/docs/HR_Policy_2026.pdf"

    print(f"Running OCR pipeline on: {pdf_path}")
    result = pipeline.process_pdf(pdf_path, strategy=OCRStrategy.AUTO)

    print(f"Document Name:        {result['document_name']}")
    print(f"Total Pages:          {result['total_pages']}")
    print(f"Engine Used:          {result['engine_used']}")
    print(f"Document Confidence:  {result['document_confidence']:.3f}")

    assert result["total_pages"] == 15
    assert result["document_confidence"] > 0.80
    assert len(result["pages"]) == 15

    # Check page 12 (WFH allowance)
    p12 = result["pages"][11]
    print(f"\nPage 12 Overview:")
    print(f" - Provenance:   {p12['provenance']}")
    print(f" - Confidence:   {p12['confidence']}")
    print(f" - Blocks Count: {p12['blocks_count']}")
    print(f" - Preview Text: {p12['text'][:120]}...")
    assert "internet allowance" in p12["text"].lower()

    print("\n" + "=" * 60)
    print("ALL OCR TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_confidence_calculator()
    test_page_detector()
    test_layout_builder()
    test_pipeline_on_document()
