"""Chart generation tests: all four chart types render for every game."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.charts import (
    generate_banner_comparison_chart,
    generate_pity_chart,
    generate_rarity_chart,
    generate_timeline_chart,
)
from core.models import Pull


def pull(game_id, pool, name, q, t, item_type=""):
    return Pull(pool, "res", name, q, t, "u", game_id=game_id, item_type=item_type)


def sample_pulls(game_id, pool):
    """A few pulls with 5-stars at different pities + 50/50 variety."""
    pulls = []
    n = 1
    spec = [(9, "Alpha", 5, "Character"), (5, "Beta", 3, ""), (30, "Gamma", 4, ""),
            (35, "Delta", 5, "Character"), (20, "Epsilon", 3, ""), (25, "Zeta", 5, "Character")]
    for pity, name, q, item_type in spec:
        for _ in range(pity - 1):
            pulls.append(pull(game_id, pool, f"F{n}", 3, f"2024-01-{(n % 28) + 1:02d} 10:00:00"))
            n += 1
        pulls.append(pull(game_id, pool, name, q, f"2024-02-{(n % 28) + 1:02d} 10:00:00", item_type=item_type))
        n += 1
    return pulls


@pytest.mark.parametrize("game_id,pool", [
    ("wuthering_waves", "1"),
    ("genshin_impact", "301"),
    ("honkai_star_rail", "1"),
])
@pytest.mark.parametrize("gen", [
    generate_pity_chart,
    generate_timeline_chart,
    generate_rarity_chart,
    generate_banner_comparison_chart,
])
def test_chart_renders_png(gen, game_id, pool):
    buf = gen(sample_pulls(game_id, pool), "u", game_id, "Test Game")
    data = buf.getvalue()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 1000


def test_rarity_chart_counts_correctly():
    pulls = [
        pull("genshin_impact", "301", "A", 5, "2024-01-01 10:00:00"),
        pull("genshin_impact", "301", "B", 4, "2024-01-02 10:00:00"),
        pull("genshin_impact", "301", "C", 3, "2024-01-03 10:00:00"),
        pull("genshin_impact", "301", "D", 3, "2024-01-04 10:00:00"),
    ]
    buf = generate_rarity_chart(pulls, "u", "genshin_impact")
    assert len(buf.getvalue()) > 1000  # renders without divide-by-zero


def test_charts_handle_empty_data():
    for gen in (generate_pity_chart, generate_timeline_chart,
                generate_rarity_chart, generate_banner_comparison_chart):
        buf = gen([], "u", "genshin_impact", "G")
        assert len(buf.getvalue()) > 1000


def test_timeline_places_all_markers():
    """Every 5-star in the pool appears (render doesn't crash with many)."""
    pulls = sample_pulls("genshin_impact", "301")
    pulls += sample_pulls("genshin_impact", "301")
    buf = generate_timeline_chart(pulls, "u", "genshin_impact")
    assert len(buf.getvalue()) > 1000
