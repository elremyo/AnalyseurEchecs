"""Cache SQLite local pour les parties Chess.com."""

import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "chessbot.db",
)


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crée les tables si elles n'existent pas encore."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id      TEXT PRIMARY KEY,
                username     TEXT NOT NULL,
                date         TEXT,
                white        TEXT,
                black        TEXT,
                user_color   TEXT,
                result       TEXT,
                user_result  TEXT,
                eco          TEXT,
                opening      TEXT,
                white_elo    INTEGER,
                black_elo    INTEGER,
                time_control TEXT,
                termination  TEXT,
                pgn          TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                username  TEXT PRIMARY KEY,
                last_sync TEXT
            )
        """)
        conn.commit()


def upsert_games(games: List[Dict[str, Any]]) -> int:
    """Insère les nouvelles parties (ignore les doublons). Retourne le nombre ajouté."""
    if not games:
        return 0
    with _connect() as conn:
        cursor = conn.executemany("""
            INSERT OR IGNORE INTO games
                (game_id, username, date, white, black, user_color, result, user_result,
                 eco, opening, white_elo, black_elo, time_control, termination, pgn)
            VALUES
                (:game_id, :username, :date, :white, :black, :user_color, :result, :user_result,
                 :eco, :opening, :white_elo, :black_elo, :time_control, :termination, :pgn)
        """, games)
        count = cursor.rowcount
        conn.commit()
    return count


def update_sync_log(username: str) -> None:
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO sync_log (username, last_sync) VALUES (?, ?)
        """, (username, datetime.now().isoformat()))
        conn.commit()


def get_last_sync(username: str) -> Optional[str]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT last_sync FROM sync_log WHERE username = ?", (username,)
        ).fetchone()
        return row["last_sync"] if row else None


def get_cached_games(username: str) -> List[Dict[str, Any]]:
    """Retourne toutes les parties en cache pour un joueur, triées par date décroissante."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM games WHERE username = ? ORDER BY date DESC", (username,)
        ).fetchall()
        return [dict(row) for row in rows]