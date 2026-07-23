from app.config import settings
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.retrieval_provider import RetrievalProvider


def get_llm_provider():
    provider = settings.llm_provider.lower().strip()

    if provider == "retrieval":
        return RetrievalProvider()

    if provider == "openai":
        return OpenAIProvider()

    if provider == "ollama":
        return OllamaProvider()

    if provider == "gemini":
        return GeminiProvider()

    if provider == "claude":
        return ClaudeProvider()

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {settings.llm_provider}. "
        "Allowed values are: retrieval, openai, ollama, gemini, claude"
    )

