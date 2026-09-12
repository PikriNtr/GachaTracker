from typing import List, Dict, Any
from core.models import Pull


def parse_wuwa_records(raw_records: List[Dict[str, Any]], player_id: str) -> List[Pull]:
    """Converts raw Kuro API pull dictionaries into a list of normalized Pull objects."""
    pulls = []
    for item in raw_records:
        card_pool_type = str(item.get("cardPoolType", "1"))
        resource_id = str(item.get("resourceId", ""))
        resource_name = str(item.get("name") or item.get("resourceName") or "Unknown")
        quality_level = int(item.get("qualityLevel", 3))
        time_str = str(item.get("time", ""))
        count_str = str(item.get("count", "1"))

        pulls.append(Pull(
            card_pool_type=card_pool_type,
            resource_id=resource_id,
            resource_name=resource_name,
            quality_level=quality_level,
            time=time_str,
            player_id=player_id,
            game_id="wuthering_waves",
            count=count_str
        ))
    return pulls
