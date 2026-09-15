"""Banner schedule commands: /banners (view), /bannerset (add/update), /bannerremove."""
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from analytics import DEFAULT_GAME, GAME_BANNER_CONFIGS, GAME_DISPLAY_NAMES, GAME_ORDER
from analytics.schedule_time import canonical, now_canonical, parse_timestamp
from bot.embeds import C_BLUE, C_GREEN, C_GREY, C_RED, FOOTER
from database import Repository

repo = Repository()

GAME_CHOICES = [
    app_commands.Choice(name="Wuthering Waves", value="wuthering_waves"),
    app_commands.Choice(name="Genshin Impact", value="genshin_impact"),
    app_commands.Choice(name="Honkai: Star Rail", value="honkai_star_rail"),
]

# Pool picker: Discord choices are static, so one combined dropdown across all
# games. Value encodes "game_id:pool_id" so the game is derived from the pick.
# 17 entries fits Discord's 25-choice limit.
def _all_pool_choices() -> list[app_commands.Choice]:
    choices = []
    for gid in GAME_ORDER:
        cfg = GAME_BANNER_CONFIGS[gid]
        display = GAME_DISPLAY_NAMES[gid]
        for pid in cfg["pools"]:
            choices.append(app_commands.Choice(
                name=f"{display} — {cfg['names'][pid]}", value=f"{gid}:{pid}"))
    return choices


POOL_CHOICES = _all_pool_choices()


def _resolve_pool_choice(choice_value: str) -> tuple[str, str]:
    """Splits a POOL_CHOICES value into (game_id, pool_id)."""
    game_id, pool_id = choice_value.split(":", 1)
    return game_id, pool_id


class BannersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------------
    @app_commands.command(name="banners", description="What banner is running right now in each pool (plus upcoming)")
    @app_commands.describe(game="Which game to check")
    @app_commands.choices(game=GAME_CHOICES)
    async def banners_cmd(self, interaction: discord.Interaction,
                          game: Optional[app_commands.Choice[str]] = None):
        game_id = game.value if game else "wuthering_waves"
        cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
        display = GAME_DISPLAY_NAMES.get(game_id, game_id)

        active = repo.get_active_banners(game_id)
        upcoming = repo.get_upcoming_banners(game_id)

        e = discord.Embed(
            title=f"{display} — Current Banners",
            description=f"As of `{now_canonical()}` UTC",
            color=C_BLUE,
        )

        if not active and not upcoming:
            e.description = (
                "No banner schedule recorded yet.\n\n"
                "Anyone can add one:\n"
                "`/bannerset pool:<pool> banner:<name> start:<YYYY-MM-DD HH:MM> end:<YYYY-MM-DD HH:MM>`\n\n"
                "Times are UTC."
            )
            e.set_footer(text=FOOTER)
            await interaction.response.send_message(embed=e)
            return

        missing_hint = False
        for pool_id in cfg["pools"]:
            pool_name = cfg["names"].get(pool_id, f"Pool {pool_id}")
            a = active.get(pool_id)
            if a:
                value = (
                    f"**{a['banner_name']}**\n"
                    f"Since `{a['start_time']}` • ends `{a['end_time']}`"
                )
            else:
                value = "No active banner recorded"
                missing_hint = True
            ups = upcoming.get(pool_id, [])
            if ups:
                next_lines = [
                    f"• **{u['banner_name']}** `{u['start_time']}` → `{u['end_time']}`"
                    for u in ups[:3]
                ]
                value += "\n**Upcoming:**\n" + "\n".join(next_lines)
            e.add_field(name=pool_name, value=value, inline=False)

        if missing_hint:
            e.description += (
                "\n\n💡 Seeing pools without a current banner? "
                "Anyone can fix that with `/bannerset`."
            )

        e.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=e)

    # ------------------------------------------------------------------
    @app_commands.command(name="bannerset", description="Add or update a banner schedule window (anyone can contribute)")
    @app_commands.describe(
        pool="Game + banner pool",
        banner="Banner name, e.g. 'Yanqing - Genshin of Frost'",
        start="Start time, e.g. 2025-01-15 11:00 (UTC)",
        end="End time, e.g. 2025-02-05 17:59 (UTC)",
    )
    @app_commands.choices(pool=POOL_CHOICES)
    async def bannerset_cmd(self, interaction: discord.Interaction,
                            pool: app_commands.Choice[str],
                            banner: str,
                            start: str,
                            end: str):
        await interaction.response.defer(ephemeral=True)
        game_id, pool_id = _resolve_pool_choice(pool.value)
        cfg = GAME_BANNER_CONFIGS[game_id]
        display = GAME_DISPLAY_NAMES[game_id]

        if not banner or not banner.strip():
            e = discord.Embed(title="Missing Banner Name",
                              description="Give the banner a name, e.g. `banner:Yanqing - Genshin of Frost`",
                              color=C_RED)
            e.set_footer(text=FOOTER)
            await interaction.followup.send(embed=e, ephemeral=True)
            return
        banner_name = banner.strip()[:120]

        start_dt = parse_timestamp(start or "")
        end_dt = parse_timestamp(end or "")
        if start_dt is None or end_dt is None:
            e = discord.Embed(
                title="Bad Timestamp",
                description=(
                    "Could not parse start/end. Accepted examples (all UTC):\n"
                    "`2025-01-15 11:00:00` • `2025-01-15 11:00` • "
                    "`2025-01-15 11am` • `2025-01-15 1:30pm` • `2025-01-15`"
                ),
                color=C_RED,
            )
            e.set_footer(text=FOOTER)
            await interaction.followup.send(embed=e, ephemeral=True)
            return
        if end_dt <= start_dt:
            e = discord.Embed(title="Bad Range",
                              description="End time must be after start time.", color=C_RED)
            e.set_footer(text=FOOTER)
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        row_id = repo.upsert_banner_schedule(
            game_id=game_id,
            card_pool_type=pool_id,
            banner_name=banner_name,
            start_time=canonical(start_dt),
            end_time=canonical(end_dt),
            created_by=str(interaction.user.id),
        )

        active_now = now_canonical()
        is_live = canonical(start_dt) <= active_now <= canonical(end_dt)
        e = discord.Embed(
            title="Banner Schedule Saved",
            description=(
                f"**{display}** — {cfg['names'][pool_id]}\n"
                f"**{banner_name}**\n"
                f"`{canonical(start_dt)}` → `{canonical(end_dt)}`\n\n"
                + ("🟢 This window is **live now** — `/banners` shows it as current."
                   if is_live else "Scheduled — `/banners` will show it once the window starts.")
            ),
            color=C_GREEN,
        )
        e.set_footer(text=f"Schedule id {row_id}  •  {FOOTER}")
        await interaction.followup.send(embed=e, ephemeral=True)

    # ------------------------------------------------------------------
    @app_commands.command(name="bannerremove", description="Remove banner schedule windows for a pool")
    @app_commands.describe(
        pool="Game + pool to clear",
        only_current="Only remove the currently-active window (default: remove all for that pool)",
    )
    @app_commands.choices(pool=POOL_CHOICES)
    async def bannerremove_cmd(self, interaction: discord.Interaction,
                               pool: app_commands.Choice[str],
                               only_current: Optional[bool] = False):
        await interaction.response.defer(ephemeral=True)
        game_id, pool_id = _resolve_pool_choice(pool.value)
        cfg = GAME_BANNER_CONFIGS[game_id]

        removed = repo.delete_banner_windows(game_id, pool_id, only_active=bool(only_current))
        scope = "active window" if only_current else "all windows"
        e = discord.Embed(
            title="Banner Schedule Removed",
            description=f"Deleted **{removed}** {scope} for **{cfg['names'][pool_id]}**.",
            color=C_GREEN if removed else C_GREY,
        )
        e.set_footer(text=FOOTER)
        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(BannersCog(bot))
