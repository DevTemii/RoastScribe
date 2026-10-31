"""Normalise a raw idea / elevator pitch."""
import re

from ..schemas.roast import ParsedInput

MAX_CHARS = 6000


def parse_text(content: str) -> ParsedInput:
    text = re.sub(r"\s+", " ", content).strip()[:MAX_CHARS]
    first_sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return ParsedInput(source="idea", title=first_sentence[:60] or None, text=text)
