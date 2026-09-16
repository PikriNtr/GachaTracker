# GachaTracker

> A modular, multi-game gacha history tracker and analytics framework for Discord.

GachaTracker is an open-source framework designed to make it easy to build **Discord bots that track, store, and analyze gacha history across multiple games**.

The project uses a plugin-based architecture. Each supported game provides its own plugin containing game-specific API integration, history parsing, banner definitions, and gacha rules, while the core system handles common functionality such as data storage, pity calculation, statistics, analytics, and Discord integration.

The initial implementation will be based on **Wuthering Waves**, using an existing WuWa tracker as the foundation.

---

# Table of Contents

- [Overview](#overview)
- [Motivation](#motivation)
- [Goals](#goals)
- [Non-Goals](#non-goals)
- [Core Concept](#core-concept)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Plugin System](#plugin-system)
- [Normalized Data](#normalized-data)
- [Gacha System](#gacha-system)
- [Pity Calculation](#pity-calculation)
- [Data Model](#data-model)
- [Analytics](#analytics)
- [Luck Analysis](#luck-analysis)
- [Probability Analysis](#probability-analysis)
- [Monte Carlo Simulation](#monte-carlo-simulation)
- [Machine Learning](#machine-learning)
- [Discord Integration](#discord-integration)
- [Database](#database)
- [Web Dashboard](#web-dashboard)
- [Configuration](#configuration)
- [Development Roadmap](#development-roadmap)
- [Testing](#testing)
- [Security and Privacy](#security-and-privacy)
- [Design Principles](#design-principles)
- [Future Possibilities](#future-possibilities)
- [Technology Stack](#technology-stack)
- [Success Criteria](#success-criteria)
- [Initial Milestone](#initial-milestone)
- [Project Status](#project-status)
- [License](#license)

---

# Overview

GachaTracker is designed to provide a common infrastructure for tracking gacha history across multiple games.

Instead of creating a separate Discord bot for every game, GachaTracker provides a shared core and a plugin system.

```text
                         GachaTracker
                              │
              ┌───────────────┴───────────────┐
              │                               │
          Core Engine                    Game Plugins
              │                               │
       ┌──────┼──────┐             ┌──────────┼──────────┐
       │      │      │             │          │          │
     Gacha  Pity  Analytics       WuWa      Genshin     HSR
                                  Plugin     Plugin    Plugin
```

The core system is responsible for functionality shared between games:

- Discord commands
- user management
- database storage
- pull history
- pity calculations
- statistics
- analytics
- simulations
- configuration
- plugin management

Game plugins are responsible for game-specific functionality:

- API integration
- history importing
- response parsing
- banner definitions
- rarity systems
- pity rules
- featured item rules
- game-specific mechanics

This separation allows additional games to be added without rewriting the entire application.

---

# Motivation

Most gacha tracking bots are tightly coupled to a single game.

For example:

```text
WuWa Bot
│
├── WuWa API
├── WuWa history parser
├── WuWa pity system
└── Discord commands
```

If another game needs to be supported, much of the implementation has to be duplicated.

GachaTracker aims to solve this problem by separating game-specific logic from the common tracking infrastructure.

```text
Game-specific logic
        │
        ▼
   Game Plugin
        │
        ▼
 GachaTracker Core
        │
   ┌────┼────┐
   ▼    ▼    ▼
Discord DB Analytics
```

The result is a system that is easier to:

- maintain
- extend
- test
- reuse
- contribute to

---

# Goals

## Primary Goals

### 1. Modular architecture

Game-specific functionality should be isolated into independent plugins.

### 2. Multi-game support

The same core system should support multiple gacha games.

### 3. Gacha history tracking

Users should be able to import and store their pull history.

### 4. Accurate pity calculation

The system should calculate pity according to the rules of each supported game.

### 5. Statistical analysis

Users should be able to understand their gacha history through useful statistics.

### 6. Discord-first experience

The initial interface should be implemented through Discord slash commands.

### 7. Extensibility

Developers should be able to create new game plugins without modifying the core system unnecessarily.

---

# Non-Goals

GachaTracker is **not intended to**:

- automate gacha pulls
- manipulate game accounts
- perform unauthorized actions against game services
- exploit game APIs
- store game passwords
- guarantee future gacha outcomes
- claim that machine learning can reliably predict random pulls

The project focuses on:

> **Tracking, analyzing, and visualizing gacha history.**

---

# Core Concept

GachaTracker consists of several layers:

```text
┌─────────────────────────────────────────────┐
│                 Discord Bot                 │
├─────────────────────────────────────────────┤
│              Application Layer              │
│       Commands / Embeds / User Input        │
├─────────────────────────────────────────────┤
│            GachaTracker Core                │
│     Gacha / Pity / Statistics / Users       │
├─────────────────────────────────────────────┤
│              Plugin Interface               │
├─────────────────────────────────────────────┤
│               Game Plugins                  │
│       WuWa / Genshin / HSR / ZZZ / ...      │
├─────────────────────────────────────────────┤
│                Persistence                  │
│                  SQLite                     │
└─────────────────────────────────────────────┘
```

The primary architectural principle is:

> **The core should not need to know the internal implementation details of a specific game.**

Instead, each plugin provides the information required by the core.

---

# Architecture

## High-Level Architecture

```text
                         User
                           │
                           ▼
                    Discord Command
                           │
                           ▼
                   Command Handler
                           │
                           ▼
                 GachaTracker Core
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Game Plugin    Database     Analytics
              │
       ┌──────┴──────┐
       ▼             ▼
    API Client     Parser
```

---

## Example Data Flow

Suppose a user imports their Wuthering Waves history.

```text
User
 │
 │ /gacha import
 ▼
Discord Bot
 │
 ▼
WuWa Plugin
 │
 ├── Fetch history
 │
 └── Parse response
          │
          ▼
     Normalized Pull
          │
          ▼
   GachaTracker Core
          │
          ▼
       Database
          │
          ▼
      Analytics
          │
          ▼
    Discord Response
```

The plugin converts game-specific API data into a normalized internal format.

This allows the rest of GachaTracker to remain game-agnostic.

---

# Project Structure

A proposed project structure:

```text
GachaTracker/
│
├── bot/
│   ├── commands/
│   │   ├── gacha.py
│   │   ├── profile.py
│   │   └── stats.py
│   │
│   ├── embeds/
│   │   ├── gacha.py
│   │   ├── stats.py
│   │   └── errors.py
│   │
│   └── bot.py
│
├── core/
│   ├── game.py
│   ├── player.py
│   ├── banner.py
│   ├── pull.py
│   ├── pity.py
│   └── statistics.py
│
├── games/
│   ├── wuthering_waves/
│   │   ├── api.py
│   │   ├── parser.py
│   │   ├── banners.py
│   │   └── game.py
│   │
│   ├── genshin/
│   │   └── ...
│   │
│   ├── star_rail/
│   │   └── ...
│   │
│   └── zzz/
│       └── ...
│
├── database/
│   ├── models.py
│   ├── repository.py
│   └── migrations/
│
├── analytics/
│   ├── pity.py
│   ├── luck.py
│   ├── distribution.py
│   └── probability.py
│
├── ml/
│   ├── features.py
│   ├── models.py
│   └── evaluation.py
│
├── config/
│   └── config.toml
│
├── tests/
│   ├── core/
│   ├── games/
│   ├── analytics/
│   └── database/
│
├── docs/
│
├── README.md
├── pyproject.toml
├── LICENSE
└── .gitignore
```

The structure is expected to evolve as the project develops.

---

# Plugin System

The plugin system is the most important architectural component of GachaTracker.

Each game implements a common interface.

Conceptually:

```python
class GachaGame:
    name: str

    def import_history(self, data):
        ...

    def normalize_pull(self, data):
        ...

    def calculate_pity(self, history):
        ...

    def get_banner_info(self):
        ...
```

The core interacts with the game through this interface.

---

## Wuthering Waves Plugin

The initial plugin could look conceptually like:

```python
class WutheringWaves(GachaGame):

    name = "wuthering_waves"

    def import_history(self, data):
        ...

    def normalize_pull(self, data):
        ...

    def calculate_pity(self, history):
        ...
```

A future Genshin plugin would implement the same interface:

```python
class Genshin(GachaGame):

    name = "genshin"

    def import_history(self, data):
        ...

    def normalize_pull(self, data):
        ...

    def calculate_pity(self, history):
        ...
```

Discord commands should not need to know how each game works.

For example:

```python
game = GachaTracker.get_game("wuthering_waves")

history = game.import_history(data)

stats = game.calculate_pity(history)
```

---

# Normalized Data

Different games use different API formats.

One game might return:

```json
{
    "name": "Character A",
    "rarity": 5,
    "time": "2026-09-12"
}
```

Another might return:

```json
{
    "item_name": "Character A",
    "rank": 5,
    "timestamp": "2026-09-12"
}
```

The plugin converts both into a common internal representation.

Example:

```python
Pull(
    item_id="character_a",
    item_name="Character A",
    rarity=5,
    banner_type="character",
    timestamp=...,
    pity=72
)
```

This allows the analytics system to process pulls without caring about the original API format.

---

# Gacha System

The gacha system should be generic enough to represent different types of banners.

Possible banner types include:

```text
Character
Weapon
Standard
Beginner
Event
Light Cone
W-Engine
```

Each game plugin should be able to define:

- rarity levels
- pity limits
- soft pity behavior
- hard pity
- featured item rules
- 50/50 systems
- banner categories
- guarantee mechanics

The core should provide the infrastructure while plugins provide the rules.

---

# Pity Calculation

Pity is calculated from normalized pull history.

Example:

```text
Pull #1
Pull #2
Pull #3
...
Pull #70
Pull #71 → 5★
```

The system determines:

```text
Pity = 71
```

The pity counter then resets.

Different games can have different pity mechanics, so the actual calculation should be handled by the game's plugin or its configured gacha rules.

---

# Data Model

A simplified data model could contain the following entities.

## User

```text
User
├── id
├── discord_id
└── created_at
```

## Game Account

```text
GameAccount
├── id
├── user_id
├── game
├── server
└── metadata
```

## Pull

```text
Pull
├── id
├── account_id
├── banner_id
├── item_id
├── item_name
├── rarity
├── pity
└── timestamp
```

## Banner

```text
Banner
├── id
├── game
├── name
├── type
├── start_time
└── end_time
```

---

# Analytics

Analytics are one of the main features of GachaTracker.

The system can calculate:

## Basic Statistics

- total pulls
- total 5★ pulls
- total 4★ pulls
- average pity
- median pity
- minimum pity
- maximum pity
- standard deviation

## Banner Statistics

- pulls per banner
- 5★ rate
- featured item rate
- pulls until featured item
- banner comparison
- weapon statistics

## Player Statistics

- total pulls
- total 5★ characters
- average pity
- early 5★ rate
- 50/50 win rate
- longest pity
- shortest pity

---

# Luck Analysis

GachaTracker can provide a statistical interpretation of a user's pull history.

Example:

```text
╭────────────────────────────╮
│       GACHA ANALYSIS       │
├────────────────────────────┤
│ Total Pulls       482      │
│ Average Pity      68.9     │
│ Best Pull           8      │
│ Worst Pull         80      │
│                            │
│ Luck Score        82/100   │
│                            │
│ Your history is unusually  │
│ favorable compared with    │
│ simulated histories.       │
╰────────────────────────────╯
```

The luck score should be clearly documented as a statistical metric rather than an objective measurement.

---

# Probability Analysis

GachaTracker can provide probability-oriented information.

For example:

```text
Current Pity: 63

Estimated probability of obtaining
a 5★ within the next 10 pulls:

████████████████░░░░  ~80%
```

The exact result depends on the game's configured probability and pity mechanics.

The system should distinguish between:

- theoretical probability
- historical frequency
- simulation results
- statistical estimates
- ML model outputs

These should never be presented as equivalent.

---

# Monte Carlo Simulation

Monte Carlo simulation can be used to analyze how unusual a player's pull history is.

For example:

```text
                 Simulation
                      │
                      ▼
              10,000 Players
                      │
                      ▼
               Pity Distribution
                      │
                      ▼
             Compare User Data
                      │
                      ▼
              Percentile Result
```

Example:

```text
Your Average Pity: 61.2

Statistical Percentile:

0% ────────────────●──────────── 100%
                   ▲
                  78%
```

This can provide a more meaningful statistical interpretation than simply labeling a player as "lucky."

---

# Machine Learning

Machine learning is an optional advanced component.

GachaTracker should not use ML for deterministic calculations such as basic pity counting.

Instead, ML can be used for experimentation and research.

Potential applications include:

- statistical probability estimation
- anomaly detection
- pull behavior clustering
- historical pattern analysis
- simulation modeling
- comparative model evaluation

---

## Important Limitation

Gacha outcomes are generally random.

Therefore, GachaTracker should **not** claim that machine learning can reliably predict the next pull.

Avoid:

```text
AI predicts that your next pull will be a 5★.
```

Prefer:

```text
Based on the configured probability model,
your estimated probability of receiving a 5★
within the next N pulls is X%.
```

Any ML experiment should be compared against an appropriate statistical baseline.

---

# Discord Integration

The primary interface will use Discord slash commands.

Possible commands:

```text
/gacha import
/gacha history
/gacha pity
/gacha stats
/gacha luck
/gacha banner
/gacha simulate
```

---

## `/gacha import`

Imports the user's game history.

Example:

```text
Importing history...

████████████████████ 100%

482 pulls imported successfully.
```

---

## `/gacha history`

Displays recent pulls.

```text
Recent Pulls

1. Character A — 5★
2. Character B — 4★
3. Weapon C — 3★
4. Character D — 4★
```

---

## `/gacha pity`

Displays current pity.

```text
Current Pity

Character Banner
63 pulls

Last 5★:
Character A

Last 5★ Pity:
71
```

---

## `/gacha stats`

Displays statistical information.

```text
Gacha Statistics

Total Pulls:       482
5★:                  7
Average Pity:      68.9
Median Pity:        71
50/50 Wins:       4 / 7
```

---

## `/gacha luck`

Displays statistical analysis.

```text
Luck Analysis

Overall: 82 / 100

Average Pity
Your      68.9
Expected  ~70

50/50 Rate
Your      57.1%
Expected  50%
```

---

# Database

The initial implementation can use SQLite.

Advantages:

- simple deployment
- no external database required
- easy local development
- portable
- sufficient for small and medium deployments

A future deployment can support PostgreSQL through a database abstraction layer.

Possible architecture:

```text
GachaTracker
     │
     ▼
Repository Layer
     │
 ┌───┴────┐
 ▼        ▼
SQLite  PostgreSQL
```

---

# Web Dashboard

A web dashboard can eventually be added.

Possible architecture:

```text
                  GachaTracker
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
      Discord Bot                REST API
                                      │
                                      ▼
                                Web Dashboard
```

The dashboard could display:

- pull history
- pity graphs
- banner statistics
- luck percentile
- pull distributions
- account statistics
- historical trends

---

# Configuration

Configuration should be kept outside the source code.

Example:

```toml
[bot]
token = "YOUR_TOKEN"

[database]
url = "sqlite:///gachatracker.db"

[games]
wuthering_waves = true
genshin = false
star_rail = false
```

Sensitive credentials should never be committed to Git.

A `.env` file can be used for secrets:

```env
DISCORD_TOKEN=...
```

The `.env` file should be included in `.gitignore`.

---

# Development Roadmap

## Phase 0 — Planning

- [x] Define architecture (see ARCHITECTURE.md)
- [x] Define plugin interface (`core/game.py` — `GachaGame` ABC)
- [x] Define normalized data model (`core/models.py` — `Pull`, `Banner`, `GameAccount`)
- [x] Define database schema (`database/repository.py`)
- [x] Define testing strategy (pytest suite in `tests/`)

---

# Phase 1 — Wuthering Waves MVP

Use the existing WuWa tracker as the initial implementation.

- [x] Refactor existing bot
- [x] Separate Discord commands
- [x] Separate WuWa API client
- [x] Separate history parser
- [x] Create core gacha models
- [x] Implement pity calculation
- [x] Implement SQLite storage

### Goal

Have the existing WuWa tracker running on top of the new GachaTracker architecture.

---

# Phase 2 — Plugin Architecture

- [x] Create `GachaGame`
- [x] Create normalized pull model
- [x] Create banner interface
- [x] Create plugin registry
- [x] Implement plugin loading
- [x] Move WuWa functionality into its own plugin

### Goal

The core system should no longer depend directly on Wuthering Waves.

---

# Phase 3 — Analytics

- [x] Average pity
- [x] Median pity
- [x] Pity distribution
- [x] Early pull statistics
- [x] 50/50 statistics
- [x] Banner statistics
- [x] Luck percentile
- [x] Monte Carlo simulation

### Goal

Transform GachaTracker from a simple tracker into a gacha analytics platform.

---

# Phase 4 — Second Game

Add another supported game.

Potential candidates:

- Genshin Impact
- Honkai: Star Rail
- Zenless Zone Zero

This phase is important because it tests whether the plugin architecture is genuinely reusable.

### Goal

Add a second game without unnecessarily modifying the core engine.

---

# Phase 5 — Machine Learning

- [ ] Create feature extraction system
- [ ] Establish statistical baselines
- [ ] Experiment with ML models
- [ ] Compare ML against statistical methods
- [ ] Evaluate model performance
- [ ] Document limitations

### Goal

Determine whether ML provides useful information beyond traditional statistical analysis.

---

# Phase 6 — Web Dashboard

- [x] REST API
- [x] Authentication
- [x] Dashboard
- [x] Interactive charts
- [x] Pull history viewer
- [x] Pity visualization

### Goal

Make GachaTracker usable outside Discord.

---

# Phase 7 — Public Plugin Ecosystem

Eventually, developers should be able to create external GachaTracker plugins.

Conceptually:

```text
GachaTracker
│
├── WuWa Plugin
├── Genshin Plugin
├── HSR Plugin
├── ZZZ Plugin
│
└── Community Plugins
    ├── Game A
    ├── Game B
    └── Game C
```

A future plugin system could potentially support external packages such as:

```bash
pip install gachatracker-somegame
```

The exact plugin distribution mechanism will be determined later.

---

# Testing

Testing is especially important because incorrect pity calculations can produce misleading statistics.

Tests should cover:

## Core

- pull normalization
- pity calculation
- banner handling
- database operations

## Game Plugins

- API parsing
- history parsing
- banner classification
- game-specific pity rules

## Analytics

- average calculations
- percentile calculations
- probability calculations
- simulation results

Example:

```text
tests/
├── core/
│   ├── test_pity.py
│   ├── test_pull.py
│   └── test_banner.py
│
├── games/
│   └── wuthering_waves/
│       ├── test_parser.py
│       └── test_pity.py
│
└── analytics/
    ├── test_statistics.py
    └── test_simulation.py
```

---

# Security and Privacy

GachaTracker should follow a privacy-conscious design.

The system should avoid storing:

- game passwords
- unnecessary authentication tokens
- unnecessary personal information

Only information required for tracking and analysis should be stored.

Users should eventually have a way to delete their stored data.

For example:

```text
/gacha delete
```

API usage should respect the rules and limitations of the relevant game services.

---

# Design Principles

## 1. Separation of Concerns

Discord logic should not contain game-specific logic.

### Bad

```text
Discord Command
      ↓
WuWa API
      ↓
WuWa-specific calculations
```

### Better

```text
Discord Command
      ↓
GachaTracker Core
      ↓
Game Plugin
```

---

## 2. Plugin Over Duplication

Adding another game should involve creating a plugin rather than copying the entire bot.

---

## 3. Statistics Before ML

Use deterministic calculations where deterministic calculations are appropriate.

Machine learning should supplement analytics rather than replace basic mathematics.

---

## 4. Explainable Analytics

Statistics should be understandable.

For example:

```text
Luck Score: 82

Based on:

• 482 total pulls
• 7 five-stars
• Average pity: 68.9
• 57.1% 50/50 win rate
• 8-pull earliest 5★
```

This is preferable to presenting an unexplained number.

---

## 5. Game-Agnostic Core

The core engine should not contain assumptions that only apply to one game.

Game-specific rules belong inside plugins.

---

## 6. Data First

Raw imported history should be preserved in a structured form whenever practical.

Analytics should be derived from stored data rather than permanently storing only calculated results.

This allows future versions of the analytics engine to recalculate statistics without requiring users to re-import their history.

---

# Future Possibilities

The plugin architecture allows many additional features.

## Advanced Analytics

- pity heatmaps
- pull timelines
- banner comparisons
- account progression
- currency efficiency
- probability calculators
- historical trend analysis

## Social Features

- anonymous server leaderboards
- luck rankings
- pull showcases
- achievements

## Achievements

Possible achievements:

```text
🏆 Early Bird
Obtain a 5★ within 10 pulls.

🏆 Maximum Pain
Reach hard pity.

🏆 Coin Flip Master
Win 5 consecutive 50/50s.

🏆 Statistical Anomaly
Achieve an extremely unusual pull distribution.
```

## Notifications

The bot could eventually notify users when:

- a tracked banner is ending
- a new banner starts
- new history is available
- statistics are updated

## API

A public API could allow other applications to consume GachaTracker data.

---

# Example User Experience

A new user joins a Discord server running GachaTracker.

They run:

```text
/gacha
```

The bot responds:

```text
GachaTracker

Choose a game:

[ Wuthering Waves ]
[ Genshin Impact ]
[ Honkai: Star Rail ]
```

The user selects a game and imports their history.

GachaTracker processes it:

```text
Importing history...

████████████████████ 100%

482 pulls imported.
```

The user can then run:

```text
/gacha pity
/gacha stats
/gacha luck
/gacha history
```

---

# Example Multi-Game Profile

Eventually, a user could track multiple games:

```text
╭─────────────────────────────────╮
│        GachaTracker Profile     │
├─────────────────────────────────┤
│                                 │
│ Wuthering Waves                 │
│ ├── 482 pulls                   │
│ ├── 7 five-stars                │
│ └── Luck: 82/100                │
│                                 │
│ Genshin Impact                  │
│ ├── 731 pulls                   │
│ ├── 11 five-stars               │
│ └── Luck: 64/100                │
│                                 │
│ Honkai: Star Rail               │
│ ├── 392 pulls                   │
│ ├── 6 five-stars                │
│ └── Luck: 71/100                │
│                                 │
╰─────────────────────────────────╯
```

The same framework handles all supported games.

---

# Why This Project Is Interesting

GachaTracker combines several areas of software engineering and data science:

```text
                    GachaTracker
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Discord         Backend       Database
          │              │              │
          └──────────────┼──────────────┘
                         │
                 ┌───────┴───────┐
                 ▼               ▼
             Statistics          ML
                 │               │
                 └───────┬───────┘
                         ▼
                   Visualization
```

The project provides opportunities to learn and demonstrate:

- Python
- Discord development
- API integration
- software architecture
- plugin systems
- databases
- statistical analysis
- data visualization
- machine learning
- testing
- documentation
- open-source development

---

# Technology Stack

The initial implementation is expected to use:

| Component | Technology |
|---|---|
| Language | Python |
| Discord | `discord.py` |
| Database | SQLite |
| Database Layer | SQLAlchemy |
| Configuration | TOML / `.env` |
| Statistics | NumPy / SciPy |
| Data Processing | Pandas |
| ML | scikit-learn / PyTorch |
| Visualization | Matplotlib / Plotly |
| Testing | pytest |
| API | FastAPI |
| Frontend | TBD |

The technology stack may evolve during development.

---

# Performance

GachaTracker should eventually support:

- multiple Discord servers
- many users
- large pull histories
- multiple game plugins

Database queries should be indexed appropriately.

Expensive analytics should be cached or calculated asynchronously where necessary.

Large Monte Carlo simulations can be moved to background workers.

---

# Success Criteria

## MVP

- [x] WuWa history can be imported
- [x] Pull history is stored
- [x] Pity is calculated correctly
- [x] Discord commands work
- [x] Basic statistics are available

## Framework

- [x] Game plugins are isolated
- [x] Core does not depend on a specific game
- [x] A second game can be added cleanly
- [x] Plugin documentation exists (docs/PLUGIN_DEVELOPMENT.md)

## Analytics

- [x] Pity distribution
- [x] Luck analysis
- [x] Monte Carlo simulation
- [x] Statistical explanations

## Advanced

- [ ] ML experimentation
- [x] Web dashboard
- [ ] External plugin support
- [x] Public API

---

# Initial Milestone

The first concrete milestone is:

> **Transform the existing Wuthering Waves Discord tracker into the first GachaTracker plugin while keeping the current functionality working.**

Migration path:

```text
Current WuWa Bot
       │
       ▼
Architecture Refactor
       │
       ▼
GachaTracker Core
       │
       ▼
WuWa Plugin
       │
       ▼
Working GachaTracker MVP
```

Once this is stable, a second game can be implemented to validate the architecture.

---

# Repository Philosophy

GachaTracker should prioritize:

```text
Simple Core
     +
Modular Plugins
     +
Reliable Statistics
     +
Clear Documentation
     +
Extensible Architecture
```

The first version does not need every planned feature.

A small, well-designed Wuthering Waves implementation is preferable to a large unfinished multi-game system.

---

# Project Status

**Status:** Multi-game platform shipped — Discord bot (3 games), REST API, and web dashboard live; see `ROADMAP.md` for the current phase list.

### Current Focus

- Zenless Zone Zero plugin (closes Phase 8)
- Machine learning research (Phase 10)
- External plugin system (Phase 13)
- Production infrastructure (Phase 14)

### Planned

- Multi-game support
- Advanced analytics
- Monte Carlo simulation
- Machine learning experiments
- Web dashboard
- External plugin system

---

# License

TBD.

The final license will be selected before the first public release.

---

# Summary

GachaTracker aims to become more than a Discord gacha bot.

It is intended to be a **general-purpose framework for collecting, normalizing, analyzing, and visualizing gacha history across multiple games**.

The project starts with Wuthering Waves, but the architecture is designed around the idea that:

```text
One Core
   +
Many Game Plugins
   =
One Gacha Tracking Platform
```

The long-term goal is to make adding a new game straightforward while providing increasingly powerful statistical and analytical tools on top of the same underlying data.