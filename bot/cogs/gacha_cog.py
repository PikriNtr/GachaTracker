from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from analytics import (
    DEFAULT_GAME,
    GAME_BANNER_CONFIGS,
    calculate_astrite_cost,
    calculate_pity_summary,
    get_game_banner_names,
)
from bot.embeds import (
    C_GOLD,
    C_GREEN,
    C_RED,
    FOOTER,
    calculate_embed,
    history_embed,
    no_data_embed,
    pity_embed,
    stats_embed,
)
from core.registry import registry
from database import Repository

repo = Repository()

# Shared game selector for all commands (kept in sync with games/ plugins)
GAME_CHOICES = [
    app_commands.Choice(name="Wuthering Waves", value="wuthering_waves"),
    app_commands.Choice(name="Genshin Impact", value="genshin_impact"),
    app_commands.Choice(name="Honkai: Star Rail", value="honkai_star_rail"),
]


def _plugin_for(game_id: str):
    return registry.get(game_id)


class GachaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    async def _resolve_game(self, interaction: discord.Interaction, game_id: str, ephemeral: bool = False):
        """Returns the plugin for game_id, or sends an error embed and returns None."""
        plugin = _plugin_for(game_id)
        if plugin is None:
            e = discord.Embed(
                title="Unknown Game",
                description=f"No plugin registered for game `{game_id}`.",
                color=C_RED,
            )
            e.set_footer(text=FOOTER)
            if interaction.response.is_done():
                await interaction.followup.send(embed=e, ephemeral=ephemeral)
            else:
                await interaction.response.send_message(embed=e, ephemeral=ephemeral)
        return plugin

    async def _load_account(self, interaction: discord.Interaction, game_id: str, ephemeral: bool = False):
        """Returns (account, pulls) or (None, None) after sending the no-data embed."""
        discord_id = str(interaction.user.id)
        account = repo.get_account_by_discord_id(discord_id, game_id)
        pulls = repo.get_pulls(discord_id, game_id)
        if not account or not pulls:
            e = no_data_embed(game_id)
            if interaction.response.is_done():
                await interaction.followup.send(embed=e, ephemeral=ephemeral)
            else:
                await interaction.response.send_message(embed=e, ephemeral=ephemeral)
            return None, None
        return account, pulls

    # ------------------------------------------------------------------
    # /import
    # ------------------------------------------------------------------
    @app_commands.command(name="import", description="Sync your gacha history using your import URL (private)")
    @app_commands.describe(
        game="Which game's history to import",
        url="Your gacha history URL (WuWa: Convene URL / Genshin: Wish URL)"
    )
    @app_commands.choices(game=GAME_CHOICES)
    async def import_cmd(self, interaction: discord.Interaction, url: str,
                         game: Optional[app_commands.Choice[str]] = None):
        # Ephemeral response for user privacy
        await interaction.response.defer(ephemeral=True)
        game_id = game.value if game else "wuthering_waves"

        plugin = await self._resolve_game(interaction, game_id, ephemeral=True)
        if plugin is None:
            return
        discord_id = str(interaction.user.id)

        try:
            player_id, pulls = await plugin.fetch_and_parse(url)
            if not pulls:
                embed = discord.Embed(
                    title="Import Failed",
                    description="No gacha records were returned. Please make sure you viewed your history in-game before copying the URL.",
                    color=C_RED
                )
                embed.set_footer(text=FOOTER)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
            featured_pool = cfg["featured_pool"]

            # Snapshot BEFORE: totals from what's already stored.
            # All displayed numbers are recomputed from the merged, deduplicated
            # history — never accumulated across imports.
            old_pulls = repo.get_pulls(discord_id, game_id)
            old_summary = calculate_pity_summary(old_pulls, game_id) if old_pulls else {}
            old_total = len(old_pulls)
            old_5star = sum(len(s.get("history_5star", [])) for s in old_summary.values())
            old_4star = sum(1 for p in old_pulls if p.quality_level == 4)
            p_old = old_summary.get(featured_pool, {})

            repo.save_account(discord_id=discord_id, game_id=game_id, player_id=player_id)
            new_count = repo.save_pulls(discord_id=discord_id, game_id=game_id, player_id=player_id, pulls=pulls)

            # State AFTER: from the full merged history in the DB.
            all_db_pulls = repo.get_pulls(discord_id, game_id)
            summary = calculate_pity_summary(all_db_pulls, game_id)
            p1 = summary.get(featured_pool, {})
            total_db = len(all_db_pulls)
            new_5star = sum(len(s.get("history_5star", [])) for s in summary.values())
            new_4star = sum(1 for p in all_db_pulls if p.quality_level == 4)

            delta_5 = new_5star - old_5star
            delta_4 = new_4star - old_4star
            cap = p1.get("max_pity", 80)
            guaranteed_str = " ✅ Guaranteed" if p1.get("is_guaranteed") else ""

            if new_count == 0:
                description = (
                    f"Player ID: **{player_id}**\n"
                    f"Already up to date — no new pulls found.\n\n"
                    f"Total recorded pulls: **{total_db}**\n"
                    f"Current {p1.get('name', 'Featured')} Pity: **{p1.get('current_pity', 0)} / {cap}**{guaranteed_str}"
                )
            else:
                # Deltas: strictly what changed since the last import
                pity_line = f"Current {p1.get('name', 'Featured')} Pity: **{p1.get('current_pity', 0)} / {cap}**{guaranteed_str}"
                if old_total > 0:
                    old_pity = p_old.get("current_pity", 0)
                    pity_line = (
                        f"{p1.get('name', 'Featured')} Pity: **{old_pity} → {p1.get('current_pity', 0)} / {cap}**"
                        f" (+{p1.get('current_pity', 0) - old_pity}){guaranteed_str}"
                    )
                w5050_delta = (p1.get("won_5050", 0) - p_old.get("won_5050", 0),
                               p1.get("lost_5050", 0) - p_old.get("lost_5050", 0))
                fifty_line = ""
                if w5050_delta != (0, 0):
                    fifty_line = f"\n50/50 since last sync: **{w5050_delta[0]} Won** / **{w5050_delta[1]} Lost**"

                description = (
                    f"Player ID: **{player_id}**\n"
                    f"New pulls imported: **{new_count}**\n\n"
                    f"Total pulls: **{old_total:,} → {total_db:,}**\n"
                    f"New 5-stars: **{delta_5}**  •  New 4-stars: **{delta_4}**\n"
                    f"{pity_line}"
                    f"{fifty_line}"
                )

            embed = discord.Embed(
                title=f"{plugin.name} History Synced Successfully",
                description=description,
                color=C_GREEN
            )
            embed.set_footer(text=FOOTER)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="Import Failed",
                description=f"Error: `{str(e)}`",
                color=C_RED
            )
            embed.set_footer(text=FOOTER)
            await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /pity
    # ------------------------------------------------------------------
    @app_commands.command(name="pity", description="Check current pity count and guarantee status per banner")
    @app_commands.describe(game="Which game to check")
    @app_commands.choices(game=GAME_CHOICES)
    async def pity_cmd(self, interaction: discord.Interaction,
                       game: Optional[app_commands.Choice[str]] = None):
        game_id = game.value if game else "wuthering_waves"
        account, pulls = await self._load_account(interaction, game_id)
        if not account:
            return

        summary = calculate_pity_summary(pulls, game_id)
        embed = pity_embed(account.player_id, summary, game_id)
        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /calculate
    # ------------------------------------------------------------------
    @app_commands.command(name="calculate", description="Calculate pull cost and 50/50 scenarios for your next 5-star")
    @app_commands.describe(game="Which game to check")
    @app_commands.choices(game=GAME_CHOICES)
    async def calculate_cmd(self, interaction: discord.Interaction,
                            game: Optional[app_commands.Choice[str]] = None):
        game_id = game.value if game else "wuthering_waves"
        account, pulls = await self._load_account(interaction, game_id)
        if not account:
            return

        summary = calculate_pity_summary(pulls, game_id)
        featured_pool = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])["featured_pool"]
        p1 = summary.get(featured_pool, {})
        calc = calculate_astrite_cost(p1.get("current_pity", 0), p1.get("is_guaranteed", False),
                                      max_pity=p1.get("max_pity", 80), game_id=game_id)
        embed = calculate_embed(account.player_id, summary, calc, game_id)
        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /stats
    # ------------------------------------------------------------------
    @app_commands.command(name="stats", description="View lifetime pull statistics and currency investment")
    @app_commands.describe(game="Which game to check")
    @app_commands.choices(game=GAME_CHOICES)
    async def stats_cmd(self, interaction: discord.Interaction,
                        game: Optional[app_commands.Choice[str]] = None):
        game_id = game.value if game else "wuthering_waves"
        account, pulls = await self._load_account(interaction, game_id)
        if not account:
            return

        summary = calculate_pity_summary(pulls, game_id)
        embed = stats_embed(account.player_id, pulls, summary, game_id)
        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /history
    # ------------------------------------------------------------------
    @app_commands.command(name="history", description="View full 5-star pull log and 50/50 records")
    @app_commands.describe(game="Which game to check", banner="Select banner to view 5-star log")
    @app_commands.choices(game=GAME_CHOICES)
    async def history_cmd(self, interaction: discord.Interaction,
                          game: Optional[app_commands.Choice[str]] = None,
                          banner: Optional[str] = None):
        game_id = game.value if game else "wuthering_waves"
        account, pulls = await self._load_account(interaction, game_id)
        if not account:
            return

        summary = calculate_pity_summary(pulls, game_id)
        names = get_game_banner_names(game_id)
        cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
        if banner is None:
            banner = cfg["featured_pool"]
        banner = str(banner).strip()
        if banner not in cfg["pools"]:
            e = discord.Embed(
                title="Unknown Banner",
                description=f"Banner `{banner}` is not valid for this game. Valid: {', '.join(cfg['pools'])}",
                color=C_RED,
            )
            e.set_footer(text=FOOTER)
            await interaction.response.send_message(embed=e)
            return
        b_info = summary.get(banner, {})
        b_name = names.get(banner, f"Banner {banner}")
        p5_hist = b_info.get("history_5star", [])

        embed = history_embed(account.player_id, summary, b_name, p5_hist)
        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /chart
    # ------------------------------------------------------------------
    @app_commands.command(name="chart", description="Generate a visual pity distribution graph for your 5-star pulls")
    @app_commands.describe(game="Which game to check")
    @app_commands.choices(game=GAME_CHOICES)
    async def chart_cmd(self, interaction: discord.Interaction,
                        game: Optional[app_commands.Choice[str]] = None):
        await interaction.response.defer()
        game_id = game.value if game else "wuthering_waves"
        account, pulls = await self._load_account(interaction, game_id, ephemeral=False)
        if not account:
            return

        from analytics import generate_pity_chart
        plugin = _plugin_for(game_id)
        chart_buf = generate_pity_chart(pulls, account.player_id, game_id,
                                        plugin.name if plugin else "")
        file = discord.File(fp=chart_buf, filename="pity_chart.png")

        embed = discord.Embed(
            title=f"Pity Distribution Graph  Player {account.player_id}",
            description="Green = Won 50/50  •  Red = Lost 50/50  •  Gold = Ongoing Pity",
            color=C_GREEN
        )
        embed.set_image(url="attachment://pity_chart.png")
        embed.set_footer(text=FOOTER)

        await interaction.followup.send(embed=embed, file=file)

    # ------------------------------------------------------------------
    # /simulate
    # ------------------------------------------------------------------
    @app_commands.command(name="simulate", description="Run 10,000 Monte Carlo simulations to calculate your statistical luck percentile")
    @app_commands.describe(game="Which game to check")
    @app_commands.choices(game=GAME_CHOICES)
    async def simulate_cmd(self, interaction: discord.Interaction,
                           game: Optional[app_commands.Choice[str]] = None):
        await interaction.response.defer()
        game_id = game.value if game else "wuthering_waves"
        account, pulls = await self._load_account(interaction, game_id, ephemeral=False)
        if not account:
            return

        from analytics import generate_simulation_chart, run_monte_carlo_simulation
        plugin = _plugin_for(game_id)
        sim_res = run_monte_carlo_simulation(pulls, num_sims=10000, game_id=game_id)
        chart_buf = generate_simulation_chart(sim_res, account.player_id,
                                              plugin.name if plugin else "")
        file = discord.File(fp=chart_buf, filename="simulation_chart.png")

        pct = sim_res["luck_percentile"]
        rating = sim_res["luck_rating"]
        u_avg = sim_res["user_avg_pity"]
        s_avg = sim_res["sim_mean_pity"]
        from bot.embeds import game_ui
        pull_plural = game_ui(game_id)["pull_noun_plural"]

        embed = discord.Embed(
            title=f"Monte Carlo Luck Analysis  Player {account.player_id}",
            description=f"Rating: **{rating}**",
            color=C_GREEN if pct >= 50 else C_GOLD
        )
        embed.add_field(
            name="Luck Percentile",
            value=f"**{pct}%** luckier than simulated players",
            inline=True
        )
        embed.add_field(
            name="Your Avg Pity",
            value=f"**{u_avg:.1f}** {pull_plural} / 5-star",
            inline=True
        )
        embed.add_field(
            name="Simulated Avg Pity",
            value=f"**{s_avg:.1f}** {pull_plural} / 5-star",
            inline=True
        )
        embed.add_field(
            name="50/50 Performance",
            value=f"Won: **{sim_res['user_won_5050']}**  •  Lost: **{sim_res['user_lost_5050']}**",
            inline=False
        )
        embed.add_field(
            name="Simulation Scope",
            value=f"Evaluated across **10,000** simulated player histories in **{sim_res['elapsed_sec']}s**.",
            inline=False
        )
        embed.set_image(url="attachment://simulation_chart.png")
        embed.set_footer(text=FOOTER)

        await interaction.followup.send(embed=embed, file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(GachaCog(bot))

