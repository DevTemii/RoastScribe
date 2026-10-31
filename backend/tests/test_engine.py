from dataclasses import replace

import httpx
from fastapi.testclient import TestClient

from app.config import settings
from app.engine import gemma_client
from app.engine.buzzwords import buzzword_score, find_buzzwords
from app.engine.gemma_client import extract_json
from app.engine.mock_engine import generate_mock_roast
from app.engine.prompt_builder import build_system_prompt
from app.main import app
from app.parsers.text_parser import parse_text
from app.plugins import load_personas

PITCH = "Our AI-native, blockchain-powered platform leverages synergy to disrupt dog walking."


def test_buzzwords():
    found = find_buzzwords(PITCH)
    assert {"ai-native", "synergy", "leverage"} <= set(found) or "synergy" in found
    assert 1 <= buzzword_score(found, PITCH) <= 10


def test_mock_is_schema_valid_and_deterministic():
    p = load_personas()["gordon_ramsay"]
    a = generate_mock_roast(parse_text(PITCH), p, 2)
    b = generate_mock_roast(parse_text(PITCH), p, 2)
    assert a == b and a.engine == "mock" and len(a.the_burn) == 3


def test_prompt_contains_persona_and_schema():
    p = load_personas()["cynical_vc"]
    s = build_system_prompt(p, 3, ["synergy"])
    assert "Where's the moat?" in s and "the_rescue" in s and "synergy" in s


def test_extract_json_handles_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 1} hope that helps') == {"a": 1}


async def test_falls_back_to_mock_when_ollama_down(monkeypatch):
    async def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(gemma_client, "_ask_gemma", boom)
    r = await gemma_client.roast(parse_text(PITCH), load_personas()["cynical_vc"], 2)
    assert r.engine == "mock"


GOOD = {
    "product_name": "Dogly",
    "one_line_summary": "A dog walking app.",
    "roast_title": "Fetch Funding",
    "the_burn": ["a", "b", "c"],
    "cringe_metrics": {
        "buzzword_score": "5/10",
        "buzzwords_found": [],
        "uniqueness_rating": "Clone",
        "survival_probability": "20%",
    },
    "the_rescue": {"fatal_flaw": "x", "who_might_actually_pay": "y", "the_pivot": "z"},
}


async def test_gemma_api_key_path(monkeypatch):
    import json

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers.get("x-goog-api-key")
        seen["url"] = str(request.url)
        text = "```json\n" + json.dumps(GOOD) + "\n```"
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})

    real = httpx.AsyncClient
    monkeypatch.setattr(
        gemma_client.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw)
    )
    monkeypatch.setattr(gemma_client, "settings", replace(settings, gemma_api_key="k-123", force_mock=False))
    r = await gemma_client.roast(parse_text(PITCH), load_personas()["cynical_vc"], 2)
    assert r.engine == "gemma" and r.product_name == "Dogly"
    assert seen["key"] == "k-123" and "gemma" in seen["url"] and seen["url"].endswith(":generateContent")


async def test_bad_api_key_falls_through_to_mock(monkeypatch):
    real = httpx.AsyncClient
    monkeypatch.setattr(
        gemma_client.httpx,
        "AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(lambda r: httpx.Response(403)), **kw),
    )
    monkeypatch.setattr(gemma_client, "settings", replace(settings, gemma_api_key="bad", force_mock=False))
    r = await gemma_client.roast(parse_text(PITCH), load_personas()["cynical_vc"], 2)
    assert r.engine == "mock"


def test_api_roast_end_to_end(monkeypatch):
    monkeypatch.setattr(gemma_client, "settings", replace(settings, force_mock=True))
    c =TestClient(app)
    r = c.post("/api/roast", json={"input_type": "idea", "content": PITCH, "persona": "gen_z_founder", "spice_level": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["cringe_metrics"]["survival_probability"].endswith("%")
    assert c.post("/api/roast", json={"input_type": "idea", "content": "x", "persona": "nope"}).status_code == 404
    assert c.get("/api/personas").json()
