import streamlit as st


class SettingsCallbacks:
    """Callbacks Streamlit pour la gestion des paramètres de l'analyseur."""
    
    @staticmethod
    def on_depth_change() -> None:
        """Gère le changement de profondeur d'analyse."""
        st.session_state.user_depth = st.session_state.depth_slider
    
    @staticmethod
    def on_best_arrow_toggle() -> None:
        """Gère le changement d'affichage des flèches de meilleure alternative."""
        st.session_state.show_best_arrow = st.session_state.best_arrow_toggle
    
    @staticmethod
    def on_threat_arrows_toggle() -> None:
        """Gère le changement d'affichage des flèches de menaces."""
        st.session_state.show_threat_arrows = st.session_state.threat_arrows_toggle
    
    @staticmethod
    def initialize_settings_if_needed() -> None:
        """Initialise les paramètres s'ils n'existent pas."""
        if "user_depth" not in st.session_state:
            st.session_state.user_depth = 10
        if "show_best_arrow" not in st.session_state:
            st.session_state.show_best_arrow = True
        if "show_threat_arrows" not in st.session_state:
            st.session_state.show_threat_arrows = False
