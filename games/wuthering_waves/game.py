from typing import Any, Dict, List, Tuple

from core.game import GachaGame
from core.models import Banner, Pull
from games.wuthering_waves.api import fetch_all_convene_history
from games.wuthering_waves.banners import WUWA_BANNERS
from games.wuthering_waves.parser import parse_wuwa_records


class WutheringWavesPlugin(GachaGame):
    @property
    def id(self) -> str:
        return "wuthering_waves"

    @property
    def name(self) -> str:
        return "Wuthering Waves"

    async def fetch_and_parse(self, url: str) -> Tuple[str, List[Pull]]:
        """Fetches history via API and returns (player_id, list of Pulls).

        fetch_all_convene_history now returns (player_id, pulls_by_pool) where
        pulls_by_pool is a dict mapping pool_type_str → list of raw API dicts.
        """
        player_id, pulls_by_pool = await fetch_all_convene_history(url)
        pulls = parse_wuwa_records(pulls_by_pool, player_id)
        return player_id, pulls

    def parse_history(self, raw_data: Dict[str, Any]) -> List[Pull]:
        player_id = str(raw_data.get("player_id", "unknown"))
        records = raw_data.get("records", [])
        # Wrap as pool "1" for legacy compat
        return parse_wuwa_records({"1": records}, player_id)

    def get_banners(self) -> Dict[str, Banner]:
        return WUWA_BANNERS
