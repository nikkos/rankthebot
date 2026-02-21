from __future__ import annotations


def visibility_score(mention_rate_pct: float, avg_position: float | None) -> float:
    if mention_rate_pct <= 0:
        return 0.0
    if avg_position is None:
        return min(100.0, mention_rate_pct)

    # Position 1 keeps full weight; lower ranks decay.
    position_factor = max(0.25, 1.0 - ((avg_position - 1.0) * 0.18))
    return round(min(100.0, mention_rate_pct * position_factor), 1)
