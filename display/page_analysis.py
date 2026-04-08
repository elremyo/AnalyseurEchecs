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


def render_page_analysis():
    """Affiche l'interface complète d'analyse."""

    
    with st.container(horizontal=True, vertical_alignment="bottom"):
        # Bouton de retour
        if st.button("Retour au dashboard",
            key="back_to_dashboard",
            help="Revenir au tableau de bord",
            icon=":material/arrow_back:",
            type="secondary"
        ):
            st.session_state.view_mode = "dashboard"
            st.session_state.analysis_result = None  # Effacer les résultats
            st.rerun()

        # Display game results at the top
        display_game_result()

    col_board, col_datas = st.columns(spec=[5,3], gap="small", border=True)

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

                
                st.session_state.move_index = max(0, min(st.session_state.move_index, max_index))

                for move in moves[:st.session_state.move_index]:
                    board.push(move)

                last_move = moves[st.session_state.move_index - 1] if st.session_state.move_index > 0 else None

                render_score_bar()
                render_board(board, last_move=last_move, flipped=st.session_state.board_flipped)

        except Exception as e:
            st.error(f"Erreur pendant l'affichage du plateau : {e}")

    with col_datas:
        # Boutons de navigation
        render_navigation_buttons(max_index)
        
        # Description du coup
        display_move_description()
        
        # Graphique des scores
        render_moves_graph(current_index=max(0, st.session_state.get("move_index", 0) - 1))
        
        # Onglets Récap et Coups
        recap, coups = st.tabs(["Récap", "Coups"])
        with recap:
            # Moments clés
            display_key_moments()
            display_total_moves_by_quality()
        with coups:
            display_all_moves_recap()
