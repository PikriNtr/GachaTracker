from typing import Any, Dict, List, Tuple

from core.game import GachaGame
from core.models import Banner, Pull
from games.honkai_star_rail.banners import HSR_BANNERS
from games.honkai_star_rail.parser import parse_hsr_records
from games.hoyoverse_api import fetch_all_history


class HonkaiStarRailPlugin(GachaGame):
    @property
    def id(self) -> str:
        return "honkai_star_rail"

    @property
    def name(self) -> str:
        return "Honkai: Star Rail"

    async def fetch_and_parse(self, url: str) -> Tuple[str, List[Pull]]:
        """Fetches history via API and returns (player_id/uid, list of Pulls)."""
        uid, records_by_type = await fetch_all_history(url, "honkai_star_rail")
        pulls: List[Pull] = []
        for _gacha_type, records in records_by_type.items():
            pulls.extend(parse_hsr_records(records, uid))
        return uid, pulls

    def parse_history(self, raw_data: Dict[str, Any]) -> List[Pull]:
        player_id = str(raw_data.get("player_id", "unknown"))
        records = raw_data.get("records", [])
        return parse_hsr_records(records, player_id)

    def get_banners(self) -> Dict[str, Banner]:
        return HSR_BANNERS
