import streamlit as st
import os
from typing import Any, Dict, List, Optional

def init_session_state() -> None:
    """
    Initialise toutes les clés de session utilisées par l'application.
    
    Contrat complet des clés de session :
    - analysis_result: Optional[AnalysisResult] - Résultat complet d'analyse de partie
    - pgn_last: str - Dernier PGN entré par l'utilisateur
    - pgn_last_analyzed: str - Dernier PGN analysé avec succès
    - board_flipped: bool - Orientation de l'échiquier
    - user_depth: int - Profondeur d'analyse Stockfish
    - show_best_arrow: bool - Afficher les flèches du meilleur coup
    - show_threat_arrows: bool - Afficher les flèches des menaces
    - username: str - Nom d'utilisateur depuis env ou défaut
    - move_index: int - Index du coup actuellement sélectionné
    - pgn_text_input: str - Contenu du widget PGN
    - analyze_error: Optional[str] - Message d'erreur d'analyse
    """
    defaults = {
        # Analyse et PGN
        "analysis_result": None,
        "pgn_last": "",
        "pgn_last_analyzed": "",
        "pgn_text_input": "",
        
        # Affichage et navigation
        "board_flipped": False,
        "user_depth": 15,
        "show_best_arrow": True,
        "show_threat_arrows": False,
        "move_index": 0,
        "move_index_slider": 1,
        
        # Utilisateur et erreurs
        "username": os.getenv("STREAMLIT_USER", "Joueur"),
        "analyze_error": None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
