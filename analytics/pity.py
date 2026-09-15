from datetime import datetime
from typing import Any, Dict, List

from core.models import Pull

STANDARD_5STAR = {"Jianxin", "Calcharo", "Verina", "Lingyang", "Encore"}

# Per-game banner configuration. Games are isolated from the core; the pity
# engine only reads from these dicts, never from game-specific modules.
GAME_BANNER_CONFIGS = {
    "wuthering_waves": {
        "pools": ["1", "2", "3", "4", "5", "6", "7"],
        "names": {
            "1": "Featured Resonator",
            "2": "Featured Weapon",
            "3": "Standard Resonator",
            "4": "Standard Weapon",
            "5": "Beginner Convene",
            "6": "Beginners Choice",
            "7": "Giveback Convene",
        },
        "pity_caps": {"1": 80, "2": 80, "3": 80, "4": 80, "5": 50, "6": 80, "7": 80},
        "5050_pools": {"1"},
        "standard_5star": STANDARD_5STAR,
        "featured_pool": "1",
        "weapon_pool": "2",
        "soft_pity": 61,
        "rateup_chance": 0.5,   # featured 5★ win chance in the event rate-up
    },
    "genshin_impact": {
        # NOTE: pool 500 (Chronicled Wish) features standard characters with a
        # rate-up but NO 50/50 guarantee carryover between wishes — it is
        # intentionally NOT in 5050_pools (treated like a standard banner).
        "pools": ["301", "400", "302", "500", "200", "100"],
        "names": {
            "301": "Character Event Wish",
            "400": "Character Event Wish-2",
            "302": "Weapon Event Wish",
            "500": "Chronicled Wish",
            "200": "Standard Wish",
            "100": "Novice Wishes",
        },
        "pity_caps": {"301": 90, "400": 90, "302": 80, "500": 90, "200": 90, "100": 20},
        "5050_pools": {"301", "400"},
        "standard_5star": {
            "Diluc", "Jean", "Qiqi", "Keqing", "Mona", "Tighnari",
            "Dehya", "Mizuki",
        },
        "featured_pool": "301",
        "weapon_pool": "302",
        "soft_pity": 74,
        "rateup_chance": 0.5,   # featured 5★ win chance in the event rate-up
    },
    "honkai_star_rail": {
        "pools": ["11", "12", "1", "2"],
        "names": {
            "11": "Standard Warp",
            "12": "Departure Warp",
            "1": "Character Event Warp",
            "2": "Light Cone Event Warp",
        },
        "pity_caps": {"11": 90, "12": 50, "1": 90, "2": 80},
        # Pool 2 (Light Cone Event) is a 75/25, not a 50/50 — not modeled as 50/50.
        "5050_pools": {"1"},
        "standard_5star": {
            "Bronya", "Gepard", "Himeko", "Welt", "Bailu", "Clara", "Yanqing",
        },
        "featured_pool": "1",
        "weapon_pool": "2",
        "soft_pity": 74,
        # Character Event is 50/50; the Light Cone Event rate-up is 75/25.
        "rateup_chance": 0.5,
    },
}

DEFAULT_GAME = "wuthering_waves"


def _game_config(game_id: str) -> Dict[str, Any]:
    return GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])


BANNER_NAMES = _game_config(DEFAULT_GAME)["names"]

PITY_CAPS = _game_config(DEFAULT_GAME)["pity_caps"]


def get_game_banner_names(game_id: str) -> Dict[str, str]:
    """Returns the banner-name mapping for a game (falls back to Wuthering Waves)."""
    return _game_config(game_id)["names"]


def _parse_time(t: str) -> datetime:
    try:
        return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def calculate_pity_summary(pulls: List[Pull], game_id: str = DEFAULT_GAME) -> Dict[str, Dict[str, Any]]:
    """Calculates current pity, total pulls, 5★ pull log, and 50/50 guarantee status for all banners.

    Mirrors the proven logic in the root kuro_api.py:
      - Groups pulls by pool type
      - Sorts each group chronologically (oldest → newest) before counting
      - Resets pity counter after every 5-star
      - Tracks 50/50 guarantee state for featured character pools

    Per-game config (pools, caps, standard 5★ set, 50/50 pools) comes from
    GAME_BANNER_CONFIGS; unknown game_ids fall back to Wuthering Waves.
    """
    cfg = _game_config(game_id)
    pools = cfg["pools"]
    standard_5star = cfg["standard_5star"]
    has_5050 = cfg["5050_pools"]

    grouped: Dict[str, List[Pull]] = {}
    for p in pulls:
        pool = str(p.card_pool_type)
        grouped.setdefault(pool, []).append(p)

    summary: Dict[str, Dict[str, Any]] = {}

    for pool_id in pools:
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
                # Off-banner weapons/light cones don't participate in the
                # character 50/50: they neither win nor lose it.
                # ("Resonator Equipment" is WuWa's weapon type; "" = legacy rows.)
                is_char = item.item_type in ("", "Character", "Resonator") or not item.item_type
                is_weapon_type = item.item_type in ("Weapon", "Light Cone", "Resonator Equipment")
                is_standard = name in standard_5star or is_weapon_type

                if pool_id in has_5050 and is_char:   # Featured character pools have 50/50 mechanic
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

        cap = cfg["pity_caps"].get(pool_id, 90)
        summary[pool_id] = {
            "name":          cfg["names"].get(pool_id, f"Banner {pool_id}"),
            "current_pity":  pity_5,    # Pulls since last 5★ (or since beginning if none)
            "max_pity":      cap,
            "total_pulls":   len(b_pulls),
            "history_5star": list(reversed(p5_history)),  # Newest-first for display
            "is_guaranteed": is_guaranteed,
            "won_5050":      won_5050_count,
            "lost_5050":     lost_5050_count,
        }

    return summary
