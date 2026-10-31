"""Gemma integration: hosted API (key) or local Ollama, with an automatic mock fallback."""
import asyncio
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


_resolved_model: str | None = None


def _rank(name: str) -> tuple:
    """Newest version first, then biggest instruction-tuned model that is still fast."""
    m = re.search(r"gemma-?(\d+(?:\.\d+)?)", name)
    size = re.search(r"(\d+)b", name)
    return (
        float(m.group(1)) if m else 0.0,
        "-it" in name,
        # 27b/31b are slow & often rate-limited; prefer them anyway only if nothing smaller is newer
        int(size.group(1)) if size else 0,
    )


async def list_gemma_models(client: httpx.AsyncClient) -> list[str]:
    """Gemma models this key can call with generateContent, best first."""
    resp = await client.get(
        f"{settings.gemma_api_base}/models",
        headers={"x-goog-api-key": settings.gemma_api_key or ""},
        params={"pageSize": 200},
    )
    resp.raise_for_status()
    names = [
        m["name"].removeprefix("models/")
        for m in resp.json().get("models", [])
        if "gemma" in m["name"] and "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    return sorted(names, key=_rank, reverse=True)


async def _model_for_api(client: httpx.AsyncClient) -> str:
    global _resolved_model
    if settings.gemma_api_model:
        return settings.gemma_api_model
    if _resolved_model is None:
        models = await list_gemma_models(client)
        if not models:
            raise EngineError(
                "Your API key has no Gemma models that support generateContent. "
                "Check /api/status, or set GEMMA_API_MODEL explicitly."
            )
        _resolved_model = models[0]
        log.info("Auto-selected Gemma model: %s (candidates: %s)", _resolved_model, models)
    return _resolved_model


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

    global _resolved_model
    async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
        model = await _model_for_api(client)
        resp = await client.post(
            f"{settings.gemma_api_base}/models/{model}:generateContent",
            headers={"x-goog-api-key": settings.gemma_api_key or ""},
            json={
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"temperature": 0.9 if spice > 1 else 0.7, "maxOutputTokens": 1800},
            },
        )
        if resp.status_code == 404:
            _resolved_model = None  # re-discover next time
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

    # A configured API key means "I want the real model": never hide failures
    # behind the mock, surface them so they can be fixed.
    if settings.gemma_api_key:
        last = "no response"
        for attempt in (1, 2, 3):
            try:
                return await _ask_gemma_api(parsed, persona, spice)
            except (json.JSONDecodeError, ValidationError, KeyError, IndexError) as exc:
                last = f"model returned unusable JSON ({exc.__class__.__name__})"
                log.warning("Gemma API bad output (attempt %d): %s", attempt, exc)
            except httpx.HTTPStatusError as exc:
                last = f"HTTP {exc.response.status_code}: {_api_error(exc.response)}"
                log.warning("Gemma API error (attempt %d): %s", attempt, last)
                if exc.response.status_code in (429, 500, 503) and attempt < 3:
                    await asyncio.sleep(2 * attempt)
                    continue
                break  # 400/401/403/404 won't fix themselves
            except httpx.HTTPError as exc:
                last = f"network error ({exc.__class__.__name__})"
                log.warning("Gemma API unreachable (attempt %d): %s", attempt, exc)
        raise EngineError(f"The Gemma API call failed — {last}")

    # No API key: try local Ollama, then fall back to the labelled demo/mock engine.
    for attempt in (1, 2):
        try:
            return await _ask_gemma(parsed, persona, spice)
        except (json.JSONDecodeError, ValidationError, KeyError) as exc:
            log.warning("Ollama returned unusable JSON (attempt %d): %s", attempt, exc)
        except httpx.HTTPError as exc:
            log.warning("Ollama unavailable (%s); using mock engine.", exc.__class__.__name__)
            break
    return generate_mock_roast(parsed, persona, spice)


class EngineError(RuntimeError):
    """The configured AI provider failed; message is safe to show the user."""


def _api_error(resp: httpx.Response) -> str:
    try:
        return str(resp.json()["error"]["message"])[:300]
    except Exception:
        return resp.text[:200]
