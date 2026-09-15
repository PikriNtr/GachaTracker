"""Deep statistics tests: distribution stats, early 5-stars, char/weapon split."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.deep_stats import EARLY_PITY_THRESHOLD, calculate_deep_statistics
from core.models import Pull


def pull(game_id, pool, name, q, t, item_type=""):
    return Pull(pool, "res", name, q, t, "u", game_id=game_id, item_type=item_type)


def filler(game_id, pool, i, t):
    return Pull(pool, f"fid{i}", f"Filler {i}", 3, t, "u", game_id=game_id)


def five(game_id, pool, name, t, item_type="Character"):
    return pull(game_id, pool, name, 5, t, item_type=item_type)


def test_distribution_values_from_chronology():
    """Fillers create real pity gaps: 5-stars land at pity 10, 41, 9."""
    pulls = []

    def add_filler(i, t):
        pulls.append(filler("genshin_impact", "301", i, t))

    for i in range(9):    # pity 1-9
        add_filler(i + 1, f"2024-01-{i + 1:02d} 10:00:00")
    pulls.append(five("genshin_impact", "301", "A", "2024-01-10 10:00:00"))          # pity 10
    for i in range(40):   # pity 1-40
        day = 11 + i
        month = 1 + (day - 1) // 28
        add_filler(100 + i, f"2024-{month:02d}-{(day - 1) % 28 + 1:02d} 10:00:00")
    pulls.append(five("genshin_impact", "301", "B", "2024-03-01 10:00:00"))          # pity 41
    for i in range(8):    # pity 1-8
        add_filler(200 + i, f"2024-03-{i + 2:02d} 10:00:00")
    pulls.append(five("genshin_impact", "301", "C", "2024-03-11 10:00:00"))          # pity 9

    d = calculate_deep_statistics(pulls, "genshin_impact")["301"]
    assert d["count"] == 3
    assert d["min"] == 9 and d["max"] == 41
    assert d["median"] == 10
    assert d["stddev"] > 0
    assert d["p25"] <= d["median"] <= d["p75"]
    assert d["pity_5star_list"] == [9, 10, 41]  # sorted


def test_early_5star_counting():
    pulls = [five("genshin_impact", "301", "A", "2024-01-01 10:00:00")]      # pity 1 (early)
    for i in range(30):  # pity 2..31
        pulls.append(filler("genshin_impact", "301", i, f"2024-01-{i + 2:02d} 10:00:00"))
    pulls.append(five("genshin_impact", "301", "B", "2024-02-01 10:00:00"))  # pity 31 (not early)
    for i in range(28):  # pity 2..29
        pulls.append(filler("genshin_impact", "301", 100 + i, f"2024-02-{i + 2:02d} 10:00:00"))
    pulls.append(five("genshin_impact", "301", "C", "2024-03-01 10:00:00"))  # pity 29 (early)

    d = calculate_deep_statistics(pulls, "genshin_impact")["301"]
    assert d["early_count"] == 2
    assert EARLY_PITY_THRESHOLD == 30
    assert d["pity_5star_list"] == [1, 29, 31]


def test_char_weapon_split():
    pulls = [
        five("genshin_impact", "301", "Nahida", "2024-01-01 10:00:00"),
        five("genshin_impact", "301", "Skyward Harp", "2024-02-01 10:00:00", item_type="Weapon"),
        five("genshin_impact", "302", "Another Weapon", "2024-03-01 10:00:00", item_type="Weapon"),
    ]
    d = calculate_deep_statistics(pulls, "genshin_impact")
    assert d["301"]["char_5star"] == 1 and d["301"]["weapon_5star"] == 1
    assert d["302"]["weapon_5star"] == 1 and d["302"]["char_5star"] == 0


def test_empty_pool_zeroes():
    d = calculate_deep_statistics([], "honkai_star_rail")["1"]
    assert d["count"] == 0 and d["median"] == 0 and d["min"] == 0 and d["max"] == 0
    assert d["stddev"] == 0.0 and d["early_count"] == 0


def test_all_pools_present():
    d = calculate_deep_statistics([], "wuthering_waves")
    assert set(d) == {"1", "2", "3", "4", "5", "6", "7"}


def test_single_pull_stddev_zero():
    pulls = [five("genshin_impact", "301", "A", "2024-01-01 10:00:00")]
    d = calculate_deep_statistics(pulls, "genshin_impact")["301"]
    assert d["count"] == 1 and d["stddev"] == 0.0 and d["early_count"] == 1
