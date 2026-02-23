from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rankthebot.core.llms.openai import OpenAIClient


def expand_intent(intent: str, client: "OpenAIClient", count: int = 40) -> list[str]:
    """Use GPT-4o-mini to generate realistic, language-aware query variants for an intent."""
    prompt = (
        f"Generate {count} realistic search queries that people would type into an AI assistant "
        f"like ChatGPT when searching for: \"{intent}\".\n\n"
        "Requirements:\n"
        "- Vary the phrasing naturally (questions, comparisons, best-of lists, recommendations, etc.)\n"
        "- Include different types of users appropriate for this specific topic\n"
        "- Write ALL queries in the same language as the intent — do not translate\n"
        "- Each query should feel like something a real person would actually type\n"
        "- No duplicates\n"
        "- Return JSON only: a flat array of strings, no explanation or extra text\n\n"
        'Format: ["query one", "query two", ...]'
    )

    raw = client.complete(prompt, temperature=0.8, model="gpt-4o-mini")

    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []

    try:
        queries = json.loads(match.group())
    except json.JSONDecodeError:
        return []

    return [q.strip() for q in queries if isinstance(q, str) and q.strip()]
