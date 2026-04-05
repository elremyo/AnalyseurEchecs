import streamlit as st
from typing import Dict, Any, List

def display_key_moments() -> None: 
    analysis_result = st.session_state.analysis_result
    analysis = analysis_result.analysis
    winner = analysis_result.winner
    key_moments = analysis_result.key_moments
    username = st.session_state.get("username", "Vous")
    white = analysis_result.white_name
    user_color = "white" if username.lower() == white.lower() else "black"

    determinants = key_moments.get("moments_determinants", [])
    critiques = key_moments.get("moments_critiques", [])

    def go_to_move(idx: int) -> None:
        st.session_state.move_index = idx

    if not determinants and not critiques:
        st.markdown("_Aucun moment décisif détecté._")
        return

    if determinants:
        if winner == user_color:
            st.markdown("✅ **Tu gagnes la partie ici :**")
        else:
            st.markdown("❌ **Tu perds la partie ici :**")

        for idx in determinants:
            move_info = analysis[idx]
            cols = st.columns([10, 1])
            with cols[0]:
                st.write(
                    f"Coup {idx + 2} ({move_info.coup}) : "
                    f"{move_info.eval / 100:+.1f}, {move_info.quality}"
                )
            with cols[1]:
                st.button(
                    ":material/search:",
                    key=f"goto_det_{idx}",
                    help="Aller au coup",
                    on_click=go_to_move,
                    args=(idx + 1,),
                    width='stretch',
                    type="tertiary"
                )

    if critiques:
        if winner == user_color:
            st.markdown("⚠️ **Tu as failli tout perdre ici :**")
        else:
            st.markdown("💥 **Tu aurais pu gagner ici :**")

        for idx in critiques:
            move_info = analysis[idx]
            cols = st.columns([10, 1])
            with cols[0]:
                st.write(
                    f"Coup {idx + 2} ({move_info.coup}) : "
                    f"{move_info.eval / 100:+.1f}, {move_info.quality}"
                )
            with cols[1]:
                st.button(
                    ":material/search:",
                    key=f"goto_crit_{idx}",
                    help="Aller au coup",
                    on_click=go_to_move,
                    args=(idx + 1,),
                    width='stretch',
                    type="tertiary"
                )
