import streamlit as st
from domain.game_analysis_service import GameAnalysisService, AnalysisResult, AnalysisError


class AnalysisCallbacks:
    """Callbacks Streamlit pour l'analyse - adapte le service à l'UI."""
    
    def __init__(self, service: GameAnalysisService):
        self.service = service
    
    def _create_progress_callback(self):
        """Crée un callback de progression pour Streamlit."""
        progress_bar = st.progress(0, text="Préparation de l'analyse")
        caption_placeholder = st.empty()
        caption_placeholder.caption("Si l'analyse est trop longue, vous pouvez diminuer la profondeur d'analyse dans les options.")
        
        def callback(current: int, total: int, message: str):
            if total > 0:
                progress_bar.progress(current / total, text=message)
            
            # Nettoyage à la fin
            if current >= total:
                progress_bar.empty()
                caption_placeholder.empty()
        
        return callback
    
    def on_analyze_click(self) -> None:
        """Callback pour le bouton Analyser."""
        pgn = st.session_state.pgn_text_input
        
        # Créer le callback de progression
        progress_callback = self._create_progress_callback()
        
        result, error = self.service.analyze_game(
            pgn=pgn,
            user_depth=st.session_state.user_depth,
            username=st.session_state.username,
            compute_threats=st.session_state.show_threat_arrows,
            progress_callback=progress_callback
        )
        
        if error:
            st.session_state.analyze_error = error.message
            return
        
        # Stockage du résultat complet
        st.session_state.update({
            "analysis_result": result,
            "pgn_last_analyzed": pgn,
            "analyze_error": None,
        })
    
    def display_error_if_any(self) -> None:
        """Affiche l'erreur s'il y en a une."""
        error = st.session_state.get("analyze_error")
        if error:
            st.error(error)
