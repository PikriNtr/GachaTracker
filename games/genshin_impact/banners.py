from core.models import Banner

GENSHIN_BANNERS = {
    "301": Banner(id="301", game_id="genshin_impact", name="Character Event Wish", type="character", pity_cap=90, has_5050=True),
    "400": Banner(id="400", game_id="genshin_impact", name="Character Event Wish-2", type="character", pity_cap=90, has_5050=True),
    "302": Banner(id="302", game_id="genshin_impact", name="Weapon Event Wish", type="weapon", pity_cap=80, has_5050=False),
    "200": Banner(id="200", game_id="genshin_impact", name="Standard Wish", type="standard", pity_cap=90, has_5050=False),
    "100": Banner(id="100", game_id="genshin_impact", name="Novice Wishes", type="beginner", pity_cap=20, has_5050=False),
}
