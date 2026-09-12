from typing import List, Dict, Any, Tuple
from core.game import GachaGame
from core.models import Pull, Banner
from games.wuthering_waves.banners import WUWA_BANNERS
from games.wuthering_waves.parser import parse_wuwa_records
from games.wuthering_waves.api import fetch_all_convene_history


class WutheringWavesPlugin(GachaGame):
    @property
    def id(self) -> str:
        return "wuthering_waves"

    @property
    def name(self) -> str:
        return "Wuthering Waves"

    async def fetch_and_parse(self, url: str) -> Tuple[str, List[Pull]]:
        """Fetches history via API and returns (player_id, list of Pulls)."""
        player_id, raw_records = await fetch_all_convene_history(url)
        pulls = parse_wuwa_records(raw_records, player_id)
        return player_id, pulls

    def parse_history(self, raw_data: Dict[str, Any]) -> List[Pull]:
        player_id = str(raw_data.get("player_id", "unknown"))
        records = raw_data.get("records", [])
        return parse_wuwa_records(records, player_id)

    def get_banners(self) -> Dict[str, Banner]:
        return WUWA_BANNERS
