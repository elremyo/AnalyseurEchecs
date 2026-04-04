import streamlit as st
import os
from typing import Any, Dict, List, Optional

def init_session_state() -> None:
    """
    Initialise toutes les clés de session utilisées par l'application.
    
    Contrat complet des clés de session :
    - analysis: List[MoveAnalysis] - Liste des analyses de coups
    - pgn_last: str - Dernier PGN entré par l'utilisateur
    - pgn_last_analyzed: str - Dernier PGN analysé avec succès
    - pgn_meta: PgnMetadata - Métadonnées du PGN (joueurs, elo, résultat, etc.)
    - white_name: str - Nom du joueur blanc
    - black_name: str - Nom du joueur noir
    - board_flipped: bool - Orientation de l'échiquier
    - user_depth: int - Profondeur d'analyse Stockfish
    - show_best_arrow: bool - Afficher les flèches du meilleur coup
    - show_threat_arrows: bool - Afficher les flèches des menaces
    - username: str - Nom d'utilisateur depuis env ou défaut
    - move_index: int - Index du coup actuellement sélectionné
    - move_index_slider: int - Valeur du slider de navigation (move_index + 1)
    - pgn_text_input: str - Contenu du widget PGN
    - key_moments: Dict[str, List[int]] - Moments déterminants et critiques
    - winner: Optional[str] - Vainqueur de la partie
    - analyze_error: Optional[str] - Message d'erreur d'analyse
    - analysis_df: Any - DataFrame pandas pour l'export
    - quality_recap: Dict[str, int] - Récapitulatif des qualités de coups
    """
    defaults = {
        # Analyse et PGN
        "analysis": None,
        "pgn_last": "",
        "pgn_last_analyzed": "",
        "pgn_meta": {},
        "pgn_text_input": "",
        
        # Joueurs et affichage
        "white_name": "Blanc",
        "black_name": "Noir",
        "board_flipped": False,
        "username": os.getenv("CHESSBOT_USERNAME", "Anonymous"),
        
        # Paramètres d'analyse
        "user_depth": 15,
        "show_best_arrow": True,
        "show_threat_arrows": False,
        
        # Navigation
        "move_index": 0,
        "move_index_slider": 1,
        
        # Résultats et métriques
        "key_moments": {},
        "winner": None,
        "analyze_error": None,
        "analysis_df": None,
        "quality_recap": {},
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
