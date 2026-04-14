from callbacks.analysis_callbacks import AnalysisCallbacks
from display.dashboard import render_dashboard


def render_page_dashboard(analysis_callbacks: AnalysisCallbacks):
    render_dashboard(analysis_callbacks)


def render_no_analysis_message():
    st.info("Aucune partie analysée. Veuillez d'abord analyser une partie depuis le tableau de bord.")
    st.session_state.view_mode = "dashboard"