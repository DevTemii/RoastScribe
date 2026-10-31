"""FastAPI application entrypoint."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .engine.gemma_client import roast
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
    return await roast(parsed, persona, req.spice_level)
