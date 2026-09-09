# API Response Schema — Backend Contract for Frontend

Hand this to your frontend dev today. This is the exact shape every endpoint returns. Build against this even before the real logic is done — mock it with static JSON matching this shape.

---

## POST `/query`

**Request body:**
```json
{
  "query": "What is the WFH internet allowance?",
  "role": "employee"
}
```
- `query` (string, required) — the user's question.
- `role` (string, optional) — only needed once RBAC is added (Tier 3). Default to `"employee"` if omitted. Frontend can ignore this field entirely until told otherwise.

---

**Response body — success case (answer given):**
```json
{
  "status": "answered",
  "answer": "The WFH internet allowance is ₹1,500/month, reimbursed quarterly.",
  "confidence": 0.82,
  "sources": [
    {
      "doc_name": "HR_Policy_2026.pdf",
      "page_num": 12,
      "snippet": "Employees working remotely are eligible for an internet allowance of ₹1,500 per month..."
    },
    {
      "doc_name": "HR_Policy_2026.pdf",
      "page_num": 13,
      "snippet": "Reimbursement is processed quarterly upon submission of..."
    }
  ]
}
```

**Response body — refusal case (low confidence / out of scope):**
```json
{
  "status": "refused",
  "answer": null,
  "confidence": 0.18,
  "sources": [],
  "reason": "insufficient_evidence"
}
```

**Response body — error case (server/API failure):**
```json
{
  "status": "error",
  "answer": null,
  "confidence": null,
  "sources": [],
  "reason": "generation_failed"
}
```

---

### Field reference

| Field | Type | Always present? | Notes |
|---|---|---|---|
| `status` | string | Yes | One of `"answered"`, `"refused"`, `"error"`. Frontend should switch UI state on this field, not on presence/absence of `answer`. |
| `answer` | string \| null | Yes (null if not answered) | The generated answer text. `null` when `status` isn't `"answered"`. |
| `confidence` | number \| null | Yes | 0.0–1.0. Useful if you want to show a confidence indicator in UI, optional to display. |
| `sources` | array | Yes (empty array if none) | Never `null` — always an array, empty when no sources. Loop over this to render citations. |
| `sources[].doc_name` | string | Yes | Display name of the source document. |
| `sources[].page_num` | number \| null | Yes | Null if the doc format has no page concept. |
| `sources[].snippet` | string | Yes | Short excerpt (~150 chars) from the chunk used. |
| `reason` | string | Only on `refused`/`error` | Machine-readable reason code. Not required to display to user, but useful for debugging. |

**Frontend rule of thumb:** always check `status` first. Don't assume `answer` exists just because the request succeeded (HTTP 200) — a refusal is still HTTP 200 with `status: "refused"`.

---

## GET `/health` (optional but recommended)

Simple liveness check so frontend can show "backend offline" instead of silently failing during demo setup.

```json
{ "status": "ok" }
```

---

## Mock data for frontend to build against today

Frontend can hardcode these three JSON blobs (answered / refused / error) and wire up UI switching on `status` before your real endpoint exists. Once your endpoint is live, they just swap the mock fetch for a real `fetch('/query', ...)` call — same shape, zero UI rework needed.

---

## Addendum: POST `/preview-confidence` (Live Typing Match Meter)

Lightweight, ultra-fast (<200ms) live preview endpoint called as the user types (recommended debounce: ~400ms). Runs vector search only (no LLM, no reranker, read-only against existing index).

### Request Body:
```json
{
  "partial_query": "what is the leave pol"
}
```
- `partial_query` (string, required) — whatever the user has typed so far.

---

### Response Body:
```json
{
  "score": 74.5,
  "status": "strong_match"
}
```

### Field Reference:

| Field | Type | Values / Range | Notes |
|---|---|---|---|
| `score` | number | `0.0` – `100.0` | Normalized match strength meter score on a 0-100 scale. |
| `status` | string | `"strong_match"`, `"weak_match"`, `"no_match"` | Categorical label: `>70` = `"strong_match"`, `40–70` = `"weak_match"`, `<40` = `"no_match"`. |

### UI Behavior:
- Call on input with ~400ms debounce.
- If user input is `< 2` characters, frontend can bypass fetch and show `score: 0`, `status: "no_match"`.
- This endpoint is read-only and never writes to query logs or triggers refusal screens.
