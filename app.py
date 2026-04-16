import streamlit as st
from utils.session import init_session_state
from display.style import set_page_style
from callbacks.analysis_callbacks import AnalysisCallbacks
from callbacks.settings_callbacks import SettingsCallbacks
from domain.game_analysis_service import GameAnalysisService
from utils.assets import stockfish_path, book_path
from dotenv import load_dotenv
from display.sidebar import render_sidebar
from display.page_analysis import render_page_analysis
from display.page_dashboard import render_page_dashboard, render_no_analysis_message

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
render_sidebar(analysis_callbacks, open_parameters)

# Gestion de la redirection après analyse
if st.session_state.get("redirect_to_analysis", False):
    st.session_state.redirect_to_analysis = False
    st.session_state.view_mode = "analysis"

# Affichage en fonction du mode
if st.session_state.view_mode == "dashboard":
    render_page_dashboard(analysis_callbacks)
    
elif st.session_state.view_mode == "analysis" and st.session_state.analysis_result and st.session_state.analysis_result.analysis:
    render_page_analysis(analysis_callbacks)
else:
    render_no_analysis_message()