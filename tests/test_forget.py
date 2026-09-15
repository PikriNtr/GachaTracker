"""Tests for /forget backing logic: delete_user_data isolation + idempotency."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import Pull
from database.repository import Repository


@pytest.fixture
def repo(tmp_path):
    return Repository(db_path=tmp_path / "forget.db")


def _seed(repo, discord_id, game_id, player_id="p1"):
    pulls = [
        Pull("1", "r", "A", 5, "2025-01-01 10:00:00", player_id, game_id=game_id),
        Pull("1", "r", "B", 3, "2025-01-02 10:00:00", player_id, game_id=game_id),
        Pull("2", "r", "C", 3, "2025-01-03 10:00:00", player_id, game_id=game_id),
    ]
    repo.save_account(discord_id=discord_id, game_id=game_id, player_id=player_id)
    repo.save_pulls(discord_id=discord_id, game_id=game_id, player_id=player_id, pulls=pulls)


def test_delete_removes_pulls_and_account(repo):
    _seed(repo, "d1", "genshin_impact")
    assert repo.get_account_by_discord_id("d1", "genshin_impact") is not None
    removed = repo.delete_user_data("d1", "genshin_impact")
    assert removed == 3
    assert repo.get_account_by_discord_id("d1", "genshin_impact") is None
    assert repo.get_pulls("d1", "genshin_impact") == []


def test_delete_isolated_per_game(repo):
    _seed(repo, "d1", "genshin_impact")
    _seed(repo, "d1", "honkai_star_rail")
    assert repo.delete_user_data("d1", "genshin_impact") == 3
    assert len(repo.get_pulls("d1", "honkai_star_rail")) == 3
    assert repo.get_account_by_discord_id("d1", "honkai_star_rail") is not None


def test_delete_isolated_per_discord_user(repo):
    _seed(repo, "d1", "genshin_impact")
    _seed(repo, "d2", "genshin_impact")
    assert repo.delete_user_data("d1", "genshin_impact") == 3
    assert len(repo.get_pulls("d2", "genshin_impact")) == 3


def test_delete_when_nothing_exists_returns_zero(repo):
    assert repo.delete_user_data("nobody", "wuthering_waves") == 0


def test_reimport_after_delete_works(repo):
    _seed(repo, "d1", "genshin_impact")
    repo.delete_user_data("d1", "genshin_impact")
    # fresh import: same rows insert again as new data
    pulls = [Pull("301", "r", "Nahida", 5, "2025-06-01 10:00:00", "p9", game_id="genshin_impact", api_id="999")]
    assert repo.save_pulls("d1", "genshin_impact", "p9", pulls) == 1
