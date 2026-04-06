import streamlit as st
from constants import PAGE_CONFIG, MENU_ITEMS


def set_page_style():
    """Applique le style global de la page."""
    st.set_page_config(
        **PAGE_CONFIG,
        menu_items=MENU_ITEMS
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