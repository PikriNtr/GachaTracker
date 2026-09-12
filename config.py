import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base directory for gacha_tracker
BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent

# Load environment variables (check gacha_tracker/.env first, then parent directory .env)
env_local = BASE_DIR / ".env"
env_parent = PARENT_DIR / ".env"

if env_local.exists():
    load_dotenv(env_local, override=True)
elif env_parent.exists():
    load_dotenv(env_parent, override=True)
else:
    load_dotenv(override=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_IDS = [gid.strip() for gid in os.getenv("GUILD_ID", "").split(",") if gid.strip()]
VOICE_CHANNEL_IDS = [vid.strip() for vid in os.getenv("VOICE_CHANNEL_ID", "").split(",") if vid.strip()]

# Database path
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "gachatracker.db"
