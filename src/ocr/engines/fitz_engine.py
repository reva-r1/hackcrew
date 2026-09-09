from typing import List, Dict, Any
from src.ocr.base import BaseOCREngine
import fitz  # PyMuPDF

class PyMuPDFEngine(BaseOCREngine):
    """
    Lightweight, high-speed document layout engine using PyMuPDF.
    Always available and runs without external C++ system dependencies.
    """

    def get_name(self) -> str:
        return "pymupdf"

    def get_version(self) -> str:
        return fitz.__version__

    def is_available(self) -> bool:
        return True

    def perform_ocr(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Parses words and layout directly from image or document page.
        """
        # Open image with fitz
        doc = fitz.open(image_path)
        page = doc[0]
        words_raw = page.get_text("words")  # returns list of (x0, y0, x1, y1, word, block_no, line_no, word_no)

        words = []
        for w in words_raw:
            x0, y0, x1, y1, word, block_num, line_num, word_num = w
            words.append({
                "text": str(word).strip(),
                "bbox": (float(x0), float(y0), float(x1), float(y1)),
                "confidence": 0.98,
                "block_num": int(block_num),
                "line_num": int(line_num),
                "word_num": int(word_num)
            })

        doc.close()
        return words
