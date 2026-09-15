# GachaTracker Architecture

> Technical architecture and design specification for GachaTracker.

---

## 1. Overview

GachaTracker is designed as a modular application consisting of:

- a Discord interface
- a game-agnostic core
- game-specific plugins
- a persistence layer
- an analytics layer
- an optional machine learning layer
- an optional web API and dashboard

The primary architectural goal is to keep **game-specific logic isolated from the core system**.

```text
                         GachaTracker
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       Discord              Core              Web API
       Interface             Engine                │
                              │                    ▼
                    ┌─────────┼─────────┐      Dashboard
                    │         │         │
                    ▼         ▼         ▼
                 Gacha     Analytics  Database
                    │
                    ▼
              Plugin System
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        WuWa     Genshin     HSR
```

---

# 2. Architectural Principles

## 2.1 Separation of Concerns

Each component should have a clearly defined responsibility.

```text
Discord
  ↓
Application
  ↓
Core
  ↓
Plugin
  ↓
Data
```

Discord commands should not directly implement game-specific calculations.

---

## 2.2 Game-Agnostic Core

The core should work without knowing the internal mechanics of a particular game.

For example, the core should understand:

```text
Pull
Banner
Rarity
Pity
Game Account
Statistics
```

But it should not contain:

```text
WuWa-specific API parsing
Genshin-specific API parsing
HSR-specific banner rules
```

Those belong to plugins.

---

## 2.3 Plugin Isolation

A game plugin should be independently testable.

```text
games/
├── wuthering_waves/
├── genshin/
├── star_rail/
└── zzz/
```

A failure in one plugin should not affect unrelated plugins.

---

## 2.4 Statistics Before Machine Learning

Deterministic calculations should be performed using traditional algorithms.

For example:

```text
Pity calculation
Average pity
Median pity
Pull counts
5★ counts
50/50 statistics
```

Machine learning should only be introduced where it provides a meaningful experimental benefit.

---

# 3. System Layers

## 3.1 Interface Layer

The interface layer handles communication with users.

Initial interface:

```text
Discord
```

Future interfaces:

```text
REST API
Web Dashboard
CLI
```

---

## 3.2 Application Layer

The application layer handles:

- command registration
- command validation
- user interaction
- response formatting
- permissions
- error handling

Example:

```text
/gacha pity
      │
      ▼
Command Handler
      │
      ▼
Core Service
```

The application layer should not directly calculate pity.

---

# 4. Core Engine

The core engine provides shared gacha functionality.

Possible components:

```text
core/
├── game.py
├── player.py
├── account.py
├── pull.py
├── banner.py
├── pity.py
└── statistics.py
```

---

## 4.1 Game

Represents a supported game.

```python
Game(
    id="wuthering_waves",
    name="Wuthering Waves"
)
```

---

## 4.2 Game Account

Represents a user's account for a particular game.

```text
GameAccount
├── id
├── user_id
├── game_id
├── server
└── metadata
```

A user may have multiple game accounts.

```text
User
├── WuWa Account
├── Genshin Account
└── HSR Account
```

---

## 4.3 Pull

A pull is the smallest unit of gacha history.

Conceptually:

```python
Pull(
    item_id="example",
    item_name="Example Character",
    rarity=5,
    banner_type="character",
    timestamp=...,
    pity=72
)
```

---

## 4.4 Banner

Represents a gacha banner.

```text
Banner
├── id
├── game_id
├── name
├── type
├── start_time
└── end_time
```

---

# 5. Normalization Layer

Different games expose different API structures.

The normalization layer converts those formats into a common representation.

```text
WuWa API
    │
    ▼
WuWa Parser
    │
    ▼
Normalized Pull
```

and:

```text
Genshin API
    │
    ▼
Genshin Parser
    │
    ▼
Normalized Pull
```

Both eventually produce:

```text
Pull
```

This is one of the most important parts of the architecture.

---

# 6. Plugin Layer

The plugin layer provides game-specific implementations.

```text
games/
│
├── wuthering_waves/
│   ├── game.py
│   ├── api.py
│   ├── parser.py
│   ├── banners.py
│   └── pity.py
│
├── genshin/
│   └── ...
│
└── star_rail/
    └── ...
```

---

# 7. Plugin Interface

Conceptually, a plugin should implement something similar to:

```python
class GachaGame:
    name: str

    def import_history(self, data):
        raise NotImplementedError

    def normalize_pull(self, data):
        raise NotImplementedError

    def get_banners(self):
        raise NotImplementedError

    def calculate_pity(self, history):
        raise NotImplementedError
```

The final interface may evolve.

---

# 8. Plugin Registry

GachaTracker should maintain a registry of available games.

Conceptually:

```python
registry.register(WutheringWaves())
registry.register(Genshin())
registry.register(StarRail())
```

A command can then request:

```python
game = registry.get("wuthering_waves")
```

The command does not need to import the WuWa implementation directly.

---

# 9. Import Pipeline

History importing should follow this flow:

```text
User
 │
 ▼
Import Command
 │
 ▼
Game Plugin
 │
 ├── Fetch
 │
 ├── Parse
 │
 └── Normalize
 │
 ▼
Core
 │
 ▼
Validation
 │
 ▼
Database
 │
 ▼
Analytics
```

---

# 10. Database Layer

The database should be accessed through a repository/data-access layer.

Instead of:

```text
Discord Command
      ↓
SQL Query
```

use:

```text
Discord Command
      ↓
Service
      ↓
Repository
      ↓
Database
```

This keeps database implementation details out of the rest of the application.

---

# 11. Database Schema

Initial entities:

```text
User
Game
GameAccount
Banner
Pull
```

Relationship:

```text
User
 │
 ├── GameAccount
 │       │
 │       ├── Pull
 │       ├── Pull
 │       └── Pull
 │
 └── GameAccount
         │
         └── Pull
```

---

# 12. Analytics Layer

Analytics should consume normalized data.

```text
Database
    │
    ▼
Analytics Engine
    │
 ┌──┼───────────┐
 ▼  ▼           ▼
Pity Luck   Distribution
 │
 ▼
Probability
```

Analytics should not directly depend on Discord.

This means the same analytics can be used by:

```text
Discord
Web Dashboard
REST API
CLI
```

---

# 13. Statistics Pipeline

Example:

```text
Pull History
     │
     ▼
Filter by Banner
     │
     ▼
Calculate Pity
     │
     ▼
Calculate Statistics
     │
     ├── Average
     ├── Median
     ├── Minimum
     ├── Maximum
     └── Standard Deviation
```

---

# 14. Simulation Layer

Monte Carlo simulation should be separate from normal statistics.

```text
Historical Data
      │
      ▼
Simulation Configuration
      │
      ▼
Monte Carlo Engine
      │
      ▼
Simulated Histories
      │
      ▼
Comparison
      │
      ▼
Percentile
```

---

# 15. Machine Learning Layer

ML should be isolated from the main analytics engine.

```text
ml/
├── features.py
├── datasets.py
├── models.py
├── training.py
└── evaluation.py
```

The ML layer can consume normalized data:

```text
Pull History
     │
     ▼
Feature Extraction
     │
     ▼
ML Model
     │
     ▼
Prediction / Classification
```

ML results should never replace deterministic pity calculations.

---

# 16. Service Layer

Business logic can be exposed through services.

Example:

```text
services/
├── gacha_service.py
├── account_service.py
├── import_service.py
└── analytics_service.py
```

Example flow:

```python
stats = gacha_service.get_statistics(
    account_id=123
)
```

The Discord command only needs to display the result.

---

# 17. Discord Architecture

The Discord layer could eventually look like:

```text
bot/
├── bot.py
├── commands/
│   ├── gacha.py
│   ├── account.py
│   └── profile.py
├── embeds/
└── views/
```

Commands should remain relatively thin.

Example:

```text
/gacha stats
     │
     ▼
Command
     │
     ▼
Analytics Service
     │
     ▼
Database
     │
     ▼
Statistics
     │
     ▼
Discord Embed
```

---

# 18. Error Handling

Errors should be categorized.

```text
ImportError
APIError
ParserError
DatabaseError
PluginError
ValidationError
```

The user should receive a useful message without exposing internal errors.

Bad:

```text
KeyError: 'records'
```

Better:

```text
Unable to import your history.

The game API returned an unexpected response.
Please try again later.
```

Internal logs can contain more detailed information.

---

# 19. Logging

Logging should provide enough information for debugging.

Suggested levels:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Example:

```text
INFO  Loading Wuthering Waves plugin
INFO  Import started for account 123
INFO  Imported 482 pulls
WARNING  Duplicate pull detected
INFO  Import completed
```

Sensitive information should not be logged.

---

# 20. Future API Architecture

A REST API can eventually expose the same core services.

```text
Discord ─────┐
             │
Web ─────────┼──► GachaTracker Services
             │
CLI ─────────┘
```

Possible API:

```text
GET /games
GET /accounts
GET /accounts/{id}/pulls
GET /accounts/{id}/pity
GET /accounts/{id}/statistics
```

The exact API will be defined later.

---

# 21. Future Dashboard

The dashboard should consume the API rather than directly access the database.

```text
Database
    ▲
    │
Backend API
    ▲
    │
Dashboard
```

This preserves the separation between frontend and backend.

---

# 22. Security Boundaries

Sensitive data should remain inside the appropriate layer.

```text
Discord
   │
   ▼
Authentication
   │
   ▼
Application
   │
   ▼
Services
   │
   ▼
Database
```

Game credentials should not be required unless absolutely necessary.

---

# 23. Deployment

Initial deployment:

```text
Linux Server
│
├── GachaTracker
├── SQLite
└── Discord Bot
```

Future deployment:

```text
Server
│
├── Discord Bot
├── API
├── PostgreSQL
├── Worker
└── Dashboard
```

Docker support can be introduced later.

---

# 24. Architectural Priority

When adding new features, prioritize:

1. Correctness
2. Maintainability
3. Testability
4. Extensibility
5. Performance

Avoid adding complexity before it is necessary.

---

# 25. Summary

The architecture is centered around one principle:

```text
                GachaTracker Core
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
    Discord          Web API           CLI
                       │
                       ▼
                  Core Services
                       │
              ┌────────┴────────┐
              ▼                 ▼
          Analytics          Database
              │
              ▼
         Game Plugins
       ┌──────┼──────┐
       ▼      ▼      ▼
     WuWa   Genshin  HSR
```

Game-specific logic stays in plugins.

Common functionality stays in the core.

This makes GachaTracker scalable from a single-game Discord bot into a multi-game gacha analytics platform.