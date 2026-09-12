import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import List
from core.models import Pull
from analytics.pity import calculate_pity_summary

def generate_pity_chart(pulls: List[Pull], player_id: str) -> io.BytesIO:
    """Generates a dark-themed bar chart showing pity count for every 5-star pulled."""
    summary = calculate_pity_summary(pulls)
    p1 = summary.get("1", {})
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

    ax.axhline(y=62, color='#E8B84B', linestyle='--', alpha=0.7, label='Soft Pity (~62)')
    ax.axhline(y=80, color='#E05252', linestyle=':', alpha=0.7, label='Hard Pity (80)')

    for bar, pity_val in zip(bars, pities):
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
    ax.set_title(f'Featured Resonator Pity History  •  Player {player_id}', color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)

    ax.set_ylim(0, 95)
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
