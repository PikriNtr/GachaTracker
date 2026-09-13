from datetime import datetime
from typing import List, Dict, Any
from core.models import Pull


STANDARD_5STAR = {"Jianxin", "Calcharo", "Verina", "Lingyang", "Encore"}

BANNER_NAMES = {
    "1": "Featured Resonator",
    "2": "Featured Weapon",
    "3": "Standard Resonator",
    "4": "Standard Weapon",
    "5": "Beginner Convene",
    "6": "Beginners Choice",
    "7": "Giveback Convene",
}

PITY_CAPS = {
    "1": 80,
    "2": 80,
    "3": 80,
    "4": 80,
    "5": 50,
    "6": 80,
    "7": 80,
}


def _parse_time(t: str) -> datetime:
    try:
        return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def calculate_pity_summary(pulls: List[Pull]) -> Dict[str, Dict[str, Any]]:
    """Calculates current pity, total pulls, 5★ pull log, and 50/50 guarantee status for all banners.

    Mirrors the proven logic in the root kuro_api.py:
      - Groups pulls by pool type
      - Sorts each group chronologically (oldest → newest) before counting
      - Resets pity counter after every 5-star
      - Tracks 50/50 guarantee state for Featured Resonator (pool 1)
    """
    grouped: Dict[str, List[Pull]] = {}
    for p in pulls:
        pool = str(p.card_pool_type)
        grouped.setdefault(pool, []).append(p)

    summary: Dict[str, Dict[str, Any]] = {}

    for pool_id in ["1", "2", "3", "4", "5", "6", "7"]:
        b_pulls = grouped.get(pool_id, [])

        # Sort chronologically (oldest first) so pity counter runs forward in time.
        # This matches kuro_api.py's `list(reversed(banner_pulls))` pattern where
        # banner_pulls are stored newest-first.
        chronological = sorted(b_pulls, key=lambda p: _parse_time(p.time))

        pity_5 = 0
        pity_4 = 0
        p5_history = []
        is_guaranteed = False   # False = on 50/50, True = next 5★ is guaranteed
        won_5050_count = 0
        lost_5050_count = 0

        for item in chronological:
            pity_5 += 1
            pity_4 += 1
            quality = int(item.quality_level)
            name = item.resource_name

            if quality == 5:
                is_standard = name in STANDARD_5STAR

                if pool_id == "1":   # Featured Resonator only has 50/50 mechanic
                    if is_guaranteed:
                        result_str = "Guaranteed"
                        is_guaranteed = False
                    elif is_standard:
                        result_str = "Lost 50/50"
                        lost_5050_count += 1
                        is_guaranteed = True   # Next pull is guaranteed
                    else:
                        result_str = "Won 50/50"
                        won_5050_count += 1
                        is_guaranteed = False
                else:
                    result_str = "N/A"

                p5_history.append({
                    "name":        name,
                    "pity":        pity_5,
                    "time":        item.time,
                    "result":      result_str,
                    "is_standard": is_standard,
                })
                pity_5 = 0   # Reset 5-star pity counter

            elif quality == 4:
                pity_4 = 0   # Reset 4-star pity counter

        cap = PITY_CAPS.get(pool_id, 80)
        summary[pool_id] = {
            "name":          BANNER_NAMES.get(pool_id, f"Banner {pool_id}"),
            "current_pity":  pity_5,    # Pulls since last 5★ (or since beginning if none)
            "max_pity":      cap,
            "total_pulls":   len(b_pulls),
            "history_5star": list(reversed(p5_history)),  # Newest-first for display
            "is_guaranteed": is_guaranteed,
            "won_5050":      won_5050_count,
            "lost_5050":     lost_5050_count,
        }

    return summary
