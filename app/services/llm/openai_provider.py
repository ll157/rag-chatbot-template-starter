from typing import List

from openai import OpenAI

from app.config import settings
from app.services.llm.prompt import build_context_from_sources, build_rag_prompt


class OpenAIProvider:
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, question: str, sources: List[dict]) -> str:
        context = build_context_from_sources(sources, settings.llm_max_context_chars)
        if not context.strip():
            return "I could not find relevant information in the documents."
        prompt = build_rag_prompt(question=question, context=context)
        response = self.client.responses.create(model=settings.openai_model, input=prompt)
        return response.output_text
