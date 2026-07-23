from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Chatbot Starter"
    app_env: str = "local"

    upload_dir: str = "data/uploads"
    chroma_dir: str = "data/chroma"
    documents_metadata_path: str = "data/documents.json"

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # retrieval | openai | ollama | gemini | claude
    llm_provider: str = "retrieval"
    llm_max_context_chars: int = 6000

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4.1-mini"

    # Ollama Local
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"

    # Claude
    anthropic_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-5"
    claude_max_tokens: int = 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
