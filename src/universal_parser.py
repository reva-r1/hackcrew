import os
from pathlib import Path
from typing import List, Dict, Any

from src.ocr.pipeline import DocumentOCRPipeline

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".gif", ".ico"}
TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".log", ".yaml", ".yml", ".py", ".js", ".html", ".tsv", ".xml"}
WORD_EXTENSIONS = {".docx", ".doc"}
PDF_EXTENSIONS = {".pdf"}

SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | TEXT_EXTENSIONS | WORD_EXTENSIONS | PDF_EXTENSIONS

def parse_any_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Universal document parser converting ANY uploaded file into machine-readable page records.
    Returns:
    [
        {
            "page_num": int,
            "text": str,
            "confidence": float,
            "provenance": "DIGITAL" | "OCR-EASYOCR" | "OCR-TESSERACT" | "TEXT-PLAIN" | "DOCX"
        },
        ...
    ]
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    # 1. PDF Documents
    if ext in PDF_EXTENSIONS:
        pipeline = DocumentOCRPipeline()
        result = pipeline.process_pdf(str(path))
        pages = []
        for p in result["pages"]:
            text = p["text"].strip()
            if text:
                pages.append({
                    "page_num": p["page_number"],
                    "text": text,
                    "confidence": p.get("confidence", 1.0),
                    "provenance": p.get("provenance", "DIGITAL")
                })
        return pages

    # 2. Images (PNG, JPG, TIFF, etc.) -> Direct OCR
    if ext in IMAGE_EXTENSIONS:
        pipeline = DocumentOCRPipeline()
        result = pipeline.process_image(str(path))
        p = result["pages"][0]
        return [{
            "page_num": 1,
            "text": p["text"].strip(),
            "confidence": p.get("confidence", 0.95),
            "provenance": p.get("provenance", "OCR-IMAGE")
        }]

    # 3. Microsoft Word (.docx)
    if ext in WORD_EXTENSIONS:
        import docx
        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        
        # Also extract text from any tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                if row_text:
                    paragraphs.append(row_text)

        full_doc_text = "\n\n".join(paragraphs)
        return [{
            "page_num": 1,
            "text": full_doc_text.strip(),
            "confidence": 1.0,
            "provenance": "DOCX"
        }]

    # 4. Dedicated CSV / TSV Parser
    if ext in {".csv", ".tsv"}:
        import csv
        for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]:
            try:
                with open(path, "r", encoding=enc, errors="replace") as f:
                    raw_content = f.read()
                
                if not raw_content.strip():
                    return [{
                        "page_num": 1,
                        "text": "Empty CSV file",
                        "confidence": 1.0,
                        "provenance": "CSV"
                    }]

                # Check if file is actual tabular CSV
                lines = [l for l in raw_content.splitlines() if l.strip()]
                delimiter = "\t" if ext == ".tsv" else (";" if ";" in lines[0] and "," not in lines[0] else ",")
                
                reader = csv.reader(lines, delimiter=delimiter)
                rows = [r for r in reader if r and any(c.strip() for c in r)]
                
                # If first row looks like a header with multiple columns and data rows follow
                if len(rows) > 1 and len(rows[0]) > 1:
                    headers = [h.strip() for h in rows[0]]
                    formatted_records = [f"Columns: {', '.join(headers)}\n"]
                    for idx, r in enumerate(rows[1:], start=1):
                        row_parts = []
                        for col_idx, cell in enumerate(r):
                            col_name = headers[col_idx] if col_idx < len(headers) and headers[col_idx] else f"Field{col_idx+1}"
                            val = cell.strip()
                            if val:
                                row_parts.append(f"{col_name}: {val}")
                        if row_parts:
                            formatted_records.append(f"Row {idx} -> " + " | ".join(row_parts))
                    
                    full_text = "\n".join(formatted_records)
                else:
                    # Non-tabular CSV (e.g. exported markdown or text saved as .csv)
                    full_text = raw_content.strip()

                return [{
                    "page_num": 1,
                    "text": full_text,
                    "confidence": 1.0,
                    "provenance": "CSV"
                }]
            except Exception as pe:
                continue

    # 5. Text / Markdown / Code / JSON
    if ext in TEXT_EXTENSIONS or True:  # default fallback
        for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                with open(path, "r", encoding=enc, errors="replace") as f:
                    content = f.read()
                return [{
                    "page_num": 1,
                    "text": content.strip(),
                    "confidence": 1.0,
                    "provenance": "TEXT-PLAIN"
                }]
            except Exception:
                continue

        return [{
            "page_num": 1,
            "text": path.read_text(errors="ignore").strip(),
            "confidence": 1.0,
            "provenance": "TEXT-PLAIN"
        }]

