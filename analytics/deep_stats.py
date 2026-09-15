"""Deep statistics (Phase 4): pity distribution stats, early 5-stars, char/weapon split.

All values are computed from the pity histories in calculate_pity_summary —
i.e., always recomputed from merged history, never accumulated.
"""
import statistics
from typing import Any, Dict, List

from analytics.pity import DEFAULT_GAME, GAME_BANNER_CONFIGS, calculate_pity_summary
from core.models import Pull

# A 5-star pulled at or below this pity counts as "early".
EARLY_PITY_THRESHOLD = 30

WEAPON_ITEM_TYPES = {"Weapon", "Light Cone", "Resonator Equipment"}


def _percentile(sorted_vals: List[float], pct: float) -> float:
    """Linear-interpolated percentile on a pre-sorted list."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = k - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def calculate_deep_statistics(pulls: List[Pull], game_id: str = DEFAULT_GAME) -> Dict[str, Any]:
    """Computes distribution stats over 5-star pity values for every pool.

    Per pool:
      pity_5star_list : every 5-star's pity (oldest -> newest)
      median / min / max / stddev / p25 / p75
      early_count     : 5-stars at pity <= EARLY_PITY_THRESHOLD
      char_5star / weapon_5star : counts split by item_type
    """
    cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
    summary = calculate_pity_summary(pulls, game_id)

    # item_type lookup for char/weapon split (keyed by pool+name+time like the DB unique key)
    result: Dict[str, Any] = {}

    for pool_id in cfg["pools"]:
        pool_pulls = [p for p in pulls if str(p.card_pool_type) == pool_id and p.quality_level == 5]
        weapon_5 = sum(1 for p in pool_pulls if p.item_type in WEAPON_ITEM_TYPES)
        char_5 = len(pool_pulls) - weapon_5

        history = summary.get(pool_id, {}).get("history_5star", [])
        pities = sorted(item["pity"] for item in history)

        stats: Dict[str, Any] = {
            "pity_5star_list": list(pities),
            "count": len(pities),
        }
        if pities:
            stats.update({
                "median": statistics.median(pities),
                "min": min(pities),
                "max": max(pities),
                "stddev": statistics.pstdev(pities) if len(pities) > 1 else 0.0,
                "p25": _percentile(pities, 25),
                "p75": _percentile(pities, 75),
                "early_count": sum(1 for v in pities if v <= EARLY_PITY_THRESHOLD),
            })
        else:
            stats.update({
                "median": 0, "min": 0, "max": 0, "stddev": 0.0,
                "p25": 0, "p75": 0, "early_count": 0,
            })
        stats["char_5star"] = char_5
        stats["weapon_5star"] = weapon_5
        result[pool_id] = stats

    return result
