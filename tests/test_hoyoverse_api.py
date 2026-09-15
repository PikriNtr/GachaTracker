"""HoYoverse API client tests (no network): URL parsing, config separation."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from games.hoyoverse_api import GAME_API_CONFIGS, HoyoverseAPIError, parse_gacha_url

GENSHIN_URL = ("https://public-operation-hk4e-sg.hoyoverse.com/gacha_info/api/getGachaLog"
               "?authkey_ver=1&sign_type=2&auth_appid=webview_gacha&lang=en"
               "&authkey=abc123%2Fdef%3D%3D&game_biz=hk4e_global"
               "&page=2&size=20&gacha_type=301&end_id=1700000000000000000")


def test_genshin_url_parsing():
    p = parse_gacha_url(GENSHIN_URL, "genshin_impact")
    assert p["api_domain"] == "https://public-operation-hk4e-sg.hoyoverse.com"
    assert p["path"] == "/gacha_info/api/getGachaLog"
    qs = p["query_string"]
    assert "authkey=abc123%2Fdef%3D%3D" in qs   # preserved encoding
    assert "page=" not in qs and "size=" not in qs
    assert "gacha_type=" not in qs and "end_id=" not in qs
    assert "lang=en" in qs


def test_hsr_url_parsing():
    hsr = ("https://public-operation-hkrpg-sg.hoyoverse.com"
           "/common/hkrpg_gacha_record/api/getGachaLog?authkey_ver=1&sign_type=2"
           "&lang=en&authkey=xyz789&game_biz=hkrpg_global")
    p = parse_gacha_url(hsr, "honkai_star_rail")
    assert p["api_domain"] == "https://public-operation-hkrpg-sg.hoyoverse.com"
    assert p["path"] == "/common/hkrpg_gacha_record/api/getGachaLog"
    assert p["gacha_types"] == ["11", "12", "1", "2"]
    assert "authkey=xyz789" in p["query_string"]


def test_gacha_types_match_pity_configs():
    from analytics.pity import GAME_BANNER_CONFIGS
    for game_id, cfg in GAME_API_CONFIGS.items():
        api_types = set(cfg["gacha_types"])
        pity_pools = set(GAME_BANNER_CONFIGS[game_id]["pools"])
        assert api_types == pity_pools, f"{game_id}: API {api_types} != pity {pity_pools}"


def test_missing_authkey_raises():
    with pytest.raises(HoyoverseAPIError, match="authkey"):
        parse_gacha_url("https://public-operation-hk4e-sg.hoyoverse.com/gacha_info/api/getGachaLog?lang=en",
                        "genshin_impact")


def test_raw_equals_in_authkey_get_encoded():
    # Reference fixAuthkey behavior: raw '=' in authkey (not %-encoded) gets
    # encoded so query parsing is unambiguous; '+' passes through (form-encoding).
    url = ("https://public-operation-hk4e-sg.hoyoverse.com/gacha_info/api/getGachaLog"
           "?authkey=a+b=c&lang=en")
    p = parse_gacha_url(url, "genshin_impact")
    assert "authkey=a+b%3Dc" in p["query_string"]


def test_unknown_game_rejected():
    with pytest.raises(KeyError):
        parse_gacha_url(GENSHIN_URL, "unknown_game")
