from typing import List

import anthropic

from app.config import settings
from app.services.llm.prompt import build_context_from_sources, build_rag_prompt


class ClaudeProvider:
    def __init__(self):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=claude")
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def generate(self, question: str, sources: List[dict]) -> str:
        context = build_context_from_sources(sources, settings.llm_max_context_chars)
        if not context.strip():
            return "I could not find relevant information in the documents."
        prompt = build_rag_prompt(question=question, context=context)
        message = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "\n".join(
            block.text for block in message.content
            if getattr(block, "type", None) == "text"
        ).strip()
