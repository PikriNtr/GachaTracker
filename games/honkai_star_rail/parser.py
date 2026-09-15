from typing import Any, Dict, List

from core.models import Pull


def parse_hsr_records(records: List[Dict[str, Any]], player_id: str) -> List[Pull]:
    """Converts raw HoYoverse getGachaLog item dicts into normalized Pull objects.

    HSR records carry the same shape as Genshin's:
        {"uid": "...", "gacha_type": "11", "item_id": "...", "count": "1",
         "time": "2024-01-01 12:34:56", "name": "Seele", "lang": "en-us",
         "item_type": "Character", "rank_type": "5", "id": "17xxxxxxxxx"}

    - `gacha_type` is already a numeric string and is used as card_pool_type.
    - Dedup relies on the repository's (pool, name, time) unique constraint,
      same as the other plugins.
    """
    pulls: List[Pull] = []
    for item in records:
        pulls.append(Pull(
            card_pool_type=str(item.get("gacha_type", "")),
            resource_id=str(item.get("item_id", "") or item.get("id", "")),
            resource_name=str(item.get("name") or "Unknown"),
            quality_level=int(item.get("rank_type", 3)),
            time=str(item.get("time", "")),
            player_id=player_id,
            game_id="honkai_star_rail",
            count=str(item.get("count", "1")),
            item_type=str(item.get("item_type", "") or ""),
            api_id=str(item.get("id", "") or ""),
        ))
    return pulls
