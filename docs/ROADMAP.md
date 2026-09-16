# GachaTracker Roadmap

> Development roadmap for GachaTracker.

---

# Vision

GachaTracker aims to evolve from a **Wuthering Waves Discord tracker** into a **modular, multi-game gacha tracking and analytics platform**.

```text
Existing WuWa Bot
       │
       ▼
GachaTracker MVP
       │
       ▼
Plugin Architecture
       │
       ▼
Multi-Game Support
       │
       ▼
Advanced Analytics
       │
       ▼
ML Experiments
       │
       ▼
Web Platform
       │
       ▼
Community Plugin Ecosystem
```

---

# Phase 0 — Project Setup

### Goal

Establish the repository and development foundation.

### Tasks

- [x] Create GitHub repository (github.com/PikriNtr/GachaTracker)
- [x] Create project structure
- [x] Add `README.md`
- [x] Add `ARCHITECTURE.md`
- [x] Add `PLUGIN_DEVELOPMENT.md`
- [x] Add `ROADMAP.md`
- [x] Add `.gitignore`
- [x] Add `pyproject.toml`
- [x] Choose license
- [x] Configure formatting/linting (ruff — see pyproject.toml)
- [x] Configure pytest

### Result

A clean repository ready for development.

---

# Phase 1 — WuWa MVP

### Goal

Move the existing Wuthering Waves tracker into the new architecture.

### Tasks

- [x] Refactor existing `bot.py`
- [x] Separate Discord commands
- [x] Separate WuWa API client
- [x] Separate history parser
- [x] Create normalized `Pull` model
- [x] Create `Banner` model
- [x] Create `GameAccount` model
- [x] Implement pity calculation
- [x] Implement database storage
- [x] Implement history import
- [x] Preserve existing functionality

### Success Criteria

The existing WuWa tracker works while using the new architecture.

```text
Discord
   ↓
Core
   ↓
WuWa Plugin
   ↓
Database
```

---

# Phase 2 — Core Abstraction

### Goal

Remove WuWa-specific assumptions from the core.

### Tasks

- [x] Create `GachaGame` interface
- [x] Create plugin registry
- [x] Create game abstraction
- [x] Create generic banner system
- [x] Create generic pity system
- [x] Create normalized pull system
- [x] Move WuWa implementation into plugin
- [x] Add plugin tests

### Success Criteria

The core can operate without importing WuWa-specific modules directly.

---

# Phase 3 — Data Layer

### Goal

Create a reliable persistence system.

### Tasks

- [x] Finalize database schema
- [x] Implement repository layer
- [x] Add database migrations
- [x] Add indexes
- [x] Add duplicate detection
- [x] Add import transactions
- [x] Add data deletion (`/forget` command + `Repository.delete_user_data`)
- [x] Add backup considerations (see Data Backup section below)

### Success Criteria

History can be imported repeatedly without creating duplicate records.

Example:

```text
Initial import:
482 records → 482 inserted

Second import:
482 records → 0 inserted

New history:
500 records → 18 inserted
```

### Data Backup

All state is a single SQLite file: `gacha_tracker/data/gachatracker.db`
(excluded from git). Backup = copy that file while the bot is stopped, or use
`sqlite3 data/gachatracker.db ".backup 'backup.db'"` while it runs. Restore =
replace the file and restart. To wipe a game entirely, users run `/forget`.

---

# Phase 4 — Analytics

### Goal

Turn GachaTracker into an analytics system rather than just a history viewer.

### Tasks

- [x] Total pull count
- [x] 5★ count
- [x] 4★ count
- [x] Average pity
- [x] Median pity (`analytics/deep_stats.py`)
- [x] Minimum pity (`analytics/deep_stats.py`)
- [x] Maximum pity (`analytics/deep_stats.py`)
- [x] Standard deviation (`analytics/deep_stats.py`)
- [x] Banner statistics
- [x] Character statistics (`deep_stats.char_5star`)
- [x] Weapon statistics (`deep_stats.weapon_5star`)
- [x] 50/50 statistics
- [x] Early 5★ statistics (`deep_stats.early_count`, threshold ≤30)

### Success Criteria

Users can meaningfully analyze their own history.

---

# Phase 5 — Visualization

### Goal

Make statistics easier to understand.

### Tasks

- [x] Pity distribution
- [x] Pull timeline (`/chart type:Pull Timeline`)
- [x] Banner comparison (`/chart type:Banner Comparison`)
- [x] Rarity distribution (`/chart type:Rarity Distribution`)
- [x] 5★ interval chart (covered by Pull Timeline — each 5★ marker shows its pity, i.e. the interval since the previous 5★)
- [x] Banner schedule Gantt (`/chart type:Banner Schedule`)
- [x] Luck percentile visualization
- [x] Discord image/chart generation

Example:

```text
Pity Distribution

80 ┤       █
70 ┤   █   █ █
60 ┤ █ █ █ █ █
50 ┤ █ █ █ █ █ █
40 ┤ █ █ █ █ █ █
   └────────────────
```

---

# Phase 6 — Luck Analysis

### Goal

Create a statistical interpretation of pull history.

### Tasks

- [x] Define luck metric
- [x] Establish statistical baseline
- [x] Calculate percentile
- [x] Compare pity against expected values
- [x] Compare 50/50 performance
- [x] Document methodology (`docs/LUCK_METHODOLOGY.md`)
- [x] Avoid misleading "luck prediction"

### Success Criteria

The bot can explain why a user is statistically above or below a reference distribution.

---

# Phase 7 — Monte Carlo Simulation

### Goal

Allow users to compare their history against simulated histories.

### Tasks

- [x] Build simulation engine
- [x] Configure game probability models
- [x] Generate simulated histories
- [x] Calculate simulated distributions
- [x] Calculate percentiles
- [x] Compare real vs simulated history
- [x] Optimize large simulations

Example:

```text
10,000 simulated histories
          │
          ▼
   Pity Distribution
          │
          ▼
   Compare User Data
          │
          ▼
     Percentile
```

---

# Phase 8 — Second Game

### Goal

Prove that the plugin architecture works.

Potential games:

- [x] Genshin Impact
- [x] Honkai: Star Rail
- [ ] Zenless Zone Zero

Only one should be implemented initially.

### Success Criteria

A second game can be added without rewriting the core.

---

# Phase 9 — Multi-Game Profiles

### Goal

Allow users to track multiple games simultaneously.

Example:

```text
User
│
├── Wuthering Waves
│   └── 482 pulls
│
├── Genshin Impact
│   └── 731 pulls
│
└── Honkai: Star Rail
    └── 392 pulls
```

### Tasks

- [x] Multi-game accounts
- [x] Game selector
- [x] Game-specific profiles
- [x] Unified profile (`/profile` with comparison chart)
- [x] Cross-game statistics

---

# Phase 10 — Machine Learning Research

### Goal

Explore whether machine learning can provide useful analysis beyond traditional statistics.

### Tasks

- [ ] Define ML research questions
- [ ] Build dataset pipeline
- [ ] Create feature extraction
- [ ] Establish statistical baselines
- [ ] Implement baseline ML models
- [ ] Evaluate models
- [ ] Document results
- [ ] Determine whether ML provides meaningful value

Potential experiments:

```text
Classification
Regression
Clustering
Anomaly Detection
Probability Estimation
```

### Important Constraint

ML should not be marketed as a reliable predictor of random gacha outcomes.

The project should explicitly document the limitations.

---

# Phase 11 — REST API

### Goal

Separate the GachaTracker core from the Discord interface.

### Tasks

- [x] Create FastAPI application
- [x] Authentication
- [x] Account endpoints
- [x] Pull endpoints
- [x] Statistics endpoints
- [x] Pity endpoints
- [x] API documentation

Possible endpoints:

```text
GET /games
GET /accounts
GET /accounts/{id}
GET /accounts/{id}/pulls
GET /accounts/{id}/pity
GET /accounts/{id}/statistics
```

---

# Phase 12 — Web Dashboard

### Goal

Provide a visual interface for users.

### Tasks

- [x] Dashboard design
- [x] Account overview
- [x] Pull history
- [x] Pity visualization
- [x] Banner statistics
- [x] Luck analysis
- [x] Interactive charts
- [x] Responsive design

Architecture:

```text
             GachaTracker
                  │
              REST API
                  │
             ┌────┴────┐
             ▼         ▼
          Discord   Dashboard
```

---

# Phase 13 — External Plugin System

### Goal

Allow developers to create third-party game plugins.

### Tasks

- [ ] Define plugin specification
- [ ] Define plugin metadata
- [ ] Define plugin discovery
- [ ] Define version compatibility
- [ ] Define plugin validation
- [ ] Create plugin template
- [ ] Create plugin documentation
- [ ] Create example third-party plugin

Potential future installation:

```bash
pip install gachatracker-examplegame
```

---

# Phase 14 — Production Infrastructure

### Goal

Make the project suitable for larger deployments.

### Tasks

- [ ] PostgreSQL support
- [ ] Docker support
- [ ] Background workers
- [ ] Caching
- [ ] Rate limiting
- [ ] Monitoring
- [ ] Error reporting
- [ ] Automated backups
- [ ] CI/CD

Potential architecture:

```text
                 Load Balancer
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
      Discord Bot                REST API
          │                         │
          └────────────┬────────────┘
                       ▼
                   Services
                       │
              ┌────────┴────────┐
              ▼                 ▼
          PostgreSQL          Worker
```

---

# Milestones

## v0.1 — WuWa Tracker

- [x] Existing WuWa functionality migrated
- [x] Basic database
- [x] Pity calculation
- [x] Discord commands

---

## v0.2 — Core Framework

- [x] Plugin interface
- [x] Plugin registry
- [x] Normalized data model
- [x] WuWa plugin

---

## v0.3 — Analytics

- [x] Statistics
- [x] Pity distribution
- [x] Luck analysis
- [x] Simulation

---

## v0.4 — Multi-Game

- [x] Second game
- [x] Multi-game accounts
- [x] Game selection

---

## v0.5 — ML Research

- [ ] Dataset pipeline
- [ ] Baseline models
- [ ] ML experiments
- [ ] Evaluation

---

## v0.6 — API

- [x] REST API (FastAPI, `api/` package, shipped Phase 11)
- [x] Authentication (X-API-Key for writes, optional key-gating for reads)
- [x] API documentation (Swagger at `/docs`, ReDoc at `/redoc`)

---

## v0.7 — Dashboard

- [x] Web dashboard (`api/static/`, served by the API at `/`)
- [x] Charts (interactive, per-game tabs)
- [x] Account management (Discord-ID lookup, `?id=` URL parameter)

---

## v1.0 — GachaTracker Platform

Target capabilities:

- [ ] Stable core
- [ ] Multiple game plugins
- [ ] Reliable analytics
- [ ] Discord interface
- [ ] REST API
- [ ] Web dashboard
- [ ] Plugin documentation
- [ ] Automated tests
- [ ] Production deployment support

---

# Development Priorities

When deciding what to implement next, prioritize:

```text
Correctness
    ↓
Architecture
    ↓
Testing
    ↓
Core Features
    ↓
Analytics
    ↓
Performance
    ↓
Advanced Features
```

Avoid implementing advanced features before the underlying data model is stable.

---

# What Should NOT Be Done Too Early

The following should not be priorities during the first MVP:

- Machine learning
- Web dashboard
- Public API
- External plugin marketplace
- Complex distributed infrastructure
- PostgreSQL
- Microservices

The initial focus should be:

```text
WuWa
 ↓
Core
 ↓
Database
 ↓
Pity
 ↓
Analytics
```

---

# Definition of Done

A feature is considered complete when:

- [ ] Implementation exists
- [ ] Tests exist
- [ ] Error handling exists
- [ ] Documentation exists
- [ ] Existing functionality still works
- [ ] No unnecessary game-specific code was introduced into the core

---

# Long-Term Vision

The final goal is not simply:

> "A Discord bot that tracks gacha."

The long-term goal is:

> **A modular platform for collecting, normalizing, analyzing, and visualizing gacha history across multiple games.**

The evolution should look like:

```text
                 GachaTracker
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
    Discord          Web            API
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Core Engine
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      Gacha       Analytics         DB
        │             │
        │        ┌────┴────┐
        │        ▼         ▼
        │      Stats       ML
        │
        ▼
   Plugin System
   ┌────┼────┬────┐
   ▼    ▼    ▼    ▼
 WuWa  GI   HSR  ZZZ
```

---

# Current Focus

Phases 0–9 and 11–12 are complete: multi-game Discord experience
(import/pity/stats/history/chart/simulate/profile/forget/banners), three live game
plugins (Wuthering Waves, Genshin Impact, Honkai: Star Rail), per-game pity
and probability models, idempotent imports with api-based deduplication,
deep statistics, a full visualization suite (including the banner-schedule
Gantt), the REST API (Phase 11), and the interactive web dashboard (Phase 12).

The remaining phases are 8's last game (Zenless Zone Zero), 10 (ML research),
13 (external plugin system), and 14 (production infrastructure).

---

# Status

**Current Stage:** Multi-game platform with API + dashboard (Phases 0–9, 11–12 complete)

**Current Target:** v1.0 — Platform (ZZZ plugin, ML research, external plugins, production infra)

**Next Major Milestone:** Zenless Zone Zero plugin (closes Phase 8) or production infrastructure (Phase 14)
