"""
Centralized configuration. All runtime behavior (which LLM provider to use,
DB connection, etc.) is driven by environment variables so the app can be
redeployed / retargeted without code changes.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny"

    # --- LLM routing ---
    # "ollama" for local / offline demo, "anthropic" for cloud
    llm_provider: str = "ollama"

    # Local (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"

    # Cloud (Anthropic)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # --- Retrieval ---
    top_k: int = 2
    similarity_threshold: float = 0.35  # below this -> "insufficient information"
    chunk_tokens: int = 650
    chunk_overlap_tokens: int = 100

    # --- App ---
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
