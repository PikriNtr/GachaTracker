import io
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')  # noqa: E402  (must run before pyplot usage; non-interactive backend)

from typing import Any, Dict, List  # noqa: E402

from analytics.pity import DEFAULT_GAME, GAME_BANNER_CONFIGS, calculate_pity_summary
from core.models import Pull

_DARK_FIG = '#1E1F22'
_DARK_AX = '#2B2D31'
_TEXT = '#DBDEE1'
_GRID = '#4E5058'
_EDGE = '#111214'

_RESULT_COLORS = {
    'Won 50/50': '#4CAF7D',
    'Lost 50/50': '#E05252',
    'Guaranteed': '#9B72CF',
    'Ongoing': '#E8B84B',
}


def _parse_time(t: str) -> datetime:
    try:
        return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def _style_dark(fig, ax) -> None:
    fig.patch.set_facecolor(_DARK_FIG)
    ax.set_facecolor(_DARK_AX)
    ax.tick_params(axis='x', colors=_TEXT)
    ax.tick_params(axis='y', colors=_TEXT)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(_GRID)
    ax.spines['left'].set_color(_GRID)


def _save(fig) -> io.BytesIO:
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_pity_chart(pulls: List[Pull], player_id: str, game_id: str = DEFAULT_GAME,
                        game_name: str = "") -> io.BytesIO:
    """Generates a dark-themed bar chart showing pity count for every 5-star pulled.

    Uses the per-game banner config for the featured pool, hard/soft pity
    reference lines, and the chart title.
    """
    cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
    featured_pool = cfg["featured_pool"]
    soft_pity = cfg["soft_pity"]
    hard_pity = cfg["pity_caps"].get(featured_pool, 80)
    banner_name = cfg["names"].get(featured_pool, "Featured Banner")
    game_label = f"  •  {game_name}" if game_name else ""

    summary = calculate_pity_summary(pulls, game_id)
    p1 = summary.get(featured_pool, {})
    history_5star = p1.get("history_5star", [])

    names = [item["name"] for item in history_5star]
    pities = [item["pity"] for item in history_5star]
    results = [item["result"] for item in history_5star]

    current_pity = p1.get("current_pity", 0)
    if current_pity > 0:
        names.append("Current")
        pities.append(current_pity)
        results.append("Ongoing")

    if not names:
        names = ["Current"]
        pities = [current_pity]
        results = ["Ongoing"]

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    _style_dark(fig, ax)

    colors = [_RESULT_COLORS.get(r, '#4B8DF8') for r in results]

    bars = ax.bar(range(len(names)), pities, color=colors, edgecolor=_EDGE, linewidth=1.2, width=0.5)

    ax.axhline(y=soft_pity, color='#E8B84B', linestyle='--', alpha=0.7, label=f'Soft Pity (~{soft_pity})')
    ax.axhline(y=hard_pity, color='#E05252', linestyle=':', alpha=0.7, label=f'Hard Pity ({hard_pity})')

    for bar, pity_val in zip(bars, pities, strict=False):
        height = bar.get_height()
        ax.annotate(f'{pity_val}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha='center', va='bottom', color='#FFFFFF', fontweight='bold', fontsize=9)

    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=20, ha='right', color=_TEXT, fontsize=9)
    ax.set_ylabel('Pity Count', color=_TEXT, fontsize=10, fontweight='bold')
    ax.set_title(f'{banner_name} Pity History{game_label}  •  Player {player_id}', color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)

    ax.set_ylim(0, hard_pity + 15)
    ax.legend(facecolor=_DARK_AX, edgecolor=_GRID, labelcolor=_TEXT, loc='upper left', fontsize=8)

    return _save(fig)


def generate_timeline_chart(pulls: List[Pull], player_id: str, game_id: str = DEFAULT_GAME,
                            game_name: str = "") -> io.BytesIO:
    """Pull timeline: cumulative pulls over time with 5-stars marked at their pity.

    5-star markers are colored by 50/50 result; the featured character pool is used.
    """
    cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
    featured_pool = cfg["featured_pool"]
    banner_name = cfg["names"].get(featured_pool, "Featured Banner")
    game_label = f"  •  {game_name}" if game_name else ""

    pool_pulls = [p for p in pulls if str(p.card_pool_type) == featured_pool]
    pool_pulls = sorted(pool_pulls, key=lambda p: _parse_time(p.time))

    if not pool_pulls:
        pool_pulls = pulls
    chronological = sorted(pool_pulls, key=lambda p: _parse_time(p.time))

    dates = [_parse_time(p.time) for p in chronological]
    cumulative = list(range(1, len(chronological) + 1))

    summary = calculate_pity_summary(chronological, game_id)
    p1 = summary.get(featured_pool, {})

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=150)
    _style_dark(fig, ax)

    ax.plot(dates, cumulative, color='#4B8DF8', linewidth=2, label='Cumulative pulls')

    # Walk the pull list, tracking current pity, to place 5-star markers at (date, cumulative)
    pity = 0
    pity_by_time = {}
    for p in chronological:
        pity += 1
        if p.quality_level == 5:
            pity_by_time[_parse_time(p.time)] = (pity, p.resource_name, p.item_type)
            pity = 0

    plotted = set()
    for p in chronological:
        t = _parse_time(p.time)
        if t in pity_by_time and t not in plotted:
            plotted.add(t)
            pv, name, item_type = pity_by_time[t]
            is_weapon = item_type in ("Weapon", "Light Cone", "Resonator Equipment")
            color = '#9B72CF' if is_weapon else '#E8B84B'
            ax.scatter([t], [cumulative[dates.index(t)]], color=color, s=70,
                       edgecolors=_EDGE, linewidth=1.2, zorder=3)
            ax.annotate(f'{name} ({pv})', xy=(t, cumulative[dates.index(t)]),
                        xytext=(0, 8), textcoords="offset points",
                        ha='center', color='#FFFFFF', fontsize=7.5, rotation=0)

    # ongoing pity marker
    current_pity = p1.get("current_pity", 0)
    if current_pity and dates:
        ax.scatter([dates[-1]], [cumulative[-1]], color='#E8B84B', marker='*',
                   s=160, edgecolors=_EDGE, linewidth=1, zorder=3,
                   label=f'Now (pity {current_pity})')

    ax.set_title(f'{banner_name} Timeline{game_label}  •  Player {player_id}', color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)
    ax.set_ylabel('Cumulative pulls', color=_TEXT, fontsize=10, fontweight='bold')
    ax.legend(facecolor=_DARK_AX, edgecolor=_GRID, labelcolor=_TEXT, loc='upper left', fontsize=8)

    return _save(fig)


def generate_rarity_chart(pulls: List[Pull], player_id: str, game_id: str = DEFAULT_GAME,
                          game_name: str = "") -> io.BytesIO:
    """Rarity distribution: bar chart of pull counts per rarity level."""
    game_label = f"  •  {game_name}" if game_name else ""

    counts: dict[int, int] = {}
    for p in pulls:
        counts[p.quality_level] = counts.get(p.quality_level, 0) + 1

    rarities = sorted(counts)
    values = [counts[r] for r in rarities]
    color_map = {3: '#4B8DF8', 4: '#9B72CF', 5: '#E8B84B'}
    colors = [color_map.get(r, '#4CAF7D') for r in rarities]

    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=150)
    _style_dark(fig, ax)

    bars = ax.bar([f"{r}★" for r in rarities], values, color=colors, edgecolor=_EDGE, linewidth=1.2, width=0.55)

    total = len(pulls)
    for bar, val in zip(bars, values, strict=False):
        height = bar.get_height()
        pct = (val / total * 100) if total else 0
        ax.annotate(f'{val:,}\n({pct:.1f}%)',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4), textcoords="offset points",
                    ha='center', va='bottom', color='#FFFFFF', fontweight='bold', fontsize=9)

    ax.set_title(f'Rarity Distribution{game_label}  •  Player {player_id}', color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)
    ax.set_ylabel('Pulls', color=_TEXT, fontsize=10, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.25 if values else 1)

    return _save(fig)


def generate_banner_comparison_chart(pulls: List[Pull], player_id: str, game_id: str = DEFAULT_GAME,
                                     game_name: str = "") -> io.BytesIO:
    """Banner comparison: total pulls + average 5-star pity per banner."""
    cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
    game_label = f"  •  {game_name}" if game_name else ""

    summary = calculate_pity_summary(pulls, game_id)
    labels: list[str] = []
    totals: list[int] = []
    avg_pities: list[float] = []
    for pool_id in cfg["pools"]:
        p = summary.get(pool_id, {})
        if not p.get("total_pulls"):
            continue
        hist = p.get("history_5star", [])
        avg = (sum(h["pity"] for h in hist) / len(hist)) if hist else 0.0
        labels.append(p.get("name", pool_id))
        totals.append(p["total_pulls"])
        avg_pities.append(avg)

    if not labels:
        labels, totals, avg_pities = ["No data"], [0], [0.0]

    fig, ax = plt.subplots(figsize=(8.5, 4.4), dpi=150)
    _style_dark(fig, ax)

    x = range(len(labels))
    bars = ax.bar(x, totals, color='#4B8DF8', alpha=0.85, edgecolor=_EDGE, linewidth=1.2, width=0.55, label='Total pulls')
    ax.bar_label(bars, padding=3, color='#FFFFFF', fontsize=9, fontweight='bold')

    ax2 = ax.twinx()
    ax2.plot(x, avg_pities, color='#E8B84B', marker='o', linewidth=2, markersize=7,
             markeredgecolor=_EDGE, markeredgewidth=1, label='Avg 5★ pity')
    for xi, av in zip(x, avg_pities, strict=False):
        if av:
            ax2.annotate(f'{av:.0f}', xy=(xi, av), xytext=(0, 7), textcoords="offset points",
                         ha='center', color='#E8B84B', fontsize=9, fontweight='bold')
    ax2.set_ylabel('Avg 5★ pity', color='#E8B84B', fontsize=10, fontweight='bold')
    ax2.tick_params(axis='y', colors='#E8B84B')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_color(_GRID)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=15, ha='right', color=_TEXT, fontsize=8.5)
    ax.set_ylabel('Total pulls', color=_TEXT, fontsize=10, fontweight='bold')
    ax.set_title(f'Banner Comparison{game_label}  •  Player {player_id}', color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, facecolor=_DARK_AX, edgecolor=_GRID,
              labelcolor=_TEXT, loc='upper right', fontsize=8)

    return _save(fig)


def generate_banner_schedule_chart(windows: List[Dict[str, Any]], player_id: str,
                                   game_id: str = DEFAULT_GAME, game_name: str = "") -> io.BytesIO:
    """Gantt-style chart of the crowdsourced banner schedule for one game.

    `windows` is the list from Repository.get_banner_windows(game_id): dicts with
    card_pool_type, banner_name, start_time, end_time (canonical timestamps).
    One row per pool (banner-config order), one bar per scheduled window,
    colored by banner name; a dashed 'Now' line marks the current UTC time.
    """
    cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
    game_label = f"  •  {game_name}" if game_name else ""

    if not windows:
        fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
        _style_dark(fig, ax)
        ax.text(0.5, 0.5, "No banner schedule recorded yet — use /bannerset",
                ha='center', va='center', color=_TEXT, fontsize=11, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return _save(fig)

    pool_names = {str(pid): cfg["names"].get(str(pid), f"Pool {pid}") for pid in cfg["pools"]}
    # Y rows: one per configured pool (config order); unknown pools appended.
    y_labels: list[str] = []
    for pid in cfg["pools"]:
        y_labels.append(pool_names[str(pid)])
    extra = sorted({str(w["card_pool_type"]) for w in windows} - set(pool_names))
    y_labels.extend(f"Pool {e}" for e in extra)
    y_pos = {label: i for i, label in enumerate(y_labels)}
    label_by_pool = {**pool_names, **{e: f"Pool {e}" for e in extra}}

    fig, ax = plt.subplots(figsize=(9, max(4.2, 0.55 * len(y_labels) + 1.6)), dpi=150)
    _style_dark(fig, ax)

    colors = ['#4B8DF8', '#9B72CF', '#E8B84B', '#4CAF7D', '#E05252', '#FF9F1C', '#2EC4B6']
    color_pool = {label: colors[i % len(colors)] for i, label in enumerate(y_labels)}

    now = datetime.utcnow()
    for w in windows:
        pid = str(w["card_pool_type"])
        start, end = _parse_time(w["start_time"]), _parse_time(w["end_time"])
        if start is datetime.min or end is datetime.min or end <= start:
            continue
        label = label_by_pool.get(pid, f"Pool {pid}")
        name = str(w["banner_name"])
        ax.barh(y_pos[label], width=end - start, left=start, height=0.62,
                color=color_pool[label], edgecolor=_EDGE, linewidth=1.1, alpha=0.92)
        mid = start + (end - start) / 2
        ax.text(mid, y_pos[label], name[:36], ha='center', va='center',
                color='#FFFFFF', fontsize=8, fontweight='bold')

    ax.axvline(now, color='#E8B84B', linestyle='--', linewidth=1.8, alpha=0.9, label='Now (UTC)')

    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(y_labels, color=_TEXT, fontsize=9)
    ax.invert_yaxis()  # first configured pool on top
    ax.grid(True, axis='x', color=_GRID, alpha=0.3)
    ax.set_title(f'Banner Schedule{game_label}  •  Player {player_id}',
                 color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)
    ax.legend(facecolor=_DARK_AX, edgecolor=_GRID, labelcolor=_TEXT, loc='upper left', fontsize=8)

    return _save(fig)


def generate_profile_chart(profile: dict, player_id: str) -> io.BytesIO:
    """Multi-game profile visual: grouped bars per game (pulls, 5-stars) +
    featured-pity progress markers. `profile` is the dict from
    analytics.profile.unified_profile()."""
    games = profile.get("games", {})
    if not games:
        fig, ax = plt.subplots(figsize=(7, 3), dpi=150)
        _style_dark(fig, ax)
        ax.text(0.5, 0.5, "No gacha data yet — use /import first",
                ha='center', va='center', color=_TEXT, fontsize=11, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return _save(fig)

    order = [gid for gid in ("wuthering_waves", "genshin_impact", "honkai_star_rail") if gid in games]
    display = {"wuthering_waves": "WuWa", "genshin_impact": "Genshin", "honkai_star_rail": "HSR"}

    labels = [display.get(gid, gid) for gid in order]
    totals = [games[gid]["total_pulls"] for gid in order]
    fives = [games[gid]["count_5"] for gid in order]
    pities = [games[gid]["featured_pity"] for gid in order]
    caps = [games[gid]["featured_cap"] for gid in order]

    fig, ax = plt.subplots(figsize=(8.5, 4.4), dpi=150)
    _style_dark(fig, ax)

    x = range(len(order))
    width = 0.38
    bars1 = ax.bar([i - width / 2 for i in x], totals, width, color='#4B8DF8',
                   edgecolor=_EDGE, linewidth=1.2, label='Total pulls')
    bars2 = ax.bar([i + width / 2 for i in x], fives, width, color='#E8B84B',
                   edgecolor=_EDGE, linewidth=1.2, label='5-stars')

    ax.bar_label(bars1, padding=3, color='#FFFFFF', fontsize=9, fontweight='bold')
    ax.bar_label(bars2, padding=3, color='#E8B84B', fontsize=9, fontweight='bold')

    # featured pity annotation under each game label
    for i, (gid, pity, cap) in enumerate(zip(order, pities, caps, strict=False)):
        status = " ★guaranteed" if games[gid]["is_guaranteed"] else ""
        ax.annotate(f"{display.get(gid, gid)} featured: {pity}/{cap}{status}",
                    xy=(i, 0), xytext=(0, -34), textcoords="offset points",
                    ha='center', color='#9B72CF', fontsize=8.5)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, color=_TEXT, fontsize=10)
    ax.tick_params(axis='x', pad=22)  # room for the pity annotations
    ax.set_ylabel('Count', color=_TEXT, fontsize=10, fontweight='bold')
    ax.set_ylim(0, max(totals) * 1.2 if totals else 1)
    ax.set_title(f'Cross-Game Profile  •  Player {player_id}', color='#FFFFFF',
                 fontsize=11, fontweight='bold', pad=12)
    ax.legend(facecolor=_DARK_AX, edgecolor=_GRID, labelcolor=_TEXT, loc='upper right', fontsize=8)

    return _save(fig)
