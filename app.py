import streamlit as st
import chess
from utils.session import init_session_state
from display.style import set_page_style
from display.dashboard import render_dashboard
from display.board import render_board
from utils.pgn_utils import get_moves_from_pgn_cached
from display.navigation import render_navigation_buttons
from display.move_description import display_move_description
from display.moves_recap import display_all_moves_recap
from display.key_moments import display_key_moments
from display.quality_summary import display_total_moves_by_quality
from display.graph import render_moves_graph, render_score_bar
from display.result import display_game_result
from callbacks.analysis_callbacks import AnalysisCallbacks
from callbacks.settings_callbacks import SettingsCallbacks
from domain.game_analysis_service import GameAnalysisService
from utils.assets import stockfish_path, book_path
from dotenv import load_dotenv

# Initialisation
init_session_state()
load_dotenv()
set_page_style()

# Initialisation des services
analysis_service = GameAnalysisService(stockfish_path, book_path)
analysis_callbacks = AnalysisCallbacks(analysis_service)

# État de vue
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "dashboard"  # "dashboard" ou "analysis"

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

# Sidebar
with st.sidebar:    
    if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
        # Affichage des erreurs
        analysis_callbacks.display_error_if_any()
        display_key_moments()
        display_total_moves_by_quality()
    else:
        if st.button("Options",
                    key="open_parameters_sidebar",
                    help="Ouvrir les paramètres de l'analyseur",
                    icon=":material/settings:",
                    type="secondary",
                    width='stretch'
                    ):
            open_parameters()

        pgn_text = st.text_area(
            "PGN de la partie :",
            placeholder="Collez ici le PGN de la partie",
            height=200,
            key="pgn_text_input",
        )

        st.button("Analyser",
                     disabled=not (pgn_text and pgn_text.strip()),
                     type="primary",
                     icon=":material/monitoring:",
                     width='stretch',
                     on_click=analysis_callbacks.on_analyze_click)

        with st.expander("Comment copier un PGN ?", expanded=False, icon=":material/help:"):
            st.markdown(
                "1. Ouvrez la partie sur Chess.com ou Lichess.org.\n"
                "2. Cliquez sur le bouton **Partager** ou **Exporter**.\n"
                "3. Sélectionnez l'option **Copier le PGN**.\n"
                "4. Collez-le dans le champ ci-dessus."
            )

# Configuration de la page
st.set_page_config(
    page_title="Analyseur d'échecs", 
    page_icon=":material/chess:"
)


# Gestion de la redirection après analyse
if st.session_state.get("redirect_to_analysis", False):
    st.session_state.redirect_to_analysis = False
    st.session_state.view_mode = "analysis"

# Affichage en fonction du mode
if st.session_state.view_mode == "dashboard":
    render_dashboard()
    
elif st.session_state.view_mode == "analysis" and st.session_state.analysis_result and st.session_state.analysis_result.analysis:
    
    if st.button("Retour au dashboard",
                key="back_to_dashboard",
                help="Revenir au tableau de bord",
                icon=":material/arrow_back:",
                type="secondary",
                width='stretch'
    ):
        st.session_state.view_mode = "dashboard"
        st.session_state.analysis_result = None  # Effacer les résultats
        st.rerun()
    
    col_board, col_datas = st.columns(spec=[5,3], gap="small", border=True)

    with col_board:
        # Display game info at the top of board column
        with st.container(horizontal=True, vertical_alignment="bottom"):
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
    st.session_state.view_mode = "dashboard"