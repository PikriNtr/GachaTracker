from typing import List, Dict, Any
from core.models import Pull


def parse_wuwa_records(pulls_by_pool: Dict[str, List[Dict[str, Any]]], player_id: str) -> List[Pull]:
    """Converts raw Kuro API pull dicts (keyed by pool number) into normalized Pull objects.

    IMPORTANT: The API returns `cardPoolType` as a descriptive STRING name
    (e.g. "Resonators Accurate Modulation"), NOT the integer pool number.
    We must use the dict KEY (the integer we passed to the API) as the canonical
    card_pool_type, and completely ignore the API's `cardPoolType` string field.
    """
    pulls: List[Pull] = []
    for pool_type, records in pulls_by_pool.items():
        for item in records:
            # Always use pool_type (the number key) — never item['cardPoolType'] (a name string)
            resource_id   = str(item.get("resourceId", ""))
            resource_name = str(item.get("name") or item.get("resourceName") or "Unknown")
            quality_level = int(item.get("qualityLevel", 3))
            time_str      = str(item.get("time", ""))
            count_str     = str(item.get("count", "1"))

            pulls.append(Pull(
                card_pool_type=pool_type,   # numeric pool id, e.g. "1", "2", etc.
                resource_id=resource_id,
                resource_name=resource_name,
                quality_level=quality_level,
                time=time_str,
                player_id=player_id,
                game_id="wuthering_waves",
                count=count_str,
                item_type=str(item.get("resourceType", "") or ""),
            ))
    return pulls
