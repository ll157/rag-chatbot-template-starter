from typing import List


class RetrievalProvider:
    """No-LLM fallback. Lets the template run with zero API keys."""

    def generate(self, question: str, sources: List[dict]) -> str:
        return (
            "Retrieval-only mode is on, so no LLM was called. "
            "The most relevant passages are listed in the sources below."
        )
