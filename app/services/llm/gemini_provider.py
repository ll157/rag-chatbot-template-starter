from typing import List

from google import genai

from app.config import settings
from app.services.llm.prompt import build_context_from_sources, build_rag_prompt


class GeminiProvider:
    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate(self, question: str, sources: List[dict]) -> str:
        context = build_context_from_sources(sources, settings.llm_max_context_chars)
        if not context.strip():
            return "I could not find relevant information in the documents."
        prompt = build_rag_prompt(question=question, context=context)
        response = self.client.models.generate_content(
            model=settings.gemini_model, contents=prompt
        )
        return response.text or ""
