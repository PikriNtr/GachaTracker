# GachaTracker

> A modular, multi-game gacha history tracker and analytics framework for Discord.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.4%2B-5865F2.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**GachaTracker** is an open-source framework designed to track, store, analyze, and visualize gacha history across multiple games through a Discord bot interface.

Built around a **modular plugin architecture**, game-specific API integrations, log parsing, banner definitions, and gacha rules remain completely isolated from the core system.

---

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure `.env`**
   Ensure `.env` contains your `DISCORD_TOKEN`, `GUILD_ID`, and optional `VOICE_CHANNEL_ID`.

3. **Run the Bot**
   ```bash
   python main.py
   ```

---

## Discord Commands

- `/import <url>` — Sync your convene history (private)
- `/pity` — Check current pity count and guarantee status per banner
- `/calculate` — Astrite cost to get your next 5-star (all scenarios)
- `/stats` — Lifetime pull statistics and Astrite investment
- `/history [banner]` — Full 5-star pull log with 50/50 records
- `/chart` — Generate visual dark-themed pity distribution graph image
- `/help` — Bot commands and setup guide
- `/ping` — Bot latency and operational status
