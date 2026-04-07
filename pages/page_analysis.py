import streamlit as st
import chess
from display.board import render_board
from utils.pgn_utils import get_moves_from_pgn_cached
from display.navigation import render_navigation_buttons
from display.move_description import display_move_description
from display.moves_recap import display_all_moves_recap
from display.graph import render_moves_graph, render_score_bar
from display.result import display_game_result

# Show analysis interface if analysis exists
if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
    st.columns(1)[0].container().markdown("")  # Add some space
    
    col_board, col_datas = st.columns(spec=[5,3], gap="small", border=True)

    with col_board:
        # Display game info at the top of board column
        with st.container(horizontal=True, vertical_alignment="bottom"):
            if st.button("Retour",
                        key="back_to_dashboard",
                        help="Revenir au tableau de bord",
                        icon=":material/arrow_back:",
                        type="secondary"
            ):
                st.session_state.analysis_result = None
                st.session_state.redirect_to_dashboard = True
            if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
                display_game_result()

        try:
            max_index = len(st.session_state.analysis_result.analysis)
            pgn_to_use = st.session_state.get("pgn_last_analyzed", "")
            if not pgn_to_use:
                st.error("Aucune partie analysée à afficher.")
                render_board(board=chess.Board())
            else:
                moves = get_moves_from_pgn_cached(pgn_to_use)
                board = chess.Board()

                render_navigation_buttons(max_index)
                st.session_state.move_index = max(0, min(st.session_state.move_index, max_index))

                for move in moves[:st.session_state.move_index]:
                    board.push(move)

                last_move = moves[st.session_state.move_index - 1] if st.session_state.move_index > 0 else None

                render_score_bar()
                render_board(board, last_move=last_move, flipped=st.session_state.board_flipped)

        except Exception as e:
            st.error(f"Erreur pendant l'affichage du plateau : {e}")

    with col_datas:
        # Afficher le sélecteur de coups
        render_moves_graph(current_index=max(0, st.session_state.get("move_index", 0) - 1))
        display_move_description()
        display_all_moves_recap()
else:
    st.info("Aucune partie analysée. Veuillez d'abord analyser une partie depuis le tableau de bord.")
