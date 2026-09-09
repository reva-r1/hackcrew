# Ingestion Pipeline Spec

This runs once per document upload — offline, before any user query. Fully backend, no frontend dependency (frontend just needs an "upload" button that POSTs a file; everything below happens server-side).

---

## Pipeline steps

### 1. Load
Accept the raw file (PDF to start — that covers most enterprise docs). Use `pypdf` or `pdfplumber` to extract raw text page by page. Keep page numbers attached to text as you extract — you'll need this for citations later.

### 2. Clean
- Strip obvious noise: repeated headers/footers, page numbers embedded in text, excessive whitespace.
- Don't over-engineer this for a hackathon — basic whitespace/newline cleanup is enough.

### 3. Chunk
- Chunk size: **300–500 tokens**, with **~50 token overlap** between consecutive chunks (so a sentence split across a chunk boundary isn't lost).
- Use a simple recursive splitter (LangChain's `RecursiveCharacterTextSplitter` is fine, or write your own — split on paragraph breaks first, fall back to sentence breaks if a paragraph is too long).
- **Keep page_num attached to each chunk** — if a chunk spans two pages, use the page it starts on.

### 4. Enrich (optional — Tier 2, skip if short on time)
- One LLM call per *document* (not per chunk) — generate a 1-sentence summary.
- Prepend that summary to each chunk before embedding: `f"[{doc_summary}] {chunk_text}"`.
- Store both versions: the enriched text (for embedding) and the original clean text (for citation display — don't show the summary prefix to the user).

### 5. Embed
- Model: `sentence-transformers`, `all-MiniLM-L6-v2` (free, local, fast enough on CPU for hackathon-scale corpora — hundreds to low-thousands of chunks).
- Embed every chunk (enriched version if step 4 was done, otherwise raw chunk text).

### 6. Store
Two indexes, both keyed by the same `chunk_id`:
- **Vector store** (Chroma/FAISS) — embedding + chunk_id.
- **BM25 index** (`rank_bm25` or SQLite FTS5) — raw chunk text + chunk_id.
- **Metadata store** (can be the same SQLite DB) — one row per chunk_id: `doc_name`, `page_num`, `chunk_text` (original, unenriched), `doc_id`, and (later, Tier 3) `role`/`department` tags.

---

## Suggested metadata schema (SQLite table)

```sql
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    doc_name TEXT NOT NULL,
    page_num INTEGER,
    chunk_text TEXT NOT NULL,
    doc_summary TEXT,
    role_tags TEXT,  -- comma-separated, e.g. "HR,All_Employees" — Tier 3, leave NULL for now
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Vector store and BM25 index reference `chunk_id` — this table is your single source of truth for anything you need to display or filter on later (citations, RBAC).

---

## Interface contract

```
ingest_document(file_path: str, doc_name: str) -> {
    doc_id: str,
    chunks_created: int,
    status: "success" | "failed"
}
```

This is the one function your upload endpoint calls. Frontend hits `/upload`, backend runs this pipeline, returns a simple success/failure + chunk count so the UI can show "Document processed: 47 chunks created."

---

## What NOT to build for a hackathon

- OCR for scanned/image PDFs — assume text-based PDFs unless your docs specifically need it.
- Multi-format support (Word, HTML, etc.) beyond PDF — add only if you have real spare time.
- Incremental re-ingestion / diffing on re-upload — just treat every upload as new unless you're doing Tier 3 versioning.

---

## Order to build this in

1. Load + clean + chunk (get raw text → chunks working, print them out, sanity check).
2. Embed + store in vector DB (test retrieval manually before wiring up hybrid search).
3. Add BM25 index alongside it.
4. Add metadata table + citation fields.
5. Enrichment step — only if 1-4 are solid with time to spare.

This directly feeds Tier 1 Section 1 (hybrid search) from the build spec doc — you need working chunks + both indexes before hybrid search has anything to search over.
