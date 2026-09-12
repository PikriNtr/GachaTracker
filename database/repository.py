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

            # Pulls table
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
                pity_at_pull INTEGER DEFAULT 0,
                is_5050_win INTEGER,
                UNIQUE(discord_id, game_id, player_id, card_pool_type, resource_name, time)
            )
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
        """Saves pulls idempotently. Returns count of newly inserted pulls."""
        inserted_count = 0
        with self._get_conn() as conn:
            cursor = conn.cursor()
            for p in pulls:
                win_val = 1 if p.is_5050_win is True else (0 if p.is_5050_win is False else None)
                cursor.execute("""
                INSERT OR IGNORE INTO pulls 
                (discord_id, game_id, player_id, card_pool_type, resource_id, resource_name, quality_level, time, pity_at_pull, is_5050_win)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (discord_id, game_id, player_id, p.card_pool_type, p.resource_id, p.resource_name, p.quality_level, p.time, p.pity_at_pull, win_val))
                if cursor.rowcount > 0:
                    inserted_count += 1
            conn.commit()
        return inserted_count

    def get_pulls(self, discord_id: str, game_id: str = "wuthering_waves", card_pool_type: Optional[str] = None) -> List[Pull]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if card_pool_type:
                cursor.execute("""
                SELECT card_pool_type, resource_id, resource_name, quality_level, time, player_id, game_id, pity_at_pull, is_5050_win
                FROM pulls
                WHERE discord_id = ? AND game_id = ? AND card_pool_type = ?
                ORDER BY time ASC
                """, (discord_id, game_id, str(card_pool_type)))
            else:
                cursor.execute("""
                SELECT card_pool_type, resource_id, resource_name, quality_level, time, player_id, game_id, pity_at_pull, is_5050_win
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
                    pity_at_pull=r["pity_at_pull"],
                    is_5050_win=win_val
                ))
            return result
