from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Chatbot Starter"
    app_env: str = "local"

    upload_dir: str = "数据/上传文件"
    chroma_dir: str = "数据/向量库"
    documents_metadata_path: str = "数据/文档清单.json"

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

    # DeepSeek (OpenAI-compatible Chat Completions)
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    deepseek_max_tokens: int = 512
    deepseek_timeout_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
