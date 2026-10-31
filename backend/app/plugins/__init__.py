"""Plugin discovery: drop a JSON file in a plugin folder and it is loaded."""
import json
import logging
from functools import lru_cache

from ..config import settings
from ..schemas.roast import Persona

log = logging.getLogger(__name__)


@lru_cache
def load_personas() -> dict[str, Persona]:
    personas: dict[str, Persona] = {}
    for path in sorted(settings.personas_dir.glob("*.json")):
        try:
            persona = Persona.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:  # bad contributor file shouldn't kill the server
            log.warning("Skipping invalid persona %s: %s", path.name, exc)
            continue
        personas[persona.id] = persona
    return personas


@lru_cache
def load_buzzwords() -> list[str]:
    words: set[str] = set()
    for path in sorted(settings.buzzwords_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            words.update(w.lower() for w in data.get("words", []))
        except Exception as exc:
            log.warning("Skipping invalid buzzword file %s: %s", path.name, exc)
    return sorted(words)
