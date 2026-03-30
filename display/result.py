import re
from urllib.parse import urlparse

import streamlit as st


def _safe_game_link(url: str):
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


def display_game_result():

    if "pgn_last_analyzed" not in st.session_state or not st.session_state.pgn_last_analyzed:
        return
    
    pgn = st.session_state.pgn_last_analyzed

    # Résultat : recherche la balise [Result "..."] ou la ligne "1-0", "0-1", "1/2-1/2"
    result = None
    m = re.search(r'\[Result\s+"([^"]+)"\]', pgn)
    if m:
        result = m.group(1)
    else:
        # Fallback : cherche la dernière occurrence de 1-0, 0-1, 1/2-1/2 dans le texte
        m = re.findall(r'(1-0|0-1|1/2-1/2)', pgn)
        if m:
            result = m[-1]
        else:
            result = "?"

    if result == "1-0":
        winner_color = "⬜"
    elif result == "0-1":
        winner_color = "⬛"
    elif result in ("1/2-1/2", "½-½"):
        winner_color = "🟰"
    else:
        winner_color = "❓"

    # Affichage de la terminaison
    termination = None
    is_chesscom = "chess.com" in pgn.lower()
    m = re.search(r'\[Termination\s+"([^"]+)"\]', pgn)
    if is_chesscom and m:
        termination = m.group(1)
    else:
        # Pour tout le reste (lichess, parties historiques, etc.), on reconstruit à partir du résultat
        if result == "1-0":
            termination = "Victoire des Blancs"
        elif result == "0-1":
            termination = "Victoire des Noirs"
        elif result in ("1/2-1/2", "½-½"):
            termination = "Partie nulle"
        else:
            termination = "Résultat inconnu"

    # Lien Chess.com ou Lichess
    link = None
    m = re.search(r'\[Link\s+"([^"]+)"\]', pgn)
    if m:
        link = m.group(1)
    else:
        # Lichess Site "https://lichess.org/FLYtItYV"] ou [GameId "FLYtItYV"]: [
        m = re.search(r'\[Site\s+"(https?://lichess\.org/[\w\d]+)"\]', pgn)
        if m:
            link = m.group(1)
        else:
            m = re.search(r'\[GameId\s+"([\w\d]+)"\]', pgn)
            if m:
                link = f"https://lichess.org/{m.group(1)}"

    link = _safe_game_link(link) if link else None

    with st.container(border=False):
        if link:
            st.markdown(f"{winner_color}**{termination}** (:material/open_in_new: [Lien de la partie]({link}))")
        else:
            st.markdown(f"{winner_color}**{termination}**")
