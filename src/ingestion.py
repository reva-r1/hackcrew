import os
import src.config  # Enforces OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from src.config import (
    EMBEDDING_MODEL_NAME,
    CHUNK_SIZE_TOKENS,
    CHUNK_OVERLAP_TOKENS,
)
from src.database import init_db, insert_chunks, delete_chunks_by_doc_name
from src.vector_store import VectorStore
from src.bm25_index import BM25Index

_EMBEDDER: Optional[SentenceTransformer] = None

def get_embedder() -> SentenceTransformer:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _EMBEDDER

def clean_text(text: str) -> str:
    """Cleans raw extracted PDF text, removing noise and excessive whitespace."""
    if not text:
        return ""
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove repeated page numbers / header patterns like 'Page 12 of 20' or standalone digits on a line
    text = re.sub(r'(?i)\bpage\s+\d+(\s+of\s+\d+)?\b', '', text)
    # Collapse multiple spaces and horizontal whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    # Collapse more than two consecutive newlines into two
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def approximate_tokens(text: str) -> int:
    """Approximates token count (1 word is ~1.3 tokens)."""
    words = len(text.split())
    return int(words * 1.3)

def split_text_recursive(
    text: str,
    max_tokens: int = CHUNK_SIZE_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS
) -> List[str]:
    """
    Splits text recursively using paragraph breaks, line breaks, and sentences
    to maintain semantic coherence while targeting max_tokens with overlap_tokens.
    """
    if not text.strip():
        return []

    if approximate_tokens(text) <= max_tokens:
        return [text.strip()]

    # Hierarchy of separators
    separators = ["\n\n", "\n", ". ", "; ", ", ", " "]
    
    def _split(t: str, sep_idx: int) -> List[str]:
        if sep_idx >= len(separators):
            # Fallback: slice by words
            words = t.split()
            chunks = []
            target_words = int(max_tokens / 1.3)
            overlap_words = int(overlap_tokens / 1.3)
            step = max(1, target_words - overlap_words)
            for i in range(0, len(words), step):
                chunk_words = words[i:i + target_words]
                chunks.append(" ".join(chunk_words))
            return chunks

        sep = separators[sep_idx]
        parts = t.split(sep)
        chunks = []
        curr_chunk: List[str] = []
        curr_tokens = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue
            part_tokens = approximate_tokens(part)
            
            if part_tokens > max_tokens:
                # If a single part exceeds max_tokens, recursively split it with next separator
                if curr_chunk:
                    joined = sep.join(curr_chunk)
                    chunks.append(joined)
                    curr_chunk = []
                    curr_tokens = 0
                sub_chunks = _split(part, sep_idx + 1)
                chunks.extend(sub_chunks)
            elif curr_tokens + part_tokens <= max_tokens:
                curr_chunk.append(part)
                curr_tokens += part_tokens
            else:
                joined = sep.join(curr_chunk)
                chunks.append(joined)
                # Apply overlap from previous chunk if possible
                overlap_collector: List[str] = []
                overlap_accum = 0
                for prev_part in reversed(curr_chunk):
                    p_tok = approximate_tokens(prev_part)
                    if overlap_accum + p_tok <= overlap_tokens:
                        overlap_collector.insert(0, prev_part)
                        overlap_accum += p_tok
                    else:
                        break
                curr_chunk = overlap_collector + [part]
                curr_tokens = sum(approximate_tokens(p) for p in curr_chunk)

        if curr_chunk:
            chunks.append(sep.join(curr_chunk))

        return [c.strip() for c in chunks if c.strip()]

    return _split(text, 0)

def extract_pages_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extracts text page by page from a PDF file with 1-based page numbers, using OCR pipeline when needed."""
    try:
        from src.ocr.pipeline import DocumentOCRPipeline
        pipeline = DocumentOCRPipeline()
        ocr_result = pipeline.process_pdf(file_path)
        
        pages = []
        for p in ocr_result["pages"]:
            cleaned = clean_text(p["text"])
            if cleaned:
                pages.append({
                    "page_num": p["page_number"],
                    "text": cleaned,
                    "confidence": p.get("confidence", 1.0),
                    "provenance": p.get("provenance", "DIGITAL")
                })
        if pages:
            return pages
    except Exception as e:
        print(f"Notice: OCR pipeline fallback to standard reader: {e}")

    reader = PdfReader(file_path)
    pages = []
    for idx, page in enumerate(reader.pages):
        raw_text = page.extract_text() or ""
        cleaned = clean_text(raw_text)
        if cleaned:
            pages.append({
                "page_num": idx + 1,
                "text": cleaned
            })
    return pages

def ingest_document(file_path: str, doc_name: str) -> Dict[str, Any]:
    """
    Full ingestion pipeline matching ingestion-pipeline-spec.md:
    1. Load PDF page by page
    2. Clean text
    3. Chunk (300-500 tokens, ~50 overlap) with page_num tracking
    4. Embed with all-MiniLM-L6-v2
    5. Store in vector store (Chroma) + BM25 index + SQLite metadata table

    Interface contract:
    {
        "doc_id": str,
        "chunks_created": int,
        "status": "success" | "failed"
    }
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {
                "doc_id": "",
                "chunks_created": 0,
                "status": "failed",
                "error": f"File not found: {file_path}"
            }

        # Initialize SQLite DB
        init_db()

        # Step 1 & 2: Extract & clean pages using Universal Parser (PDF, Image OCR, Docx, Text)
        from src.universal_parser import parse_any_file
        pages_data = parse_any_file(str(path))
        if not pages_data:
            return {
                "doc_id": "",
                "chunks_created": 0,
                "status": "failed",
                "error": "No readable text extracted from document"
            }

        doc_id = str(uuid.uuid4())[:8]

        # Step 3: Chunking across pages, retaining starting page_num
        chunks_to_insert = []
        chunk_idx = 0

        for p in pages_data:
            page_num = p["page_num"]
            page_text = p["text"]
            page_chunks = split_text_recursive(page_text)

            for chunk_str in page_chunks:
                chunk_id = f"{doc_id}_c{chunk_idx}"
                chunks_to_insert.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "page_num": page_num,
                    "chunk_text": chunk_str,
                    "doc_summary": None,
                    "role_tags": None
                })
                chunk_idx += 1

        if not chunks_to_insert:
            return {
                "doc_id": doc_id,
                "chunks_created": 0,
                "status": "failed",
                "error": "No chunks generated"
            }

        # Step 4: Embed with all-MiniLM-L6-v2
        embedder = get_embedder()
        chunk_texts = [c["chunk_text"] for c in chunks_to_insert]
        embeddings = embedder.encode(chunk_texts, show_progress_bar=False, normalize_embeddings=True).tolist()

        # Step 4.5: Purge existing chunks for this doc_name across storage layers to prevent duplicates
        delete_chunks_by_doc_name(doc_name)

        # Step 5: Store in Vector Store (Chroma)
        vector_store = VectorStore()
        vector_store.delete_chunks_by_doc_name(doc_name)
        chunk_ids = [c["chunk_id"] for c in chunks_to_insert]
        metadatas = [
            {
                "doc_id": c["doc_id"],
                "doc_name": c["doc_name"],
                "page_num": c["page_num"]
            }
            for c in chunks_to_insert
        ]
        vector_store.add_chunks(
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas
        )

        # Step 6: Store in BM25 index
        bm25_index = BM25Index()
        bm25_index.delete_chunks_by_doc_name(doc_name)
        bm25_index.add_chunks(
            chunk_ids=chunk_ids,
            documents=chunk_texts,
            metadatas=metadatas
        )

        # Step 7: Store in SQLite metadata table
        insert_chunks(chunks_to_insert)


        # Step 8: Cloud sync to Supabase
        try:
            from src.supabase_client import sync_chunks_to_supabase
            sync_chunks_to_supabase(chunks_to_insert)
        except Exception as se:
            print(f"Notice: Supabase cloud sync skipped or failed: {se}")

        avg_conf = round(sum(p.get("confidence", 1.0) for p in pages_data) / len(pages_data), 3) if pages_data else 1.0
        primary_prov = pages_data[0].get("provenance", "DIGITAL") if pages_data else "DIGITAL"
        preview_text = chunks_to_insert[0]["chunk_text"][:250] if chunks_to_insert else ""

        return {
            "doc_id": doc_id,
            "doc_name": doc_name,
            "chunks_created": len(chunks_to_insert),
            "confidence": avg_conf,
            "provenance": primary_prov,
            "preview_text": preview_text,
            "file_url": f"/uploads/{doc_name}",
            "status": "success"
        }

    except Exception as e:
        return {
            "doc_id": "",
            "chunks_created": 0,
            "status": "failed",
            "error": str(e)
        }
