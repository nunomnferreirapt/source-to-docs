"""Tokenization and keyword extraction shared by index, gaps and drift."""

from __future__ import annotations

import re
from collections import Counter

STOPWORDS: frozenset[str] = frozenset(
    """
    a about above after again against all also am an and any are as at be because
    been before being below between both but by can could did do does doing done
    down during each few for from further get got had has have having he her here
    hers herself him himself his how i if in into is it its itself just let like
    me more most my myself no nor not now of off on once only or other our ours
    ourselves out over own same she should so some still such than that the their
    theirs them themselves then there these they this those through to too under
    until up us very was we were what when where which while who whom why will
    with would you your yours yourself yourselves
    yeah yes okay ok right thanks thank hi hello please sure well really think know
    going want need one two three new also something anything thing things way
    make makes made see look looking said say says take back last asked getting worked
    told went put lot much many every someone another else around already
    """.split()
)

_TOKEN = re.compile(r"[a-z][a-z0-9\-]{2,}")
_PLACEHOLDER = re.compile(r"^person-\d+$")


def normalize(token: str) -> str:
    """Light, deterministic normalization: lowercase and strip a plural s."""
    token = token.lower().strip("-")
    if len(token) > 4 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        token = token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    """Return content tokens in order, stopwords removed."""
    tokens = []
    for raw in _TOKEN.findall(text.lower()):
        token = normalize(raw)
        if len(token) < 3 or token in STOPWORDS or _PLACEHOLDER.match(token):
            continue
        tokens.append(token)
    return tokens


def keywords(text: str, limit: int | None = None) -> list[str]:
    """Unique tokens ordered by frequency, then alphabetically. Deterministic."""
    counts = Counter(tokenize(text))
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    result = [token for token, _ in ordered]
    return result[:limit] if limit else result


def overlap(block_keywords: list[str], section_keywords: list[str]) -> float:
    """Fraction of block keywords that appear in the section. 0.0 to 1.0."""
    if not block_keywords:
        return 0.0
    section = set(section_keywords)
    hits = sum(1 for keyword in block_keywords if keyword in section)
    return round(hits / len(block_keywords), 3)
