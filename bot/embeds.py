import discord
from typing import Dict, Any, List

C_BLUE   = 0x4B8DF8
C_GOLD   = 0xE8B84B
C_GREEN  = 0x4CAF7D
C_RED    = 0xE05252
C_PURPLE = 0x9B72CF
C_GREY   = 0x5C6370

FOOTER = "GachaTracker  •  /help for command list"

def make_progress_bar(current: int, total: int, length: int = 10) -> str:
    pct = min(1.0, max(0.0, current / total)) if total > 0 else 0
    filled = int(round(pct * length))
    return "█" * filled + "░" * (length - filled)

def no_data_embed() -> discord.Embed:
    e = discord.Embed(
        title="No Convene History Found",
        description=(
            "You haven't synced your convene history yet.\n\n"
            "How to sync:\n"
            "1. Open Wuthering Waves and view your Convene History in-game.\n"
            "2. Run the PowerShell script to get your URL:\n"
            "```powershell\n"
            'iwr -UseBasicParsing -Headers @{"User-Agent"="Mozilla/5.0"} '
            "https://raw.githubusercontent.com/wuwatracker/wuwatracker/"
            "747a48b1b994baa9c372a4fb933ea7588428bd4b/import.ps1 | iex\n"
            "```\n"
            "3. Use `/import <url>` to sync your history."
        ),
        color=C_GREY
    )
    e.set_footer(text=FOOTER)
    return e

def help_embed() -> discord.Embed:
    e = discord.Embed(
        title="Wuthering Waves Convene Tracker",
        description="A personal gacha history tracker powered by the Kuro Games API.",
        color=C_BLUE
    )
    e.add_field(
        name="Commands",
        value=(
            "`/import <url>`  Sync your convene history (private, only you see it)\n"
            "`/pity`          Current pity count and guarantee status per banner\n"
            "`/calculate`     Astrite cost to get your next 5-star (all scenarios)\n"
            "`/stats`         Lifetime pull statistics and Astrite investment\n"
            "`/history`       Full 5-star pull log with 50/50 records\n"
            "`/chart`         Generate visual pity distribution graph image\n"
            "`/ping`          Bot latency"

        ),
        inline=False
    )
    e.set_footer(text=FOOTER)
    return e

def pity_embed(player_id: str, summary: Dict[str, Dict[str, Any]]) -> discord.Embed:
    e = discord.Embed(
        title=f"Convene Pity  Player {player_id}",
        color=C_GOLD
    )

    p1 = summary.get("1", {})
    bar1 = make_progress_bar(p1.get("current_pity", 0), 80)
    g1 = "Next 5-star is 100% Guaranteed" if p1.get("is_guaranteed") else "Next 5-star is 50/50 Chance"
    e.add_field(
        name="Featured Resonator",
        value=(
            f"Pity: **{p1.get('current_pity', 0)} / 80**  `{bar1}`\n"
            f"Status: {g1}\n"
            f"Record: {p1.get('won_5050', 0)} Won  •  {p1.get('lost_5050', 0)} Lost  •  Total Pulls: {p1.get('total_pulls', 0)}"
        ),
        inline=False
    )

    p2 = summary.get("2", {})
    bar2 = make_progress_bar(p2.get("current_pity", 0), 80)
    e.add_field(
        name="Featured Weapon",
        value=(
            f"Pity: **{p2.get('current_pity', 0)} / 80**  `{bar2}`\n"
            f"Status: 100% Guaranteed (No 50/50 on weapon banner)\n"
            f"Total Pulls: {p2.get('total_pulls', 0)}"
        ),
        inline=False
    )

    p3 = summary.get("3", {})
    bar3 = make_progress_bar(p3.get("current_pity", 0), 80)
    e.add_field(
        name="Standard Resonator",
        value=f"Pity: **{p3.get('current_pity', 0)} / 80**  `{bar3}`  •  Total: {p3.get('total_pulls', 0)}",
        inline=False
    )

    p4 = summary.get("4", {})
    bar4 = make_progress_bar(p4.get("current_pity", 0), 80)
    e.add_field(
        name="Standard Weapon",
        value=f"Pity: **{p4.get('current_pity', 0)} / 80**  `{bar4}`  •  Total: {p4.get('total_pulls', 0)}",
        inline=False
    )

    e.set_footer(text=FOOTER)
    return e

def calculate_embed(player_id: str, summary: Dict[str, Dict[str, Any]], calc: Dict[str, Any]) -> discord.Embed:
    e = discord.Embed(
        title=f"Astrite Cost Calculator  Player {player_id}",
        color=C_GOLD
    )
    g_text = "100% Guaranteed next 5-star" if calc["is_guaranteed"] else "50/50 Chance on next 5-star"
    e.description = f"Current pity: **{calc['current_pity']} / 80**  •  Status: **{g_text}**"

    best = calc["best_case"]
    avg = calc["avg_case"]
    worst = calc["worst_case"]

    e.add_field(
        name="Best Case",
        value=f"**{best['pulls']}** pull  •  **{best['astrites']:,}** Astrites",
        inline=True
    )
    e.add_field(
        name="Average Case",
        value=f"**~{avg['pulls']}** pulls  •  **{avg['astrites']:,}** Astrites",
        inline=True
    )
    e.add_field(
        name="Worst Case",
        value=f"**{worst['pulls']}** pulls  •  **{worst['astrites']:,}** Astrites",
        inline=True
    )

    e.add_field(
        name="Scenario Notes",
        value=worst["note"],
        inline=False
    )

    w_pity = summary.get("2", {}).get("current_pity", 0)
    w_rem = max(0, 80 - w_pity)
    e.add_field(
        name="Featured Weapon (100% Guaranteed)",
        value=f"Current pity: **{w_pity} / 80**  •  Max pulls needed: **{w_rem}**  •  Max Astrites: **{w_rem * 160:,}**",
        inline=False
    )

    e.set_footer(text=FOOTER)
    return e

def stats_embed(player_id: str, pulls: List[Any], summary: Dict[str, Dict[str, Any]]) -> discord.Embed:
    total_pulls = len(pulls)
    total_astrites = total_pulls * 160

    p5_all = [p for p in pulls if p.quality_level == 5]
    p4_all = [p for p in pulls if p.quality_level == 4]
    p3_all = [p for p in pulls if p.quality_level == 3]

    p5_count = len(p5_all)
    p4_count = len(p4_all)

    r5_pct = (p5_count / total_pulls * 100) if total_pulls else 0
    r4_pct = (p4_count / total_pulls * 100) if total_pulls else 0

    p1 = summary.get("1", {})
    won_5050 = p1.get("won_5050", 0)
    lost_5050 = p1.get("lost_5050", 0)
    tot_5050 = won_5050 + lost_5050
    win_pct = (won_5050 / tot_5050 * 100) if tot_5050 else 0

    p5_pities = [item["pity"] for item in p1.get("history_5star", [])]
    avg_pity = (sum(p5_pities) / len(p5_pities)) if p5_pities else 0

    e = discord.Embed(
        title=f"Convene Statistics  Player {player_id}",
        color=C_PURPLE
    )

    e.add_field(name="Total Pulls", value=f"**{total_pulls:,}**", inline=True)
    e.add_field(name="Astrite Investment", value=f"**{total_astrites:,}** Astrites", inline=True)
    e.add_field(name="5-Star Count", value=f"**{p5_count}** ({r5_pct:.2f}%)", inline=True)

    e.add_field(name="4-Star Count", value=f"**{p4_count}** ({r4_pct:.2f}%)", inline=True)
    e.add_field(name="3-Star Count", value=f"**{len(p3_all):,}**", inline=True)
    e.add_field(name="Average 5-Star Pity", value=f"**{avg_pity:.1f}** pulls", inline=True)

    e.add_field(
        name="50/50 Performance",
        value=f"Won: **{won_5050}**  •  Lost: **{lost_5050}**  •  Win Rate: **{win_pct:.1f}%**",
        inline=False
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
