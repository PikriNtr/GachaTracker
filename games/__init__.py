# Games package initialization

from games.wuthering_waves import WutheringWavesPlugin
from games.genshin_impact import GenshinImpactPlugin
from games.honkai_star_rail import HonkaiStarRailPlugin


def register_all_plugins(registry) -> None:
    """Registers every built-in game plugin into the given PluginRegistry."""
    registry.register(WutheringWavesPlugin())
    registry.register(GenshinImpactPlugin())
    registry.register(HonkaiStarRailPlugin())

