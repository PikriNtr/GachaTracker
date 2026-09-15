import asyncio
import urllib.parse
from typing import Any, Dict, List, Tuple

import aiohttp

API_DOMAIN_CN = "https://public-operation-hk4e.mihoyo.com"
API_DOMAIN_OS = "https://public-operation-hk4e-sg.hoyoverse.com"

GACHA_TYPES = ["301", "400", "302", "200", "100"]
PAGE_SIZE = 20

# Pacing: HoYoverse rate-limits ("visit too frequently") when pages are
# requested back-to-back. The reference community clients sleep between
# pages and retry with backoff on -110 / "visit too frequently".
PAGE_DELAY_SEC = 0.5
RETRY_ATTEMPTS = 5
RETRY_DELAY_SEC = 6.0


class GenshinAPIError(Exception):
    pass


def parse_gacha_url(url: str) -> Dict[str, str]:
    """Parses a Wish History URL (copied from game client cache/log) into params.

    The URL carries a long `authkey` plus `auth_appid=webview_gacha`,
    `game_biz=hk4e_<region>` etc. We only need the query string as-is plus a
    chosen API domain.
    """
    raw_url = url.strip().strip("<>\"'")
    parsed = urllib.parse.urlparse(raw_url)
    qs = urllib.parse.parse_qs(parsed.query)

    authkey = qs.get("authkey", [None])[0]
    if not authkey:
        raise GenshinAPIError("Missing required URL parameter: 'authkey'. Please copy a fresh Wish History URL.")

    # authkey often arrives double-encoded; fix if it contains raw '=' not urlencoded
    if "=" in authkey and "%" not in authkey:
        authkey = urllib.parse.quote_plus(authkey)

    # Strip pagination params — we manage them ourselves
    drop = {"page", "size", "gacha_type", "end_id", "lang"}
    filtered = [(k, v[0]) for k, v in qs.items() if k not in drop]

    # Re-add lang default if it was stripped
    lang = qs.get("lang", ["en-us"])[0]
    filtered.append(("lang", lang))

    api_domain = API_DOMAIN_OS if "hoyoverse.com" in raw_url else API_DOMAIN_CN

    return {
        "api_domain": api_domain,
        "query_string": urllib.parse.urlencode(filtered),
        "lang": lang,
    }


async def fetch_gacha_page(
    session: aiohttp.ClientSession,
    params: Dict[str, str],
    gacha_type: str,
    page: int,
    end_id: str = "0",
) -> List[Dict[str, Any]]:
    """Fetches one page (20 records) of wish history for a gacha type.

    Retries with backoff on rate-limit errors ("visit too frequently").
    """
    url = (
        f"{params['api_domain']}/gacha_info/api/getGachaLog"
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
                    raise GenshinAPIError(f"API returned HTTP {resp.status} for gacha_type={gacha_type} page={page}")
                data = await resp.json(content_type=None)
                if not data or data.get("retcode") != 0:
                    message = data.get("message", "unknown error") if data else "empty response"
                    # Rate-limited: retry after a pause instead of failing
                    if "visit too frequently" in message.lower() or "too fast" in message.lower():
                        last_error = message
                        await asyncio.sleep(RETRY_DELAY_SEC * (attempt + 1))
                        continue
                    raise GenshinAPIError(f"HoYoverse API error: {message}")
                return (data.get("data") or {}).get("list") or []
        except GenshinAPIError:
            raise
        except Exception:
            # Network hiccup: brief pause then retry
            last_error = "network error"
            await asyncio.sleep(RETRY_DELAY_SEC / 2)
    raise GenshinAPIError(
        f"HoYoverse API rate-limited or unreachable after {RETRY_ATTEMPTS} attempts: {last_error}"
    )


async def fetch_all_wish_history(url: str) -> Tuple[str, Dict[str, List[Dict[str, Any]]]]:
    """Fetches full wish history across all gacha types via paginated requests.

    Returns (uid, records_by_gacha_type). Records arrive newest-first; we
    preserve that order (callers reverse when needed), matching WuWa plugin.
    """
    params = parse_gacha_url(url)
    uid = ""
    records_by_type: Dict[str, List[Dict[str, Any]]] = {}

    async with aiohttp.ClientSession() as session:
        for gacha_type in GACHA_TYPES:
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
        raise GenshinAPIError("Could not determine UID from wish history response.")
    return uid, records_by_type
