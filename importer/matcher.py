"""Taxonomy fuzzy matching using rapidfuzz."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from rapidfuzz import fuzz

LOW_CONFIDENCE_THRESHOLD = 0.70
MIN_MATCH_THRESHOLD = 0.50


@dataclass
class MatchResult:
    code: Optional[str]
    name: Optional[str]
    confidence: float

    @property
    def needs_review(self) -> bool:
        return self.confidence < LOW_CONFIDENCE_THRESHOLD

    @property
    def is_unmatched(self) -> bool:
        return self.code is None


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = "".join(c if c.isalnum() or c.isspace() else " " for c in text)
    return " ".join(text.split())


@lru_cache(maxsize=1)
def _load_corpus() -> list[dict]:
    """Load taxonomy corpus from db (cached for session lifetime)."""
    from app.db import Category, get_session
    with get_session() as session:
        cats = session.query(Category).all()
        return [
            {
                "code": c.code,
                "name": c.name,
                "description": c.description or "",
                "norm_name": _normalize(c.name),
                "norm_desc": _normalize(c.description or ""),
            }
            for c in cats
        ]


def match(description: str) -> MatchResult:
    norm_desc = _normalize(description)
    corpus = _load_corpus()

    best_code: Optional[str] = None
    best_name: Optional[str] = None
    best_score = 0.0

    for entry in corpus:
        score_name = fuzz.token_sort_ratio(norm_desc, entry["norm_name"]) / 100
        score_desc = fuzz.token_sort_ratio(norm_desc, entry["norm_desc"]) / 100 if entry["norm_desc"] else 0
        score = max(score_name, score_desc * 0.9)

        if score > best_score:
            best_score = score
            best_code = entry["code"]
            best_name = entry["name"]

    if best_score < MIN_MATCH_THRESHOLD:
        return MatchResult(code=None, name=None, confidence=0.0)

    return MatchResult(code=best_code, name=best_name, confidence=round(best_score, 3))


def match_batch(descriptions: list[str]) -> list[MatchResult]:
    return [match(d) for d in descriptions]


def clear_corpus_cache() -> None:
    _load_corpus.cache_clear()
