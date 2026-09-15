from typing import Dict, Optional

from .game import GachaGame


class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, GachaGame] = {}

    def register(self, plugin: GachaGame) -> None:
        self._plugins[plugin.id] = plugin

    def get(self, game_id: str) -> Optional[GachaGame]:
        return self._plugins.get(game_id)

    def list_games(self) -> Dict[str, str]:
        return {gid: plugin.name for gid, plugin in self._plugins.items()}

registry = PluginRegistry()
