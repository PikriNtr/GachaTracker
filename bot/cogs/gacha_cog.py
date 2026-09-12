import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from database import Repository
from games.wuthering_waves import WutheringWavesPlugin
from analytics import calculate_pity_summary, calculate_astrite_cost, BANNER_NAMES
from bot.embeds import (
    no_data_embed,
    pity_embed,
    calculate_embed,
    stats_embed,
    history_embed,
    C_GREEN,
    C_RED,
    FOOTER
)


repo = Repository()
wuwa_plugin = WutheringWavesPlugin()

class GachaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="import", description="Sync your Wuthering Waves convene history using your URL (private)")
    @app_commands.describe(url="Your Convene History URL from the import.ps1 script")
    async def import_cmd(self, interaction: discord.Interaction, url: str):
        # Ephemeral response for user privacy
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)

        try:
            player_id, pulls = await wuwa_plugin.fetch_and_parse(url)
            if not pulls:
                embed = discord.Embed(
                    title="Import Failed",
                    description="No convene records were returned. Please make sure you viewed Convene History in-game before running the script.",
                    color=C_RED
                )
                embed.set_footer(text=FOOTER)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            repo.save_account(discord_id=discord_id, game_id="wuthering_waves", player_id=player_id)
            new_count = repo.save_pulls(discord_id=discord_id, game_id="wuthering_waves", player_id=player_id, pulls=pulls)

            summary = calculate_pity_summary(repo.get_pulls(discord_id, "wuthering_waves"))
            p1 = summary.get("1", {})

            embed = discord.Embed(
                title="Convene History Synced Successfully",
                description=(
                    f"Player ID: **{player_id}**\n"
                    f"New pulls imported: **{new_count}**\n"
                    f"Total recorded pulls: **{len(pulls)}**\n\n"
                    f"Current Featured Resonator Pity: **{p1.get('current_pity', 0)} / 80**"
                ),
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

    @app_commands.command(name="pity", description="Check current pity count and guarantee status per banner")
    async def pity_cmd(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        account = repo.get_account_by_discord_id(discord_id, "wuthering_waves")
        pulls = repo.get_pulls(discord_id, "wuthering_waves")

        if not account or not pulls:
            await interaction.response.send_message(embed=no_data_embed())
            return

        summary = calculate_pity_summary(pulls)
        embed = pity_embed(account.player_id, summary)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="calculate", description="Calculate Astrite cost and 50/50 scenarios for your next 5-star")
    async def calculate_cmd(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        account = repo.get_account_by_discord_id(discord_id, "wuthering_waves")
        pulls = repo.get_pulls(discord_id, "wuthering_waves")

        if not account or not pulls:
            await interaction.response.send_message(embed=no_data_embed())
            return

        summary = calculate_pity_summary(pulls)
        p1 = summary.get("1", {})
        calc = calculate_astrite_cost(p1.get("current_pity", 0), p1.get("is_guaranteed", False))
        embed = calculate_embed(account.player_id, summary, calc)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="View lifetime pull statistics and Astrite investment")
    async def stats_cmd(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        account = repo.get_account_by_discord_id(discord_id, "wuthering_waves")
        pulls = repo.get_pulls(discord_id, "wuthering_waves")

        if not account or not pulls:
            await interaction.response.send_message(embed=no_data_embed())
            return

        summary = calculate_pity_summary(pulls)
        embed = stats_embed(account.player_id, pulls, summary)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="history", description="View full 5-star pull log and 50/50 records")
    @app_commands.describe(banner="Select banner to view 5-star log")
    @app_commands.choices(banner=[
        app_commands.Choice(name="Featured Resonator", value="1"),
        app_commands.Choice(name="Featured Weapon", value="2"),
        app_commands.Choice(name="Standard Resonator", value="3"),
        app_commands.Choice(name="Standard Weapon", value="4"),
        app_commands.Choice(name="Beginner Convene", value="5"),
        app_commands.Choice(name="Beginners Choice", value="6"),
    ])
    async def history_cmd(self, interaction: discord.Interaction, banner: Optional[str] = "1"):
        discord_id = str(interaction.user.id)
        account = repo.get_account_by_discord_id(discord_id, "wuthering_waves")
        pulls = repo.get_pulls(discord_id, "wuthering_waves")

        if not account or not pulls:
            await interaction.response.send_message(embed=no_data_embed())
            return

        summary = calculate_pity_summary(pulls)
        b_info = summary.get(banner, {})
        b_name = BANNER_NAMES.get(banner, "Featured Resonator")
        p5_hist = b_info.get("history_5star", [])

        embed = history_embed(account.player_id, summary, b_name, p5_hist)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="chart", description="Generate a visual pity distribution graph for your 5-star pulls")
    async def chart_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        discord_id = str(interaction.user.id)
        account = repo.get_account_by_discord_id(discord_id, "wuthering_waves")
        pulls = repo.get_pulls(discord_id, "wuthering_waves")

        if not account or not pulls:
            await interaction.followup.send(embed=no_data_embed())
            return

        from analytics import generate_pity_chart
        chart_buf = generate_pity_chart(pulls, account.player_id)
        file = discord.File(fp=chart_buf, filename="pity_chart.png")

        embed = discord.Embed(
            title=f"Pity Distribution Graph  Player {account.player_id}",
            description="Green = Won 50/50  •  Red = Lost 50/50  •  Gold = Ongoing Pity",
            color=C_GREEN
        )
        embed.set_image(url="attachment://pity_chart.png")
        embed.set_footer(text=FOOTER)

        await interaction.followup.send(embed=embed, file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(GachaCog(bot))

