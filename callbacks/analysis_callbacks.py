import streamlit as st
from domain.game_analysis_service import GameAnalysisService, AnalysisResult, AnalysisError


class AnalysisCallbacks:
    """Callbacks Streamlit pour l'analyse - adapte le service à l'UI."""
    
    def __init__(self, service: GameAnalysisService):
        self.service = service
    
    def on_analyze_click(self) -> None:
        """Callback pour le bouton Analyser."""
        pgn = st.session_state.pgn_text_input
        
        result, error = self.service.analyze_game(
            pgn=pgn,
            user_depth=st.session_state.user_depth,
            compute_threats=st.session_state.show_threat_arrows
        )
        
        if error:
            st.session_state.analyze_error = error.message
            return
        
        # Stockage du résultat
        st.session_state.update({
            "analysis": result.analysis,
            "white_name": result.white_name,
            "black_name": result.black_name,
            "pgn_last_analyzed": pgn,
            "winner": result.winner,
            "key_moments": result.key_moments,
            "move_index": 0,
            "analyze_error": None,
        })
    
    def display_error_if_any(self) -> None:
        """Affiche l'erreur s'il y en a une."""
        error = st.session_state.get("analyze_error")
        if error:
            st.error(error)
