"""Gemma integration: hosted API (key) or local Ollama, with an automatic mock fallback."""
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


async def _ask_gemma_api(parsed: ParsedInput, persona: Persona, spice: int) -> RoastResponse:
    """Hosted Gemma through the Google AI Studio API (authenticated with an API key).

    Gemma models on this API reject `system_instruction` and JSON mode, so the
    persona prompt is sent as part of the user turn and the JSON is parsed
    defensively.
    """
    buzz = find_buzzwords(parsed.text)
    prompt = f"{build_system_prompt(persona, spice, buzz)}\n\n{build_user_prompt(parsed)}"
    parts: list[dict] = [{"text": prompt}]
    if parsed.image_b64:
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": parsed.image_b64}})

    async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
        resp = await client.post(
            f"{settings.gemma_api_base}/models/{settings.gemma_api_model}:generateContent",
            headers={"x-goog-api-key": settings.gemma_api_key or ""},
            json={
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"temperature": 0.9 if spice > 1 else 0.7},
            },
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    result = RoastResponse.model_validate({**extract_json(text), "engine": "gemma", "persona": persona.id})
    if buzz and not result.cringe_metrics.buzzwords_found:
        result.cringe_metrics.buzzwords_found = buzz[:8]
    return result


async def roast(parsed: ParsedInput, persona: Persona, spice: int) -> RoastResponse:
    """Hosted Gemma API (if a key is set) -> Ollama -> mock. Each gets two tries for bad JSON."""
    if settings.force_mock:
        return generate_mock_roast(parsed, persona, spice)

    providers = []
    if settings.gemma_api_key:
        providers.append(("Gemma API", _ask_gemma_api))
    providers.append(("Ollama", _ask_gemma))

    for name, ask in providers:
        for attempt in (1, 2):
            try:
                return await ask(parsed, persona, spice)
            except (json.JSONDecodeError, ValidationError, KeyError, IndexError) as exc:
                log.warning("%s returned unusable JSON (attempt %d): %s", name, attempt, exc)
            except httpx.HTTPStatusError as exc:
                log.warning("%s rejected the request (HTTP %s); trying next provider.", name, exc.response.status_code)
                break
            except httpx.HTTPError as exc:
                log.warning("%s unavailable (%s); trying next provider.", name, exc.__class__.__name__)
                break
    return generate_mock_roast(parsed, persona, spice)
