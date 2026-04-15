import streamlit as st
from utils.safe_html import escape_html
from utils.eco_openings import get_opening_name


def display_game_result():

    if "pgn_last_analyzed" not in st.session_state or not st.session_state.pgn_last_analyzed:
        return
    
    # Utiliser les métadonnées PGN depuis analysis_result
    analysis_result = st.session_state.analysis_result
    pgn_meta = analysis_result.pgn_meta
    result = pgn_meta.result
    termination = pgn_meta.termination
    link = pgn_meta.link
    eco = pgn_meta.eco
    opening_name = get_opening_name(eco) if eco else "Ouverture inconnue"

    # Déterminer l'icône du vainqueur
    if result == "1-0":
        winner_color = "⬜"
    elif result == "0-1":
        winner_color = "⬛"
    elif result in ("1/2-1/2", "½-½"):
        winner_color = "🟰"
    else:
        winner_color = "❓"

    with st.container(horizontal = True, width="content"):
        # Afficher l'ouverture
        st.markdown(f":material/book: **{opening_name}**")
        
        termination_escaped = escape_html(termination)
        if link:
            st.markdown(f"{winner_color}**{termination_escaped}** (:material/open_in_new: [Lien de la partie]({link}))")
        else:
            st.markdown(f"{winner_color}**{termination_escaped}**")
