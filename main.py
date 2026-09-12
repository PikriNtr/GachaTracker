import sys
from config import DISCORD_TOKEN
from bot.bot import bot

def main():
    if not DISCORD_TOKEN or DISCORD_TOKEN.strip() == "" or DISCORD_TOKEN == "your_bot_token_here":
        print("\n[ERROR] DISCORD_TOKEN not found in environment or .env file!")
        sys.exit(1)

    print("Starting GachaTracker Bot...", flush=True)
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
