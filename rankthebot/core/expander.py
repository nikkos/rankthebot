from __future__ import annotations

from itertools import product

PERSONAS = [
    "small business owner",
    "enterprise buyer",
    "developer",
    "agency",
]

MODIFIERS = [
    "budget",
    "enterprise",
    "beginner",
    "advanced",
]

PHRASING_TEMPLATES = [
    "best {intent} for {persona}",
    "recommend a {intent} for {persona}",
    "what {intent} should I use as a {persona}",
    "{intent} comparison for {persona}",
]


def expand_intent(intent: str) -> list[str]:
    intent = intent.strip()
    variants: list[str] = []
    for template, persona, modifier in product(PHRASING_TEMPLATES, PERSONAS, MODIFIERS):
        q = template.format(intent=intent, persona=persona)
        variants.append(f"{modifier} {q}")
    # Keep order stable while deduplicating.
    return list(dict.fromkeys(variants))
