# Archivum AI — Enterprise Multi-Modal RAG Platform

> **Zero-Hallucination Enterprise Search with Dual-Path Hybrid Retrieval, Universal OCR, and Real-Time Typing Match Meter.**

---

## Overview

**Archivum AI** is an enterprise knowledge assistant designed for mission-critical accuracy. Unlike naive RAG systems that hallucinate when information is missing, Archivum enforces a two-tier anti-hallucination refusal gate, combines exact keyword search with deep semantic embeddings, and features a live typing preview meter that shows query match strength in sub-50ms.

---

## Key Features

1. **Universal Multi-Format Ingestion:**
   - Native text **PDF** processing.
   - Computer vision OCR pipeline for **PNG, JPG, WEBP** (OpenCV deskewing & binarization + Tesseract / EasyOCR fallback).
   - Structured **CSV** tabular parsing with row-aware semantic representations.

2. **Dual-Path Cognitive Query Routing:**
   - **Broad Executive Summarization:** Automatically identifies overview queries and synthesizes multi-section summaries across documents.
   - **Pinpoint Fact Extraction:** Searches specific facts using hybrid retrieval and neural reranking.

3. **Hybrid Sparse + Dense Retrieval (RRF):**
   - Combines exact lexical matching (BM25Okapi for numbers, codes, and acronyms) with dense semantic embeddings (`all-MiniLM-L6-v2` in ChromaDB) via Reciprocal Rank Fusion.

4. **Neural Cross-Encoder & Anti-Hallucination Refusal Gate:**
   - Evaluates retrieved candidates with `cross-encoder/ms-marco-MiniLM-L-6-v2`.
   - Hard 0.40 confidence safety threshold: queries below 0.40 are deterministically refused with complete audit logging.
   - Generative consistency guard (`is_negative_answer`): prevents the model from returning high confidence when the context lacks the facts.

5. **Live Keystroke Match Meter (`/preview-confidence`):**
   - Real-time debounced confidence preview updating in sub-50ms as the user types, before submitting the query.

6. **Editorial Glassmorphism UI:**
   - Dark-mode executive workspace with Cabinet Grotesk / Inter typography, rich source citation badges, and drag-and-drop document upload vault.

---

## System Architecture

```
                                +---------------------------+
                                |  Editorial Web UI / API   |
                                +-------------+-------------+
                                              |
                     +------------------------+------------------------+
                     | (POST /upload)         | (POST /preview-conf)   | (POST /query)
                     v                        v                        v
        +-------------------------+  +-------------------+  +-------------------------+
        | Universal Parser & OCR  |  | Sub-50ms Cosine   |  | Dual-Path Router        |
        | - PDF, Images, CSV      |  | Vector Preview    |  | - Summarize vs Fact     |
        +------------+------------+  +-------------------+  +------------+------------+
                     |                                                   |
                     v                                                   v
        +-------------------------+                         +-------------------------+
        | Dual Storage Layer      |                         | Hybrid Retrieval (RRF)  |
        | - SQLite Metadata       |                         | - BM25Okapi (Sparse)    |
        | - ChromaDB Vectors      |                         | - ChromaDB (Dense)      |
        +-------------------------+                         +------------+------------+
                                                                         |
                                                                         v
                                                            +-------------------------+
                                                            | Neural Cross-Encoder    |
                                                            | (ms-marco-MiniLM-L-6-v2)|
                                                            +------------+------------+
                                                                         |
                                                                         v
                                                            +-------------------------+
                                                            | 0.40 Confidence Gate    |
                                                            | < 0.40 -> Deterministic |
                                                            |           Refusal       |
                                                            | >= 0.40 -> LLM Generate |
                                                            +-------------------------+
```

---

## Quickstart

### 1. Prerequisites
- Python 3.10+
- (Optional) Tesseract OCR installed on your system for image OCR.

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/your-org/archivum-ai.git
cd archivum-ai
pip install -r requirements.txt
```

### 3. Environment Setup
Copy the example environment file:
```bash
cp .env.example .env
```

### 4. Run the Server
Launch the FastAPI application:
```bash
python run_server.py
```
Open your browser and navigate to:
```
http://localhost:8000
```

---

## Automated Testing

Run the full pytest suite (100% passing across 14 test suites):
```bash
pytest tests/
```

Individual test suites:
- `pytest tests/test_step4_dual_paths.py` (Dual-path summarization & refusal test)
- `pytest tests/test_csv_ingestion.py` (CSV table ingestion & query test)
- `pytest tests/test_ocr.py` (Computer vision OCR pipeline test)
- `pytest tests/test_preview_confidence.py` (Live match meter calibration test)
- `pytest tests/test_step5_api.py` (REST API endpoint verification)
- `pytest tests/test_universal_ocr_upload.py` (End-to-end multi-format upload & RAG test)

---

## Project Structure

```
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules for clean commits
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── docs/                     # Specifications & presentation slide deck
│   ├── ppt.md                # Simplified slide deck & presentation reference
│   ├── api-response-schema.md# REST API contract specification
│   ├── ingestion-pipeline-spec.md # OCR & ingestion architecture spec
│   └── rag-tier1-tier2-buildspec.md # Dual-path & refusal gate spec
│
├── src/                      # Core backend application
│   ├── app.py                # FastAPI routes & query router
│   ├── bm25_index.py         # BM25Okapi keyword search
│   ├── config.py             # Global thresholds & settings
│   ├── database.py           # SQLite persistence layer
│   ├── generator.py          # Grounded LLM response synthesizer
│   ├── hybrid_search.py      # Reciprocal Rank Fusion
│   ├── ingestion.py          # Chunking & indexing coordinator
│   ├── refusal.py            # Anti-hallucination refusal & audit logs
│   ├── reranker.py           # Cross-encoder neural reranker
│   ├── universal_parser.py   # Multi-format document parser
│   ├── vector_store.py       # ChromaDB vector store
│   └── ocr/                  # Computer vision OCR subsystem
│
├── static/                   # Editorial glassmorphic web UI
│   ├── index.html            # Web interface layout
│   ├── style.css             # Glassmorphic CSS styling
│   ├── app.js                # Frontend state machine & live match meter
│   └── hero_vault.jpg        # Editorial hero graphic
│
├── tests/                    # 14 automated pytest suites
│
├── data/                     # Ingested indices & persistent storage
│   ├── chroma_db/            # Vector embeddings
│   ├── docs/                 # Document storage
│   ├── test_assets/          # Sample images for testing
│   ├── rag_storage.db        # SQLite database
│   └── bm25_index.pkl        # BM25 serialized index
│
└── scripts/                  # Developer CLI tools
    ├── ask.py                # Terminal interactive query client
    └── create_test_images.py # Generator for synthetic test assets
```

---

## License
MIT License.
