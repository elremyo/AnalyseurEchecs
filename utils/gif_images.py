import random
import requests
import os
import streamlit as st
import threading
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


# Variable globale pour stocker les GIFs accessibles
_reachable_gifs_cache = []
_cache_initialized = False
_cache_lock = threading.Lock()


def _is_reachable(gif_url: str) -> bool:
    """Vérifie si une URL de GIF est accessible."""
    try:
        return requests.head(gif_url, timeout=3).status_code == 200
    except Exception:
        return False


def _initialize_cache():
    """Initialise le cache des GIFs accessibles en arrière-plan."""
    global _reachable_gifs_cache, _cache_initialized
    
    with _cache_lock:
        if _cache_initialized:
            return
        
        # Commence avec le GIF local comme fallback
        _reachable_gifs_cache = []
        
        # Teste chaque URL en arrière-plan
        for gif_url in chess_gifs:
            if _is_reachable(gif_url):
                _reachable_gifs_cache.append(gif_url)
        
        _cache_initialized = True


def get_random_gif() -> Optional[str]:
    """Retourne un GIF aléatoire parmi les URLs valides sans bloquer le thread principal."""
    global _reachable_gifs_cache, _cache_initialized
    
    # Initialise le cache si ce n'est pas déjà fait (non bloquant)
    if not _cache_initialized:
        # Lance l'initialisation en arrière-plan si besoin
        if not _reachable_gifs_cache:
            threading.Thread(target=_initialize_cache, daemon=True).start()
        
        # Retourne le fallback immédiatement
        return _fallback_gif()
    
    # Retourne un GIF aléatoire si disponible
    if _reachable_gifs_cache:
        return random.choice(_reachable_gifs_cache)
    
    return _fallback_gif()


def _fallback_gif() -> Optional[str]:
    """Retourne le GIF local de fallback."""
    fallback_path = os.path.join(assets_path, 'checkmate_gif.gif')
    return fallback_path if os.path.exists(fallback_path) else None
