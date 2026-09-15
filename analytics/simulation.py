import io
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple
from core.models import Pull
from analytics.pity import calculate_pity_summary, GAME_BANNER_CONFIGS, DEFAULT_GAME

# Per-game base probability models for the Monte Carlo engine.
# base          : 5★ chance per pull before soft pity
# soft_start    : pull number where the rate starts ramping
# soft_step     : rate added per pull after soft_start
# cap           : hard pity (guaranteed 5★)
# Mirrors community-measured/official models:
#   WuWa: base 0.8%, soft ~61, +5%/pull, cap 80
#   Genshin / HSR: base 0.6%, soft 74, +6%/pull, cap 90
PROBABILITY_MODELS = {
    "wuthering_waves": {"base": 0.008, "soft_start": 61, "soft_step": 0.05, "cap": 80},
    "genshin_impact":  {"base": 0.006, "soft_start": 74, "soft_step": 0.06, "cap": 90},
    "honkai_star_rail": {"base": 0.006, "soft_start": 74, "soft_step": 0.06, "cap": 90},
}


def _model_for(game_id: str) -> Dict[str, Any]:
    return PROBABILITY_MODELS.get(game_id, PROBABILITY_MODELS[DEFAULT_GAME])


def _pull_probability(model: Dict[str, Any], pity: int) -> float:
    if pity >= model["cap"]:
        return 1.0
    if pity >= model["soft_start"]:
        return model["base"] + (pity - model["soft_start"] + 1) * model["soft_step"]
    return model["base"]


def run_monte_carlo_simulation(pulls: List[Pull], num_sims: int = 10000,
                               game_id: str = DEFAULT_GAME) -> Dict[str, Any]:
    """Runs Monte Carlo gacha simulations and calculates user's statistical luck percentile.

    Uses the per-game probability model (base rate, soft-pity ramp, hard pity cap).
    """
    summary = calculate_pity_summary(pulls, game_id)
    cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
    featured_pool = cfg["featured_pool"]  # explicit; never derive from a set (hash order varies)
    rateup_chance = float(cfg.get("rateup_chance", 0.5))
    model = _model_for(game_id)

    p1 = summary.get(featured_pool, {})
    history_5star = p1.get("history_5star", [])

    user_total_pulls = p1.get("total_pulls", len(pulls))
    user_5star_count = len(history_5star)
    user_won_5050 = p1.get("won_5050", 0)
    user_lost_5050 = p1.get("lost_5050", 0)

    p5_pities = [item["pity"] for item in history_5star]
    user_avg_pity = (sum(p5_pities) / len(p5_pities)) if p5_pities else p1.get("current_pity", 0)

    target_featured = max(1, user_won_5050 + (1 if p1.get("is_guaranteed") else 0))

    sim_total_pulls = []
    sim_avg_pities = []

    t0 = time.time()
    for _ in range(num_sims):
        featured = 0
        guaranteed = False
        pity = 0
        p_count = 0
        player_pities = []

        while featured < target_featured:
            p_count += 1
            pity += 1
            prob = _pull_probability(model, pity)

            if np.random.random() < prob:
                player_pities.append(pity)
                if guaranteed or np.random.random() < rateup_chance:
                    featured += 1
                    guaranteed = False
                else:
                    guaranteed = True
                pity = 0

        sim_total_pulls.append(p_count)
        sim_avg_pities.append(sum(player_pities) / len(player_pities) if player_pities else float(model["cap"]))

    t1 = time.time()
    sim_avg_pities = np.array(sim_avg_pities)
    sim_total_pulls = np.array(sim_total_pulls)

    # Calculate percentile: % of simulated players with WORSE (higher) average pity than user
    if user_avg_pity > 0:
        luck_percentile = float((sim_avg_pities > user_avg_pity).mean() * 100.0)
    else:
        luck_percentile = 50.0

    if luck_percentile >= 95:
        rating = "Legendary Luck (Top 5%)"
    elif luck_percentile >= 80:
        rating = "Extremely Lucky (Top 20%)"
    elif luck_percentile >= 60:
        rating = "Above Average Luck"
    elif luck_percentile >= 40:
        rating = "Average / Balanced Luck"
    elif luck_percentile >= 20:
        rating = "Below Average Luck"
    elif luck_percentile >= 5:
        rating = "Unlucky (Bottom 20%)"
    else:
        rating = "Unfortunate (Bottom 5%)"

    return {
        "num_simulations": num_sims,
        "game_id": game_id,
        "elapsed_sec": round(t1 - t0, 3),
        "user_avg_pity": user_avg_pity,
        "user_5star_count": user_5star_count,
        "user_won_5050": user_won_5050,
        "user_lost_5050": user_lost_5050,
        "luck_percentile": round(luck_percentile, 1),
        "luck_rating": rating,
        "sim_mean_pity": round(float(sim_avg_pities.mean()), 1),
        "sim_median_pity": round(float(np.median(sim_avg_pities)), 1),
        "sim_avg_pities": sim_avg_pities,
    }

def generate_simulation_chart(sim_results: Dict[str, Any], player_id: str,
                              game_name: str = "") -> io.BytesIO:
    """Generates a dark-themed Monte Carlo simulation distribution graph with user position marker."""
    sim_pities = sim_results["sim_avg_pities"]
    user_avg = sim_results["user_avg_pity"]
    percentile = sim_results["luck_percentile"]

    game_label = f"  •  {game_name}" if game_name else ""

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    fig.patch.set_facecolor('#1E1F22')
    ax.set_facecolor('#2B2D31')

    n, bins, patches = ax.hist(sim_pities, bins=30, color='#4B8DF8', alpha=0.7, edgecolor='#111214', linewidth=1)

    # Highlight user's position
    ax.axvline(x=user_avg, color='#E8B84B', linestyle='--', linewidth=2.5, label=f'YOU ({user_avg:.1f} pity)')

    ax.annotate(
        f'YOU ARE HERE\n{percentile}% Luckier than average',
        xy=(user_avg, max(n) * 0.75),
        xytext=(user_avg + 5, max(n) * 0.85),
        arrowprops=dict(facecolor='#E8B84B', edgecolor='#E8B84B', shrink=0.05, width=1.5, headwidth=6),
        color='#FFFFFF', fontweight='bold', fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="#111214", ec="#E8B84B", lw=1)
    )

    ax.set_title(f'Monte Carlo Pity Distribution (10,000 Players){game_label}  •  Player {player_id}', color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)
    ax.set_xlabel('Average Pity per 5-Star', color='#DBDEE1', fontsize=10, fontweight='bold')
    ax.set_ylabel('Number of Simulated Players', color='#DBDEE1', fontsize=10, fontweight='bold')

    ax.tick_params(axis='x', colors='#DBDEE1')
    ax.tick_params(axis='y', colors='#DBDEE1')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#4E5058')
    ax.spines['left'].set_color('#4E5058')

    ax.legend(facecolor='#2B2D31', edgecolor='#4E5058', labelcolor='#DBDEE1', loc='upper left', fontsize=9)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf
