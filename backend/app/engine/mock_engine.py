"""Offline fallback: deterministic, persona-flavoured roasts with no model needed."""
import hashlib
import re

from ..schemas.roast import (
    CringeMetrics,
    ParsedInput,
    Persona,
    RoastResponse,
    TheRescue,
)
from .buzzwords import buzzword_score, find_buzzwords

BURNS = [
    "You've built a {kind} in a market where the incumbents have more engineers than you have users.",
    "The pitch says 'revolutionary'. The product says 'a form with a database'.",
    "Your moat is a drawbridge. Left permanently down. With a welcome mat.",
    "Solving a problem nobody has, for people who'd rather not pay, using a stack nobody asked for.",
    "A weekend of ChatGPT could clone this by Monday, and someone already did, on Sunday.",
    "The roadmap has 14 features. The core one still doesn't quite work.",
    "Your onboarding asks for more commitment than my last relationship.",
    "It's not a startup, it's a feature that's still waiting for a company to join.",
    "Positioning check: 'for everyone' means 'for no one', and the analytics will confirm it.",
    "Monetisation strategy: 'we'll figure it out after we have users.' Bold. Users disagree.",
]
UNIQUENESS = ["Drowning in clones", "One of 4,000 identical decks", "Mildly differentiated vibes", "Genuinely odd (and not in a good way)"]
FLAWS = [
    "No distribution strategy: the product is built, but nobody knows it exists and there's no repeatable way to reach buyers.",
    "It's a feature, not a product. A larger platform can ship it in a sprint and your 'moat' disappears.",
    "Unclear who the buyer is, so every conversion step leaks and every sales call goes sideways.",
    "Retention: nothing brings users back after day one, so growth is a leaky bucket.",
]
PAYERS = [
    "Small teams with an acute, expensive version of this exact pain and a budget owner who can say yes this week.",
    "Agencies and freelancers who'd resell it to clients and measure value in hours saved.",
    "A narrow niche (one industry, one workflow) that today solves this with spreadsheets and swearing.",
]
PIVOTS = [
    "Narrow to one painful workflow for one niche, charge from day one, and ship an integration they already use. Depth beats breadth.",
    "Turn the core feature into an API/plugin for an existing platform and ride its distribution instead of building your own.",
    "Go back to ten users, watch them struggle, and rebuild around the single action they repeat. Cut everything else.",
]


STOPWORDS = {"our", "a", "an", "the", "my", "we", "this", "that", "it", "is", "its", "i", "its", "your", "for", "of", "to"}


def _pick(items: list[str], seed: int, offset: int = 0) -> str:
    return items[(seed + offset) % len(items)]


def _name(parsed: ParsedInput) -> str:
    if parsed.source == "github" and parsed.title:
        return parsed.title
    if parsed.title and parsed.source in {"url"}:
        return re.split(r"[|\-–—:]", parsed.title)[0].strip()[:40] or "Unnamed Product"
    words = [w for w in re.findall(r"[A-Za-z][\w'-]+", parsed.text) if w.lower() not in STOPWORDS]
    return " ".join(w.capitalize() for w in words[:2]) or "Unnamed Product"


def generate_mock_roast(parsed: ParsedInput, persona: Persona, spice_level: int) -> RoastResponse:
    seed = int(hashlib.sha256((parsed.text + persona.id).encode()).hexdigest(), 16)
    found = find_buzzwords(parsed.text)
    score = buzzword_score(found, parsed.text)
    kind = {"idea": "pitch", "github": "repo", "url": "website", "image": "UI"}[parsed.source]

    opener = _pick(persona.mock_openers or ["Let's see what we have here."], seed)
    catch = _pick(persona.catchphrases, seed, 1)
    burns = [
        f"{opener} {_pick(BURNS, seed).format(kind=kind)}",
        _pick(BURNS, seed, 3).format(kind=kind),
        f"{_pick(BURNS, seed, 6).format(kind=kind)} {catch}",
    ]
    if spice_level == 3:
        burns[1] += " I've seen more defensibility in a paper umbrella."
    if spice_level == 1:
        burns = [b.split(". ")[0].rstrip(".") + "... but we can fix that." for b in burns]

    base_survival = 38 - score * 2 - (spice_level - 1) * 3
    survival = max(3, min(61, base_survival + seed % 11))
    name = _name(parsed)
    return RoastResponse(
        product_name=name,
        one_line_summary=f"A {kind} that sounds like {parsed.text[:90].rstrip()}{'…' if len(parsed.text) > 90 else ''}, but with extra steps.",
        roast_title=f"{name}: {_pick(['Ambition Exceeds Execution', 'A Solution Looking For A Problem', 'Pivot Early, Pivot Often', 'Series Z Energy, Seed Reality'], seed, 2)}",
        the_burn=burns,
        cringe_metrics=CringeMetrics(
            buzzword_score=f"{score}/10",
            buzzwords_found=found[:8],
            uniqueness_rating=_pick(UNIQUENESS, seed),
            survival_probability=f"{survival}%",
        ),
        the_rescue=TheRescue(
            fatal_flaw=_pick(FLAWS, seed),
            who_might_actually_pay=_pick(PAYERS, seed, 1),
            the_pivot=_pick(PIVOTS, seed, 2),
        ),
        engine="mock",
        persona=persona.id,
    )
