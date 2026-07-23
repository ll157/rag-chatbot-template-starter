from typing import List

from app.services.llm.factory import get_llm_provider


def generate_answer(question: str, sources: List[dict]) -> str:
    provider = get_llm_provider()
    return provider.generate(question=question, sources=sources)
