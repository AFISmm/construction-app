"""Internationalization helpers: t(key) lookup and sidebar language toggle."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

_TRANSLATIONS_DIR = Path(__file__).parent / "translations"
_cache: dict[str, dict[str, str]] = {}
ALLOWED_LANGS: frozenset[str] = frozenset({"es", "en"})


def _load(lang: str) -> dict[str, str]:
    if lang not in ALLOWED_LANGS:
        lang = "es"
    if lang not in _cache:
        path = _TRANSLATIONS_DIR / f"{lang}.json"
        if not path.exists():
            _cache[lang] = {}
        else:
            with open(path, encoding="utf-8") as f:
                _cache[lang] = json.load(f)
    return _cache[lang]


def t(key: str, **kwargs) -> str:
    lang = st.session_state.get("lang", "en")
    value = _load(lang).get(key, key)
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return value


def fmt_money(value, currency: str = "USD") -> str:
    """Format monetary value as US$1,234.56 regardless of currency setting."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "US$0.00"
    import math
    if math.isnan(v) or math.isinf(v):
        return "US$0.00"
    if v < 0:
        return f"-US${abs(v):,.2f}"
    return f"US${v:,.2f}"


def set_language(lang: str) -> None:
    """Set active language and clear translation cache."""
    if lang in ALLOWED_LANGS:
        st.session_state["lang"] = lang
        _cache.clear()


def language_toggle() -> None:
    current = st.session_state.get("lang", "en")
    labels = ["🇪🇸 Español", "🇺🇸 English"]
    codes = ["es", "en"]
    idx = codes.index(current) if current in codes else 0
    selected_label = st.radio(
        t("nav.language_toggle"),
        labels,
        index=idx,
        horizontal=True,
        key="_lang_radio",
        label_visibility="collapsed",
    )
    selected = codes[labels.index(selected_label)]
    if selected != st.session_state.get("lang"):
        st.session_state["lang"] = selected
        _cache.clear()
        st.rerun()
