"""Environment & model configuration."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")  # backend/.env (git-ignored); real env vars win


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    # Hosted Gemma via the Google AI Studio (Gemini) API. Takes priority over Ollama.
    gemma_api_key: str | None = os.getenv("GEMMA_API_KEY") or os.getenv("GOOGLE_API_KEY")
    # Empty = auto-discover the best Gemma model your key can use (ListModels).
    gemma_api_model: str = os.getenv("GEMMA_API_MODEL", "").strip()
    gemma_api_base: str = os.getenv(
        "GEMMA_API_BASE", "https://generativelanguage.googleapis.com/v1beta"
    )
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    text_model: str = os.getenv("ROAST_TEXT_MODEL", "gemma2:2b")
    vision_model: str = os.getenv("ROAST_VISION_MODEL", "paligemma")
    # Seconds to wait for Ollama before falling back to the mock engine.
    ollama_timeout: float = float(os.getenv("OLLAMA_TIMEOUT", "90"))
    # Force the mock engine (useful for demos and tests).
    force_mock: bool = os.getenv("ROAST_FORCE_MOCK", "").lower() in {"1", "true", "yes"}
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    http_timeout: float = float(os.getenv("HTTP_TIMEOUT", "10"))
    cors_origins: list[str] = field(
        default_factory=lambda: _split(
            os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        )
    )
    personas_dir: Path = BASE_DIR / "plugins" / "personas"
    buzzwords_dir: Path = BASE_DIR / "plugins" / "buzzwords"


settings = Settings()
