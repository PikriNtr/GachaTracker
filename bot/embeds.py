from typing import Any, Dict, List, Optional

import discord

from analytics.deep_stats import EARLY_PITY_THRESHOLD
from analytics.pity import DEFAULT_GAME, GAME_BANNER_CONFIGS

C_BLUE   = 0x4B8DF8
C_GOLD   = 0xE8B84B
C_GREEN  = 0x4CAF7D
C_RED    = 0xE05252
C_PURPLE = 0x9B72CF
C_GREY   = 0x5C6370

FOOTER = "GachaTracker  •  /help for command list"

# Per-game presentation: currency names and terminology. Math lives in
# analytics; this dict only controls what the user sees.
GAME_UI = {
    "wuthering_waves": {
        "currency": "Astrites",
        "currency_one": "Astrite",
        "gacha_noun": "Convene",          # "Convene Pity", "Convene Statistics"
        "pull_noun": "pull",
        "pull_noun_plural": "pulls",
    },
    "genshin_impact": {
        "currency": "Primogems",
        "currency_one": "Primogem",
        "gacha_noun": "Wish",
        "pull_noun": "wish",
        "pull_noun_plural": "wishes",
    },
    "honkai_star_rail": {
        "currency": "Stellar Jades",
        "currency_one": "Stellar Jade",
        "gacha_noun": "Warp",
        "pull_noun": "warp",
        "pull_noun_plural": "warps",
    },
}


def game_ui(game_id: str) -> Dict[str, str]:
    return GAME_UI.get(game_id, GAME_UI[DEFAULT_GAME])


def game_config(game_id: str) -> Dict[str, Any]:
    return GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])


def make_progress_bar(current: int, total: int, length: int = 10) -> str:
    pct = min(1.0, max(0.0, current / total)) if total > 0 else 0
    filled = int(round(pct * length))
    return "█" * filled + "░" * (length - filled)

def no_data_embed(game_id: str = DEFAULT_GAME) -> discord.Embed:
    ui = game_ui(game_id)
    if game_id == "honkai_star_rail":
        how_to = (
            "You haven't synced your warp history yet.\n\n"
            "How to sync:\n"
            "1. Open Honkai: Star Rail and view your Warp History in-game.\n"
            "2. Get your Warp History URL (from the client log/cache, e.g. with a "
            "GetLink script like the Genshin one — the URL format is identical).\n"
            "3. Use `/import <url> game:Honkai: Star Rail` to sync your history."
        )
    elif game_id == "genshin_impact":
        how_to = (
            "You haven't synced your wish history yet.\n\n"
            "How to sync:\n"
            "1. Open Genshin Impact and view your Wish History in-game.\n"
            "2. Get your Wish History URL, e.g. with the tracker script:\n"
            "```powershell\n"
            "powershell -ExecutionPolicy Bypass -File tracker\\Genshin-GetLink.ps1\n"
            "```\n"
            "3. Use `/import <url> game:Genshin Impact` to sync your history."
        )
    else:
        how_to = (
            "You haven't synced your convene history yet.\n\n"
            "How to sync:\n"
            "1. Open Wuthering Waves and view your Convene History in-game.\n"
            "2. Run the PowerShell script to get your URL:\n"
            "```powershell\n"
            'iwr -UseBasicParsing -Headers @{"User-Agent"="Mozilla/5.0"} '
            "https://raw.githubusercontent.com/wuwatracker/wuwatracker/"
            "747a48b1b994baa9c372a4fb933ea7588428bd4b/import.ps1 | iex\n"
            "```\n"
            "3. Use `/import <url> game:Wuthering Waves` to sync your history."
        )
    e = discord.Embed(
        title=f"No {ui['gacha_noun']} History Found",
        description=how_to,
        color=C_GREY
    )
    e.set_footer(text=FOOTER)
    return e

def help_embed() -> discord.Embed:
    e = discord.Embed(
        title="GachaTracker",
        description="Multi-game gacha tracker — Wuthering Waves, Genshin Impact & Honkai: Star Rail.",
        color=C_BLUE
    )
    e.add_field(
        name="Commands",
        value=(
            "`/import <url> [game]`  Sync your gacha history (private, only you see it)\n"
            "`/pity [game]`          Current pity count and guarantee status per banner\n"
            "`/calculate [game]`     Astrite/Primogem cost for your next 5-star (all scenarios)\n"
            "`/stats [game]`         Lifetime pull statistics and currency investment\n"
            "`/history [game] [banner]`  Full 5-star pull log with 50/50 records\n"
            "`/chart [game]`         Generate visual pity distribution graph image\n"
            "`/simulate [game]`      Run 10,000 Monte Carlo simulations to get your Luck Percentile\n"
            "`/profile`               Unified cross-game view with lifetime totals\n"
            "`/banners [game]`        Current + upcoming banners per pool\n"
            "`/bannerset [game]`      Add/update a banner schedule (advanced)\n"
            "`/forget [game]`         Delete your stored data for a game\n"
            "`/ping`                 Bot latency"
        ),
        inline=False
    )
    e.set_footer(text=FOOTER)
    return e

def pity_embed(player_id: str, summary: Dict[str, Dict[str, Any]], game_id: str = DEFAULT_GAME) -> discord.Embed:
    ui = game_ui(game_id)
    cfg = game_config(game_id)
    e = discord.Embed(
        title=f"{ui['gacha_noun']} Pity  Player {player_id}",
        color=C_GOLD
    )

    for pool_id in cfg["pools"]:
        p = summary.get(pool_id, {})
        total = p.get("total_pulls", 0)
        cap = p.get("max_pity", cfg["pity_caps"].get(pool_id, 80))
        # Clamp anomalies (e.g. banner changed mid-cycle) so we never show 92/90
        pity_now = min(p.get("current_pity", 0), cap)
        bar = make_progress_bar(pity_now, cap)

        if pool_id in cfg["5050_pools"]:
            status = "Next 5-star is 100% Guaranteed" if p.get("is_guaranteed") else "Next 5-star is 50/50 Chance"
            status_line = f"Status: {status}\n"
            record = f"Record: {p.get('won_5050', 0)} Won  •  {p.get('lost_5050', 0)} Lost  •  "
        else:
            status_line = "Status: 100% Guaranteed at hard pity (no 50/50 on this banner)\n"
            record = ""

        e.add_field(
            name=p.get("name", f"Banner {pool_id}"),
            value=(
                f"Pity: **{pity_now} / {cap}**  `{bar}`\n"
                f"{status_line}"
                f"{record}Total Pulls: {total}"
            ),
            inline=False
        )

    e.set_footer(text=FOOTER)
    return e

def calculate_embed(player_id: str, summary: Dict[str, Dict[str, Any]], calc: Dict[str, Any],
                    game_id: str = DEFAULT_GAME) -> discord.Embed:
    ui = game_ui(game_id)
    currency = ui["currency"]
    e = discord.Embed(
        title=f"{ui['currency_one']} Cost Calculator  Player {player_id}",
        color=C_GOLD
    )
    g_text = "100% Guaranteed next 5-star" if calc["is_guaranteed"] else "50/50 Chance on next 5-star"
    e.description = f"Current pity: **{calc['current_pity']} / {calc['max_pity']}**  •  Status: **{g_text}**"

    best = calc["best_case"]
    avg = calc["avg_case"]
    worst = calc["worst_case"]

    e.add_field(
        name="Best Case",
        value=f"**{best['pulls']}** {ui['pull_noun']}  •  **{best['astrites']:,}** {currency}",
        inline=True
    )
    e.add_field(
        name="Average Case",
        value=f"**~{avg['pulls']}** {ui['pull_noun_plural']}  •  **{avg['astrites']:,}** {currency}",
        inline=True
    )
    e.add_field(
        name="Worst Case",
        value=f"**{worst['pulls']}** {ui['pull_noun_plural']}  •  **{worst['astrites']:,}** {currency}",
        inline=True
    )

    e.add_field(
        name="Scenario Notes",
        value=worst["note"],
        inline=False
    )

    # Weapon-event banner reference
    weapon_pool = game_config(game_id).get("weapon_pool", "2")
    w = summary.get(weapon_pool, {})
    w_cap = w.get("max_pity", 80)
    w_pity = w.get("current_pity", 0)
    w_rem = max(0, w_cap - w_pity)
    e.add_field(
        name=f"{w.get('name', 'Featured Weapon')} (100% Guaranteed)",
        value=f"Current pity: **{w_pity} / {w_cap}**  •  Max {ui['pull_noun_plural']} needed: **{w_rem}**  •  Max {currency}: **{w_rem * 160:,}**",
        inline=False
    )

    e.set_footer(text=FOOTER)
    return e

def stats_embed(player_id: str, pulls: List[Any], summary: Dict[str, Dict[str, Any]],
                game_id: str = DEFAULT_GAME,
                deep: Optional[Dict[str, Dict[str, Any]]] = None) -> discord.Embed:
    ui = game_ui(game_id)
    cfg = game_config(game_id)
    currency = ui["currency"]
    total_pulls = len(pulls)
    total_currency = total_pulls * 160

    p5_all = [p for p in pulls if p.quality_level == 5]
    p4_all = [p for p in pulls if p.quality_level == 4]
    p3_all = [p for p in pulls if p.quality_level == 3]

    p5_count = len(p5_all)
    p4_count = len(p4_all)

    r5_pct = (p5_count / total_pulls * 100) if total_pulls else 0
    r4_pct = (p4_count / total_pulls * 100) if total_pulls else 0

    featured_pool = cfg["featured_pool"]  # explicit; set iteration order is nondeterministic
    p1 = summary.get(featured_pool, {})
    won_5050 = p1.get("won_5050", 0)
    lost_5050 = p1.get("lost_5050", 0)
    tot_5050 = won_5050 + lost_5050
    win_pct = (won_5050 / tot_5050 * 100) if tot_5050 else 0

    p5_pities = [item["pity"] for item in p1.get("history_5star", [])]
    avg_pity = (sum(p5_pities) / len(p5_pities)) if p5_pities else 0

    e = discord.Embed(
        title=f"{ui['gacha_noun']} Statistics  Player {player_id}",
        color=C_PURPLE
    )

    e.add_field(name="Total Pulls", value=f"**{total_pulls:,}**", inline=True)
    e.add_field(name=f"{ui['currency_one']} Investment", value=f"**{total_currency:,}** {currency}", inline=True)
    e.add_field(name="5-Star Count", value=f"**{p5_count}** ({r5_pct:.2f}%)", inline=True)

    e.add_field(name="4-Star Count", value=f"**{p4_count}** ({r4_pct:.2f}%)", inline=True)
    e.add_field(name="3-Star Count", value=f"**{len(p3_all):,}**", inline=True)
    e.add_field(name="Average 5-Star Pity", value=f"**{avg_pity:.1f}** {ui['pull_noun_plural']}", inline=True)

    e.add_field(
        name="50/50 Performance",
        value=f"Won: **{won_5050}**  •  Lost: **{lost_5050}**  •  Win Rate: **{win_pct:.1f}%**",
        inline=False
    )

    if deep:
        featured = cfg["featured_pool"]
        d = deep.get(featured, {})
        if d.get("count"):
            spread = f"Min **{d['min']}**  •  Median **{d['median']:.0f}**  •  Max **{d['max']}**  •  σ **{d['stddev']:.1f}**"
            quartiles = f"IQR **{d['p25']:.0f}–{d['p75']:.0f}**  •  Early (≤{EARLY_PITY_THRESHOLD}): **{d['early_count']}** of {d['count']}"
            e.add_field(name=f"5★ Pity Distribution ({p1.get('name', 'Featured')})",
                        value=spread + "\n" + quartiles, inline=False)
        if d.get("char_5star") or d.get("weapon_5star"):
            e.add_field(
                name="5★ Type Split (all banners)",
                value=f"Characters: **{d['char_5star']}**  •  Weapons/Cones: **{d['weapon_5star']}**",
                inline=False,
            )

    e.set_footer(text=FOOTER)
    return e

def history_embed(player_id: str, summary: Dict[str, Dict[str, Any]], banner_name: str, p5_history: List[Dict[str, Any]]) -> discord.Embed:
    e = discord.Embed(
        title=f"5-Star History  {banner_name}",
        description=f"Player ID: **{player_id}**",
        color=C_BLUE
    )

    if not p5_history:
        e.description += "\n\nNo 5-star pulls recorded for this banner yet."
    else:
        lines = [f"{'Name':<20} {'Pity':<6} {'Result':<14} {'Date'}"]
        lines.append("─" * 60)
        for h in reversed(p5_history):
            name = h['name'][:19]
            pity = str(h['pity'])
            res = h['result']
            dt = h['time'][:10]
            lines.append(f"{name:<20} {pity:<6} {res:<14} {dt}")

        table = "\n".join(lines)
        e.add_field(
            name="Pull Records",
            value=f"```text\n{table}\n```",
            inline=False
        )

    e.set_footer(text=FOOTER)
    return e
