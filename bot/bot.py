import discord
from discord.ext import commands, tasks
from config import GUILD_IDS, VOICE_CHANNEL_IDS
from core.registry import registry
from games import register_all_plugins
from bot.cogs import UtilityCog, GachaCog


# Populate the global plugin registry before cogs load
register_all_plugins(registry)


intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class GachaTrackerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Load cogs
        await self.add_cog(UtilityCog(self))
        await self.add_cog(GachaCog(self))

        # Sync slash commands
        if GUILD_IDS:
            for gid in GUILD_IDS:
                guild = discord.Object(id=int(gid))
                self.tree.copy_global_to(guild=guild)
                try:
                    synced = await self.tree.sync(guild=guild)
                    print(f" Synced {len(synced)} command(s) instantly to guild {gid}.", flush=True)
                except Exception as e:
                    print(f" Guild sync failed for {gid}: {e}", flush=True)
        else:
            print(" No GUILD_ID configured.", flush=True)

        try:
            synced = await self.tree.sync()
            print(f" Synced {len(synced)} command(s) globally (DMs may take up to 1hr).", flush=True)
        except Exception as e:
            print(f" Global sync failed: {e}", flush=True)

bot = GachaTrackerBot()

# ─────────────────────────────────────────────
# 24/7 Voice Connection Task
# ─────────────────────────────────────────────
@tasks.loop(seconds=15)
async def keep_voice_alive():
    if not VOICE_CHANNEL_IDS:
        return

    for vc_id_str in VOICE_CHANNEL_IDS:
        try:
            vc_id = int(vc_id_str)
        except ValueError:
            continue

        channel = bot.get_channel(vc_id)
        if not channel:
            try:
                channel = await bot.fetch_channel(vc_id)
            except Exception:
                continue

        if not isinstance(channel, discord.VoiceChannel):
            continue

        guild = channel.guild
        perms = channel.permissions_for(guild.me)
        if not perms.connect:
            print(f" [WARNING] Bot lacks 'Connect' permission for Voice Channel '{channel.name}' ({channel.id}) in '{guild.name}'", flush=True)
            continue

        voice_client = guild.voice_client

        if voice_client is None:
            try:
                await channel.connect(reconnect=True, self_deaf=True, timeout=15.0)
                print(f" Connected to 24/7 Voice Channel: '{channel.name}' ({channel.id}) in '{guild.name}'", flush=True)
            except Exception as e:
                print(f" Failed to connect to VC {vc_id}: {e}", flush=True)
        elif voice_client.channel.id != channel.id:
            try:
                await voice_client.move_to(channel)
                print(f" Moved to 24/7 Voice Channel: '{channel.name}' ({channel.id}) in '{guild.name}'", flush=True)
            except Exception as e:
                print(f" Failed to move to VC {vc_id}: {e}", flush=True)
        elif not voice_client.is_connected():
            try:
                await voice_client.connect(reconnect=True, self_deaf=True, timeout=15.0)
            except Exception as e:
                print(f" Failed to reconnect to VC {vc_id}: {e}", flush=True)

@bot.event
async def on_ready():
    print("=" * 50, flush=True)
    print(f" GachaTracker Bot: {bot.user} (ID: {bot.user.id})", flush=True)
    print(f" discord.py: {discord.__version__}", flush=True)
    print(f" Latency: {round(bot.latency * 1000)}ms", flush=True)
    print(f" Servers: {len(bot.guilds)}", flush=True)
    for g in bot.guilds:
        print(f"   - {g.name} ({g.id})", flush=True)
    print("=" * 50, flush=True)

    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="Convene History  |  /help"
    ))

    if VOICE_CHANNEL_IDS and not keep_voice_alive.is_running():
        keep_voice_alive.start()
        print(f" 24/7 Voice Channel auto-reconnect loop started for ID(s): {', '.join(VOICE_CHANNEL_IDS)}", flush=True)
