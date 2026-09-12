from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class User:
    id: int
    discord_id: str
    created_at: str

@dataclass
class GameAccount:
    id: Optional[int]
    discord_id: str
    game_id: str
    player_id: str
    server: str = "global"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Banner:
    id: str
    game_id: str
    name: str
    type: str  # e.g., "character", "weapon", "standard", "beginner"
    pity_cap: int = 80
    has_5050: bool = True

@dataclass
class Pull:
    card_pool_type: str     # Banner category ID e.g. "1", "2"
    resource_id: str        # Item ID
    resource_name: str      # Item Name
    quality_level: int      # Rarity e.g. 5, 4, 3
    time: str               # ISO timestamp string
    player_id: str          # Account owner
    game_id: str = "wuthering_waves"
    count: str = "1"
    pity_at_pull: int = 0   # Calculated pity count when pulled
    is_5050_win: Optional[bool] = None  # True if won 50/50, False if lost, None if N/A or guaranteed
