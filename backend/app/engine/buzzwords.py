"""Deterministic buzzword detector backed by plugins/buzzwords/*.json."""
import re

from ..plugins import load_buzzwords


def find_buzzwords(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for word in load_buzzwords():
        if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", lowered):
            found.append(word)
    return found


def buzzword_score(found: list[str], text: str) -> int:
    """0-10 score: density-weighted, so a long README isn't unfairly punished."""
    words = max(len(text.split()), 1)
    density = len(found) / words * 100
    return max(0, min(10, round(len(found) * 1.2 + density * 2)))
