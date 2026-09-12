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

def calculate_pity_summary(pulls: List[Pull]) -> Dict[str, Dict[str, Any]]:
    """Calculates current pity, total pulls, 5★ pull log, and 50/50 guarantee status for all banners."""
    grouped: Dict[str, List[Pull]] = {}
    for p in pulls:
        pool = str(p.card_pool_type)
        grouped.setdefault(pool, []).append(p)

    summary: Dict[str, Dict[str, Any]] = {}

    for pool_id in ["1", "2", "3", "4", "5", "6"]:
        b_pulls = grouped.get(pool_id, [])
        pity = 0
        p5_history = []
        is_guaranteed = False
        won_5050_count = 0
        lost_5050_count = 0

        for item in b_pulls:
            pity += 1
            if item.quality_level == 5:
                is_standard = item.resource_name in STANDARD_5STAR
                result_str = "Guaranteed"

                if pool_id == "1":
                    if is_standard:
                        lost_5050_count += 1
                        is_guaranteed = True
                        result_str = "Lost 50/50"
                    else:
                        won_5050_count += 1
                        is_guaranteed = False
                        result_str = "Won 50/50"

                p5_history.append({
                    "name": item.resource_name,
                    "pity": pity,
                    "time": item.time,
                    "result": result_str,
                    "is_standard": is_standard,
                })
                pity = 0

        cap = PITY_CAPS.get(pool_id, 80)
        summary[pool_id] = {
            "name": BANNER_NAMES.get(pool_id, f"Banner {pool_id}"),
            "current_pity": pity,
            "max_pity": cap,
            "total_pulls": len(b_pulls),
            "history_5star": p5_history,
            "is_guaranteed": is_guaranteed,
            "won_5050": won_5050_count,
            "lost_5050": lost_5050_count,
        }

    return summary
