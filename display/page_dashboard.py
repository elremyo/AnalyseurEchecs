import streamlit as st
from display.dashboard import render_dashboard


def render_page_dashboard():
    """Affiche le tableau de bord."""
    render_dashboard()


def render_no_analysis_message():
    """Affiche le message quand aucune analyse n'est disponible."""
    st.info("Aucune partie analysée. Veuillez d'abord analyser une partie depuis le tableau de bord.")
    st.session_state.view_mode = "dashboard"
