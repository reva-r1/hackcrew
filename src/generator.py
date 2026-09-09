import os
from typing import List, Dict, Any, Optional
import src.config
from src.config import GROQ_API_KEY, GROQ_BASE_URL, REASONING_LLM_MODEL, FAST_LLM_MODEL

def generate_answer(
    query: str,
    context_chunks: List[Dict[str, Any]],
    model: str = REASONING_LLM_MODEL
) -> Optional[str]:
    """
    Calls Groq API (using OpenAI-compatible endpoint) with llama-3.3-70b-versatile
    to synthesize a grounded enterprise response based solely on retrieved chunks.
    """
    api_key = os.environ.get("GROQ_API_KEY") or GROQ_API_KEY
    if not api_key:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        # Build clean context block
        context_blocks = []
        for idx, chunk in enumerate(context_chunks, start=1):
            meta = chunk.get("metadata", {})
            doc_name = meta.get("doc_name", "Document")
            page = meta.get("page_num", "N/A")
            context_blocks.append(f"[Document: {doc_name} | Page: {page}]\n{chunk.get('text', '')}")

        context_str = "\n\n---\n\n".join(context_blocks)

        system_prompt = (
            "You are an enterprise AI assistant. Answer the user's question accurately, "
            "directly, and concisely based strictly on the provided document excerpts. "
            "Do not extrapolate or assume facts not stated in the text."
        )

        user_content = f"CONTEXT:\n{context_str}\n\nQUESTION: {query}\n\nANSWER:"

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=500
            )
        except Exception as err:
            if "model_not_found" in str(err) or "does not exist" in str(err):
                # Fallback to available Groq models on this account
                fallback_model = "openai/gpt-oss-120b"
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
            else:
                raise err

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Generation error: {e}")
        return None

def generate_summary(
    query: str,
    context_chunks: List[Dict[str, Any]],
    model: str = REASONING_LLM_MODEL
) -> Optional[str]:
    """
    Synthesizes a structured document overview/summary across multiple section chunks.
    Grounded strictly in retrieved document sections.
    """
    api_key = os.environ.get("GROQ_API_KEY") or GROQ_API_KEY
    if not api_key:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        context_blocks = []
        for idx, chunk in enumerate(context_chunks, start=1):
            meta = chunk.get("metadata", {})
            doc_name = meta.get("doc_name", "Document")
            page = meta.get("page_num", "N/A")
            context_blocks.append(f"[Section {idx} | Document: {doc_name} | Page: {page}]\n{chunk.get('text', '')}")

        context_str = "\n\n---\n\n".join(context_blocks)

        system_prompt = (
            "You are an enterprise AI knowledge assistant. Provide a structured, high-level, "
            "comprehensive overview and summary of the document based strictly on the provided section excerpts. "
            "Highlight the primary purpose, core operational areas, responsibilities, and key rules covered. "
            "Organize your answer with clear headings and bullet points. Ground every point in the provided text."
        )

        user_content = f"DOCUMENT EXCERPTS:\n{context_str}\n\nUSER REQUEST: {query}\n\nEXECUTIVE SUMMARY:"

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=700
            )
        except Exception as err:
            fallback_model = "openai/gpt-oss-120b"
            response = client.chat.completions.create(
                model=fallback_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=700
            )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Summary generation error: {e}")
        return None


def rewrite_query(raw_query: str) -> str:
    """
    Tier 2 Section 5: Query rewriting / HyDE expansion using llama-3.1-8b-instant.
    """
    api_key = os.environ.get("GROQ_API_KEY") or GROQ_API_KEY
    if not api_key:
        return raw_query

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=FAST_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a search query optimizer. Given a user question, rewrite it to be clearer, more specific, and keyword-rich for search retrieval. Return only the rewritten query with no intro or explanation."
                },
                {"role": "user", "content": raw_query}
            ],
            temperature=0.2,
            max_tokens=100
        )

        rewritten = response.choices[0].message.content
        return rewritten.strip() if rewritten else raw_query

    except Exception:
        return raw_query

def format_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formats sources array matching api-response-schema.md:
    [{
      "doc_name": "HR_Policy_2026.pdf",
      "page_num": 12,
      "snippet": "Employees working remotely are eligible..."
    }]
    """
    sources = []
    seen = set()

    for chunk in chunks:
        meta = chunk.get("metadata", {})
        raw_text = chunk.get("text", "")
        # Clean text snippet of around ~150 chars
        snippet = raw_text.replace("\n", " ").strip()
        if len(snippet) > 150:
            snippet = snippet[:147] + "..."

        doc_name = meta.get("doc_name", "Unknown")
        page_num = meta.get("page_num")
        
        # Deduplicate identical snippets from same doc & page
        content_key = (doc_name, page_num, snippet[:80])
        if content_key in seen:
            continue
        seen.add(content_key)

        sources.append({
            "doc_name": doc_name,
            "page_num": page_num,
            "snippet": snippet
        })

    return sources
