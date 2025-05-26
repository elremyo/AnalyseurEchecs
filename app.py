import streamlit as st
import chess

from engine.analysis import *
from utils.display import *
from utils.session import *
from utils.display import *
from utils.assets import stockfish_path, book_path


set_page_style()
init_session_state()


col1, col2, col3 = st.columns(spec=[3,5,4], gap="small", border=True)

with col1:
    pgn_text = st.text_area("PGN de la partie :", placeholder="Collez ici le PGN de la partie", height=120)
    user_depth = st.slider("Profondeur d'analyse", min_value=10, max_value=20, value=16,help="L'analyse sera plus longue avec une profondeur élevée.")
    
    if st.button("Analyser", disabled=not pgn_text.strip()):
        analysis, white_name, black_name = analyze_game(pgn_text, user_depth, stockfish_path,book_path)
        st.session_state.analysis = analysis
        st.session_state.white_name = white_name
        st.session_state.black_name = black_name
        st.session_state.pgn_last = pgn_text
        st.session_state.move_index = 0

    if st.session_state.analysis:
        st.divider()
        display_quality_table()



with col2:
    if st.session_state.analysis:
        try:
            game=load_pgn(pgn_text)
            board = chess.Board()
            moves = [move for move in game.mainline_moves()]
            max_index = len(moves)

            # Initialisation de l'index du coup courant
            if "move_index" not in st.session_state:
                st.session_state.move_index = 0

            # Boutons navigation
            col_flip, col_first, col_prev, col_next, col_last = st.columns(5)
            with col_flip:
                if st.button("", 
                             icon=":material/swap_vert:",
                             use_container_width=True,
                             key="flip_board"):
                    st.session_state.board_flipped = not st.session_state.board_flipped            
            with col_first:
                if st.button("",
                             icon=":material/first_page:",
                             help = "Premier coup",
                             use_container_width=True,
                             key="first_move") and st.session_state.move_index > 0:
                    st.session_state.move_index = 0
            with col_prev:
                if st.button("",
                             icon=":material/chevron_left:",
                             help = "Coup précédent",
                             use_container_width=True,
                             key="prev_move") and st.session_state.move_index > 0:
                    st.session_state.move_index -= 1
            with col_next:
                if st.button("",
                             icon=":material/chevron_right:",
                             help = "Coup suivant",
                             use_container_width=True,
                             key="next_move") and st.session_state.move_index < max_index:
                    st.session_state.move_index += 1
            with col_last:
                if st.button("",
                             icon=":material/last_page:",
                             help = "Dernier coup",
                             use_container_width=True,
                             key="last_move") and st.session_state.move_index < max_index:
                    st.session_state.move_index = max_index
        
            # Limite l'index dans les bornes
            st.session_state.move_index = max(0, min(st.session_state.move_index, max_index))

            # Applique les coups jusqu'à l'index courant
            for move in moves[:st.session_state.move_index]:
                board.push(move)
            st.caption(f"Coup {st.session_state.move_index} / {max_index}")

            render_svg(board, flipped=st.session_state.board_flipped)


        except Exception as e:
            st.error(f"Erreur pendant l'analyse : {e}")




with col3:
    if st.session_state.analysis:
        #Afficher l'histogramme
        display_graph(current_index=max(0, st.session_state.get("move_index", 0) - 1))

        #Afficher le coup joué et le meilleur coup
        display_move_description()
