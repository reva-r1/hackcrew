# Enterprise RAG Chatbot

An enterprise document Q&A chatbot that answers strictly from your uploaded documents — and explicitly **refuses to answer** when a question isn't covered, instead of hallucinating a confident-sounding wrong answer.

Built for [Hackathon Name] in 48 hours.

---

## The Problem

Enterprise teams bury important information in scattered PDFs, policy handbooks, and SOPs. Generic chatbots either can't find the right answer, or — worse — make one up. In an enterprise setting, a hallucinated policy answer is a real liability, not just an inconvenience.

This project answers questions strictly from a company's own documents, and is honest when it doesn't know something.

---

## What It Does

- Upload internal documents (PDF, CSV, tabular data)
- Ask questions in natural language
- Get answers grounded in the actual document content, with citations back to the exact source page/section
- If a question isn't covered by the uploaded docs, the system **deterministically refuses to answer** rather than guessing

---

## Architecture

### Ingestion Pipeline (runs once per uploaded document)

```
Upload → Clean/Parse → Chunk (300-500 tokens, ~50 token overlap)
       → Embed → Store in Vector DB + BM25 index (metadata: doc name, page number)
```

### Query Pipeline (runs per question)

```
Question → Hybrid Search (Vector + BM25, Reciprocal Rank Fusion)
         → Cross-Encoder Reranking
         → Confidence-Gated Refusal Check
         → Answer Generation (with citations)  OR  Deterministic Refusal
```

Two distinct query paths:
- **Specific-fact questions** ("What is the WFH internet allowance?") → standard retrieve → rerank → answer flow
- **Broad/summarization questions** ("What is this policy about?") → separate synthesis path that pulls multiple sections, since no single chunk represents an entire document

---

## Why Deterministic Refusal, Not LLM-Judged Refusal

Most RAG systems either always answer, or use a second LLM call to "judge" whether the first answer is trustworthy. That approach is slower (extra API call per query), non-deterministic (an LLM judging an LLM can itself be wrong), and adds a second point of failure.

This system instead gates on **retrieval confidence** — a numeric threshold applied to the reranked similarity score. It's:
- Deterministic and explainable in one sentence
- Fast — no extra LLM call
- Not something that can be talked out of it by clever prompting

---

## Tech Stack

| Component | Tool | Why |
|---|---|---|
| Generation LLM | Groq API (Llama 3.3 70B) | Free tier, extremely fast (500+ tok/s), no GPU cost |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Free, runs locally on CPU |
| Reranking | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) | Free, local, improves retrieval precision |
| Keyword search | `rank_bm25` | Classic keyword scoring, complements vector search |
| Storage | SQLite (metadata) + local vector store | Lightweight, no external DB dependency |
| Backend | FastAPI | Fast to build, async-friendly |
| Frontend | React 18 + Vite | Humanistic editorial UI, dark/light themes, live preview |

No model training or fine-tuning required — every component is either a pretrained local model or a free hosted API.

---

## API Endpoints

### `POST /upload`
Uploads and ingests a document (PDF/CSV).

```json
{
  "doc_id": "e794c92e",
  "doc_name": "policy.pdf",
  "chunks_created": 12,
  "status": "success"
}
```

### `POST /query`
Asks a question against ingested documents.

```json
{
  "status": "answered",
  "answer": "...",
  "confidence": 0.87,
  "sources": [
    { "doc_name": "policy.pdf", "page_num": 4, "snippet": "..." }
  ]
}
```

Possible `status` values: `answered`, `refused`, `error`.

### `POST /preview-confidence`
Lightweight live-typing endpoint — returns a match-strength score as the user types, before they submit the full question. No LLM call; vector search only, optimized for sub-200ms response.

```json
{ "score": 82, "status": "strong_match" }
```

Full field-level contract lives in `docs/api-response-schema.md`.

---

## What Makes This Different

- **Deterministic, math-based refusal** instead of a second LLM judging the first
- **Dual query paths** for specific facts vs. broad summarization — most RAG hackathon projects only handle one well
- **Live confidence preview** while typing, before the question is even submitted
- **Zero training cost** — fully reproducible on free-tier tools, no GPU required
- **Tested, not just demoed** — automated test suite covering ingestion, retrieval accuracy, refusal correctness, and API contracts; real issues (cross-document retrieval contamination, threshold miscalibration) were caught and fixed during testing, not discovered live

---

## Project Structure

```
.
├── src/
│   ├── app.py                # FastAPI app, /query, /upload endpoints
│   ├── config.py             # Global settings & thresholds
│   ├── ingestion.py          # Chunking, embedding, indexing
│   ├── hybrid_search.py      # Hybrid search (Dense + BM25)
│   ├── reranker.py           # Cross-encoder reranking
│   ├── refusal.py            # Confidence-gate logic
│   └── ocr/                  # Document parsing & OCR pipeline
├── frontend/                 # React + Vite application
├── static/                   # Compiled frontend assets served by FastAPI
├── tests/                    # Pytest suite
├── data/                     # Local storage & documents
├── docs/                     # Specifications and API contracts
└── README.md
```

---

## Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env file
GROQ_API_KEY=your_key_here

# 3. Run the application
python run_server.py
```

Server runs at `http://localhost:8000`. Full endpoint docs at `http://localhost:8000/docs` (FastAPI auto-generated).

---

## Testing

```bash
pytest tests/
```

Covers document ingestion, hybrid retrieval, confidence-gate accuracy on labeled in-scope/out-of-scope test sets, and API contract validation.

---

## Team

- **Backend / RAG pipeline / ML:** [Your name]
- **Frontend:** [Teammate names]

---

## Built For

[Hackathon name, date, and any track/category info]
