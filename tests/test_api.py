"""REST API tests: read routers, auth modes, write endpoints, pagination."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi.testclient", reason="fastapi not installed")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import Pull  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    """API app against a temp DB, seeded with one user's data, reads open."""
    import config
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "api.db")
    monkeypatch.setattr(config, "API_KEY", "test-key-123")
    monkeypatch.setattr(config, "API_REQUIRE_KEY_FOR_READS", False)

    import api.deps as deps
    monkeypatch.setattr(deps, "_repo", None)  # reset the cached repo

    # seed before first request so the cached repo opens the temp DB
    from database.repository import Repository
    repo = Repository(db_path=config.DB_PATH)
    pulls = [
        Pull("301", "r1", "Nahida", 5, "2024-01-01 10:00:00", "700001",
             game_id="genshin_impact", item_type="Character", pity_at_pull=1, is_5050_win=True),
        Pull("301", "r2", "F", 3, "2024-01-02 10:00:00", "700001", game_id="genshin_impact"),
        Pull("301", "r3", "F2", 4, "2024-01-03 10:00:00", "700001", game_id="genshin_impact"),
    ]
    repo.save_account(discord_id="d1", game_id="genshin_impact", player_id="700001")
    repo.save_pulls("d1", "genshin_impact", "700001", pulls)

    from fastapi import FastAPI

    from api.main import app as real_app
    test_app = FastAPI()
    test_app.include_router(real_app.router)

    from fastapi.testclient import TestClient
    with TestClient(test_app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_games_listing(client):
    r = client.get("/games")
    assert r.status_code == 200
    ids = [g["game_id"] for g in r.json()["games"]]
    assert ids == ["wuthering_waves", "genshin_impact", "honkai_star_rail"]


def test_accounts_listing(client):
    r = client.get("/accounts/d1")
    assert r.status_code == 200
    body = r.json()
    assert body["accounts"][0]["player_id"] == "700001"
    assert body["accounts"][0]["total_pulls"] == 3


def test_accounts_404_for_unknown_user(client):
    assert client.get("/accounts/nobody").status_code == 404


def test_pulls_pagination_and_filters(client):
    full = client.get("/accounts/d1/pulls/genshin_impact").json()
    assert full["total"] == 3 and len(full["items"]) == 3

    page = client.get("/accounts/d1/pulls/genshin_impact", params={"limit": 1, "offset": 1}).json()
    assert page["total"] == 3 and len(page["items"]) == 1 and page["offset"] == 1

    fives = client.get("/accounts/d1/pulls/genshin_impact",
                       params={"quality_level": 5}).json()
    assert fives["total"] == 1 and fives["items"][0]["resource_name"] == "Nahida"
    assert fives["items"][0]["pity_at_pull"] == 1


def test_pity_endpoint(client):
    r = client.get("/accounts/d1/pity/genshin_impact")
    assert r.status_code == 200
    body = r.json()
    assert body["player_id"] == "700001"
    assert body["banners"]["301"]["max_pity"] == 90
    assert body["banners"]["301"]["is_guaranteed"] is False


def test_stats_endpoint(client):
    r = client.get("/accounts/d1/stats/genshin_impact")
    assert r.status_code == 200
    d = r.json()["pools"]["301"]
    assert d["count"] == 1 and d["char_5star"] == 1 and d["weapon_5star"] == 0


def test_profile_endpoint(client):
    r = client.get("/accounts/d1/profile")
    assert r.status_code == 200
    body = r.json()
    assert "700001" in body["player_label"]
    assert body["profile"]["total_pulls"] == 3


def test_unknown_game_404(client):
    assert client.get("/accounts/d1/pity/unknown_game").status_code == 404


def test_banners_empty_ok(client):
    r = client.get("/banners/genshin_impact")
    assert r.status_code == 200
    assert r.json()["active"] == {}


# ── writes: key required ─────────────────────────────────────────────
def test_import_requires_key(client):
    r = client.post("/accounts/d2/import/genshin_impact", json={"url": "https://x"})
    assert r.status_code == 401


def test_import_bad_key(client):
    r = client.post("/accounts/d2/import/genshin_impact", json={"url": "https://x"},
                    headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_delete_requires_key(client):
    assert client.delete("/accounts/d1/genshin_impact").status_code == 401


def test_delete_with_key(client):
    r = client.delete("/accounts/d1/genshin_impact", headers={"X-API-Key": "test-key-123"})
    assert r.status_code == 200
    assert r.json()["deleted_pulls"] == 3
    # gone
    assert client.get("/accounts/d1/pity/genshin_impact").status_code == 404


def test_reads_gate_toggle(client, monkeypatch):
    """The one-config-line switch: API_REQUIRE_KEY_FOR_READS gates reads too."""
    import config
    monkeypatch.setattr(config, "API_REQUIRE_KEY_FOR_READS", True)

    # open client now rejected
    assert client.get("/accounts/d1/pity/genshin_impact").status_code == 401
    # with key -> allowed
    ok = client.get("/accounts/d1/pity/genshin_impact", headers={"X-API-Key": "test-key-123"})
    assert ok.status_code == 200
