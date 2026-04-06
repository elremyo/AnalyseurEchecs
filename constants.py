"""
Constantes globales de l'application ChessBot.
Centralise toutes les constantes utilisées dans différents modules.
"""

import os
from utils.assets import assets_path

# ============================================================================
# LIMITES ET CONTRAINTES
# ============================================================================

# Limites PGN pour éviter les parties trop lourdes
MAX_PGN_CHARACTERS = 350_000
MAX_MAINLINE_HALFMOVES = 400

# ============================================================================
# CONFIGURATION ÉCHEQUIER
# ============================================================================

# Taille de l'échiquier
BOARD_SIZE = 800  # in pixels

# Dimensions pour le rendu de l'échiquier
SQUARE_SIZE_PX = 45.7
BOARD_MARGIN_PX = 10
QUALITY_ICON_SIZE = 20

# ============================================================================
# COULEURS (Échiquier et Interface)
# ============================================================================

# Palette de couleurs pour l'échiquier
BOARD_COLORS = {
    "square_light": "#ebecd0",
    "square_dark": "#739552",
    "arrow": "#ff0000",
    "margin": "#181818",  # Same as background in config.toml
    "best_arrow": "#98bc499e",
    "threat_arrow": "#c02424b9",
    "default_light": "#ffffff",
    "default_dark": "#000000"
}

# Couleurs pour les qualités de coups
QUALITY_COLORS = {
    "Théorique": "#a88764",
    "Gaffe": "#c93233",
    "Erreur": "#dc8c2a",
    "Imprécision": "#e8b443",
    "Bon": "#78af8b",
    "Excellent": "#67ac49",
    "Meilleur": "#98bc49",
    "Critique": "#4c8caf",
    "Brillant": "#1baa9b"
}

# Couleurs pour les cases de l'échiquier selon la qualité
QUALITY_BOARD_COLORS = {
    "Théorique": ("#ccb08c", "#ae8763"),
    "Gaffe": ("#df8973", "#c0604a"),
    "Erreur": ("#e9b373", "#cc8a49"),
    "Imprécision": ("#f2cd7f", "#d4a456"),
    "Bon": ("#c4c49f", "#a79c77"),
    "Excellent": ("#c5ca80", "#a8a257"),
    "Meilleur": ("#c5ca80", "#a8a257"),
    "Critique": ("#a7b2b2", "#8a8a8a"),
    "Brillant": ("#1baa9b", "#1baa9b")
}

# ============================================================================
# RESSOURCES IMAGES
# ============================================================================

# Chemins vers les images de qualité
QUALITY_IMAGES = {
    "Théorique": os.path.join(assets_path, "theorique.png"),
    "Gaffe": os.path.join(assets_path, "gaffe.png"),
    "Erreur": os.path.join(assets_path, "erreur.png"),
    "Imprécision": os.path.join(assets_path, "imprecision.png"),
    "Bon": os.path.join(assets_path, "bon.png"),
    "Excellent": os.path.join(assets_path, "excellent.png"),
    "Meilleur": os.path.join(assets_path, "meilleur.png"),
    "Critique": os.path.join(assets_path, "tres_bon.png"),
    "Brillant": os.path.join(assets_path, "brillant.png")
}

# ============================================================================
# CONFIGURATION MOTEUR D'ANALYSE
# ============================================================================

# Paramètres Stockfish par défaut
DEFAULT_SKILL_LEVEL = 20
DEFAULT_HASH = 128
DEFAULT_MINIMUM_THINKING_TIME = 0
DEFAULT_THREADS = min(8, max(1, (os.cpu_count() or 4) // 2))

# ============================================================================
# INTERFACE UTILISATEUR
# ============================================================================

# Configuration de la page Streamlit
PAGE_CONFIG = {
    "page_title": "ChessBot",
    "layout": "wide",
    "page_icon": "♟️",
    "initial_sidebar_state": "expanded"
}

# Menu items (désactivés pour l'instant)
MENU_ITEMS = {
    'Get Help': None,
    'Report a bug': None,
    'About': None
}

# ============================================================================
# ANALYSE ET ÉVALUATION
# ============================================================================

# Valeur pour les positions de mat (en centipawns)
MATE_VALUE = 1200

# Seuils pour l'évaluation des coups (en centipawns)
EVAL_THRESHOLDS = {
    "BRILLIANT": 300,
    "CRITICAL": 200,
    "EXCELLENT": 150,
    "GOOD": 100,
    "INACCURACY": 40,
    "MISTAKE": 100,
    "BLUNDER": 300,
    "BEST_MOVE": 10,
    "EXCELLENT_MOVE": 40,
    "GOOD_MOVE": 80,
    "INACCURATE_MOVE": 200,
    "MISTAKE_MOVE": 400,
    "WINNING_THRESHOLD": 600,
    "LOSING_THRESHOLD": -600,
    "MATE_IN_NEGATIVE": -2,
    "MATE_IN_NEGATIVE_BIG": -5,
    "MATE_IN_POSITIVE": -4,
    "MATE_IN_SAME": 2,
    "GOOD_CP_THRESHOLD": 400,
    "GOOD_CP_LOWER": 150,
    "ERROR_CP_UPPER": -100
}

# Plage de valeurs CP pour le calcul des chances de victoire
CP_MIN = -1000
CP_MAX = 1000

# Facteur pour le calcul des chances de victoire
WIN_CHANCE_FACTOR = 0.00368208
