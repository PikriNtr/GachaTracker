import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.models import Pull, GameAccount
from config import DB_PATH


class Repository:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Accounts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                player_id TEXT NOT NULL,
                server TEXT DEFAULT 'global',
                metadata TEXT,
                UNIQUE(discord_id, game_id, player_id)
            )
            """)

            # Pulls table — dedup is handled by partial unique indexes below
            # (api_id when the game API provides one, natural key otherwise),
            # so the table itself carries no inline UNIQUE constraint.
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pulls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                player_id TEXT NOT NULL,
                card_pool_type TEXT NOT NULL,
                resource_id TEXT,
                resource_name TEXT NOT NULL,
                quality_level INTEGER NOT NULL,
                time TEXT NOT NULL,
                item_type TEXT DEFAULT '',
                api_id TEXT DEFAULT '',
                pity_at_pull INTEGER DEFAULT 0,
                is_5050_win INTEGER
            )
            """)

            # Migrations for DBs created before these columns existed
            cursor.execute("PRAGMA table_info(pulls)")
            cols = {row[1] for row in cursor.fetchall()}
            if "item_type" not in cols:
                cursor.execute("ALTER TABLE pulls ADD COLUMN item_type TEXT DEFAULT ''")
            if "api_id" not in cols:
                cursor.execute("ALTER TABLE pulls ADD COLUMN api_id TEXT DEFAULT ''")

            # Legacy DBs carry an inline UNIQUE(discord_id, game_id, player_id,
            # card_pool_type, resource_name, time) which collapses distinct pulls
            # sharing a timestamp (e.g. duplicate items inside one 10-pull).
            # Detect it and rebuild the table without it, preserving all rows.
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='pulls'")
            table_sql = cursor.fetchone()["sql"] or ""
            if "UNIQUE(" in table_sql.replace(" ", "").upper():
                cursor.execute("ALTER TABLE pulls RENAME TO pulls_legacy")
                cursor.execute("""
                CREATE TABLE pulls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    player_id TEXT NOT NULL,
                    card_pool_type TEXT NOT NULL,
                    resource_id TEXT,
                    resource_name TEXT NOT NULL,
                    quality_level INTEGER NOT NULL,
                    time TEXT NOT NULL,
                    item_type TEXT DEFAULT '',
                    api_id TEXT DEFAULT '',
                    pity_at_pull INTEGER DEFAULT 0,
                    is_5050_win INTEGER
                )
                """)
                cursor.execute("""
                INSERT INTO pulls
                    (discord_id, game_id, player_id, card_pool_type, resource_id, resource_name,
                     quality_level, time, item_type, api_id, pity_at_pull, is_5050_win)
                SELECT discord_id, game_id, player_id, card_pool_type, resource_id, resource_name,
                       quality_level, time, COALESCE(item_type, ''), COALESCE(api_id, ''),
                       pity_at_pull, is_5050_win
                FROM pulls_legacy
                """)
                cursor.execute("DROP TABLE pulls_legacy")

            # Dedup indexes:
            # - api_id (Genshin/HSR): the API's per-pull id is unique, even inside
            #   one 10-pull where names/timestamps repeat.
            # - natural key (WuWa, no per-pull id): old behavior.
            cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pulls_api_id
            ON pulls(discord_id, game_id, api_id)
            WHERE api_id != ''
            """)
            cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pulls_natural
            ON pulls(discord_id, game_id, player_id, card_pool_type, resource_name, time)
            WHERE api_id = ''
            """)
            conn.commit()

    def save_account(self, discord_id: str, game_id: str, player_id: str, metadata: Optional[Dict[str, Any]] = None) -> GameAccount:
        meta_json = json.dumps(metadata or {})
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO accounts (discord_id, game_id, player_id, metadata)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(discord_id, game_id, player_id) DO UPDATE SET metadata=excluded.metadata
            """, (discord_id, game_id, player_id, meta_json))
            conn.commit()
            account_id = cursor.lastrowid

        return GameAccount(id=account_id, discord_id=discord_id, game_id=game_id, player_id=player_id, metadata=metadata or {})

    def get_account_by_discord_id(self, discord_id: str, game_id: str = "wuthering_waves") -> Optional[GameAccount]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, discord_id, game_id, player_id, server, metadata
            FROM accounts
            WHERE discord_id = ? AND game_id = ?
            LIMIT 1
            """, (discord_id, game_id))
            row = cursor.fetchone()
            if not row:
                return None
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            return GameAccount(id=row["id"], discord_id=row["discord_id"], game_id=row["game_id"], player_id=row["player_id"], server=row["server"], metadata=meta)

    def save_pulls(self, discord_id: str, game_id: str, player_id: str, pulls: List[Pull]) -> int:
        """Saves pulls idempotently. Returns count of newly inserted pulls.

        Dedup scheme:
        - Pulls with an api_id (Genshin/HSR): unique on (discord_id, game_id, api_id).
        - Pulls without one (WuWa): unique on the (player, pool, name, time) natural key.
        """
        inserted_count = 0
        with self._get_conn() as conn:
            cursor = conn.cursor()
            for p in pulls:
                win_val = 1 if p.is_5050_win is True else (0 if p.is_5050_win is False else None)
                cursor.execute("""
                INSERT OR IGNORE INTO pulls 
                (discord_id, game_id, player_id, card_pool_type, resource_id, resource_name, quality_level, time, item_type, api_id, pity_at_pull, is_5050_win)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (discord_id, game_id, player_id, p.card_pool_type, p.resource_id, p.resource_name, p.quality_level, p.time, p.item_type, p.api_id, p.pity_at_pull, win_val))
                if cursor.rowcount > 0:
                    inserted_count += 1
            conn.commit()
        return inserted_count

    def get_pulls(self, discord_id: str, game_id: str = "wuthering_waves", card_pool_type: Optional[str] = None) -> List[Pull]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if card_pool_type:
                cursor.execute("""
                SELECT card_pool_type, resource_id, resource_name, quality_level, time, player_id, game_id, item_type, api_id, pity_at_pull, is_5050_win
                FROM pulls
                WHERE discord_id = ? AND game_id = ? AND card_pool_type = ?
                ORDER BY time ASC
                """, (discord_id, game_id, str(card_pool_type)))
            else:
                cursor.execute("""
                SELECT card_pool_type, resource_id, resource_name, quality_level, time, player_id, game_id, item_type, api_id, pity_at_pull, is_5050_win
                FROM pulls
                WHERE discord_id = ? AND game_id = ?
                ORDER BY time ASC
                """, (discord_id, game_id))
            
            rows = cursor.fetchall()
            result = []
            for r in rows:
                win_val = True if r["is_5050_win"] == 1 else (False if r["is_5050_win"] == 0 else None)
                result.append(Pull(
                    card_pool_type=r["card_pool_type"],
                    resource_id=r["resource_id"],
                    resource_name=r["resource_name"],
                    quality_level=r["quality_level"],
                    time=r["time"],
                    player_id=r["player_id"],
                    game_id=r["game_id"],
                    item_type=r["item_type"] or "",
                    api_id=r["api_id"] or "",
                    pity_at_pull=r["pity_at_pull"],
                    is_5050_win=win_val
                ))
            return result
