from typing import Dict, Any
from analytics.simulation import PROBABILITY_MODELS, DEFAULT_GAME

ASTRITE_PER_PULL = 160

def _expected_pulls_per_5star(model: Dict[str, Any]) -> int:
    """Analytic mean pulls per 5★ under a base/soft-pity/hard-cap model."""
    base = model["base"]
    soft_start = model["soft_start"]
    soft_step = model["soft_step"]
    cap = model["cap"]

    expected = 0.0
    survival = 1.0  # probability of NOT having hit a 5★ yet at pull i
    for i in range(1, cap + 1):
        p = base if i < soft_start else min(1.0, base + (i - soft_start + 1) * soft_step)
        expected += survival * i * p
        survival -= survival * p
        if survival <= 1e-9:
            break
    if survival > 0:
        expected += survival * cap
    return max(1, round(expected))


def calculate_astrite_cost(current_pity: int, is_guaranteed: bool, max_pity: int = 80,
                           game_id: str = DEFAULT_GAME) -> Dict[str, Any]:
    """Calculates best, average, and worst case pull and currency cost scenarios.

    The average case is the model's expected pulls per 5★ minus current pity
    (i.e., expected additional pulls), floored at 1.
    """
    model = PROBABILITY_MODELS.get(game_id, PROBABILITY_MODELS[DEFAULT_GAME])
    exp_pulls = _expected_pulls_per_5star(model)

    pulls_to_next_5star = max(0, max_pity - current_pity)
    best_case_pulls = 1
    avg_pulls = max(1, min(exp_pulls - current_pity, pulls_to_next_5star))

    if is_guaranteed:
        worst_case_pulls = max(1, pulls_to_next_5star)
        worst_case_note = "100% Guaranteed on next 5-star (no 50/50 risk)"
    else:
        worst_case_pulls = pulls_to_next_5star + max_pity
        worst_case_note = f"If you lose 50/50 at pull {pulls_to_next_5star}, +{max_pity} pulls to hit 100% guarantee"

    return {
        "current_pity": current_pity,
        "is_guaranteed": is_guaranteed,
        "max_pity": max_pity,
        "pulls_to_next_5star": pulls_to_next_5star,
        "best_case": {
            "pulls": best_case_pulls,
            "astrites": best_case_pulls * ASTRITE_PER_PULL
        },
        "avg_case": {
            "pulls": avg_pulls,
            "astrites": avg_pulls * ASTRITE_PER_PULL
        },
        "worst_case": {
            "pulls": worst_case_pulls,
            "astrites": worst_case_pulls * ASTRITE_PER_PULL,
            "note": worst_case_note
        }
    }
