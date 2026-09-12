from typing import Dict, Any

ASTRITE_PER_PULL = 160

def calculate_astrite_cost(current_pity: int, is_guaranteed: bool, max_pity: int = 80) -> Dict[str, Any]:
    """Calculates best, average, and worst case pull and Astrite cost scenarios."""
    pulls_to_next_5star = max(0, max_pity - current_pity)
    best_case_pulls = 1
    avg_pulls = max(1, min(pulls_to_next_5star, 40))

    if is_guaranteed:
        worst_case_pulls = pulls_to_next_5star
        worst_case_note = "100% Guaranteed on next 5-star (no 50/50 risk)"
    else:
        worst_case_pulls = pulls_to_next_5star + max_pity
        worst_case_note = f"If you lose 50/50 at pull {pulls_to_next_5star}, +{max_pity} pulls to hit 100% guarantee"

    return {
        "current_pity": current_pity,
        "is_guaranteed": is_guaranteed,
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
