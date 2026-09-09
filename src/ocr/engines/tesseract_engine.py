import shutil
from typing import List, Dict, Any
from PIL import Image
from src.ocr.base import BaseOCREngine

class TesseractOCREngine(BaseOCREngine):
    """Concrete implementation of BaseOCREngine using Tesseract OCR."""

    def __init__(self, tesseract_cmd: str = "tesseract"):
        self.tesseract_cmd = tesseract_cmd

    def get_name(self) -> str:
        return "tesseract"

    def get_version(self) -> str:
        try:
            import pytesseract
            return str(pytesseract.get_tesseract_version())
        except Exception:
            return "unknown"

    def is_available(self) -> bool:
        try:
            import pytesseract
            return shutil.which(self.tesseract_cmd) is not None
        except Exception:
            return False

    def perform_ocr(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Runs Tesseract OCR via image_to_data and parses word layout elements.
        """
        if not self.is_available():
            raise RuntimeError("Tesseract OCR is not installed or not in PATH.")

        import pytesseract
        from pytesseract import Output

        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=Output.DICT)

        words = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            if not text or conf < 0:
                continue

            x = float(data['left'][i])
            y = float(data['top'][i])
            w = float(data['width'][i])
            h = float(data['height'][i])

            words.append({
                "text": text,
                "bbox": (x, y, x + w, y + h),
                "confidence": round(max(0.0, min(1.0, conf / 100.0)), 3),
                "block_num": int(data['block_num'][i]),
                "line_num": int(data['line_num'][i]),
                "word_num": int(data['word_num'][i])
            })

        return words
