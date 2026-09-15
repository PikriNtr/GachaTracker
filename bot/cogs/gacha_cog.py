from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from analytics import (
    DEFAULT_GAME,
    GAME_BANNER_CONFIGS,
    GAME_DISPLAY_NAMES,
    GAME_ORDER,
    calculate_astrite_cost,
    calculate_deep_statistics,
    calculate_pity_summary,
    get_game_banner_names,
    unified_profile,
)
from bot.embeds import (
    C_GOLD,
    C_GREEN,
    C_GREY,
    C_PURPLE,
    C_RED,
    FOOTER,
    calculate_embed,
    history_embed,
    make_progress_bar,
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


class ForgetConfirmView(discord.ui.View):
    """Ephemeral confirm/cancel for /forget. Only the invoker can click."""

    def __init__(self, invoker_id: int):
        super().__init__(timeout=30)
        self.invoker_id = invoker_id
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message("This confirmation isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Delete my data", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        button.disabled = True
        self.cancel_button.disabled = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        self.confirm.disabled = True
        await interaction.response.defer()
        self.stop()


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
        deep = calculate_deep_statistics(pulls, game_id)
        embed = stats_embed(account.player_id, pulls, summary, game_id, deep=deep)
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
    # /forget
    # ------------------------------------------------------------------
    @app_commands.command(name="forget", description="Delete your stored gacha data for a game (private, irreversible)")
    @app_commands.describe(game="Which game's data to delete")
    @app_commands.choices(game=GAME_CHOICES)
    async def forget_cmd(self, interaction: discord.Interaction,
                         game: Optional[app_commands.Choice[str]] = None):
        game_id = game.value if game else "wuthering_waves"
        plugin = await self._resolve_game(interaction, game_id, ephemeral=True)
        if plugin is None:
            return

        discord_id = str(interaction.user.id)
        account = repo.get_account_by_discord_id(discord_id, game_id)
        pulls = repo.get_pulls(discord_id, game_id)
        if not account or not pulls:
            e = discord.Embed(
                title="Nothing to Delete",
                description=f"You have no stored {plugin.name} data.",
                color=C_GREY,
            )
            e.set_footer(text=FOOTER)
            await interaction.response.send_message(embed=e, ephemeral=True)
            return

        view = ForgetConfirmView(interaction.user.id)
        e = discord.Embed(
            title=f"Delete {plugin.name} Data?",
            description=(
                f"This permanently removes **{len(pulls):,}** pulls and your account link "
                f"for {plugin.name}.\n\n**This cannot be undone.**"
            ),
            color=C_RED,
        )
        e.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=e, view=view, ephemeral=True)

        await view.wait()
        if view.confirmed:
            removed = repo.delete_user_data(discord_id, game_id)
            done = discord.Embed(
                title="Data Deleted",
                description=f"Removed **{removed:,}** {plugin.name} pulls. Re-import any time with `/import`.",
                color=C_GREEN,
            )
            done.set_footer(text=FOOTER)
            await interaction.followup.send(embed=done, ephemeral=True)
        else:
            cancelled = discord.Embed(
                title="Cancelled",
                description="Your data was not touched.",
                color=C_GREY,
            )
            cancelled.set_footer(text=FOOTER)
            await interaction.followup.send(embed=cancelled, ephemeral=True)

    # ------------------------------------------------------------------
    # /profile — unified multi-game view + cross-game stats
    # ------------------------------------------------------------------
    @app_commands.command(name="profile", description="Your unified profile across all games, with cross-game statistics")
    async def profile_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        discord_id = str(interaction.user.id)

        pulls_by_game = {}
        for gid in GAME_ORDER:
            pulls_by_game[gid] = repo.get_pulls(discord_id, gid)
        profile = unified_profile(pulls_by_game)

        if not profile["games"]:
            e = discord.Embed(
                title="No Data Yet",
                description="Import at least one game with `/import <url>` to build your profile.",
                color=C_GREY,
            )
            e.set_footer(text=FOOTER)
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        player_label = ", ".join(
            repo.get_account_by_discord_id(discord_id, gid).player_id or "?"
            for gid in profile["games"]
            if repo.get_account_by_discord_id(discord_id, gid)
        ) or discord_id

        # Chart first: user sees the visual with this command
        from analytics import generate_profile_chart
        chart_buf = generate_profile_chart(profile, player_label)
        file = discord.File(fp=chart_buf, filename="profile_chart.png")

        embed = discord.Embed(
            title=f"Cross-Game Profile  •  {player_label}",
            color=C_PURPLE,
        )
        embed.description = (
            f"**{profile['total_pulls']:,}** lifetime pulls  •  "
            f"**{profile['total_5']}** five-stars ({profile['rate_5']:.2f}%)  •  "
            f"~**{profile['total_currency']:,}** currency equivalent"
        )

        for gid in GAME_ORDER:
            g = profile["games"].get(gid)
            if not g:
                continue
            display = GAME_DISPLAY_NAMES[gid]
            guar = " ✅ Guaranteed" if g["is_guaranteed"] else ""
            bar = make_progress_bar(g["featured_pity"], g["featured_cap"])
            embed.add_field(
                name=display,
                value=(
                    f"Pulls: **{g['total_pulls']:,}**  •  5★: **{g['count_5']}** ({g['rate_5']:.2f}%)  •  "
                    f"4★: **{g['count_4']}**\n"
                    f"{g['featured_name']}: **{g['featured_pity']} / {g['featured_cap']}**  `{bar}`{guar}\n"
                    f"50/50: **{g['won_5050']}W / {g['lost_5050']}L** ({g['win_rate_5050']:.0f}%)  •  "
                    f"Avg pity: **{g['avg_pity']:.1f}**"
                ),
                inline=False,
            )

        # Cross-game lifetime stats
        wr = profile["lifetime_5050_win_rate"]
        embed.add_field(
            name="Cross-Game Lifetime",
            value=(
                f"Pulls: **{profile['total_pulls']:,}**  •  5★: **{profile['total_5']}**  •  "
                f"4★: **{profile['total_4']}**\n"
                f"Overall 5★ rate: **{profile['rate_5']:.2f}%**  •  "
                f"Lifetime 50/50 win rate: **{wr:.1f}%**"
            ),
            inline=False,
        )

        embed.set_image(url="attachment://profile_chart.png")
        embed.set_footer(text=FOOTER)
        await interaction.followup.send(embed=embed, file=file)

    # ------------------------------------------------------------------
    # /chart
    # ------------------------------------------------------------------
    @app_commands.command(name="chart", description="Generate a visual chart of your gacha data")
    @app_commands.describe(game="Which game to check", type="Which chart to draw")
    @app_commands.choices(game=GAME_CHOICES, type=[
        app_commands.Choice(name="Pity History", value="pity"),
        app_commands.Choice(name="Pull Timeline", value="timeline"),
        app_commands.Choice(name="Rarity Distribution", value="rarity"),
        app_commands.Choice(name="Banner Comparison", value="banners"),
    ])
    async def chart_cmd(self, interaction: discord.Interaction,
                        game: Optional[app_commands.Choice[str]] = None,
                        type: Optional[app_commands.Choice[str]] = None):
        await interaction.response.defer()
        game_id = game.value if game else "wuthering_waves"
        chart_type = type.value if type else "pity"
        account, pulls = await self._load_account(interaction, game_id, ephemeral=False)
        if not account:
            return

        from analytics import charts
        plugin = _plugin_for(game_id)
        game_name = plugin.name if plugin else ""

        generators = {
            "pity": charts.generate_pity_chart,
            "timeline": charts.generate_timeline_chart,
            "rarity": charts.generate_rarity_chart,
            "banners": charts.generate_banner_comparison_chart,
        }
        gen = generators.get(chart_type, charts.generate_pity_chart)
        chart_buf = gen(pulls, account.player_id, game_id, game_name)
        file = discord.File(fp=chart_buf, filename=f"{chart_type}_chart.png")

        titles = {
            "pity": "Pity Distribution Graph",
            "timeline": "Pull Timeline",
            "rarity": "Rarity Distribution",
            "banners": "Banner Comparison",
        }
        descriptions = {
            "pity": "Green = Won 50/50  •  Red = Lost 50/50  •  Purple = Guaranteed  •  Gold = Ongoing Pity",
            "timeline": "Line = cumulative pulls  •  Dots = 5-stars (label shows pity)  •  Star = current position",
            "rarity": "Pull counts per rarity with percentages",
            "banners": "Bars = total pulls per banner  •  Yellow line = average 5★ pity",
        }
        embed = discord.Embed(
            title=f"{titles[chart_type]}  Player {account.player_id}",
            description=descriptions[chart_type],
            color=C_GREEN
        )
        embed.set_image(url=f"attachment://{chart_type}_chart.png")
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

