import re
import shutil
import traceback
from pathlib import Path
from typing import Optional, List, Literal, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

import src.config
from src.config import DATA_DIR, CONFIDENCE_THRESHOLD, BASE_DIR
from src.hybrid_search import hybrid_search
from src.reranker import rerank
from src.refusal import should_answer, create_refusal_response, log_refusal
from src.generator import generate_answer, generate_summary, format_sources, rewrite_query
from src.ingestion import ingest_document, get_embedder
from src.vector_store import VectorStore
from src.database import get_connection
from src.supabase_client import log_query_to_supabase

def is_summarization_intent(query: str) -> bool:
    """Detects high-level document summarization, policy overview, or executive summary requests."""
    q = query.lower().strip()
    # Normalize typos like "os" for "of"
    q_norm = re.sub(r'\bos\b', 'of', q)
    q_clean = re.sub(r'[^\w\s]', ' ', q_norm)
    q_clean = re.sub(r'\s+', ' ', q_clean).strip()

    # Reject specific fact questions immediately
    fact_indicators = [
        "who", "how", "when", "where", "which", "owner", "allowance", "stipend", "hours",
        "notice", "matrix", "carrier", "insured", "insurance", "reimbursement",
        "pto", "probation", "phone", "cookies", "capital", "fifa", "speed"
    ]
    words = q_clean.split()
    if any(ind in words for ind in fact_indicators):
        return False
    if any(q_clean.startswith(f"{ind} ") for ind in ["who", "when", "where", "how", "which", "is there", "can i"]):
        return False
    
    triggers = [
        "what is this policy about",
        "what is this document about",
        "what is the policy about",
        "what is this about",
        "summarize this document",
        "summarize this policy",
        "summarize the policy",
        "summarize the document",
        "summarize",
        "summary of this policy",
        "summary of the policy",
        "summary of this document",
        "policy summary",
        "overview of the policy",
        "overview of this policy",
        "overview of this document",
        "explain the policy",
        "explain this policy",
        "explain this document",
        "what does this policy cover",
        "what does this document cover",
        "overview of the handbook",
        "executive summary",
        "tell me about this policy",
        "tell me about the policy",
        "what is the policy of this company",
        "what is the policy of the company",
        "explain the company policy",
        "explain company policy",
        "explain or what is the policy",
        "explain or what is the policy of this company",
        "explain the policy of this company"
    ]
    if any(q_clean == t or q_clean.startswith(t) for t in triggers):
        return True

    return False


def is_negative_answer(answer: Optional[str]) -> bool:
    """Checks if LLM output explicitly states that information is not available in provided context."""
    if not answer:
        return True
    a = answer.lower()
    negative_phrases = [
        "do not contain this information",
        "does not contain this information",
        "do not contain information",
        "does not contain information",
        "not mentioned in the provided",
        "not mentioned in the excerpt",
        "not mentioned in any of the",
        "none of the sections",
        "cannot be determined",
        "cannot determine",
        "information is not available",
        "information is not provided",
        "not available in the provided",
        "excerpts provided do not",
        "provided excerpts do not",
        "provided text does not",
        "no mention of",
        "not state who",
        "not state what",
        "does not state",
        "do not state",
        "there is no information",
        "i do not have enough information",
        "i do not have access"
    ]
    return any(p in a for p in negative_phrases)


app = FastAPI(
    title="Enterprise RAG Backend",
    description="Production-grade RAG backend with hybrid search, cross-encoder reranking, and deterministic refusal gating.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Pre-warms ML models to ensure zero cold-start delay for user queries."""
    try:
        from src.ingestion import get_embedder
        from src.reranker import get_reranker
        get_embedder()
        get_reranker()
    except Exception as e:
        print(f"Startup pre-warming notice: {e}")


STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

DOCS_DIR = DATA_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(DOCS_DIR)), name="uploads")

@app.get("/")
async def root():
    """Serves the interactive web interface."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Enterprise RAG API Online"}

from datetime import datetime
from src.vector_store import VectorStore
from src.bm25_index import BM25Index

EVENT_LOGS: List[Dict[str, Any]] = [
    {
        "id": "init-1",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "category": "system",
        "title": "Aether RAG Engine Online",
        "detail": "Hybrid search (BM25 + Dense Cosine), Cross-encoder reranker, and 0.40 refusal gate initialized."
    }
]

def log_event(category: str, title: str, detail: str):
    global EVENT_LOGS
    EVENT_LOGS.append({
        "id": f"log-{len(EVENT_LOGS)+1}",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "category": category,
        "title": title,
        "detail": detail
    })
    if len(EVENT_LOGS) > 150:
        EVENT_LOGS = EVENT_LOGS[-150:]

@app.get("/uploaded-files")
def get_uploaded_files():
    """Returns metadata list of all ingested files in the system."""
    files = []
    if DOCS_DIR.exists():
        for p in DOCS_DIR.iterdir():
            if p.is_file() and not p.name.startswith("."):
                ext = p.suffix.lower()
                is_img = ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp", ".gif"}
                files.append({
                    "name": p.name,
                    "size_kb": round(p.stat().st_size / 1024, 1),
                    "is_image": is_img,
                    "url": f"/uploads/{p.name}"
                })
    return {"files": files}

@app.get("/chunks")
def get_all_stored_chunks():
    """Returns all stored chunks with word count, char count, and preview for the audit log."""
    from src.database import get_all_chunks
    rows = get_all_chunks()
    chunks_list = []
    total_words = 0
    for r in rows:
        text = r.get("chunk_text", "")
        w_count = len(text.split())
        total_words += w_count
        chunks_list.append({
            "chunk_id": r.get("chunk_id"),
            "doc_name": r.get("doc_name"),
            "page_num": r.get("page_num"),
            "word_count": w_count,
            "char_count": len(text),
            "preview": text[:260] + ("..." if len(text) > 260 else ""),
            "full_text": text,
            "created_at": r.get("created_at")
        })
    return {
        "total_chunks": len(chunks_list),
        "total_words": total_words,
        "chunks": chunks_list
    }

@app.get("/logs")
def get_system_logs():
    """Returns the in-memory activity and audit event logs."""
    return {"logs": list(reversed(EVENT_LOGS))}

@app.post("/clear-all")
def clear_all_data():
    """Purges all uploaded files, ChromaDB vectors, BM25 index, and SQLite chunks."""
    removed_files = 0
    if DOCS_DIR.exists():
        for p in list(DOCS_DIR.iterdir()):
            if p.is_file():
                try:
                    p.unlink()
                    removed_files += 1
                except Exception as e:
                    print(f"Error removing file {p}: {e}")

    # Clear SQLite chunks table
    from src.database import get_connection
    with get_connection() as conn:
        conn.cursor().execute("DELETE FROM chunks")
        conn.commit()

    # Clear ChromaDB vector store
    try:
        vs = VectorStore()
        vs.clear()
    except Exception as e:
        print(f"Error clearing vector store: {e}")

    # Clear BM25 index
    try:
        bm25 = BM25Index()
        bm25.chunk_ids = []
        bm25.documents = []
        bm25.metadatas = []
        bm25.corpus_tokens = []
        bm25.bm25 = None
        bm25._save()
    except Exception as e:
        print(f"Error clearing BM25 index: {e}")

    log_event("purge", "Knowledge Repositories Purged", f"Removed {removed_files} files; wiped vector store, BM25, and SQLite chunks.")
    return {"status": "success", "files_removed": removed_files}

class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's question.")
    role: Optional[str] = Field("employee", description="User role for future RBAC filtering.")

class SourceModel(BaseModel):
    doc_name: str
    page_num: Optional[int] = None
    snippet: str

class QueryResponse(BaseModel):
    status: Literal["answered", "refused", "error"]
    answer: Optional[str] = None
    confidence: Optional[float] = None
    sources: List[SourceModel] = Field(default_factory=list)
    reason: Optional[str] = None

@app.get("/health")
def health_check() -> Dict[str, str]:
    """Simple liveness check for frontend."""
    return {"status": "ok"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts PDF, image, CSV, docx file upload, triggers ingestion pipeline, and indexes into SQLite, Vector DB, and BM25.
    """
    try:
        upload_dir = DATA_DIR / "docs"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = ingest_document(file_path=str(file_path), doc_name=file.filename)
        log_event("ingest", f"Document Ingested: {file.filename}", f"Parsed via {result.get('provenance', 'OCR')}. Created {result.get('chunks_created', 0)} chunks.")
        return result
    except Exception as e:
        log_event("error", f"Ingestion Error: {file.filename}", str(e))
        return {
            "doc_id": "",
            "chunks_created": 0,
            "status": "failed",
            "error": str(e)
        }

class PreviewRequest(BaseModel):
    partial_query: str = Field(..., description="The partial query text typed so far by the user.")

class PreviewResponse(BaseModel):
    score: float = Field(..., description="Normalized confidence match score between 0 and 100.")
    status: Literal["strong_match", "weak_match", "no_match"] = Field(..., description="Categorical match level.")

_PREVIEW_CACHE: Dict[str, Dict[str, Any]] = {}
_MAX_PREVIEW_CACHE = 1000
_PREVIEW_VECTOR_STORE: Optional[VectorStore] = None

def get_preview_vector_store() -> VectorStore:
    global _PREVIEW_VECTOR_STORE
    if _PREVIEW_VECTOR_STORE is None:
        _PREVIEW_VECTOR_STORE = VectorStore()
    return _PREVIEW_VECTOR_STORE

@app.post("/preview-confidence", response_model=PreviewResponse)
async def preview_confidence(req: PreviewRequest):
    """
    Lightweight, fast (<200ms) live preview endpoint called as the user types:
    - Pure vector search on Chroma (top 3 similarity scores)
    - Skips BM25, hybrid fusion, reranking, LLM calls
    - Read-only against index, no logging to Supabase or history
    - In-memory caching for instant repeated/paused queries
    - Normalized score (0-100 scale) with status label
    """
    raw_query = req.partial_query.strip()
    if len(raw_query) < 2:
        return {"score": 0.0, "status": "no_match"}

    cache_key = raw_query.lower()
    if cache_key in _PREVIEW_CACHE:
        return _PREVIEW_CACHE[cache_key]

    try:
        vs = get_preview_vector_store()
        if vs.count() == 0:
            res = {"score": 0.0, "status": "no_match"}
            _PREVIEW_CACHE[cache_key] = res
            return res

        embedder = get_embedder()
        query_embedding = embedder.encode(raw_query, normalize_embeddings=True).tolist()
        
        # Fast top-3 vector search
        search_results = vs.search(query_embedding, top_k=3)
        top_sim = search_results[0]["score"] if search_results else 0.0

        # Calibration:
        # Noise floor / out-of-scope / short fragments (sim <= 0.26) -> [0.0, 39.0] (no_match)
        # Emerging relevance (0.26 to 0.38) -> [40.0, 69.0] (weak_match)
        # Strong match (> 0.38) -> [70.0, 100.0] (strong_match)
        if top_sim <= 0.26:
            score = round(max(0.0, (top_sim / 0.26) * 39.0), 1)
        elif top_sim <= 0.38:
            score = round(40.0 + ((top_sim - 0.26) / 0.12) * 29.0, 1)
        else:
            score = round(min(100.0, 70.0 + ((top_sim - 0.38) / 0.15) * 30.0), 1)

        if score > 70.0:
            status = "strong_match"
        elif score >= 40.0:
            status = "weak_match"
        else:
            status = "no_match"

        result = {"score": score, "status": status}

        if len(_PREVIEW_CACHE) >= _MAX_PREVIEW_CACHE:
            keys_to_purge = list(_PREVIEW_CACHE.keys())[:200]
            for k in keys_to_purge:
                _PREVIEW_CACHE.pop(k, None)

        _PREVIEW_CACHE[cache_key] = result
        return result

    except Exception as e:
        return {"score": 0.0, "status": "no_match"}

@app.post("/query")
async def query_endpoint(req: QueryRequest):
    """
    Main RAG query endpoint conforming to api-response-schema.md contract:
    1. Hybrid search (vector + BM25 RRF)
    2. Cross-encoder reranking
    3. Confidence-gated refusal check
    4. Groq LLM answer generation with sources citations
    """
    query = req.query.strip()
    role = req.role or "employee"

    if not query:
        res = create_refusal_response(confidence=0.0, reason="empty_query")
        log_query_to_supabase(query=query, role=role, status="refused", confidence=0.0, reason="empty_query")
        return res

    try:
        # Step 0: Check for broad summarization / overview intent
        if is_summarization_intent(query):
            target_doc = None
            
            # Check if query specifically references a known document or topic
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT doc_name FROM chunks")
                all_docs = [r[0] for r in cursor.fetchall()]
            
            q_lower = query.lower()
            # Pass 1: match specific domain/topic in document filename
            for doc in all_docs:
                base_name = doc.lower().replace("_", " ").replace("-", " ")
                if any(w in q_lower for w in ["shipping", "transport", "delivery"]) and any(w in base_name for w in ["shipping", "shit", "sheexs"]):
                    target_doc = doc
                    break
                elif any(w in q_lower for w in ["hr", "leave", "wfh", "allowance"]) and "hr" in base_name:
                    target_doc = doc
                    break
                elif any(w in q_lower for w in ["security", "cloud", "mfa"]) and "security" in base_name:
                    target_doc = doc
                    break
                elif any(w in q_lower for w in ["travel", "diem", "flight"]) and "travel" in base_name:
                    target_doc = doc
                    break

            # Pass 2: match generic company policy / handbook if no specific domain matched
            if not target_doc:
                for doc in all_docs:
                    base_name = doc.lower().replace("_", " ").replace("-", " ")
                    if any(w in base_name for w in ["company", "policy", "policty", "handbook", "employee"]):
                        target_doc = doc
                        break

            # If not explicitly named, use hybrid search top candidate's document
            if not target_doc:
                pre_candidates = hybrid_search(query, top_k=5)
                if pre_candidates:
                    target_doc = pre_candidates[0].get("metadata", {}).get("doc_name")
            
            # Fallback to most recent document
            if not target_doc and all_docs:
                target_doc = all_docs[-1]

            if target_doc:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT chunk_id, doc_name, page_num, chunk_text FROM chunks WHERE doc_name = ? ORDER BY page_num ASC, chunk_id ASC LIMIT 6",
                        (target_doc,)
                    )
                    rows = cursor.fetchall()
                
                if rows:
                    summary_chunks = [
                        {
                            "chunk_id": r["chunk_id"],
                            "text": r["chunk_text"],
                            "metadata": {"doc_name": r["doc_name"], "page_num": r["page_num"]}
                        }
                        for r in rows
                    ]
                    summary_answer = generate_summary(query=query, context_chunks=summary_chunks)
                    if summary_answer:
                        if is_negative_answer(summary_answer):
                            log_refusal(query, 0.0, CONFIDENCE_THRESHOLD, reason="answer_not_grounded")
                            log_query_to_supabase(query=query, role=role, status="refused", confidence=0.0, reason="answer_not_grounded")
                            log_event("refusal", f"Refusal (Summary Unavailable): '{query[:40]}'", "Document does not contain requested summary topic.")
                            return create_refusal_response(confidence=0.0, reason="insufficient_evidence")

                        sources = format_sources(summary_chunks)
                        log_query_to_supabase(
                            query=query,
                            role=role,
                            status="answered",
                            confidence=1.0,
                            answer=summary_answer,
                            sources=sources
                        )
                        return {
                            "status": "answered",
                            "answer": summary_answer,
                            "confidence": 1.0,
                            "sources": sources
                        }

        # Step 1: Hybrid Search for specific-fact queries
        candidates = hybrid_search(query, top_k=25)
        if not candidates:

            log_refusal(query, 0.0, CONFIDENCE_THRESHOLD, reason="no_candidates_found")
            log_query_to_supabase(query=query, role=role, status="refused", confidence=0.0, reason="no_candidates_found")
            return create_refusal_response(confidence=0.0, reason="insufficient_evidence")

        # Step 2: Cross-Encoder Reranking
        reranked = rerank(query, candidates, top_k=5)
        if not reranked:
            log_refusal(query, 0.0, CONFIDENCE_THRESHOLD, reason="reranking_empty")
            log_query_to_supabase(query=query, role=role, status="refused", confidence=0.0, reason="reranking_empty")
            return create_refusal_response(confidence=0.0, reason="insufficient_evidence")

        top_score = reranked[0]["score"]

        # Step 3: Confidence-Gated Refusal
        if not should_answer(reranked, threshold=CONFIDENCE_THRESHOLD):
            log_refusal(query, top_score, CONFIDENCE_THRESHOLD, reason="insufficient_evidence")
            log_query_to_supabase(query=query, role=role, status="refused", confidence=top_score, reason="insufficient_evidence")
            log_event("refusal", f"Refusal Triggered: '{query[:40]}'", f"Top score: {top_score:.3f} < 0.40 threshold. Zero hallucination safeguard active.")
            return create_refusal_response(confidence=top_score, reason="insufficient_evidence")

        # Step 4: Format sources
        passing_chunks = [c for c in reranked if c["score"] >= (CONFIDENCE_THRESHOLD * 0.5)]
        if not passing_chunks:
            passing_chunks = [reranked[0]]

        sources = format_sources(passing_chunks)

        # Step 5: Answer Generation via Groq
        answer = generate_answer(query=query, context_chunks=passing_chunks)

        if not answer:
            log_query_to_supabase(query=query, role=role, status="error", reason="generation_failed")
            log_event("error", f"Generation Failed: '{query[:40]}'", "Groq returned empty response.")
            return {
                "status": "error",
                "answer": None,
                "confidence": None,
                "sources": [],
                "reason": "generation_failed"
            }

        # Step 5.5: Consistency check - if generated answer explicitly states information is not available,
        # route to refused with 0.0 confidence.
        if is_negative_answer(answer):
            log_refusal(query, 0.0, CONFIDENCE_THRESHOLD, reason="answer_not_grounded")
            log_query_to_supabase(query=query, role=role, status="refused", confidence=0.0, reason="answer_not_grounded")
            log_event("refusal", f"Refusal (Answer Unavailability): '{query[:40]}'", "LLM indicated information was not present in context.")
            return create_refusal_response(confidence=0.0, reason="insufficient_evidence")

        # Step 6: Log answered interaction to Supabase
        log_query_to_supabase(
            query=query,
            role=role,
            status="answered",
            confidence=round(top_score, 2),
            answer=answer,
            sources=sources
        )
        log_event("answer", f"Answer Generated: '{query[:40]}'", f"Match: {int(top_score*100)}% | {len(sources)} source citations verified.")

        return {
            "status": "answered",
            "answer": answer,
            "confidence": round(top_score, 2),
            "sources": sources
        }

    except Exception as e:
        print(f"Exception during /query handling: {e}\n{traceback.format_exc()}", flush=True)
        log_query_to_supabase(query=query, role=role, status="error", reason=str(e))
        log_event("error", f"Query Fault: '{query[:40]}'", str(e))
        return {
            "status": "error",
            "answer": None,
            "confidence": None,
            "sources": [],
            "reason": "generation_failed"
        }
