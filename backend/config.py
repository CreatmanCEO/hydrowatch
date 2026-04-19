"""Application configuration via environment variables."""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import SecretStr, Field


class Settings(BaseSettings):
    # LLM Provider Keys
    gemini_api_key: SecretStr
    cerebras_api_key: SecretStr
    anthropic_api_key: SecretStr

    # Model routing — Pool A (simple/medium, mutual fallback)
    model_pool_a_primary: str = "gemini/gemini-2.5-flash"
    model_pool_a_fallback: str = "cerebras/llama-3.3-70b"

    # Model routing — Pool B (complex tasks)
    model_pool_b_default: str = "anthropic/claude-haiku-4-5-20251001"
    model_pool_b_complex: str = "anthropic/claude-sonnet-4-5-20250514"

    llm_temperature: float = 0.1

    # Database
    database_url: str = "postgresql+asyncpg://hydrowatch:hydrowatch_dev@localhost:5432/hydrowatch"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Data — resolved relative to backend/ directory
    data_dir: str = str(Path(__file__).resolve().parent.parent / "data")
    max_csv_size_mb: int = 10

    # Langfuse (optional)
    langfuse_public_key: str = ""
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_host: str = "http://localhost:3001"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
