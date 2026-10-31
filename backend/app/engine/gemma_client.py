"""Ollama / Gemma 2 integration with an automatic mock fallback."""
import json
import logging
import re

import httpx
from pydantic import ValidationError

from ..config import settings
from ..schemas.roast import ParsedInput, Persona, RoastResponse
from .buzzwords import find_buzzwords
from .mock_engine import generate_mock_roast
from .prompt_builder import build_system_prompt, build_user_prompt

log = logging.getLogger(__name__)


def extract_json(raw: str) -> dict:
    """Tolerate fences / chatter around the JSON object."""
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(raw[start : end + 1])


async def _describe_image(client: httpx.AsyncClient, image_b64: str) -> str:
    """PaliGemma captions the screenshot; Gemma 2 then roasts the caption."""
    resp = await client.post(
        f"{settings.ollama_host}/api/generate",
        json={
            "model": settings.vision_model,
            "prompt": "Describe this app/website UI: layout, headline, copy, and visual style.",
            "images": [image_b64],
            "stream": False,
        },
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


async def _ask_gemma(parsed: ParsedInput, persona: Persona, spice: int) -> RoastResponse:
    async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
        if parsed.image_b64:
            caption = await _describe_image(client, parsed.image_b64)
            parsed = parsed.model_copy(update={"text": f"{parsed.text}\nVision model description: {caption}"})

        buzz = find_buzzwords(parsed.text)
        resp = await client.post(
            f"{settings.ollama_host}/api/chat",
            json={
                "model": settings.text_model,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.9 if spice > 1 else 0.7},
                "messages": [
                    {"role": "system", "content": build_system_prompt(persona, spice, buzz)},
                    {"role": "user", "content": build_user_prompt(parsed)},
                ],
            },
        )
        resp.raise_for_status()
        data = extract_json(resp.json()["message"]["content"])
    result = RoastResponse.model_validate({**data, "engine": "gemma", "persona": persona.id})
    # Trust the deterministic detector over the model for the found list.
    if buzz and not result.cringe_metrics.buzzwords_found:
        result.cringe_metrics.buzzwords_found = buzz[:8]
    return result


async def roast(parsed: ParsedInput, persona: Persona, spice: int) -> RoastResponse:
    """Try Gemma via Ollama (twice, for malformed JSON); fall back to the mock."""
    if settings.force_mock:
        return generate_mock_roast(parsed, persona, spice)
    for attempt in (1, 2):
        try:
            return await _ask_gemma(parsed, persona, spice)
        except (json.JSONDecodeError, ValidationError, KeyError) as exc:
            log.warning("Gemma returned unusable JSON (attempt %d): %s", attempt, exc)
        except httpx.HTTPError as exc:
            log.warning("Ollama unavailable (%s); using mock engine.", exc.__class__.__name__)
            break
    return generate_mock_roast(parsed, persona, spice)
