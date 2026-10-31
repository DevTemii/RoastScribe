"""Scrape a live website: title, hero headline, meta description, CTAs."""
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from ..config import settings
from ..schemas.roast import ParsedInput

CTA_HINTS = ("get started", "sign up", "try", "demo", "join", "start", "buy", "book", "waitlist", "free")


class ParseError(ValueError):
    """Raised with a user-presentable message."""


def normalise_url(raw: str) -> str:
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.hostname:
        raise ParseError("That doesn't look like a valid URL.")
    return raw


def _assert_public_host(url: str) -> None:
    """Basic SSRF guard: refuse localhost / private network targets."""
    host = urlparse(url).hostname or ""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ParseError(f"Couldn't resolve {host}.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ParseError("Refusing to fetch private or local addresses.")


def extract_summary(html: str) -> tuple[str | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else None
    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    description = desc_tag.get("content", "").strip() if desc_tag else ""
    h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")][:2]
    h2 = [h.get_text(" ", strip=True) for h in soup.find_all("h2")][:6]
    ctas = []
    for el in soup.find_all(["a", "button"]):
        label = el.get_text(" ", strip=True)
        if label and len(label) < 40 and any(k in label.lower() for k in CTA_HINTS):
            ctas.append(label)
    ctas = list(dict.fromkeys(ctas))[:6]

    parts = [
        f"Page title: {title}" if title else "",
        f"Meta description: {description}" if description else "",
        f"Hero headline(s): {' | '.join(h1)}" if h1 else "",
        f"Section headings: {' | '.join(h2)}" if h2 else "",
        f"Calls to action: {' | '.join(ctas)}" if ctas else "",
    ]
    return title, "\n".join(p for p in parts if p)


async def parse_url(content: str, client: httpx.AsyncClient | None = None) -> ParsedInput:
    url = normalise_url(content)
    if client is None:
        _assert_public_host(url)
    owns_client = client is None
    client = client or httpx.AsyncClient(
        timeout=settings.http_timeout,
        follow_redirects=True,
        headers={"User-Agent": "RoastScribe/0.1 (+https://github.com/roast-my-product)"},
    )
    try:
        resp = await client.get(url)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise ParseError(f"Couldn't fetch {url}: {exc.__class__.__name__}") from exc
    finally:
        if owns_client:
            await client.aclose()

    title, text = extract_summary(resp.text[:500_000])
    if not text:
        raise ParseError("The page had no readable content (is it a JS-only app?).")
    return ParsedInput(source="url", title=title, text=text, meta={"url": url})
