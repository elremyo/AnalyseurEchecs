import streamlit as st
import chess
from engine.analysis import get_moves_from_pgn


@st.cache_data
def get_moves_from_pgn_cached(pgn_text: str) -> list[chess.Move]:
    """Version cachée de get_moves_from_pgn pour l'affichage du plateau."""
    return get_moves_from_pgn(pgn_text)
