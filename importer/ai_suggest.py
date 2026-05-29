"""Suggest taxonomy categories for low-confidence import rows via OpenRouter."""
from __future__ import annotations

import json

import streamlit as st


def _get_client():
    api_key = st.secrets.get("anthropic", {}).get("api_key", "")
    if not api_key:
        return None
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")


def suggest_category(description: str, categories: list) -> str | None:
    """Return category_code for a single description. Most reliable — use as fallback."""
    client = _get_client()
    if not client:
        return None
    try:
        cat_list = "\n".join(f"- {c.code}: {c.name}" for c in categories)
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": (
                    "Construction budget expert. "
                    "Return ONLY the single best category code for this item. "
                    "No explanation. Just the code like 03.02\n\n"
                    f"CATEGORIES:\n{cat_list}\n\n"
                    f"ITEM: {description}"
                ),
            }],
        )
        code = response.choices[0].message.content.strip().strip('"').strip("'").split()[0]
        valid_codes = {c.code for c in categories}
        return code if code in valid_codes else None
    except Exception:
        return None


def suggest_categories(descriptions: list[str], categories: list) -> dict[str, str | None]:
    """Return {description: category_code} using numeric-indexed JSON for reliability."""
    client = _get_client()
    if not client:
        return {}

    cat_list = "\n".join(f"- {c.code}: {c.name}" for c in categories)
    numbered = "\n".join(f"{i + 1}. {d}" for i, d in enumerate(descriptions))
    n = len(descriptions)

    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": (
                    f"Construction budget expert. Assign all {n} items to a category.\n\n"
                    f"CATEGORIES:\n{cat_list}\n\n"
                    f"ITEMS:\n{numbered}\n\n"
                    f"Return ONLY a JSON object with numeric string keys 1-{n} and category code values. "
                    f"Include ALL {n} items. Use null if no category fits.\n"
                    f'Example: {{"1":"03.02","2":"01.01","3":null}}'
                ),
            }],
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        raw: dict = json.loads(text.strip())
        # Map numeric keys back to descriptions
        result = {}
        valid_codes = {c.code for c in categories}
        for i, desc in enumerate(descriptions):
            code = raw.get(str(i + 1))
            result[desc] = code if code and code in valid_codes else None
        return result
    except Exception:
        return {}
