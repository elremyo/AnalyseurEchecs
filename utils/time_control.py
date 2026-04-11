"""Classification des contrôles de temps Chess.com."""

from typing import Optional

# Seuils en secondes pour le temps de base
_BULLET_MAX = 179    # < 3 min
_BLITZ_MAX  = 479    # < 8 min
_RAPID_MAX  = 1799   # < 30 min

GAME_TYPES = ["Bullet", "Blitz", "Rapide", "Classique", "Inconnu"]


def classify_time_control(time_control: str) -> str:
    """
    Retourne la catégorie d'un contrôle de temps Chess.com.

    Formats attendus : "300", "300+5", "1/300" (daily), etc.
    """
    if not time_control:
        return "Inconnu"

    tc = time_control.strip()

    # Parties daily (format "1/86400")
    if tc.startswith("1/"):
        return "Classique"

    # Extraire le temps de base (avant le '+')
    base_str = tc.split("+")[0]
    try:
        base_sec = int(base_str)
    except ValueError:
        return "Inconnu"

    if base_sec <= _BULLET_MAX:
        return "Bullet"
    elif base_sec <= _BLITZ_MAX:
        return "Blitz"
    elif base_sec <= _RAPID_MAX:
        return "Rapide"
    else:
        return "Classique"