"""Suggest taxonomy categories for low-confidence import rows via OpenRouter."""
from __future__ import annotations

import json

import streamlit as st


def suggest_category(description: str, categories: list) -> str | None:
    """Return category_code for a single description. Returns None on failure."""
    api_key = st.secrets.get("anthropic", {}).get("api_key", "")
    if not api_key:
        st.error("API key de IA no configurada.")
        return None

    try:
        from openai import OpenAI

        cat_list = "\n".join(f"- {c.code}: {c.name}" for c in categories)

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": (
                    "You are a construction budget expert. "
                    "Given this line item description, return ONLY the single best matching category code from the list below. "
                    "No explanation, no JSON, just the code (e.g. 03.02).\n\n"
                    f"CATEGORIES:\n{cat_list}\n\n"
                    f"DESCRIPTION: {description}"
                ),
            }],
        )
        code = response.choices[0].message.content.strip().strip('"').strip("'")
        valid_codes = {c.code for c in categories}
        return code if code in valid_codes else None

    except Exception as e:
        st.warning(f"Error IA: {e}")
        return None


def suggest_categories(descriptions: list[str], categories: list) -> dict[str, str | None]:
    """Return {description: category_code} for a list of descriptions."""
    api_key = st.secrets.get("anthropic", {}).get("api_key", "")
    if not api_key:
        return {}

    try:
        from openai import OpenAI

        cat_list = "\n".join(f"- {c.code}: {c.name}" for c in categories)
        descriptions_text = "\n".join(f"{i + 1}. {d}" for i, d in enumerate(descriptions))

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": (
                    "You are a construction budget expert. "
                    "Assign each line item to the best matching category code.\n\n"
                    f"CATEGORIES:\n{cat_list}\n\n"
                    f"LINE ITEMS:\n{descriptions_text}\n\n"
                    "Respond with ONLY a JSON object: {\"description\": \"code\"}. "
                    "Use null if no category fits."
                ),
            }],
        )
        text = response.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    except Exception:
        return {}
