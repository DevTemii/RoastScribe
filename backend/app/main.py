"""FastAPI application entrypoint."""
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .engine.gemma_client import EngineError, list_gemma_models, roast
from .parsers import ParseError, parse_input
from .plugins import load_personas
from .schemas.roast import RoastRequest, RoastResponse

app = FastAPI(title="RoastScribe API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Next.js hops to 3001+ when 3000 is busy, so accept any local dev port.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/personas")
async def personas() -> list[dict]:
    return [
        p.model_dump(include={"id", "name", "emoji", "tagline", "catchphrases"})
        for p in load_personas().values()
    ]


@app.post("/api/roast", response_model=RoastResponse)
async def create_roast(req: RoastRequest) -> RoastResponse:
    persona = load_personas().get(req.persona)
    if persona is None:
        raise HTTPException(404, f"Unknown persona '{req.persona}'")
    try:
        parsed = await parse_input(req)
    except ParseError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        return await roast(parsed, persona, req.spice_level)
    except EngineError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.get("/api/status")
async def status() -> dict:
    """Which engine is configured, and does the hosted model actually answer?"""
    info: dict = {
        "mode": "gemma_api" if settings.gemma_api_key else ("mock" if settings.force_mock else "ollama_or_mock"),
        "gemma_api_key_set": bool(settings.gemma_api_key),
        "model": settings.gemma_api_model or "(auto)" if settings.gemma_api_key else settings.text_model,
    }
    if settings.gemma_api_key:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                models = await list_gemma_models(c)
            info["api_ok"] = True
            info["usable_gemma_models"] = models
            info["will_use"] = settings.gemma_api_model or (models[0] if models else None)
            if settings.gemma_api_model:
                info["configured_model_usable"] = settings.gemma_api_model in models
        except httpx.HTTPStatusError as exc:
            info.update(api_ok=False, error=f"HTTP {exc.response.status_code}: {exc.response.text[:200]}")
        except httpx.HTTPError as exc:
            info.update(api_ok=False, error=exc.__class__.__name__)
    return info
