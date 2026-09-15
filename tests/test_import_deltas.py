"""Import delta logic: day1/day2 imports, pity recompute (never accumulated)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import Pull
from analytics.pity import calculate_pity_summary, GAME_BANNER_CONFIGS, DEFAULT_GAME
from games.genshin_impact.parser import parse_genshin_records
from games.honkai_star_rail.parser import parse_hsr_records
from database.repository import Repository


@pytest.fixture
def repo(tmp_path):
    return Repository(db_path=tmp_path / "delta.db")


def snapshot_import(repo, game_id, discord_id, player_id, api_pulls):
    """Mirrors gacha_cog.import_cmd's before/after delta logic."""
    cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
    featured = cfg["featured_pool"]

    old = repo.get_pulls(discord_id, game_id)
    old_summary = calculate_pity_summary(old, game_id) if old else {}
    old_total = len(old)
    old_5 = sum(len(s.get("history_5star", [])) for s in old_summary.values())
    old_4 = sum(1 for p in old if p.quality_level == 4)
    p_old = old_summary.get(featured, {})

    repo.save_account(discord_id=discord_id, game_id=game_id, player_id=player_id)
    new_count = repo.save_pulls(discord_id=discord_id, game_id=game_id, player_id=player_id, pulls=api_pulls)

    merged = repo.get_pulls(discord_id, game_id)
    summary = calculate_pity_summary(merged, game_id)
    p1 = summary.get(featured, {})
    return {
        "new_count": new_count,
        "old_total": old_total, "total": len(merged),
        "delta_5": sum(len(s.get("history_5star", [])) for s in summary.values()) - old_5,
        "delta_4": sum(1 for p in merged if p.quality_level == 4) - old_4,
        "old_pity": p_old.get("current_pity", 0), "pity": p1.get("current_pity", 0),
        "old_guar": p_old.get("is_guaranteed", False), "guar": p1.get("is_guaranteed", False),
        "old_lost": p_old.get("lost_5050", 0), "lost": p1.get("lost_5050", 0),
    }


def genshin_history(n, five_at=frozenset(), start_day=1, id_offset=0):
    """Newest-first Genshin 301 history with unique ids; one pull per day."""
    out = []
    for i in range(1, n + 1):  # oldest -> newest
        day = start_day + i - 1
        t = f"2025-{1 + (day - 1) // 28:02d}-{(day - 1) % 28 + 1:02d} 10:00:00"
        if i in five_at:
            out.append({"gacha_type": "301", "name": "Nahida", "rank_type": "5",
                        "time": t, "id": str(900000 + id_offset + i), "item_type": "Character"})
        else:
            out.append({"gacha_type": "301", "name": f"Filler {id_offset + i}", "rank_type": "3",
                        "time": t, "id": str(900000 + id_offset + i)})
    return list(reversed(out))


def test_genshin_day2_delta_not_sum(repo):
    """The 180->183 case: pity 10 -> 13, never 10+183."""
    day1 = parse_genshin_records(genshin_history(180, {100, 170}), "u1")
    r1 = snapshot_import(repo, "genshin_impact", "d1", "u1", day1)
    assert r1["new_count"] == 180 and r1["total"] == 180 and r1["pity"] == 10

    day2 = parse_genshin_records(
        genshin_history(180, {100, 170}) + genshin_history(3, start_day=200, id_offset=180), "u1")
    r2 = snapshot_import(repo, "genshin_impact", "d1", "u1", day2)
    assert r2["new_count"] == 3                      # true delta
    assert r2["total"] == 183                        # merged size, not 180+183
    assert r2["old_pity"] == 10 and r2["pity"] == 13  # recomputed


def test_pity_reset_between_imports(repo):
    """Day1 pity 70; day2 contains 5-star at pull 80 -> pity resets to 10."""
    day1 = parse_genshin_records(genshin_history(70), "u2")
    r1 = snapshot_import(repo, "genshin_impact", "d2", "u2", day1)
    assert r1["pity"] == 70

    day2 = parse_genshin_records(genshin_history(90, {80}), "u2")
    r2 = snapshot_import(repo, "genshin_impact", "d2", "u2", day2)
    assert r2["new_count"] == 20 and r2["delta_5"] == 1
    assert r2["pity"] == 10  # reset honored; nothing double-counted


def test_identical_reimport_is_noop(repo):
    day1 = parse_genshin_records(genshin_history(50, {25}), "u3")
    snapshot_import(repo, "genshin_impact", "d3", "u3", day1)
    for _ in range(3):
        r = snapshot_import(repo, "genshin_impact", "d3", "u3", day1)
        assert r["new_count"] == 0
        assert r["delta_5"] == 0 and r["delta_4"] == 0


def test_hsr_new_5star_and_5050_chain(repo):
    day1 = parse_hsr_records([
        {"gacha_type": "1", "name": "Bronya", "rank_type": "5", "time": "2025-01-01 10:00:00",
         "id": "1", "item_type": "Character"},
        {"gacha_type": "1", "name": "F1", "rank_type": "3", "time": "2025-01-02 10:00:00", "id": "2"},
    ], "u4")
    r1 = snapshot_import(repo, "honkai_star_rail", "d4", "u4", day1)
    assert r1["guar"] is True and r1["lost"] == 1

    day2 = parse_hsr_records(list(reversed([
        {"gacha_type": "1", "name": "Bronya", "rank_type": "5", "time": "2025-01-01 10:00:00",
         "id": "1", "item_type": "Character"},
        {"gacha_type": "1", "name": "F1", "rank_type": "3", "time": "2025-01-02 10:00:00", "id": "2"},
        {"gacha_type": "1", "name": "Seele", "rank_type": "5", "time": "2025-02-01 10:00:00",
         "id": "3", "item_type": "Character"},
        {"gacha_type": "1", "name": "F2", "rank_type": "4", "time": "2025-02-02 10:00:00", "id": "4"},
    ])), "u4")
    r2 = snapshot_import(repo, "honkai_star_rail", "d4", "u4", day2)
    assert r2["new_count"] == 2 and r2["delta_5"] == 1 and r2["delta_4"] == 1
    assert r2["old_guar"] is True and r2["guar"] is False  # Seele consumed guarantee
    assert r2["lost"] == r2["old_lost"] == 1


def test_wuwa_natural_key_delta(repo):
    def w(pairs):
        return [Pull("1", rid, name, q, t, "1001", game_id="wuthering_waves")
                for rid, name, q, t in pairs]

    day1 = w([("1", "Jinhsi", 5, "2025-01-01 12:00:00"),
              ("2", "FA", 3, "2025-01-01 12:00:01")])
    r1 = snapshot_import(repo, "wuthering_waves", "d5", "1001", day1)
    assert r1["new_count"] == 2 and r1["pity"] == 1

    day2 = day1 + w([("3", "FB", 3, "2025-02-01 12:00:00"),
                     ("4", "FC", 3, "2025-02-01 12:00:00")])  # same second
    r2 = snapshot_import(repo, "wuthering_waves", "d5", "1001", day2)
    assert r2["new_count"] == 2 and r2["total"] == 4 and r2["pity"] == 3
