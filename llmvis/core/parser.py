from __future__ import annotations

import json
import re
from typing import Any, Optional

from llmvis.core.llms.openai import OpenAIClient

_ALLOWED_SENTIMENTS = {"positive", "neutral", "negative", "qualified"}


def _extract_json_block(text: str) -> Optional[str]:
    fence_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, flags=re.DOTALL)
    if fence_match:
        return fence_match.group(1)
    bracket_match = re.search(r"(\[\s*\{.*\}\s*\])", text, flags=re.DOTALL)
    if bracket_match:
        return bracket_match.group(1)
    return None


def _clean_mentions(data: Any) -> list[dict]:
    if not isinstance(data, list):
        return []
    clean: list[dict] = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            continue
        brand = str(item.get("brand", "")).strip()
        context = str(item.get("context", "")).strip()
        sentiment = str(item.get("sentiment", "neutral")).strip().lower()
        position = item.get("position", i)
        if not brand:
            continue
        if sentiment not in _ALLOWED_SENTIMENTS:
            sentiment = "neutral"
        try:
            position = int(position)
        except Exception:
            position = i
        clean.append(
            {
                "brand": brand,
                "position": position,
                "sentiment": sentiment,
                "context": context or brand,
            }
        )
    return clean


def parse_mentions(raw_response: str, parser_client: Optional[OpenAIClient] = None) -> list[dict]:
    if parser_client is None:
        return []

    prompt = (
        "Extract all mentioned brands/products from the response below as JSON array. "
        "Each item must contain: brand, position (first mention order, starting at 1), "
        "sentiment (positive|neutral|negative|qualified), context (short quoted phrase). "
        "Return JSON only.\n\n"
        f"Response:\n{raw_response}"
    )

    try:
        out = parser_client.complete(prompt, temperature=0.0, model="gpt-4o-mini")
    except Exception:
        return []

    block = _extract_json_block(out)
    if not block:
        return []
    try:
        data = json.loads(block)
    except json.JSONDecodeError:
        return []
    return _clean_mentions(data)
