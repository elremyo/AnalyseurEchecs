import streamlit as st


def set_page_style():
    """Applique le style global de la page."""
    st.set_page_config(
        page_title="ChessBot",
        layout="wide",
        page_icon="♟️",
        initial_sidebar_state ="expanded",
        menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
        }
        )
    st.markdown(
        """
        <style>
        html, body, .main, .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            margin-left: 1rem !important;
            margin-right: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )