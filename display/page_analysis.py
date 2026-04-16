import streamlit as st
import chess
from display.board import render_board
from utils.pgn_utils import get_moves_from_pgn_cached
from display.navigation import render_navigation_buttons
from display.move_description import display_move_description
from display.moves_recap import display_all_moves_recap
from display.graph import render_moves_graph, render_score_bar
from display.result import display_game_result
from display.key_moments import display_key_moments
from display.quality_summary import display_total_moves_by_quality
from callbacks.analysis_callbacks import AnalysisCallbacks


def _render_game_navigation(analysis_callbacks: AnalysisCallbacks) -> None:
    """Barre de navigation : retour dashboard + partie précédente/suivante."""
    username = st.session_state.get("username", "")
    game_id = (
        st.session_state.analysis_result.game_id
        if st.session_state.analysis_result
        else None
    )

    prev_game: dict | None = None
    next_game: dict | None = None
    if game_id and username:
        from utils.chesscom_cache import get_adjacent_games
        prev_game, next_game = get_adjacent_games(game_id, username)

    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button(
            "Dashboard",
            key="back_to_dashboard",
            help="Revenir au tableau de bord",
            icon=":material/arrow_back:",
            type="secondary",
        ):
            st.session_state.view_mode = "dashboard"
            st.session_state.analysis_result = None
            st.rerun()

        # Partie plus ancienne
        if prev_game:
            st.button(
                "Précédente",
                key="nav_prev_game",
                icon=":material/navigate_before:",
                help=f"Partie du {prev_game.get('date', '?')} (plus ancienne)",
                type="tertiary",
                on_click=analysis_callbacks.on_navigate_to_game,
                args=(prev_game["pgn"], prev_game["game_id"]),
            )
        else:
            st.button(
                "Précédente",
                key="nav_prev_game",
                icon=":material/navigate_before:",
                help="Aucune partie plus ancienne en cache",
                type="tertiary",
                disabled=True,
            )

        # Partie plus récente
        if next_game:
            st.button(
                "Suivante",
                key="nav_next_game",
                icon=":material/navigate_next:",
                help=f"Partie du {next_game.get('date', '?')} (plus récente)",
                type="tertiary",
                on_click=analysis_callbacks.on_navigate_to_game,
                args=(next_game["pgn"], next_game["game_id"]),
            )
        else:
            st.button(
                "Suivante",
                key="nav_next_game",
                icon=":material/navigate_next:",
                help="Aucune partie plus récente en cache",
                type="tertiary",
                disabled=True,
            )

        # Affichage du résultat de la partie courante à droite de la barre
        display_game_result()


def render_page_analysis(analysis_callbacks: AnalysisCallbacks) -> None:
    """Affiche l'interface complète d'analyse."""

    _render_game_navigation(analysis_callbacks)

    col_board, col_datas = st.columns(spec=[5, 3], gap="small", border=True)

    with col_board:
        try:
            max_index = len(st.session_state.analysis_result.analysis)
            pgn_to_use = st.session_state.get("pgn_last_analyzed", "")
            if not pgn_to_use:
                st.error("Aucune partie analysée à afficher.")
                render_board(board=chess.Board())
            else:
                moves = get_moves_from_pgn_cached(pgn_to_use)
                board = chess.Board()

                st.session_state.move_index = max(
                    0, min(st.session_state.move_index, max_index)
                )

                for move in moves[: st.session_state.move_index]:
                    board.push(move)

                last_move = (
                    moves[st.session_state.move_index - 1]
                    if st.session_state.move_index > 0
                    else None
                )

                render_score_bar()
                render_board(board, last_move=last_move, flipped=st.session_state.board_flipped)

        except Exception as e:
            st.error(f"Erreur pendant l'affichage du plateau : {e}")

    with col_datas:
        render_navigation_buttons(max_index)
        display_move_description()
        render_moves_graph(
            current_index=max(0, st.session_state.get("move_index", 0) - 1)
        )

        recap, coups = st.tabs(["Récap", "Coups"])
        with recap:
            display_key_moments()
            display_total_moves_by_quality()
        with coups:
            display_all_moves_recap()