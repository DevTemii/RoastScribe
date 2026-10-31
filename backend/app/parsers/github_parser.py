"""Fetch README, dependencies and commit metadata via the GitHub public API."""
import json
import re

import httpx

from ..config import settings
from ..schemas.roast import ParsedInput
from .web_parser import ParseError

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
REPO_RE = re.compile(r"(?:github\.com[/:])?(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$")


def parse_repo_ref(raw: str) -> tuple[str, str]:
    raw = raw.strip().split("?")[0].split("#")[0]
    raw = re.sub(r"^https?://(www\.)?", "", raw)
    m = REPO_RE.search(raw)
    if not m:
        raise ParseError("Use a repo like `owner/repo` or https://github.com/owner/repo")
    return m["owner"], m["repo"]


async def parse_github(content: str, client: httpx.AsyncClient | None = None) -> ParsedInput:
    owner, repo = parse_repo_ref(content)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "RoastScribe/0.1"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    owns = client is None
    client = client or httpx.AsyncClient(timeout=settings.http_timeout, headers=headers)

    try:
        r = await client.get(f"{API}/repos/{owner}/{repo}")
        if r.status_code == 404:
            raise ParseError(f"Repo {owner}/{repo} not found (or it's private).")
        if r.status_code == 403:
            raise ParseError("GitHub rate limit hit. Set GITHUB_TOKEN and retry.")
        r.raise_for_status()
        info = r.json()
        branch = info.get("default_branch", "main")

        async def raw(path: str) -> str | None:
            res = await client.get(f"{RAW}/{owner}/{repo}/{branch}/{path}")
            return res.text if res.status_code == 200 else None

        readme = await raw("README.md") or await raw("readme.md") or ""
        pkg = await raw("package.json")
        reqs = await raw("requirements.txt")

        commits: list[dict] = []
        cr = await client.get(f"{API}/repos/{owner}/{repo}/commits", params={"per_page": 10})
        if cr.status_code == 200:
            commits = cr.json()
    except httpx.HTTPError as exc:
        raise ParseError(f"GitHub request failed: {exc.__class__.__name__}") from exc
    finally:
        if owns:
            await client.aclose()

    deps: list[str] = []
    if pkg:
        try:
            data = json.loads(pkg)
            deps += list(data.get("dependencies", {})) + list(data.get("devDependencies", {}))
        except json.JSONDecodeError:
            pass
    if reqs:
        deps += [re.split(r"[=<>~! ]", l)[0] for l in reqs.splitlines() if l.strip() and not l.startswith("#")]

    messages = [c.get("commit", {}).get("message", "").split("\n")[0] for c in commits]
    parts = [
        f"Repository: {owner}/{repo}",
        f"Description: {info.get('description') or '(none)'}",
        f"Language: {info.get('language') or 'unknown'} | Stars: {info.get('stargazers_count', 0)} "
        f"| Forks: {info.get('forks_count', 0)} | Open issues: {info.get('open_issues_count', 0)}",
        f"Last pushed: {info.get('pushed_at')}",
        f"Dependencies ({len(deps)}): {', '.join(deps[:40])}" if deps else "Dependencies: none found",
        f"Recent commits: {' | '.join(messages)}" if messages else "",
        f"README (truncated):\n{readme[:3000]}" if readme else "README: missing (yikes)",
    ]
    return ParsedInput(
        source="github",
        title=repo,
        text="\n".join(p for p in parts if p),
        meta={"repo": f"{owner}/{repo}"},
    )
