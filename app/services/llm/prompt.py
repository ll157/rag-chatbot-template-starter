from typing import List


def build_context_from_sources(sources: List[dict], max_chars: int) -> str:
    parts = []
    total = 0

    for source in sources:
        text = (source.get("text") or "").strip()
        if not text:
            continue

        page = source.get("page")
        filename = source.get("filename") or "document"
        header = f"[{filename}, page {page}]" if page is not None else f"[{filename}]"
        block = f"{header}\n{text}"

        if total + len(block) > max_chars:
            break

        parts.append(block)
        total += len(block)

    return "\n\n".join(parts)


def build_rag_prompt(question: str, context: str) -> str:
    return f"""
You are a helpful AI assistant that answers questions from the provided documents.

Rules:
1. Answer using the Context below only.
2. If the Context does not contain enough information, say you cannot find it in the documents.
3. Do not make up information.
4. Reply in the same language as the user's question.
5. Be concise, clear, and practical.

Context:
{context}

Question:
{question}
""".strip()
