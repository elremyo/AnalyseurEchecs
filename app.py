import streamlit as st
import chess
import pandas as pd
from typing import Dict, Any, List
from dotenv import load_dotenv
from utils.session import init_session_state
from display.style import set_page_style
from display.board import render_board
from display.navigation import render_navigation_buttons, display_moves_slider
from display.move_description import display_move_description
from display.moves_recap import display_all_moves_recap
from display.quality_summary import display_total_moves_by_quality
from display.key_moments import display_key_moments
from display.graph import render_moves_graph, render_score_bar
from display.result import display_game_result
from callbacks.analysis_callbacks import AnalysisCallbacks
from callbacks.navigation_callbacks import NavigationCallbacks
from callbacks.settings_callbacks import SettingsCallbacks
from domain.game_analysis_service import GameAnalysisService
from utils.assets import stockfish_path, book_path, can_use_clipboard
from utils.debug_pgn_samples import sample_games
from utils.gif_images import get_random_gif
from utils.pgn_limits import MAX_PGN_CHARACTERS

init_session_state()
load_dotenv()

# Initialisation des services
analysis_service = GameAnalysisService(stockfish_path, book_path)
analysis_callbacks = AnalysisCallbacks(analysis_service)

set_page_style()
st.header("Road to 1000 ELO", anchor=False)

dev_mode = False

@st.dialog(title="Options")
def open_parameters() -> None:
    st.slider(
        "Profondeur d'analyse",
        min_value=10,
        max_value=20,
        value=st.session_state.user_depth,
        step=1,
        key="depth_slider",
        on_change=SettingsCallbacks.on_depth_change,
    )
    
    st.toggle(
        "Afficher la meilleure alternative", 
        value=st.session_state.show_best_arrow,
        key="best_arrow_toggle",
        on_change=SettingsCallbacks.on_best_arrow_toggle,
    )
    
    st.toggle(
        "Afficher la meilleure continuation", 
        value=st.session_state.show_threat_arrows,
        key="threat_arrows_toggle",
        on_change=SettingsCallbacks.on_threat_arrows_toggle,
    )


col_pgn, col_board, col_datas = st.columns(spec=[2,5,3], gap="small", border=True)

with col_pgn:

    if st.button("Options",
                key="open_parameters",
                help="Ouvrir les paramètres de l'analyseur",
                icon=":material/settings:",
                type="secondary",
                width='stretch'
                ):
        open_parameters()


    if dev_mode:
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
        if clipboard_content and isinstance(clipboard_content, str) and clipboard_content.strip().startswith("[Event") and len(clipboard_content.strip()) <= MAX_PGN_CHARACTERS:
            pgn_clipboard = clipboard_content.strip()
        else:
            pgn_clipboard = ""
    else:
        pgn_clipboard = ""

    # Le pgn_text_input est maintenant initialisé dans session.py

    pgn_text = st.text_area(
        "PGN de la partie :",
        placeholder="Collez ici le PGN de la partie",
        height=150,
        key="pgn_text_input",
    )


    st.button("Analyser",
                 disabled=not (pgn_text and pgn_text.strip()),
                 type="primary",
                 icon=":material/monitoring:",
                 width='stretch',
                 on_click=analysis_callbacks.on_analyze_click)

    # Affichage des erreurs
    analysis_callbacks.display_error_if_any()

    if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
        st.divider()
        display_game_result()
        display_key_moments(winner=st.session_state.analysis_result.winner)
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



with col_board:

    if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
        try:
            max_index = len(st.session_state.analysis_result.analysis)
            pgn_to_use = st.session_state.get("pgn_last_analyzed", "")
            if not pgn_to_use:
                st.error("Aucune partie analysée à afficher.")
                render_board(board=chess.Board())
            else:
                moves = analysis_service._get_moves_from_pgn_cached(pgn_to_use)
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
    else:
        #Afficher un échiquier vide
        render_board(board=chess.Board())

 

with col_datas:
    if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
        # Afficher le sélecteur de coups
        display_moves_slider(max_index)

        render_moves_graph(current_index=max(0, st.session_state.get("move_index", 0) - 1))
        display_move_description()
        display_all_moves_recap()

    else:
            st.subheader("👀 Rien à afficher pour l’instant !",anchor=False)
            gif_url = get_random_gif()
            if gif_url:
                st.image(gif_url, width='stretch')
            st.markdown("🔎 Essayez d’analyser une partie pour voir vos statistiques !")