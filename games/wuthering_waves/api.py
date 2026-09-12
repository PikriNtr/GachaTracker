import urllib.parse
import aiohttp
from typing import Dict, Any, List, Tuple

CARD_POOL_TYPES = ["1", "2", "3", "4", "5", "6", "7"]

class WuWaAPIError(Exception):
    pass

def parse_convene_url(url: str) -> Dict[str, str]:
    """Parses Convene URL into query parameters required by Kuro Games API."""
    raw_url = url.strip().strip("<>\"'")
    parsed = urllib.parse.urlparse(raw_url)
    query_str = parsed.query
    if not query_str and "?" in raw_url:
        query_str = raw_url.split("?", 1)[1]

    qs = urllib.parse.parse_qs(query_str)

    def get_val(keys: list, default=None):
        for k in keys:
            vals = qs.get(k, [])
            if vals and vals[0]:
                return vals[0]
        return default

    player_id = get_val(["player_id", "playerId"])
    record_id = get_val(["record_id", "recordId"])
    svr_id = get_val(["svr_id", "serverId"])
    lang = get_val(["lang", "languageCode"], "en")
    gacha_type = get_val(["gacha_type", "cardPoolType"], "1")

    if not player_id:
        raise WuWaAPIError("Missing required URL parameter: 'player_id'. Please copy a fresh Convene URL.")
    if not record_id:
        raise WuWaAPIError("Missing required URL parameter: 'record_id'. Please copy a fresh Convene URL.")
    if not svr_id:
        raise WuWaAPIError("Missing required URL parameter: 'svr_id'. Please copy a fresh Convene URL.")

    # Determine API domain
    if "aki-game.com" in raw_url:
        api_domain = "https://gmserver-api.aki-game2.com"
    else:
        api_domain = "https://gmserver-api.aki-game2.net"

    return {
        "api_domain": api_domain,
        "player_id": player_id,
        "record_id": record_id,
        "svr_id": svr_id,
        "lang": lang,
        "gacha_type": gacha_type,
    }

async def fetch_card_pool(session: aiohttp.ClientSession, params: Dict[str, str], card_pool_type: str) -> List[Dict[str, Any]]:
    """Queries Kuro Games API for pulls belonging to a specific banner."""
    api_url = f"{params['api_domain']}/gacha/record/query"
    payload = {
        "cardPoolId": params["record_id"],
        "cardPoolType": int(card_pool_type),
        "languageCode": params["lang"],
        "playerId": params["player_id"],
        "recordId": params["record_id"],
        "serverId": params["svr_id"],
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        async with session.post(api_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                if data and data.get("code") == 0 and "data" in data and isinstance(data["data"], list):
                    return data["data"]
    except Exception:
        pass

    # Fallback GET query string if POST fails
    try:
        qs = (
            f"svr_id={params['svr_id']}&player_id={params['player_id']}&lang={params['lang']}"
            f"&gacha_type={card_pool_type}&record_id={params['record_id']}&cardPoolType={card_pool_type}"
        )
        async with session.get(f"{api_url}?{qs}", headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                if data and data.get("code") == 0 and "data" in data and isinstance(data["data"], list):
                    return data["data"]
    except Exception:
        pass

    return []

async def fetch_all_convene_history(url: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Fetches full convene history across all card pool types. Returns (player_id, raw_records)."""
    params = parse_convene_url(url)
    player_id = params["player_id"]
    all_records = []

    async with aiohttp.ClientSession() as session:
        for pool_type in CARD_POOL_TYPES:
            pool_records = await fetch_card_pool(session, params, pool_type)
            all_records.extend(pool_records)

    return player_id, all_records
