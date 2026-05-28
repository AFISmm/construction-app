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
    lang = st.session_state.get("lang", "es")
    value = _load(lang).get(key, key)
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return value


def language_toggle() -> None:
    current = st.session_state.get("lang", "es")
    options = ["es", "en"]
    idx = options.index(current) if current in options else 0
    selected = st.radio(
        t("nav.language_toggle"),
        options,
        index=idx,
        horizontal=True,
        key="_lang_radio",
        label_visibility="collapsed",
    )
    if selected not in ALLOWED_LANGS:
        selected = "es"
    if selected != st.session_state.get("lang"):
        st.session_state["lang"] = selected
        _cache.clear()
        st.rerun()
