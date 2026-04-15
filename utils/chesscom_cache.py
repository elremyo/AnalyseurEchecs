"""Cache SQLite local pour les parties et analyses Chess.com."""

import json
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                game_id                  TEXT PRIMARY KEY,
                analyzed_at              TEXT,
                depth                    INTEGER,
                accuracy_white           REAL,
                accuracy_black           REAL,
                total_moves              INTEGER,
                best_white               INTEGER DEFAULT 0,
                excellent_white          INTEGER DEFAULT 0,
                good_white               INTEGER DEFAULT 0,
                inaccuracy_white         INTEGER DEFAULT 0,
                mistake_white            INTEGER DEFAULT 0,
                blunder_white            INTEGER DEFAULT 0,
                theoretical_white        INTEGER DEFAULT 0,
                best_black               INTEGER DEFAULT 0,
                excellent_black          INTEGER DEFAULT 0,
                good_black               INTEGER DEFAULT 0,
                inaccuracy_black         INTEGER DEFAULT 0,
                mistake_black            INTEGER DEFAULT 0,
                blunder_black            INTEGER DEFAULT 0,
                theoretical_black        INTEGER DEFAULT 0,
                key_moments_determinants TEXT,
                key_moments_critiques    TEXT,
                winner                   TEXT,
                FOREIGN KEY (game_id) REFERENCES games(game_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS moves (
                game_id        TEXT,
                move_index     INTEGER,
                coup           TEXT,
                quality        TEXT,
                eval_cp        INTEGER,
                eval_type      TEXT,
                eval_value     INTEGER,
                best_move_san  TEXT,
                best_move_uci  TEXT,
                is_best        INTEGER,
                is_theoretical INTEGER,
                accuracy_cp    REAL,
                PRIMARY KEY (game_id, move_index),
                FOREIGN KEY (game_id) REFERENCES games(game_id)
            )
        """)
        conn.commit()


# ---------------------------------------------------------------------------
# games table
# ---------------------------------------------------------------------------

def upsert_games(games: List[Dict[str, Any]]) -> int:
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
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM games WHERE username = ? ORDER BY date DESC", (username,)
        ).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# analyses + moves tables
# ---------------------------------------------------------------------------

def save_analysis(
    game_id: str,
    depth: int,
    accuracy_white: Optional[float],
    accuracy_black: Optional[float],
    total_moves: int,
    quality_recap,
    key_moments_determinants: List[int],
    key_moments_critiques: List[int],
    winner: Optional[str],
    move_rows: List[Dict[str, Any]],
) -> None:
    """Persiste une analyse complète (analyses + moves). Écrase si déjà présent."""

    def _count(quality: str, side: str) -> int:
        try:
            return int(quality_recap.loc[quality, side])
        except (KeyError, TypeError):
            return 0

    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO analyses (
                game_id, analyzed_at, depth,
                accuracy_white, accuracy_black, total_moves,
                best_white, excellent_white, good_white,
                inaccuracy_white, mistake_white, blunder_white, theoretical_white,
                best_black, excellent_black, good_black,
                inaccuracy_black, mistake_black, blunder_black, theoretical_black,
                key_moments_determinants, key_moments_critiques, winner
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, datetime.now().isoformat(), depth,
            accuracy_white, accuracy_black, total_moves,
            _count("Meilleur",    "W"), _count("Excellent",   "W"), _count("Bon",         "W"),
            _count("Imprécision", "W"), _count("Erreur",      "W"), _count("Gaffe",       "W"),
            _count("Théorique",   "W"),
            _count("Meilleur",    "B"), _count("Excellent",   "B"), _count("Bon",         "B"),
            _count("Imprécision", "B"), _count("Erreur",      "B"), _count("Gaffe",       "B"),
            _count("Théorique",   "B"),
            json.dumps(key_moments_determinants),
            json.dumps(key_moments_critiques),
            winner,
        ))
        conn.execute("DELETE FROM moves WHERE game_id = ?", (game_id,))
        conn.executemany("""
            INSERT INTO moves (
                game_id, move_index, coup, quality,
                eval_cp, eval_type, eval_value,
                best_move_san, best_move_uci,
                is_best, is_theoretical, accuracy_cp
            ) VALUES (
                :game_id, :move_index, :coup, :quality,
                :eval_cp, :eval_type, :eval_value,
                :best_move_san, :best_move_uci,
                :is_best, :is_theoretical, :accuracy_cp
            )
        """, move_rows)
        conn.commit()


def get_analysis_meta(game_id: str) -> Optional[Dict[str, Any]]:
    """Retourne {depth, analyzed_at, accuracy_white, accuracy_black} ou None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT depth, analyzed_at, accuracy_white, accuracy_black "
            "FROM analyses WHERE game_id = ?",
            (game_id,)
        ).fetchone()
        return dict(row) if row else None


def load_analysis_full(game_id: str) -> Optional[Dict[str, Any]]:
    """Retourne l'enregistrement complet de la table analyses, ou None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE game_id = ?", (game_id,)
        ).fetchone()
        return dict(row) if row else None


def load_analysis_moves(game_id: str) -> Optional[List[Dict[str, Any]]]:
    """Retourne les coups triés par move_index, ou None si absent."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM moves WHERE game_id = ? ORDER BY move_index", (game_id,)
        ).fetchall()
        return [dict(r) for r in rows] if rows else None


def get_analyzed_game_ids(game_ids: List[str]) -> set:
    """Retourne l'ensemble des game_ids ayant une analyse en cache."""
    if not game_ids:
        return set()
    placeholders = ",".join("?" for _ in game_ids)
    with _connect() as conn:
        rows = conn.execute(
            "SELECT game_id FROM analyses WHERE game_id IN ({})".format(placeholders),
            game_ids,
        ).fetchall()
        return {row["game_id"] for row in rows}

def get_analyses_meta_batch(game_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Retourne {game_id: {accuracy_white, accuracy_black, depth}} pour les IDs analysés."""
    if not game_ids:
        return {}
    placeholders = ",".join("?" for _ in game_ids)
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT game_id, accuracy_white, accuracy_black, depth "
            f"FROM analyses WHERE game_id IN ({placeholders})",
            game_ids,
        ).fetchall()
        return {row["game_id"]: dict(row) for row in rows}