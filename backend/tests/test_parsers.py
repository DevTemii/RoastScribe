import base64
import io

import httpx
import pytest
from PIL import Image

from app.parsers.github_parser import parse_github, parse_repo_ref
from app.parsers.image_parser import parse_image
from app.parsers.text_parser import parse_text
from app.parsers.web_parser import ParseError, extract_summary, parse_url


def test_text_normalises_whitespace():
    p = parse_text("  Uber   for dogs.\n\nIt's AI-native. ")
    assert p.text == "Uber for dogs. It's AI-native."
    assert p.title == "Uber for dogs."


@pytest.mark.parametrize(
    "raw",
    ["owner/repo", "https://github.com/owner/repo", "github.com/owner/repo.git", "https://github.com/owner/repo/"],
)
def test_repo_ref(raw):
    assert parse_repo_ref(raw) == ("owner", "repo")


def test_repo_ref_invalid():
    with pytest.raises(ParseError):
        parse_repo_ref("not a repo")


def test_extract_summary():
    html = "<title>Acme</title><h1>Synergy, but AI</h1><a>Get started free</a><script>x()</script>"
    title, text = extract_summary(html)
    assert title == "Acme"
    assert "Synergy, but AI" in text and "Get started free" in text and "x()" not in text


async def test_parse_url_mocked():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, text="<title>T</title><h1>Hi</h1>"))
    async with httpx.AsyncClient(transport=transport) as c:
        p = await parse_url("example.com", client=c)
    assert p.title == "T" and p.meta["url"] == "https://example.com"


async def test_parse_github_mocked():
    def handler(req: httpx.Request) -> httpx.Response:
        u = str(req.url)
        if u.endswith("/repos/o/r"):
            return httpx.Response(200, json={"description": "d", "default_branch": "main", "language": "Go"})
        if u.endswith("/commits?per_page=10"):
            return httpx.Response(200, json=[{"commit": {"message": "fix stuff\n\nbody"}}])
        if u.endswith("README.md"):
            return httpx.Response(200, text="# Hello")
        if u.endswith("package.json"):
            return httpx.Response(200, json={"dependencies": {"left-pad": "1"}})
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        p = await parse_github("o/r", client=c)
    assert "left-pad" in p.text and "fix stuff" in p.text and "# Hello" in p.text


async def test_parse_github_404():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(404))) as c:
        with pytest.raises(ParseError):
            await parse_github("o/missing", client=c)


def test_image_roundtrip():
    buf = io.BytesIO()
    Image.new("RGB", (2000, 1000), "red").save(buf, format="PNG")
    p = parse_image("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())
    out = Image.open(io.BytesIO(base64.b64decode(p.image_b64)))
    assert max(out.size) <= 1024


def test_image_invalid():
    with pytest.raises(ParseError):
        parse_image(base64.b64encode(b"nope").decode())
