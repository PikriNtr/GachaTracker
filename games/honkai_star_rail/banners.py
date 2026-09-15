from core.models import Banner

HSR_BANNERS = {
    "1": Banner(id="1", game_id="honkai_star_rail", name="Character Event Warp", type="character", pity_cap=90, has_5050=True),
    "2": Banner(id="2", game_id="honkai_star_rail", name="Light Cone Event Warp", type="weapon", pity_cap=80, has_5050=True),
    "11": Banner(id="11", game_id="honkai_star_rail", name="Standard Warp", type="standard", pity_cap=90, has_5050=False),
    "12": Banner(id="12", game_id="honkai_star_rail", name="Departure Warp", type="beginner", pity_cap=50, has_5050=False),
}
