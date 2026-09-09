# RAG Backend Build Spec — Tier 1 & Tier 2

Use this as the source-of-truth doc during build. Each section = core idea + exactly what to implement. Feed one section at a time into loop-prompting so context stays tight.

---

## TIER 1 — Build these first, in this order

### 1. Hybrid Search (BM25 + Vector Fusion)

**Core idea:** Vector search alone misses exact terms — product codes, IDs, rare names, acronyms — because embeddings favor semantic similarity over exact matches. Keyword search (BM25) catches exact matches but misses paraphrasing. Run both, then merge the ranked lists.

**What to build:**
- Vector index: your existing embedding store (Chroma/FAISS/whatever you're using).
- Keyword index: BM25 over the same chunks. Use `rank_bm25` (Python lib) — no separate DB needed, keep it in-memory or SQLite FTS5 if you want persistence.
- Fusion: **Reciprocal Rank Fusion (RRF)**. For each chunk, score = `1/(k + rank_vector) + 1/(k + rank_bm25)`, where k is a constant (typically 60). Sort by combined score, take top-N.
- Input: user query string.
- Output: ranked list of chunk IDs with fused scores.

**Interface contract:** `hybrid_search(query: str, top_k: int) -> List[{chunk_id, score, text, metadata}]`

---

### 2. Cross-Encoder Reranking

**Core idea:** Your initial retrieval (bi-encoder / vector search) scores query and document independently, then compares embeddings — fast but approximate. A cross-encoder looks at the query and document *together* in one forward pass, so it's slower but much more accurate. Use it only on the small shortlist from step 1, not the whole corpus.

**What to build:**
- Take top-N (e.g. 20-30) results from hybrid search.
- Load `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers`.
- Score each (query, chunk_text) pair.
- Re-sort by cross-encoder score, keep top-K (e.g. 5) for the generation step.

**Interface contract:** `rerank(query: str, candidates: List[chunk]) -> List[chunk]` (same shape, reordered/truncated)

---

### 3. Confidence-Gated Refusal (threshold-based, NOT judge-LLM)

**Core idea:** Don't rely on prompting the LLM to "say I don't know" — it's unreliable under pressure/jailbreak attempts. Instead, measure retrieval confidence numerically and refuse *before* generation if the evidence is weak. Deterministic, explainable, no extra LLM call.

**What to build:**
- After reranking, look at the top cross-encoder score(s) for the final chunk set.
- Set a threshold (tune empirically — start around 0.3-0.5 depending on your scorer's scale, test against known in-scope vs out-of-scope questions).
- If top score < threshold (or if too few chunks clear the bar) → return a refusal response immediately, skip the generation call entirely.
- If score clears the bar → proceed to generate the answer using only the passed chunks as context.

**Interface contract:** `should_answer(reranked_results: List[chunk], threshold: float) -> bool`
Response shape when refusing: `{status: "refused", reason: "insufficient_evidence"}`

**Note:** Log every refusal — you'll want these numbers for talking about your refusal rate later even though the dashboard itself is Tier 3.

---

## TIER 2 — Build if time allows, in this order

### 4. Citation Metadata (plain — doc name, page, snippet)

**Core idea:** Every answer should point back to exactly which chunk(s) it came from. No PDF.js highlighting, no deep-linking — just structured metadata the frontend can display as plain text.

**What to build:**
- At ingestion time, when you chunk documents, store per chunk: `doc_id`, `doc_name`, `page_num` (if available), and the raw chunk text itself.
- When generating the final answer, pass through which chunk IDs were actually used as context.
- Response includes a `sources` array: `[{doc_name, page_num, snippet}]` — snippet = first ~150 chars of the chunk, or the most relevant sentence if you want to go slightly further.

**Interface contract:** Add `sources: List[{doc_name, page_num, snippet}]` to your final response JSON.

---

### 5. Query Rewriting / Expansion (HyDE-style)

**Core idea:** Users type vague or underspecified questions. Before retrieval, have the LLM generate either (a) a clearer/expanded version of the query, or (b) a *hypothetical answer* to the question (HyDE) — then embed and search using that instead of the raw query. Hypothetical answers tend to align better with real document phrasing than short questions do.

**What to build:**
- One extra LLM call, before hybrid search: prompt = "Given this user question, write a short hypothetical answer as if you already knew the answer, using natural document-style phrasing." (or simpler: just "rewrite this query to be clearer and more specific")
- Feed the rewritten query/hypothetical answer into hybrid search instead of (or alongside) the raw query.
- Keep the *original* query around for the final generation step — don't let the LLM answer using its own hypothetical text as if it were retrieved fact.

**Interface contract:** `rewrite_query(raw_query: str) -> str`

**Cost tradeoff:** adds one LLM round-trip of latency per query. Only add this once 1-4 are solid and tested.

---

### 6. Contextual Chunk Enrichment

**Core idea:** Prepend a short summary of the parent document to every chunk before embedding it. This gives each chunk surrounding context it wouldn't otherwise have, which measurably improves retrieval (Anthropic's own research cites large gains on their benchmark).

**What to build:**
- At ingestion time, once per document: generate a 1-sentence LLM summary of the whole document.
- Prepend that summary to every chunk from that document before embedding (e.g. `"[Doc summary: ...] {chunk_text}"`).
- Store the enriched version for embedding/search, but keep the original clean chunk text for citation display (don't show the summary prefix to the user).

**Interface contract:** `enrich_chunk(chunk_text: str, doc_summary: str) -> str` — used only in the ingestion pipeline, not at query time.

---

## Suggested loop-prompting order

Feed sections to your coding assistant one at a time, in this sequence, so each step has a working, testable output before the next depends on it:

1. → Section 1 (hybrid search) → test with curl/Postman
2. → Section 2 (reranking) → test on top of 1
3. → Section 3 (refusal gate) → test with known in/out-of-scope queries
4. → Section 4 (citations) → verify response shape
5. → Section 5 (query rewriting) — optional, only if time remains
6. → Section 6 (chunk enrichment) — optional, only if time remains, note this changes your ingestion pipeline not your query pipeline

---

## What you'll likely want as separate docs next

- **API response schema doc** — the exact final JSON contract (`answer`, `sources`, `status`, `confidence`) to hand your frontend team so they can build against a mock while you build the real thing.
- **Ingestion pipeline spec** — chunking strategy, chunk size/overlap, metadata fields to attach per chunk (doc_id, page_num, role/department if doing RBAC).
- **RBAC filter spec** (Tier 3) — only write this once 1-4 above are done; small doc, just the metadata tagging + filter-before-search logic.
