"""
Application configuration using Pydantic Settings.
Reads from environment variables and .env file.
"""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Gemini / LLM ──────────────────────────────────────────
    gemini_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.2
    llm_max_context_tokens: int = 90_000

    # ── MobSF Integration ────────────────────────────────────────
    mobsf_url: str = "http://localhost:8001"
    mobsf_api_key: str = ""

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "sqlite:///./data/audit_copilot.db"

    # ── ChromaDB ─────────────────────────────────────────────────
    chroma_persist_dir: str = "./data/chroma_db"

    # ── Server ───────────────────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # ── JWT (optional MVP scaffold) ──────────────────────────────
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # ── Paths ────────────────────────────────────────────────────
    reports_dir: str = "./data/reports"
    knowledge_base_dir: str = "./data/knowledge_base"
    samples_dir: str = "./data/samples"
    uploads_dir: str = "./data/uploads"

    # ── RAG ──────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 64
    rag_top_k: int = 5

    @property
    def reports_path(self) -> Path:
        p = Path(self.reports_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def uploads_path(self) -> Path:
        p = Path(self.uploads_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def knowledge_base_path(self) -> Path:
        return Path(self.knowledge_base_dir)


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
