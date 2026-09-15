import io

import matplotlib

matplotlib.use('Agg')
from typing import List

import matplotlib.pyplot as plt

from analytics.pity import DEFAULT_GAME, GAME_BANNER_CONFIGS, calculate_pity_summary
from core.models import Pull


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
    fig.patch.set_facecolor('#1E1F22')
    ax.set_facecolor('#2B2D31')

    colors = []
    for r in results:
        if r == "Won 50/50":
            colors.append('#4CAF7D')  # Green
        elif r == "Lost 50/50":
            colors.append('#E05252')  # Red
        elif r == "Ongoing":
            colors.append('#E8B84B')  # Gold
        else:
            colors.append('#4B8DF8')  # Blue

    bars = ax.bar(range(len(names)), pities, color=colors, edgecolor='#111214', linewidth=1.2, width=0.5)

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
    ax.set_xticklabels(names, rotation=20, ha='right', color='#DBDEE1', fontsize=9)
    ax.tick_params(axis='y', colors='#DBDEE1')
    ax.set_ylabel('Pity Count', color='#DBDEE1', fontsize=10, fontweight='bold')
    ax.set_title(f'{banner_name} Pity History{game_label}  •  Player {player_id}', color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)

    ax.set_ylim(0, hard_pity + 15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#4E5058')
    ax.spines['left'].set_color('#4E5058')
    ax.legend(facecolor='#2B2D31', edgecolor='#4E5058', labelcolor='#DBDEE1', loc='upper left', fontsize=8)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf
