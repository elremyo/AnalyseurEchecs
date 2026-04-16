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

    def on_analyze_click(self, force_reanalyze: bool = False) -> None:
        """Callback pour le bouton Analyser."""
        pgn = st.session_state.pgn_text_input
        if not pgn or not pgn.strip():
            return

        game_id = self._extract_game_id(pgn)

        # ── Tentative de chargement depuis le cache ────────────────────────
        if game_id and not force_reanalyze:
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
                        return
                    # Cache corrompu → fall-through vers Stockfish

        # ── Analyse Stockfish ──────────────────────────────────────────────
        if force_reanalyze:
            st.toast("Forçage d'une nouvelle analyse...", icon=":material/refresh:")
        
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

    def on_navigate_to_game(self, pgn: str, game_id: str) -> None:
        """Charge la partie adjacente depuis le cache ou via Stockfish.

        Réinitialise move_index à 0 pour repartir du début de la nouvelle partie.
        Réutilise on_analyze_click pour bénéficier de la logique cache/fraîche.
        """
        if not pgn or not pgn.strip():
            return
        st.session_state.pgn_text_input = pgn
        st.session_state.move_index = 0
        st.session_state.move_index_slider = 1
        self.on_analyze_click()

    def on_batch_analyze_click(self, limit: int) -> None:
        """Callback pour l'analyse batch depuis le dashboard."""
        username = st.session_state.username
        
        # Créer la barre de progression et le message de statut
        progress_bar = st.progress(0, text="Préparation de l'analyse batch...")
        status_text = st.empty()
        
        def progress_callback(current: int, total: int, message: str):
            if total > 0:
                progress_bar.progress(current / total, text=f"Analyse batch : {current}/{total}")
                status_text.caption(message)
            if current >= total:
                progress_bar.empty()
                status_text.empty()
        
        try:
            success_count, error_count, analyzed_game_ids = self.service.analyze_batch(
                username=username,
                limit=limit,
                user_depth=st.session_state.user_depth,
                progress_callback=progress_callback,
            )
            
            # Afficher le résumé
            if success_count > 0:
                st.toast(f"Analyse batch terminée : {success_count} parties analysées avec succès", icon=":material/check_circle:")
            if error_count > 0:
                st.toast(f"{error_count} parties ont généré des erreurs", icon=":material/error:")
            
            # Forcer le rafraîchissement du dashboard
            if success_count > 0:
                st.rerun()
                
        except Exception as e:
            st.error(f"Erreur lors de l'analyse batch : {str(e)}")
            progress_bar.empty()
            status_text.empty()

    def display_error_if_any(self) -> None:
        """Affiche l'erreur s'il y en a une."""
        error = st.session_state.get("analyze_error")
        if error:
            st.error(error)