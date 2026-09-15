from typing import Any, Dict, List, Tuple

from core.game import GachaGame
from core.models import Banner, Pull
from games.genshin_impact.banners import GENSHIN_BANNERS
from games.genshin_impact.parser import parse_genshin_records
from games.hoyoverse_api import fetch_all_history


class GenshinImpactPlugin(GachaGame):
    @property
    def id(self) -> str:
        return "genshin_impact"

    @property
    def name(self) -> str:
        return "Genshin Impact"

    async def fetch_and_parse(self, url: str) -> Tuple[str, List[Pull]]:
        """Fetches history via API and returns (player_id/uid, list of Pulls)."""
        uid, records_by_type = await fetch_all_history(url, "genshin_impact")
        pulls: List[Pull] = []
        for _gacha_type, records in records_by_type.items():
            pulls.extend(parse_genshin_records(records, uid))
        return uid, pulls

    def parse_history(self, raw_data: Dict[str, Any]) -> List[Pull]:
        player_id = str(raw_data.get("player_id", "unknown"))
        records = raw_data.get("records", [])
        return parse_genshin_records(records, player_id)

    def get_banners(self) -> Dict[str, Banner]:
        return GENSHIN_BANNERS
