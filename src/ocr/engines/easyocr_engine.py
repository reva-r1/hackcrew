from typing import List, Dict, Any, Optional
from src.ocr.base import BaseOCREngine

_EASYOCR_READER = None

class EasyOCREngine(BaseOCREngine):
    """Concrete implementation of BaseOCREngine using EasyOCR (PyTorch-based, native, no C++ binaries)."""

    def __init__(self, languages: Optional[List[str]] = None):
        self.languages = languages or ['en']

    def get_name(self) -> str:
        return "easyocr"

    def get_version(self) -> str:
        try:
            import easyocr
            return getattr(easyocr, "__version__", "1.7.2")
        except Exception:
            return "unknown"

    def is_available(self) -> bool:
        try:
            import easyocr
            return True
        except ImportError:
            return False

    def perform_ocr(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Runs EasyOCR on an image file and extracts word/line layout elements with confidence.
        """
        global _EASYOCR_READER
        if _EASYOCR_READER is None:
            import easyocr
            _EASYOCR_READER = easyocr.Reader(self.languages, gpu=False)

        # returns list of (bbox, text, prob)
        # bbox is [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        raw_results = _EASYOCR_READER.readtext(image_path)

        words = []
        for idx, (poly, text, prob) in enumerate(raw_results, start=1):
            clean = text.strip()
            if not clean:
                continue

            x_coords = [p[0] for p in poly]
            y_coords = [p[1] for p in poly]
            x0, x1 = min(x_coords), max(x_coords)
            y0, y1 = min(y_coords), max(y_coords)

            words.append({
                "text": clean,
                "bbox": (float(x0), float(y0), float(x1), float(y1)),
                "confidence": round(float(prob), 3),
                "block_num": idx,
                "line_num": 1,
                "word_num": idx
            })

        return words
