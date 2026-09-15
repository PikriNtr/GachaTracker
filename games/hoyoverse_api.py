"""Shared HoYoverse gacha-record API client.

Genshin Impact and Honkai: Star Rail use the same getGachaLog protocol with
different API domains, path prefixes and gacha-type ids:

  Genshin : public-operation-hk4e(-sg)...  /gacha_info/api/getGachaLog   301/400/302/200/100
  HSR     : public-operation-hkrpg(-sg)... /common/hkrpg_gacha_record/api/getGachaLog   11/12/1/2

Both paginate with size=20 + end_id cursor and answer retcode 0 / "visit too
frequently" the same way. One client, two configurations.
"""
import asyncio
import urllib.parse
import aiohttp
from typing import Dict, Any, List, Tuple

# Pacing: HoYoverse rate-limits ("visit too frequently") when pages are
# requested back-to-back. The reference community clients sleep between
# pages and retry with backoff.
PAGE_DELAY_SEC = 0.5
RETRY_ATTEMPTS = 5
RETRY_DELAY_SEC = 6.0

PAGE_SIZE = 20


class HoyoverseAPIError(Exception):
    pass


GAME_API_CONFIGS = {
    "genshin_impact": {
        "api_domain_cn": "https://public-operation-hk4e.mihoyo.com",
        "api_domain_os": "https://public-operation-hk4e-sg.hoyoverse.com",
        "path": "/gacha_info/api/getGachaLog",
        "gacha_types": ["301", "400", "302", "500", "200", "100"],
    },
    "honkai_star_rail": {
        "api_domain_cn": "https://public-operation-hkrpg.mihoyo.com",
        "api_domain_os": "https://public-operation-hkrpg-sg.hoyoverse.com",
        "path": "/common/hkrpg_gacha_record/api/getGachaLog",
        "gacha_types": ["11", "12", "1", "2"],
    },
}


def parse_gacha_url(url: str, game_id: str) -> Dict[str, str]:
    """Parses a gacha-history URL (copied from game client cache/log) into params.

    The URL carries a long `authkey` plus `auth_appid=webview_gacha`,
    `game_biz=hk4e_<region>` / `hkrpg_<region>` etc. We only need the query
    string as-is plus a chosen API domain and endpoint path.
    """
    cfg = GAME_API_CONFIGS[game_id]

    raw_url = url.strip().strip("<>\"'")
    parsed = urllib.parse.urlparse(raw_url)
    qs = urllib.parse.parse_qs(parsed.query)

    authkey = qs.get("authkey", [None])[0]
    if not authkey:
        raise HoyoverseAPIError("Missing required URL parameter: 'authkey'. Please copy a fresh gacha history URL.")

    # authkey often arrives double-encoded; fix if it contains raw '=' not urlencoded
    if "=" in authkey and "%" not in authkey:
        authkey = urllib.parse.quote_plus(authkey)

    # Strip pagination params — we manage them ourselves
    drop = {"page", "size", "gacha_type", "end_id", "lang"}
    filtered = [(k, v[0]) for k, v in qs.items() if k not in drop]

    lang = qs.get("lang", ["en-us"])[0]
    if "lang" in drop:
        filtered.append(("lang", lang))

    # Honor the domain in the URL when it matches this game's known domains;
    # otherwise default by TLD (hoyoverse.com = global, mihoyo.com = CN).
    api_domain = cfg["api_domain_os"]
    known = (cfg["api_domain_cn"], cfg["api_domain_os"])
    if parsed.netloc and parsed.netloc in known:
        api_domain = parsed.netloc and f"https://{parsed.netloc}"
    elif "mihoyo.com" in raw_url and "hoyoverse.com" not in raw_url:
        api_domain = cfg["api_domain_cn"]

    return {
        "api_domain": api_domain,
        "path": cfg["path"],
        "query_string": urllib.parse.urlencode(filtered),
        "lang": lang,
        "gacha_types": cfg["gacha_types"],
    }


async def fetch_gacha_page(
    session: aiohttp.ClientSession,
    params: Dict[str, str],
    gacha_type: str,
    page: int,
    end_id: str = "0",
) -> List[Dict[str, Any]]:
    """Fetches one page (20 records) of history for a gacha type.

    Retries with backoff on rate-limit errors ("visit too frequently").
    """
    url = (
        f"{params['api_domain']}{params['path']}"
        f"?{params['query_string']}&gacha_type={gacha_type}"
        f"&page={page}&size={PAGE_SIZE}&end_id={end_id}"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    last_error: str = ""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    raise HoyoverseAPIError(f"API returned HTTP {resp.status} for gacha_type={gacha_type} page={page}")
                data = await resp.json(content_type=None)
                if not data or data.get("retcode") != 0:
                    message = data.get("message", "unknown error") if data else "empty response"
                    # Rate-limited: retry after a pause instead of failing
                    if "visit too frequently" in message.lower() or "too fast" in message.lower():
                        last_error = message
                        await asyncio.sleep(RETRY_DELAY_SEC * (attempt + 1))
                        continue
                    raise HoyoverseAPIError(f"HoYoverse API error: {message}")
                return (data.get("data") or {}).get("list") or []
        except HoyoverseAPIError:
            raise
        except Exception:
            # Network hiccup: brief pause then retry
            last_error = "network error"
            await asyncio.sleep(RETRY_DELAY_SEC / 2)
    raise HoyoverseAPIError(
        f"HoYoverse API rate-limited or unreachable after {RETRY_ATTEMPTS} attempts: {last_error}"
    )


async def fetch_all_history(url: str, game_id: str) -> Tuple[str, Dict[str, List[Dict[str, Any]]]]:
    """Fetches full gacha history across all gacha types via paginated requests.

    Returns (player_id/uid, records_by_gacha_type). Records arrive newest-first;
    we preserve that order (callers reverse when needed), matching the plugins.
    """
    params = parse_gacha_url(url, game_id)
    uid = ""
    records_by_type: Dict[str, List[Dict[str, Any]]] = {}

    async with aiohttp.ClientSession() as session:
        for gacha_type in params["gacha_types"]:
            all_records: List[Dict[str, Any]] = []
            page = 1
            end_id = "0"
            while True:
                records = await fetch_gacha_page(session, params, gacha_type, page, end_id)
                if not records:
                    break
                if not uid and records[0].get("uid"):
                    uid = str(records[0]["uid"])
                all_records.extend(records)
                end_id = str(records[-1].get("id", "0"))
                page += 1
                if len(records) < PAGE_SIZE:
                    break
                await asyncio.sleep(PAGE_DELAY_SEC)  # pacing between pages
            if all_records:
                records_by_type[gacha_type] = all_records

    if not uid:
        raise HoyoverseAPIError("Could not determine UID from gacha history response.")
    return uid, records_by_type
