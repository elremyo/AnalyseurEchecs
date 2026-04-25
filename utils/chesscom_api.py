"""Client pour l'API publique Chess.com."""

import re
import requests
from typing import Any, Dict, List, Optional

CHESSCOM_API_BASE = "https://api.chess.com/pub"
_HEADERS = {"User-Agent": "ChessBot-Personal/1.0"}
_TIMEOUT = 15


def _get(url: str) -> dict:
    response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _parse_pgn_tag(pgn: str, tag: str) -> Optional[str]:
    match = re.search(rf'\[{tag}\s+"([^"]+)"\]', pgn)
    return match.group(1) if match else None


def _determine_user_result(game: dict, user_color: str) -> str:
    DRAW_CODES = {"agreed", "repetition", "stalemate", "insufficient",
                  "timevsinsufficient", "50move"}
    side = game.get(user_color, {})
    result_code = side.get("result", "")
    if result_code == "win":
        return "win"
    if result_code in DRAW_CODES:
        return "draw"
    return "loss"


def _parse_game(game: dict, username: str) -> Optional[Dict[str, Any]]:
    pgn = game.get("pgn", "")
    if not pgn:
        return None

    white_info = game.get("white", {})
    black_info = game.get("black", {})
    white_username = white_info.get("username", "")
    black_username = black_info.get("username", "")

    user_color = "white" if white_username.lower() == username.lower() else "black"
    user_result = _determine_user_result(game, user_color)

    if user_result == "win":
        result = "1-0" if user_color == "white" else "0-1"
    elif user_result == "loss":
        result = "0-1" if user_color == "white" else "1-0"
    else:
        result = "1/2-1/2"

    game_url = game.get("url", "")
    game_id = game_url.split("/")[-1] if game_url else str(game.get("end_time", ""))

    return {
        "game_id": game_id,
        "username": username,
        "date": _parse_pgn_tag(pgn, "Date") or "",
        "end_time": game.get("end_time", 0),
        "white": white_username,
        "black": black_username,
        "user_color": user_color,
        "result": result,
        "user_result": user_result,
        "eco": _parse_pgn_tag(pgn, "ECO") or "",
        "opening": _parse_pgn_tag(pgn, "Opening") or "",
        "white_elo": white_info.get("rating", 0),
        "black_elo": black_info.get("rating", 0),
        "time_control": game.get("time_control", ""),
        "termination": _parse_pgn_tag(pgn, "Termination") or "",
        "pgn": pgn,
    }


def fetch_archives(username: str) -> List[str]:
    """Retourne la liste des URLs d'archives mensuelles du joueur."""
    data = _get(f"{CHESSCOM_API_BASE}/player/{username}/games/archives")
    return data.get("archives", [])


def fetch_games_from_archive(archive_url: str, username: str) -> List[Dict[str, Any]]:
    """Récupère et parse les parties d'une archive mensuelle."""
    data = _get(archive_url)
    games = []
    for raw in data.get("games", []):
        parsed = _parse_game(raw, username)
        if parsed:
            games.append(parsed)
    return games


def fetch_recent_games(username: str, months: int = 3) -> List[Dict[str, Any]]:
    """Récupère les parties des N derniers mois."""
    archives = fetch_archives(username)
    if not archives:
        return []

    recent = archives[-months:]
    games = []
    for archive_url in recent:
        games.extend(fetch_games_from_archive(archive_url, username))

    return games