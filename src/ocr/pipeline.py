import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from PIL import Image

from src.ocr.schemas import BlockSchema
from src.ocr.page_detector import PageDetector, OCRStrategy
from src.ocr.confidence import OCRConfidenceCalculator
from src.ocr.layout_builder import OCRLayoutBuilder
from src.ocr.classifier import DocumentClassifier
from src.ocr.engines.tesseract_engine import TesseractOCREngine
from src.ocr.engines.easyocr_engine import EasyOCREngine
from src.ocr.engines.fitz_engine import PyMuPDFEngine

class DocumentOCRPipeline:
    """
    End-to-end OCR and layout extraction pipeline combining:
    PageDetector -> Pluggable OCREngine -> OCRLayoutBuilder -> OCRConfidenceCalculator
    Supports both multi-page PDFs and standalone image files.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.detector = PageDetector(char_threshold=50)
        self.classifier = DocumentClassifier()
        self.layout_builder = OCRLayoutBuilder(classifier=self.classifier)
        
        # Pluggable engines: Tesseract -> EasyOCR -> PyMuPDF
        self.tesseract = TesseractOCREngine(tesseract_cmd or "tesseract")
        self.easyocr = EasyOCREngine()
        self.fitz_engine = PyMuPDFEngine()

    def get_engine(self):
        if self.tesseract.is_available():
            return self.tesseract
        if self.easyocr.is_available():
            return self.easyocr
        return self.fitz_engine

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Processes a standalone image file (PNG, JPG, TIFF, BMP, WEBP, etc.),
        running image preprocessing, OCR, and layout reconstruction.
        """
        from src.ocr.image_preprocessor import preprocess_image_for_ocr
        try:
            preprocess_image_for_ocr(image_path)
        except Exception as pe:
            print(f"Notice: Image preprocessor skipped: {pe}")

        with Image.open(image_path) as img:
            img_size = (img.width, img.height)
            pdf_size = (float(img.width), float(img.height))

        engine = self.get_engine()
        words = engine.perform_ocr(image_path)
        blocks = self.layout_builder.build_layout_blocks(
            words=words,
            page_number=1,
            img_size=img_size,
            pdf_size=pdf_size
        )

        page_conf = OCRConfidenceCalculator.calculate_page_confidence(blocks)
        conf_meta = OCRConfidenceCalculator.build_confidence_metadata(words, page_number=1)
        page_text = "\n\n".join([b.text for b in blocks if b.text.strip()])

        return {
            "document_name": Path(image_path).name,
            "total_pages": 1,
            "document_confidence": page_conf,
            "engine_used": engine.get_name(),
            "pages": [{
                "page_number": 1,
                "provenance": "OCR-" + engine.get_name().upper(),
                "confidence": page_conf,
                "confidence_metadata": conf_meta,
                "blocks_count": len(blocks),
                "blocks": [b.dict() for b in blocks],
                "text": page_text
            }],
            "full_text": page_text
        }

    def process_pdf(
        self,
        pdf_path: str,
        strategy: OCRStrategy = OCRStrategy.AUTO
    ) -> Dict[str, Any]:
        """
        Processes a PDF document page by page, triggering OCR where needed.
        Returns document text, layout blocks, and confidence metrics.
        """
        doc = fitz.open(pdf_path)
        pages_result = []
        page_confidences = []
        all_text_blocks = []

        engine = self.get_engine()

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc[page_idx]
            rect = page.rect
            pdf_size = (rect.width, rect.height)

            # Extract native text words to check if digital text already exists
            native_words_raw = page.get_text("words")
            native_words = []
            for w in native_words_raw:
                native_words.append({
                    "text": str(w[4]).strip(),
                    "bbox": (w[0], w[1], w[2], w[3]),
                    "confidence": 1.0,
                    "block_num": w[5],
                    "line_num": w[6],
                    "word_num": w[7]
                })

            initial_blocks = self.layout_builder.build_layout_blocks(
                words=native_words,
                page_number=page_num,
                img_size=(int(rect.width), int(rect.height)),
                pdf_size=pdf_size
            )

            # Check if page needs OCR
            needs_ocr = self.detector.evaluate_page(
                page_number=page_num,
                blocks=initial_blocks,
                strategy=strategy
            )

            if needs_ocr:
                # Render page to image for OCR
                pix = page.get_pixmap(dpi=200)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                    tmp_img_path = tmp_file.name
                    pix.save(tmp_img_path)

                try:
                    ocr_words = engine.perform_ocr(tmp_img_path)
                    blocks = self.layout_builder.build_layout_blocks(
                        words=ocr_words,
                        page_number=page_num,
                        img_size=(pix.width, pix.height),
                        pdf_size=pdf_size
                    )
                    used_words = ocr_words
                    provenance = "OCR-" + engine.get_name().upper()
                finally:
                    if os.path.exists(tmp_img_path):
                        os.remove(tmp_img_path)
            else:
                blocks = initial_blocks
                used_words = native_words
                provenance = "DIGITAL"

            page_conf = OCRConfidenceCalculator.calculate_page_confidence(blocks)
            page_confidences.append(page_conf)
            conf_meta = OCRConfidenceCalculator.build_confidence_metadata(used_words, page_num)

            page_text = "\n\n".join([b.text for b in blocks if b.text.strip()])
            all_text_blocks.append(page_text)

            pages_result.append({
                "page_number": page_num,
                "provenance": provenance,
                "confidence": page_conf,
                "confidence_metadata": conf_meta,
                "blocks_count": len(blocks),
                "blocks": [b.dict() for b in blocks],
                "text": page_text
            })

        doc.close()

        doc_conf = OCRConfidenceCalculator.calculate_document_confidence(page_confidences)

        return {
            "document_name": Path(pdf_path).name,
            "total_pages": len(pages_result),
            "document_confidence": doc_conf,
            "engine_used": engine.get_name(),
            "pages": pages_result,
            "full_text": "\n\n--- PAGE BREAK ---\n\n".join(all_text_blocks)
        }
