import discord
from discord import app_commands
from discord.ext import commands
from bot.embeds import help_embed, C_BLUE, C_GREEN, FOOTER


class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available commands and setup guide")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = help_embed()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check bot latency and operational status")
    async def ping_cmd(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Bot Status",
            description=f"Latency: **{latency}ms**  •  Operational",
            color=C_GREEN
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
