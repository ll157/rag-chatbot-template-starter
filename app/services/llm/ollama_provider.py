from typing import List

import httpx

from app.config import settings
from app.services.llm.prompt import build_context_from_sources, build_rag_prompt


class OllamaProvider:
    def generate(self, question: str, sources: List[dict]) -> str:
        context = build_context_from_sources(sources, settings.llm_max_context_chars)
        if not context.strip():
            return "I could not find relevant information in the documents."
        prompt = build_rag_prompt(question=question, context=context)
        url = f"{settings.ollama_base_url}/api/chat"
        payload = {
            "model": settings.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        with httpx.Client(timeout=120) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
        return response.json()["message"]["content"]
