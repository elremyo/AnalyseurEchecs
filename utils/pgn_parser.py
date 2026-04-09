import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class PgnMeta:
    white: str
    black: str
    white_elo: str
    black_elo: str
    result: str          # "1-0", "0-1", "1/2-1/2"
    winner: Optional[str]   # "white", "black", "draw", None
    termination: str
    link: Optional[str]
    event: Optional[str]
    date: Optional[str]
    eco: Optional[str]     # Code ECO de l'ouverture


def _safe_game_link(url: str) -> Optional[str]:
    """N'accepte que des liens https vers chess.com ou lichess.org."""
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if not u.startswith("https://"):
        return None
    try:
        parsed = urlparse(u)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return None
    if host == "lichess.org" or host.endswith(".lichess.org"):
        return u
    if host == "chess.com" or host.endswith(".chess.com"):
        return u
    return None


def _extract_tag(pgn: str, tag_name: str) -> Optional[str]:
    """Extrait une balise PGN spécifique."""
    pattern = rf'\[{tag_name}\s+"([^"]+)"\]'
    match = re.search(pattern, pgn)
    return match.group(1) if match else None


def _extract_elo(pgn: str, color: str) -> str:
    """Extrait l'ELO d'un joueur avec fallback."""
    tag_name = f"{color.capitalize()}Elo"
    elo = _extract_tag(pgn, tag_name)
    return elo if elo else "ELO?"


def _extract_result(pgn: str) -> str:
    """Extrait le résultat de la partie."""
    result = _extract_tag(pgn, "Result")
    if result:
        return result
    
    # Fallback : cherche la dernière occurrence de 1-0, 0-1, 1/2-1/2 dans le texte
    matches = re.findall(r'(1-0|0-1|1/2-1/2|½-½)', pgn)
    return matches[-1] if matches else "?"


def _determine_winner(result: str) -> Optional[str]:
    """Détermine le vainqueur à partir du résultat."""
    if result == "1-0":
        return "white"
    elif result == "0-1":
        return "black"
    elif result in ("1/2-1/2", "½-½"):
        return "draw"
    else:
        return None


def _extract_termination(pgn: str, result: str) -> str:
    """Extrait ou reconstruit la terminaison de la partie."""
    is_chesscom = "chess.com" in pgn.lower()
    termination = _extract_tag(pgn, "Termination")
    
    if is_chesscom and termination:
        return termination
    else:
        # Pour tout le reste (lichess, parties historiques, etc.), on reconstruit à partir du résultat
        if result == "1-0":
            return "Victoire des Blancs"
        elif result == "0-1":
            return "Victoire des Noirs"
        elif result in ("1/2-1/2", "½-½"):
            return "Partie nulle"
        else:
            return "Résultat inconnu"


def _extract_link(pgn: str) -> Optional[str]:
    """Extrait le lien de la partie."""
    link = _extract_tag(pgn, "Link")
    if link:
        return _safe_game_link(link)
    
    # Lichess Site "https://lichess.org/FLYtItYV"] ou [GameId "FLYtItYV"]
    site = _extract_tag(pgn, "Site")
    if site and "lichess.org" in site:
        return _safe_game_link(site)
    
    game_id = _extract_tag(pgn, "GameId")
    if game_id:
        return f"https://lichess.org/{game_id}"
    
    return None


def parse_pgn_meta(pgn: str) -> PgnMeta:
    """
    Parse PGN metadata and return a structured PgnMeta object.
    
    Args:
        pgn: The PGN text to parse
        
    Returns:
        PgnMeta: Structured metadata object
    """
    white = _extract_tag(pgn, "White") or "White"
    black = _extract_tag(pgn, "Black") or "Black"
    white_elo = _extract_elo(pgn, "white")
    black_elo = _extract_elo(pgn, "black")
    result = _extract_result(pgn)
    winner = _determine_winner(result)
    termination = _extract_termination(pgn, result)
    link = _extract_link(pgn)
    event = _extract_tag(pgn, "Event")
    date = _extract_tag(pgn, "Date")
    eco = _extract_tag(pgn, "ECO")
    
    return PgnMeta(
        white=white,
        black=black,
        white_elo=white_elo,
        black_elo=black_elo,
        result=result,
        winner=winner,
        termination=termination,
        link=link,
        event=event,
        date=date,
        eco=eco
    )
