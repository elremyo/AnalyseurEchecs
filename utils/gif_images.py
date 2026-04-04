import random
import requests
import os
import streamlit as st
from typing import Optional
from utils.assets import assets_path


chess_gifs = [
    "https://gifdb.com/images/high/cute-cats-fighting-over-chess-game-zpyt9q36qznawkc1.webp",
    "https://gifdb.com/images/high/chess-checkmate-natasha-lyonne-yhuv4j4bowlr0e0k.webp",
    "https://gifdb.com/images/high/geri-patiently-waiting-for-chess-move-ndg4p71mvtzws11v.webp",
    "https://gifdb.com/images/high/adorable-naughty-white-cat-playing-chess-nq389mt672i78q5g.webp",
    "https://gifdb.com/images/high/irritated-gaston-flipping-chess-board-gz33tqpfln3ngc98.webp",
    "https://gifdb.com/images/high/chess-game-serious-shaun-the-sheep-grtxymygnde3puwc.webp",
    "https://gifdb.com/images/high/hot-lady-capturing-chess-piece-yag0u744l3uxum4q.webp",
    "https://gifdb.com/images/high/chubby-cat-claiming-chess-piece-nng3pl7e4kp7b8kb.webp",
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHpydjY5cW9iMXpmeDlidG41NTR3eDF6YnM2MHRxYW5uc2EwdzNhcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/JuUWDI13JB0XK/giphy.gif",
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExMmY4bXk5dnhvODFocmdxNzltd29oN2RtdGJmcjk2cDA3ZHllMGVtdSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/6XlOzOgC5FTsk/giphy.gif"
]


def _is_reachable(gif_url: str) -> bool:
    """Vérifie si une URL de GIF est accessible."""
    try:
        return requests.head(gif_url, timeout=3).status_code == 200
    except Exception:
        return False


@st.cache_data(ttl=3600)
def _get_reachable_gifs() -> list[str]:
    """Retourne la liste des GIFs accessibles (mis en cache 1h)."""
    return [gif for gif in chess_gifs if _is_reachable(gif)]


def _fallback_gif() -> Optional[str]:
    """Retourne le GIF local de fallback."""
    fallback_path = os.path.join(assets_path, 'checkmate_gif.gif')
    return fallback_path if os.path.exists(fallback_path) else None


def get_random_gif() -> Optional[str]:
    """Retourne un GIF aléatoire parmi les URLs valides."""
    reachable = _get_reachable_gifs()
    return random.choice(reachable) if reachable else _fallback_gif()
