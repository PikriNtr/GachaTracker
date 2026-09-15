"""Banner schedule tests: upsert, active/upcoming windows, deletion, time parsing."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.schedule_time import canonical, parse_timestamp
from database.repository import Repository


@pytest.fixture
def repo(tmp_path):
    return Repository(db_path=tmp_path / "banners.db")


def test_parse_timestamp_formats():
    cases = {
        "2025-01-15 11:00:00": (2025, 1, 15, 11, 0, 0),
        "2025-01-15 11:00": (2025, 1, 15, 11, 0, 0),
        "2025-01-15 11am": (2025, 1, 15, 11, 0, 0),
        "2025-01-15 1pm": (2025, 1, 15, 13, 0, 0),
        "2025-01-15 1:30pm": (2025, 1, 15, 13, 30, 0),
        "2025-01-15": (2025, 1, 15, 0, 0, 0),
    }
    for raw, expected in cases.items():
        dt = parse_timestamp(raw)
        assert dt is not None, raw
        assert (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) == expected, raw


def test_parse_timestamp_rejects_garbage():
    for raw in ("", "tomorrow", "2025/13/45", "Jan 5", "2025-01-15 25:00"):
        assert parse_timestamp(raw) is None, raw


def test_canonical_is_fixed_width():
    dt = parse_timestamp("2025-01-15 1pm")
    c = canonical(dt)
    assert c == "2025-01-15 13:00:00"
    assert len(c) == 19  # string comparison safe


def test_upsert_and_active_window(repo):
    repo.upsert_banner_schedule("genshin_impact", "301", "Nahida Rerun",
                                "2025-01-15 11:00:00", "2025-02-05 17:59:00", "user1")
    # during the window
    active = repo.get_active_banners("genshin_impact", now="2025-01-20 12:00:00")
    assert active["301"]["banner_name"] == "Nahida Rerun"
    # before the window
    assert repo.get_active_banners("genshin_impact", now="2025-01-01 00:00:00") == {}
    # after the window
    assert repo.get_active_banners("genshin_impact", now="2025-03-01 00:00:00") == {}


def test_upsert_updates_existing_window(repo):
    repo.upsert_banner_schedule("genshin_impact", "301", "Nahida Rerun",
                                "2025-01-15 11:00:00", "2025-02-05 17:59:00", "user1")
    repo.upsert_banner_schedule("genshin_impact", "301", "Nahida Rerun",
                                "2025-01-15 11:00:00", "2025-02-20 17:59:00", "user2")
    windows = repo.get_banner_windows("genshin_impact", "301")
    assert len(windows) == 1  # same (game, pool, name, start) -> updated, not duplicated
    assert windows[0]["end_time"] == "2025-02-20 17:59:00"
    assert windows[0]["created_by"] == "user2"


def test_active_picks_latest_start_on_overlap(repo):
    repo.upsert_banner_schedule("wuthering_waves", "1", "Old Banner",
                                "2025-01-01 00:00:00", "2025-01-31 00:00:00", "u")
    repo.upsert_banner_schedule("wuthering_waves", "1", "New Banner",
                                "2025-01-15 00:00:00", "2025-02-10 00:00:00", "u")
    active = repo.get_active_banners("wuthering_waves", now="2025-01-20 00:00:00")
    assert active["1"]["banner_name"] == "New Banner"


def test_upcoming_windows_per_pool(repo):
    repo.upsert_banner_schedule("genshin_impact", "301", "Future A",
                                "2025-06-01 00:00:00", "2025-06-20 00:00:00", "u")
    repo.upsert_banner_schedule("genshin_impact", "301", "Future B",
                                "2025-07-01 00:00:00", "2025-07-20 00:00:00", "u")
    repo.upsert_banner_schedule("genshin_impact", "302", "Future W",
                                "2025-06-01 00:00:00", "2025-06-20 00:00:00", "u")
    repo.upsert_banner_schedule("genshin_impact", "301", "Current",
                                "2025-01-01 00:00:00", "2025-02-01 00:00:00", "u")

    up = repo.get_upcoming_banners("genshin_impact", now="2025-01-15 00:00:00")
    assert [w["banner_name"] for w in up["301"]] == ["Future A", "Future B"]  # start-ordered
    assert [w["banner_name"] for w in up["302"]] == ["Future W"]
    # active is untouched by upcoming
    active = repo.get_active_banners("genshin_impact", now="2025-01-15 00:00:00")
    assert active["301"]["banner_name"] == "Current"


def test_delete_all_vs_active_only(repo):
    repo.upsert_banner_schedule("wuthering_waves", "1", "Past",
                                "2024-12-01 00:00:00", "2024-12-20 00:00:00", "u")
    repo.upsert_banner_schedule("wuthering_waves", "1", "Live",
                                "2025-01-01 00:00:00", "2025-01-31 00:00:00", "u")
    repo.upsert_banner_schedule("wuthering_waves", "1", "Next",
                                "2025-02-01 00:00:00", "2025-02-20 00:00:00", "u")

    removed = repo.delete_banner_windows("wuthering_waves", "1", only_active=True,
                                         now="2025-01-15 00:00:00")
    assert removed == 1
    remaining = [w["banner_name"] for w in repo.get_banner_windows("wuthering_waves", "1")]
    assert remaining == ["Past", "Next"]

    removed = repo.delete_banner_windows("wuthering_waves", "1")
    assert removed == 2
    assert repo.get_banner_windows("wuthering_waves", "1") == []


def test_games_are_isolated(repo):
    repo.upsert_banner_schedule("genshin_impact", "301", "Genshin Thing",
                                "2025-01-01 00:00:00", "2025-02-01 00:00:00", "u")
    assert repo.get_banner_windows("wuthering_waves") == []
    assert repo.get_active_banners("wuthering_waves", now="2025-01-15") == {}
