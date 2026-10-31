"""Environment & model configuration."""
import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
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
