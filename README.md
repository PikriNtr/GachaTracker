# ✦ GachaTracker

> A modular, multi-game gacha history tracker and analytics framework for Discord.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.4%2B-5865F2.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active%20development-orange.svg)

**GachaTracker** is an open-source framework designed to track, store, analyze, and visualize gacha history across multiple games through a Discord bot interface.

Built around a **modular plugin architecture**, game-specific API integrations, log parsing, banner definitions, and gacha rules remain completely isolated from the core system—allowing new games to be added seamlessly.

---

## 🌟 Features

- 🧩 **Modular Plugin Architecture**: Game-specific mechanics (API fetching, pity rules, banner pools) are decoupled from the core engine.
- 📊 **Visual Distribution Graphs (`/chart`)**: Generates custom dark-themed pity bar graphs with color-coded 50/50 win/loss markers and soft/hard pity thresholds.
- 🎯 **Accurate Pity & 50/50 Tracking**: Automatically tracks current pity, total pulls, and 50/50 win/loss history (identifying standard vs. featured Resonators).
- 💰 **Astrite & Pull Cost Calculator (`/calculate`)**: Calculates best-case, average-case, and worst-case pull and Astrite cost scenarios.
- 💾 **Idempotent Local Storage**: Merges history records into a local SQLite database without creating duplicate entries.
- 🎙️ **24/7 Voice Channel Connection**: Auto-connects and auto-reconnects to designated Discord Voice Channels with self-deafen bandwidth optimization.
- 🎨 **Clean & Emoji-Free Interface**: Modern, professional Discord embeds formatted with ASCII text tables.

---

## 🏗️ Architecture Overview

```text
                        GachaTracker Framework
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
  Discord Interface          Core Engine             SQLite Database
(Slash Commands & Cogs)   (Pity, Analytics, Calc)    (Idempotent Storage)
                                  │
                                  ▼
                            Plugin Registry
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
  Wuthering Waves          Genshin Impact          Honkai: Star Rail
   (Plugin)                  (Plugin)                  (Plugin)
```

### Architectural Principles

1. **Separation of Concerns**: Discord commands handle UI presentation; Core Services compute analytics; Plugins isolate game API rules.
2. **Game-Agnostic Core**: The core engine operates on normalized `Pull`, `Banner`, and `GameAccount` models.
3. **Idempotency**: Repeatedly importing history fetches new records while safely preserving historical pulls older than 6 months.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Git**

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/discord-tracker.git
   cd discord-tracker/gacha_tracker
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Copy `.env.example` to `.env` in the repo root and fill it in:
   ```env
   # Discord Bot Token from https://discord.com/developers/applications
   DISCORD_TOKEN=your_bot_token_here

   # Optional: Server (Guild) IDs for instant command sync (comma-separated)
   GUILD_ID=123456789012345678,987654321098765432

   # Optional: Voice Channel ID for 24/7 staying
   VOICE_CHANNEL_ID=123456789012345678
   ```

4. **Launch the Bot**
   ```bash
   python main.py
   ```

---

## 📜 Discord Slash Commands

All gacha commands accept an optional `game` option (Wuthering Waves / Genshin Impact / Honkai: Star Rail); they default to Wuthering Waves.

| Command | Description |
|---|---|
| `/import <url> [game]` | Sync your gacha history privately using your in-game log URL; shows deltas (new pulls, new 5★/4★, pity before→after) |
| `/pity [game]` | Check current pity count and 50/50 guarantee status for all banners |
| `/calculate [game]` | Calculate Astrite/Primogem/Stellar Jade cost & 50/50 scenarios (best, average, worst case) |
| `/stats [game]` | View lifetime pull statistics, currency investment, and 5-star rates |
| `/history [game] [banner]` | Full 5-star pull log with 50/50 win/loss records |
| `/chart [game]` | Generate a visual dark-themed pity distribution graph image |
| `/simulate [game]` | Run 10,000 Monte Carlo simulations to get your Luck Percentile |
| `/help` | Show bot commands and setup guide |
| `/ping` | Check bot latency and operational status |

---

## 📁 Project Structure

```text
discord-tracker/
├── gacha_tracker/               # Project repository root
│   ├── main.py                  # Bot entry point launcher
│   ├── config.py                # Environment configuration loader
│   ├── core/                    # Game-agnostic core engine
│   │   ├── models.py            # Normalized data models (Pull, Banner, GameAccount)
│   │   ├── game.py              # Abstract GachaGame plugin interface
│   │   └── registry.py          # Plugin discovery & management
│   ├── database/                # Persistence layer
│   │   └── repository.py        # SQLite repository with deduplication
│   ├── analytics/               # Analytics & Math engines
│   │   ├── pity.py              # Pity counting & 50/50 analysis (per-game configs)
│   │   ├── calculator.py        # Pull-cost calculator (per-game models)
│   │   ├── charts.py            # Matplotlib visual graph renderer
│   │   └── simulation.py        # Monte Carlo luck percentile engine
│   ├── games/                   # Game plugins directory
│   │   ├── wuthering_waves/     # Wuthering Waves Plugin
│   │   │   ├── game.py          # WutheringWavesPlugin class
│   │   │   ├── api.py           # Kuro Games API client
│   │   │   ├── parser.py        # Raw response normalizer
│   │   │   └── banners.py       # Banner & 50/50 pool definitions
│   │   ├── genshin_impact/      # Genshin Impact Plugin
│   │   │   ├── game.py          # GenshinImpactPlugin class
│   │   │   ├── parser.py        # Raw response normalizer
│   │   │   └── banners.py       # Banner & 50/50 pool definitions
│   │   ├── honkai_star_rail/    # Honkai: Star Rail Plugin
│   │   │   ├── game.py          # HonkaiStarRailPlugin class
│   │   │   ├── parser.py        # Raw response normalizer
│   │   │   └── banners.py       # Banner & 50/50 pool definitions
│   │   └── hoyoverse_api.py     # Shared HoYoverse getGachaLog client (Genshin + HSR)
│   ├── bot/                     # Discord Bot Application
│   │   ├── bot.py               # Bot setup & 24/7 Voice Task loop
│   │   ├── embeds.py            # Game-aware embed UI builder
│   │   └── cogs/                # Slash command cogs
│   │       ├── gacha_cog.py     # Gacha commands (game selector)
│   │       └── utility_cog.py   # Utility commands
│   ├── tests/                   # pytest suite (pity, dedup, imports, API, UI)
│   ├── tracker/                 # Local offline URL extractor utilities
│   │   ├── Run-Tracker.bat      # Double-click script launcher
│   │   ├── WuWa-LocalTracker.ps1    # Convene URL extractor (WuWa)
│   │   ├── Genshin-GetLink.ps1      # Wish URL extractor (Genshin Impact)
│   │   ├── HSR-GetLink.ps1          # Warp URL extractor (Honkai: Star Rail)
│   │   └── WuWa-Viewer.html     # Local browser viewer
│   ├── docs/                    # System architectural documentation
│   │   ├── ARCHITECTURE.md
│   │   ├── GachaTracker.md
│   │   ├── PLUGIN_DEVELOPMENT.md
│   │   └── ROADMAP.md
│   ├── .env.example             # Environment template
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Project documentation
└── legacy/                      # Archived original single-file bot (not in repo)
```

---

## 🗺️ Roadmap Highlights

- [x] **v0.1 — WuWa MVP & Core Abstraction**: Modular plugin framework, SQLite persistence, pity engine, Discord bot.
- [x] **v0.2 — Advanced Analytics & 50/50 Calculator**: Astrite cost calculator, standard 5-star detection, 50/50 guarantee tracking.
- [x] **v0.3 — Visual Charting & Voice Support**: Matplotlib image graph generation (`/chart`), 24/7 Voice Channel auto-reconnect.
- [x] **v0.4 — Monte Carlo Luck Simulation**: Compare player pity distributions against 10,000 simulated players to calculate statistical percentiles.
- [x] **v0.5 — Multi-Game Plugins**: Genshin Impact & Honkai: Star Rail plugins via the registry; per-game probability models (`/simulate`), game-aware charts and embeds, shared HoYoverse API client.
- [ ] **v0.6 — Web Dashboard & REST API**: Standalone FastAPI service and interactive web dashboard.

---

## 🔒 Security & Privacy

- **No Password Collection**: The bot only uses temporary, official Convene history URLs generated in-game.
- **Privacy-First Import**: `/import` responses are strictly `ephemeral` (visible only to the command invoker).
- **Open Source & Transparent**: All code is open-source and easily audit-able.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
