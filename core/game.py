from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from .models import Pull, Banner

class GachaGame(ABC):
    """Abstract Base Class for all game plugins in GachaTracker."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique lower-case identifier for the game e.g. 'wuthering_waves'."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable display name for the game e.g. 'Wuthering Waves'."""
        pass

    @abstractmethod
    def parse_history(self, raw_data: Dict[str, Any]) -> List[Pull]:
        """Convert raw API payload into a list of normalized Pull objects."""
        pass

    @abstractmethod
    def get_banners(self) -> Dict[str, Banner]:
        """Return banner definitions mapping card_pool_type to Banner objects."""
        pass
