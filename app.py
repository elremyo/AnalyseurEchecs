import streamlit as st
import chess

from utils.session import *

init_session_state()

from display.style import set_page_style
from display.board import render_board
from display.navigation import render_navigation_buttons, display_moves_slider
from display.moves_info import display_move_description, display_all_moves_recap, display_total_moves_by_quality, display_key_moments
from display.graph import render_moves_graph, render_score_bar
from display.result import display_game_result
from engine.analysis import load_pgn, analyze_game
from utils.assets import stockfish_path, book_path, can_use_clipboard
from utils.eval_utils import get_winner
from utils.debug_pgn_samples import *
from utils.gif_images import *


set_page_style()
st.header("Road to 1000 ELO", anchor=False)

def open_parameters():
    @st.dialog(title="Options")
    def dialog():
        user_depth = st.slider("Profondeur d'analyse", min_value=10, max_value=20, value=10, step=1)
        st.session_state.user_depth = user_depth
        show_best_arrow = st.toggle("Afficher la meilleure alternative", value=st.session_state.get("show_best_arrow", True))
        st.session_state.show_best_arrow = show_best_arrow
        show_threat_arrows = st.toggle("Afficher la meilleure continuation", value=st.session_state.get("show_threat_arrows", False))
        st.session_state.show_threat_arrows = show_threat_arrows
    dialog()


col_pgn, col_board, col_datas = st.columns(spec=[2,5,3], gap="small", border=True)

with col_pgn:

    if st.button("Options",
                key="open_parameters",
                help="Ouvrir les paramètres de l'analyseur",
                icon=":material/settings:",
                type="secondary",
                use_container_width=True
                ):
        open_parameters()

    # Sélecteur de partie d'exemple
    sample_labels = []
    for idx, pgn in enumerate(sample_games):
        # On extrait les noms des joueurs et la date pour l'affichage
        lines = pgn.strip().splitlines()
        white = next((l.split('"')[1] for l in lines if l.startswith('[White ')), f"White {idx+1}")
        black = next((l.split('"')[1] for l in lines if l.startswith('[Black ')), f"Black {idx+1}")
        date = next((l.split('"')[1] for l in lines if l.startswith('[Date ')), "")
        sample_labels.append(f"{white} vs {black} ({date})")

    selected_idx = st.selectbox(
        "Sélectionner une partie d'exemple",
        options=list(range(len(sample_games))),
        format_func=lambda i: sample_labels[i],
        key="sample_game_select"
    )

    selected_pgn = sample_games[selected_idx].strip()
    if st.session_state.get("pgn_last", "") != selected_pgn:
        st.session_state.pgn_last = selected_pgn

    if can_use_clipboard():
        import pyperclip
        clipboard_content = pyperclip.paste()
        if clipboard_content and isinstance(clipboard_content, str) and clipboard_content.strip().startswith("[Event"):
            pgn_clipboard = clipboard_content.strip()
        else:
            pgn_clipboard = ""
    else:
        pgn_clipboard = ""

    with st.popover("Coller le PGN à analyser",use_container_width=True):
        pgn_text = st.text_area(
            "PGN de la partie :",
            placeholder="Collez ici le PGN de la partie",
            height=420,
            value=st.session_state.get("pgn_last", pgn_clipboard)
        )

    winner=get_winner(pgn_text) if pgn_text else None



    if st.button("Analyser",
                 disabled=not pgn_text.strip(),
                 type="primary",
                 icon=":material/monitoring:",
                 use_container_width=True):
        analysis, white_name, black_name = analyze_game(pgn_text, st.session_state.user_depth, stockfish_path,book_path)
        st.session_state.analysis = analysis
        st.session_state.white_name = white_name
        st.session_state.black_name = black_name
        st.session_state.pgn_last = pgn_text
        st.session_state.pgn_last_analyzed = pgn_text
        st.session_state.move_index = 0

    if st.session_state.analysis:
        st.divider()
        display_game_result()
        display_key_moments(winner=winner)
        st.divider()
        display_total_moves_by_quality()
    else:
        st.divider()
        st.subheader("✨ Coller un PGN pour commencer l'analyse", anchor=False)
        st.markdown(
            "Vous pouvez copier un PGN depuis [Chess.com](https://www.chess.com/) ou [Lichess.org](https://lichess.org/) et le coller ici pour l'analyser.",
            unsafe_allow_html=True
        )
        with st.expander("Comment copier un PGN ?", expanded=False, icon=":material/help:"):
            st.markdown(
                "1. Ouvrez la partie sur Chess.com ou Lichess.org.\n"
                "2. Cliquez sur le bouton **Partager** ou **Exporter**.\n"
                "3. Sélectionnez l'option **Copier le PGN**.\n"
                "4. Collez-le dans le champ ci-dessus."
            )
        st.session_state.analysis = None
        st.session_state.white_name = None
        st.session_state.black_name = None
        st.session_state.pgn_last = None
        st.session_state.pgn_last_analyzed = None


with col_board:

    if st.session_state.analysis:
        try:
            max_index = len(st.session_state.analysis)
            pgn_to_use = st.session_state.get("pgn_last_analyzed", pgn_text)
            game=load_pgn(pgn_to_use)
            board = chess.Board()
            moves = [move for move in game.mainline_moves()]

            # Initialisation de l'index du coup courant
            if "move_index" not in st.session_state:
                st.session_state.move_index = 0

            render_navigation_buttons(max_index)
            
            # Limite l'index dans les bornes
            st.session_state.move_index = max(0, min(st.session_state.move_index, max_index))

            # Applique les coups jusqu'à l'index courant
            for move in moves[:st.session_state.move_index]:
                board.push(move)

            last_move = moves[st.session_state.move_index - 1] if st.session_state.move_index > 0 else None
            
            # Synchronisation slider <-> move_index
            if "move_index_slider" in st.session_state:
                slider_value = st.session_state.move_index_slider - 1
                # On ne synchronise QUE si le slider a changé depuis le dernier run
                if st.session_state.get("_last_slider_value", None) != slider_value:
                    st.session_state.move_index = slider_value
                st.session_state._last_slider_value = slider_value

            render_score_bar()
            render_board(board, last_move=last_move, flipped=st.session_state.board_flipped)

        except Exception as e:
            st.error(f"Erreur pendant l'analyse : {e}")
    else:
        #Afficher un échiquier vide
        render_board(board=chess.Board())

 

with col_datas:
    if st.session_state.analysis:
        # Afficher le sélecteur de coups
        slider_value = display_moves_slider(max_index)

        # Synchronisation slider <-> move_index
        if "move_index_slider" in st.session_state:
            slider_value = st.session_state.move_index_slider - 1
            # Si le slider a changé, on pilote move_index
            if st.session_state.get("_last_slider_value", None) != slider_value:
                st.session_state.move_index = slider_value
            # Sinon, on pilote le slider avec move_index
            elif st.session_state.move_index != slider_value:
                st.session_state.move_index_slider = st.session_state.move_index + 1
            st.session_state._last_slider_value = st.session_state.move_index_slider - 1

        render_moves_graph(current_index=max(0, st.session_state.get("move_index", 0) - 1))
        display_move_description()
        display_all_moves_recap()


    else:
            st.subheader("👀 Rien à afficher pour l’instant !",anchor=False)
            st.image(get_random_gif(), use_container_width=True)
            st.markdown("🔎 Essayez d’analyser une partie pour voir vos statistiques !")
