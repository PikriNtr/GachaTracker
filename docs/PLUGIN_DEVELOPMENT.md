# GachaTracker Plugin Development

> Guide for creating game plugins for GachaTracker.

---

# 1. Introduction

GachaTracker uses a plugin architecture to support multiple games.

Each game plugin is responsible for implementing game-specific behavior while the GachaTracker core provides common functionality.

```text
                 GachaTracker
                      │
                 Plugin API
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     WuWa          Genshin          HSR
    Plugin          Plugin         Plugin
```

The goal is to make adding a new game predictable and straightforward.

---

# 2. What a Plugin Does

A game plugin may be responsible for:

- identifying the game
- connecting to the game's history source
- importing history
- parsing API responses
- normalizing pull records
- defining banners
- defining rarity rules
- defining pity rules
- defining featured item rules
- defining game-specific metadata

A plugin should **not** be responsible for:

- Discord command handling
- user authentication
- database connection management
- global analytics
- Discord embed formatting

Those responsibilities belong to the core/application layers.

---

# 3. Plugin Structure

A typical plugin:

```text
games/
└── my_game/
    ├── __init__.py
    ├── game.py
    ├── api.py
    ├── parser.py
    ├── banners.py
    ├── pity.py
    └── tests/
        ├── test_api.py
        ├── test_parser.py
        └── test_pity.py
```

Not every plugin will require every file.

---

# 4. Game Definition

The plugin should define the basic identity of the game.

Conceptually:

```python
class MyGame(GachaGame):

    id = "my_game"
    name = "My Game"
```

The ID should be:

- lowercase
- stable
- unique
- suitable for database storage

Example:

```text
wuthering_waves
genshin
star_rail
zzz
```

---

# 5. History Import

The plugin implements the game's history import process.

Conceptually:

```python
def import_history(self, source):
    data = self.api.fetch_history(source)
    return self.parser.parse(data)
```

The import process should:

1. obtain the history
2. validate the response
3. parse the response
4. normalize the records
5. return normalized pulls

---

# 6. API Layer

If a game provides an API or history endpoint, API communication should be isolated in:

```text
api.py
```

Example:

```python
class MyGameAPI:

    async def fetch_history(self, ...):
        ...
```

The API layer should not calculate pity.

It should only retrieve the data.

---

# 7. Parser Layer

The parser converts raw API responses into normalized objects.

Example:

```python
class MyGameParser:

    def parse(self, data):
        pulls = []

        for record in data:
            pulls.append(
                Pull(
                    item_id=record["id"],
                    item_name=record["name"],
                    rarity=record["rarity"],
                    timestamp=record["timestamp"]
                )
            )

        return pulls
```

The actual implementation will depend on the game.

---

# 8. Normalized Pull

All plugins should eventually produce a common pull representation.

Example:

```python
Pull(
    item_id="character_001",
    item_name="Example Character",
    rarity=5,
    banner_id="banner_001",
    banner_type="character",
    timestamp=timestamp
)
```

The normalized representation should contain only information that is useful to the core.

Game-specific raw fields can be stored separately if necessary.

---

# 9. Banner Definitions

Games may have multiple banner types.

Example:

```python
Banners = {
    "character_event": ...,
    "weapon_event": ...,
    "standard": ...
}
```

A banner definition may include:

```text
ID
Name
Type
Start Time
End Time
Rarity Rules
Pity Rules
Featured Rules
```

---

# 10. Pity System

Pity calculation should follow the game's actual mechanics.

A plugin may define:

```python
class MyGamePity(PitySystem):

    def calculate(self, history):
        ...
```

The pity system should be deterministic whenever the game rules are deterministic.

---

# 11. Pity Reset

The plugin must correctly identify when pity resets.

Example:

```text
Pull 1
Pull 2
Pull 3
...
Pull 72 → 5★
         ↓
       Reset
Pull 1
Pull 2
```

The exact reset behavior depends on the banner and game.

---

# 12. Multiple Pity Systems

Some games may have different pity counters.

For example:

```text
Character Banner
Weapon Banner
Standard Banner
```

The plugin should ensure each system is tracked independently.

Conceptually:

```text
Account
│
├── Character Pity
├── Weapon Pity
└── Standard Pity
```

---

# 13. Featured Items

Games may use featured-item mechanics.

A plugin should define how to identify:

```text
Featured
Non-featured
Guaranteed
Off-banner
```

This information can later be used by the analytics engine.

---

# 14. 50/50 Systems

If a game uses a 50/50 mechanic, the plugin should expose enough information for the core to determine:

```text
Won
Lost
Guaranteed
Unknown
```

The plugin should not assume that every game uses a 50/50 system.

---

# 15. Plugin Registration

Once the plugin is implemented, it should be registered with GachaTracker.

Conceptually:

```python
registry.register(MyGame())
```

The registry can then expose:

```python
registry.get("my_game")
```

---

# 16. Dynamic Loading

A future version may support automatic plugin discovery.

Possible approach:

```text
plugins/
│
├── wuthering_waves
├── genshin
└── star_rail
```

GachaTracker scans the plugin directory and loads valid plugins.

An external package system could eventually be supported.

---

# 17. Validation

Plugins should validate incoming data.

Examples:

```text
Missing item ID
Invalid rarity
Invalid timestamp
Unknown banner
Duplicate pull
Malformed API response
```

Invalid data should not silently enter the database.

---

# 18. Duplicate Detection

History APIs may return records that have already been imported.

The import system should therefore support idempotent imports.

Example:

```text
First import:
482 pulls → 482 new

Second import:
482 pulls → 0 new
```

If the second import contains new pulls:

```text
First import:
482 pulls

Second import:
500 pulls

Result:
18 new pulls
```

---

# 19. Ordering

Pull history should have a consistent ordering.

Internally, timestamps should be used whenever available.

The plugin should not rely solely on API response order unless the API guarantees it.

---

# 20. Time Handling

Timestamps should be normalized.

Prefer storing timestamps in UTC internally.

Display them using the user's configured timezone.

```text
Stored:
2026-09-12T12:00:00Z

Displayed:
2026-09-12 20:00
```

---

# 21. Error Handling

Plugins should raise meaningful errors.

Example:

```python
class MyGameAPIError(Exception):
    pass
```

Possible categories:

```text
APIError
AuthenticationError
ParseError
RateLimitError
InvalidHistoryError
```

The core can then convert these into user-friendly Discord responses.

---

# 22. Rate Limiting

Game APIs may impose rate limits.

Plugins should avoid unnecessary requests.

Possible strategies:

- caching
- pagination
- request throttling
- incremental imports

An import should fetch only the data necessary to update the user's history whenever possible.

---

# 23. Testing

Every plugin should include tests.

At minimum:

```text
tests/
├── test_parser.py
├── test_pity.py
└── test_banners.py
```

---

## Parser Tests

Test known API responses.

Example:

```python
def test_parse_pull():
    data = load_fixture("pull.json")

    result = parser.parse(data)

    assert result[0].rarity == 5
```

---

## Pity Tests

Use known pull sequences.

Example:

```text
3★
4★
3★
5★
```

Expected:

```text
Pity = 4
```

Test edge cases such as:

- first pull is 5★
- hard pity
- consecutive 5★
- multiple banners
- imported history gaps

---

# 24. Test Fixtures

Raw API responses should be stored as fixtures.

```text
tests/
└── fixtures/
    ├── history_page_1.json
    ├── history_page_2.json
    └── malformed_response.json
```

This avoids depending on live APIs during tests.

---

# 25. Plugin Quality Checklist

Before a plugin is considered stable:

- [ ] Game identity implemented
- [ ] History import implemented
- [ ] Parser implemented
- [ ] Pull normalization implemented
- [ ] Banner definitions implemented
- [ ] Pity rules implemented
- [ ] Featured item logic implemented
- [ ] Duplicate detection tested
- [ ] API errors handled
- [ ] Parser tests written
- [ ] Pity tests written
- [ ] Documentation written

---

# 26. Example Plugin

Conceptual implementation:

```python
class ExampleGame(GachaGame):

    id = "example_game"
    name = "Example Game"

    async def import_history(self, source):
        data = await self.api.fetch_history(source)

        pulls = self.parser.parse(data)

        return pulls

    def calculate_pity(self, history):
        return self.pity.calculate(history)

    def get_banners(self):
        return self.banners
```

The implementation should remain focused on game-specific behavior.

---

# 27. Plugin Development Philosophy

A plugin should answer:

> "How does this particular game represent and calculate gacha?"

The core should answer:

> "How does GachaTracker store, analyze, and present gacha information?"

This distinction is fundamental.

---

# 28. Adding a New Game

Recommended workflow:

```text
1. Create plugin directory
        ↓
2. Implement game definition
        ↓
3. Implement API client
        ↓
4. Implement parser
        ↓
5. Normalize pulls
        ↓
6. Define banners
        ↓
7. Implement pity rules
        ↓
8. Add tests
        ↓
9. Register plugin
        ↓
10. Test Discord commands
```

---

# 29. Future External Plugins

A future version may support third-party packages.

Potential concept:

```bash
pip install gachatracker-examplegame
```

The package could expose:

```python
GachaGamePlugin
```

GachaTracker would discover and register it automatically.

This would allow the community to add games without modifying the main repository.

---

# 30. Summary

A GachaTracker plugin should be:

```text
Small
│
├── Game-specific
├── Testable
├── Independent
└── Compatible with the Core
```

The core handles common functionality.

The plugin handles game-specific functionality.

```text
             GachaTracker Core
                     │
                Plugin API
                     │
              ┌──────┴──────┐
              ▼             ▼
          Game Plugin    Game Plugin
              │             │
          Game Rules    Game Rules
```

This architecture allows GachaTracker to grow without turning the core into a collection of game-specific code.