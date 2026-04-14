import streamlit as st
from domain.game_analysis_service import GameAnalysisService, AnalysisResult, AnalysisError


class AnalysisCallbacks:
    """Callbacks Streamlit pour l'analyse - adapte le service à l'UI."""
    
    def __init__(self, service: GameAnalysisService):
        self.service = service

    def _create_progress_callback(self):
        progress_bar = st.progress(0, text="Préparation de l'analyse")
        caption = st.empty()
        caption.caption("Si l'analyse est trop longue, diminuez la profondeur dans les options.")

        def callback(current: int, total: int, message: str):
            if total > 0:
                progress_bar.progress(current / total, text=message)
            if current >= total:
                progress_bar.empty()
                caption.empty()

        return callback

    @staticmethod
    def _extract_game_id(pgn: str) -> str | None:
        """Extrait le game_id depuis le lien PGN sans parsing complet."""
        from utils.pgn_parser import _extract_link
        link = _extract_link(pgn)
        if not link:
            return None
        segment = link.rstrip("/").split("/")[-1]
        return segment or None

    def on_analyze_click(self) -> None:
        """Callback pour le bouton Analyser."""
        pgn = st.session_state.pgn_text_input
        if not pgn or not pgn.strip():
            return

        game_id = self._extract_game_id(pgn)

        # ── Tentative de chargement depuis le cache ────────────────────────
        if game_id:
            from utils.chesscom_cache import get_analysis_meta
            meta = get_analysis_meta(game_id)
            if meta:
                cached_depth = meta.get("depth", 0)
                user_depth   = st.session_state.user_depth
                if cached_depth >= user_depth:
                    result, error = self.service.load_from_cache(
                        game_id, pgn, st.session_state.username
                    )
                    if result:
                        st.session_state.update({
                            "analysis_result":     result,
                            "pgn_last_analyzed":   pgn,
                            "analyze_error":       None,
                            "redirect_to_analysis": True,
                        })
                        st.toast(
                            f"⚡ Chargé depuis le cache (profondeur {cached_depth}).",
                            icon="⚡"
                        )
                        return
                    # Cache corrompu → fall-through vers Stockfish

        # ── Analyse Stockfish ──────────────────────────────────────────────
        progress_callback = self._create_progress_callback()
        result, error = self.service.analyze_game(
            pgn=pgn,
            user_depth=st.session_state.user_depth,
            username=st.session_state.username,
            compute_threats=st.session_state.show_threat_arrows,
            progress_callback=progress_callback,
        )

        if error:
            st.session_state.analyze_error = error.message
            return

        st.session_state.update({
            "analysis_result":      result,
            "pgn_last_analyzed":    pgn,
            "analyze_error":        None,
            "redirect_to_analysis": True,
        })

    def display_error_if_any(self) -> None:
        """Affiche l'erreur s'il y en a une."""
        error = st.session_state.get("analyze_error")
        if error:
            st.error(error)