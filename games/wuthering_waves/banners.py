from core.models import Banner

WUWA_BANNERS = {
    "1": Banner(id="1", game_id="wuthering_waves", name="Featured Resonator", type="character", pity_cap=80, has_5050=True),
    "2": Banner(id="2", game_id="wuthering_waves", name="Featured Weapon", type="weapon", pity_cap=80, has_5050=False),
    "3": Banner(id="3", game_id="wuthering_waves", name="Standard Resonator", type="character", pity_cap=80, has_5050=False),
    "4": Banner(id="4", game_id="wuthering_waves", name="Standard Weapon", type="weapon", pity_cap=80, has_5050=False),
    "5": Banner(id="5", game_id="wuthering_waves", name="Beginner Convene", type="beginner", pity_cap=50, has_5050=False),
    "6": Banner(id="6", game_id="wuthering_waves", name="Beginners Choice", type="beginner", pity_cap=80, has_5050=False),
    "7": Banner(id="7", game_id="wuthering_waves", name="Giveback Convene", type="beginner", pity_cap=80, has_5050=False),
}
