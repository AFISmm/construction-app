"""Suggest taxonomy categories for low-confidence import rows via OpenRouter."""
from __future__ import annotations

import json

import streamlit as st


def suggest_categories(descriptions: list[str], categories: list) -> dict[str, str | None]:
    """Return {description: category_code}. Returns {} if API key missing."""
    api_key = st.secrets.get("anthropic", {}).get("api_key", "")
    if not api_key:
        return {}

    from openai import OpenAI

    cat_list = "\n".join(f"- {c.code}: {c.name}" for c in categories)
    descriptions_text = "\n".join(f"{i + 1}. {d}" for i, d in enumerate(descriptions))

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    response = client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                "You are a construction budget expert. "
                "Assign each line item description to the best matching category.\n\n"
                f"CATEGORIES:\n{cat_list}\n\n"
                f"LINE ITEMS:\n{descriptions_text}\n\n"
                "Respond with ONLY a JSON object mapping each description "
                "(exactly as written) to the most appropriate category code. "
                'Example: {"Concrete foundation": "03.02", "Legal closing fees": "01.03"}\n'
                "If no category fits, use null."
            ),
        }],
    )

    try:
        text = response.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {}
