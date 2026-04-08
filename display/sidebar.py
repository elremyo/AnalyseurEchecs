import streamlit as st
from display.key_moments import display_key_moments
from display.quality_summary import display_total_moves_by_quality
from callbacks.analysis_callbacks import AnalysisCallbacks


def render_sidebar(analysis_callbacks: AnalysisCallbacks, open_parameters_func):
    """Affiche le contenu de la sidebar."""
    with st.sidebar:    
        render_sidebar_input(analysis_callbacks, open_parameters_func)


def render_sidebar_input(analysis_callbacks: AnalysisCallbacks, open_parameters_func):
    """Affiche les éléments d'entrée dans la sidebar (PGN, bouton analyser, etc.)."""
    
    if st.button("Options",
                key="open_parameters_sidebar",
                help="Ouvrir les paramètres de l'analyseur",
                icon=":material/settings:",
                type="secondary",
                width='stretch'
                ):
        open_parameters_func()

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
