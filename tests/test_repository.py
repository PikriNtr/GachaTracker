"""Repository tests: dedup schemes, api_id round-trip, legacy DB migration."""
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import Pull
from database.repository import Repository


@pytest.fixture
def repo(tmp_path):
    return Repository(db_path=tmp_path / "test.db")


def wuwa_pull(rid, name, t):
    return Pull("1", rid, name, 3, t, "p1", game_id="wuthering_waves")


def api_pull(api_id, name, t, pool="1", q=3, item_type=""):
    return Pull(pool, "res", name, q, t, "p1", game_id="honkai_star_rail",
                item_type=item_type, api_id=api_id)


# ── WuWa natural-key dedup ────────────────────────────────────────────
def test_wuwa_idempotent_insert(repo):
    pulls = [wuwa_pull("1", "Echo", "2025-01-01 10:00:00")]
    assert repo.save_pulls("d", "wuthering_waves", "p1", pulls) == 1
    assert repo.save_pulls("d", "wuthering_waves", "p1", pulls) == 0


def test_wuwa_same_timestamp_different_names_both_kept(repo):
    pulls = [
        wuwa_pull("1", "Echo A", "2025-01-01 10:00:00"),
        wuwa_pull("2", "Echo B", "2025-01-01 10:00:00"),
    ]
    assert repo.save_pulls("d", "wuthering_waves", "p1", pulls) == 2


# ── api_id dedup (Genshin/HSR) ────────────────────────────────────────
def test_api_id_dedup(repo):
    pulls = [api_pull("100", "Seele", "2025-01-01 10:00:00")]
    assert repo.save_pulls("d", "honkai_star_rail", "p1", pulls) == 1
    assert repo.save_pulls("d", "honkai_star_rail", "p1", pulls) == 0


def test_api_id_distinct_ids_same_name_and_time_both_kept(repo):
    """The 10-pull data-loss bug: same name + timestamp, unique API ids."""
    pulls = [
        api_pull("111", "Tracks of Destiny", "2025-01-01 10:00:00"),
        api_pull("112", "Tracks of Destiny", "2025-01-01 10:00:00"),
    ]
    assert repo.save_pulls("d", "honkai_star_rail", "p1", pulls) == 2
    got = repo.get_pulls("d", "honkai_star_rail")
    assert len(got) == 2
    assert {p.api_id for p in got} == {"111", "112"}


def test_same_api_id_across_games_no_conflict(repo):
    a = api_pull("100", "X", "2025-01-01 10:00:00")
    b = api_pull("100", "X", "2025-01-01 10:00:00")
    assert repo.save_pulls("d", "honkai_star_rail", "p1", [a]) == 1
    assert repo.save_pulls("d2", "genshin_impact", "p1", [b]) == 1  # keyed by discord_id+game+api_id


# ── Round-trip ────────────────────────────────────────────────────────
def test_round_trip_preserves_fields(repo):
    p = Pull("301", "item7", "Nahida", 5, "2024-01-01 10:00:00", "p1",
             game_id="genshin_impact", item_type="Character", api_id="777",
             pity_at_pull=42, is_5050_win=True)
    repo.save_pulls("d", "genshin_impact", "p1", [p])
    got = repo.get_pulls("d", "genshin_impact")
    assert len(got) == 1
    g = got[0]
    assert g.resource_name == "Nahida" and g.quality_level == 5
    assert g.item_type == "Character" and g.api_id == "777"
    assert g.pity_at_pull == 42 and g.is_5050_win is True
    assert g.game_id == "genshin_impact" and g.card_pool_type == "301"


def test_games_isolated_in_queries(repo):
    repo.save_pulls("d", "genshin_impact", "p1", [api_pull("1", "A", "2025-01-01 10:00:00")])
    repo.save_pulls("d", "wuthering_waves", "p1", [wuwa_pull("1", "B", "2025-01-01 10:00:00")])
    assert len(repo.get_pulls("d", "genshin_impact")) == 1
    assert len(repo.get_pulls("d", "wuthering_waves")) == 1


# ── Legacy DB migration ───────────────────────────────────────────────
def _make_legacy_db(path):
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE accounts (id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id TEXT NOT NULL, game_id TEXT NOT NULL, player_id TEXT NOT NULL,
        server TEXT DEFAULT 'global', metadata TEXT, UNIQUE(discord_id, game_id, player_id))""")
    conn.execute("""CREATE TABLE pulls (id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id TEXT NOT NULL, game_id TEXT NOT NULL, player_id TEXT NOT NULL,
        card_pool_type TEXT NOT NULL, resource_id TEXT, resource_name TEXT NOT NULL,
        quality_level INTEGER NOT NULL, time TEXT NOT NULL,
        pity_at_pull INTEGER DEFAULT 0, is_5050_win INTEGER,
        UNIQUE(discord_id, game_id, player_id, card_pool_type, resource_name, time))""")
    conn.execute("""INSERT INTO pulls (discord_id, game_id, player_id, card_pool_type,
        resource_name, quality_level, time)
        VALUES ('d', 'wuthering_waves', 'p1', '1', 'Old Echo', 3, '2024-12-01 10:00:00')""")
    conn.commit()
    conn.close()


def test_legacy_db_migrates_and_preserves_rows(tmp_path):
    db = tmp_path / "legacy.db"
    _make_legacy_db(db)
    repo = Repository(db_path=db)  # triggers migration

    conn = sqlite3.connect(db)
    sql = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='pulls'").fetchone()[0]
    assert "UNIQUE(" not in sql.replace(" ", "").upper()
    assert conn.execute("SELECT COUNT(*) FROM pulls").fetchone()[0] == 1
    conn.close()

    # Old row still readable; new-style api_id inserts now work on it
    pulls = [api_pull("555", "New", "2025-01-01 10:00:00")]
    assert repo.save_pulls("d", "honkai_star_rail", "p1", pulls) == 1
    assert repo.save_pulls("d", "honkai_star_rail", "p1", pulls) == 0
