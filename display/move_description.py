import streamlit as st
from typing import Dict, Any, List

from constants import QUALITY_COLORS
from utils.image_utils import load_quality_images_b64
from utils.safe_html import escape_html

def display_move_description() -> None:
    if not st.session_state.analysis_result or not st.session_state.analysis_result.analysis:
        st.write("Aucune analyse disponible.")
        return

    move_index = st.session_state.get("move_index", 0)

    if move_index == 0:
        return

    analysis_index = move_index - 1

    if analysis_index >= len(st.session_state.analysis_result.analysis):
        st.warning("Aucune analyse disponible pour ce coup.")
        return

    coup_data = st.session_state.analysis_result.analysis[analysis_index]
    meilleur_coup = coup_data.best_move
    coup_joué = coup_data.coup
    quality = coup_data.quality
    est_theorique = "Oui" if coup_data.is_theoretical else "Non"
    est_meilleur = "Oui" if coup_data.is_best else "Non"
    color_best = QUALITY_COLORS.get("Meilleur", "black")

    color_coup = QUALITY_COLORS.get(quality, "black")

    ec = escape_html(color_coup)
    ej = escape_html(coup_joué)
    eq = escape_html(quality)
    if est_theorique == "Oui":
        description = f"<span style='color:{ec};'>{ej} est un coup théorique</span>"
    elif quality == "Excellent" or quality == "Bon":
        description = f"<span style='color:{ec};'>{ej} est un {escape_html(quality.lower())} coup</span>"
    elif quality == "Imprécision" or quality == "Erreur" or quality == "Gaffe":
        description = f"<span style='color:{ec};'>{ej} est une {escape_html(quality.lower())}</span>"
    elif quality == "Meilleur":
        description = f"<span style='color:{ec};'>{ej} est le meilleur coup</span>"
    else:
        description = f"<span style='color:{ec};'>{ej} ({eq})</span>"

    meilleur_coup_html = ""
    if est_theorique != "Oui" and est_meilleur != "Oui" and quality != "Meilleur" and analysis_index > 0:
        meilleur_coup_html = (
            f"<div style='margin-top:8px; color:{escape_html(color_best)}; font-weight:bold;'>"
            f"{escape_html(meilleur_coup)} est le meilleur coup</div>"
        )


    
    with st.container(border=True):
        images_b64 = load_quality_images_b64()
        img_b64 = images_b64.get(quality)
        img_tag = ""
        if img_b64:
            img_tag = (
                f"<img src='data:image/png;base64,{img_b64}' "
                f"style='height:24px; max-width:24px; display:inline-block;margin-right:8px;margin-bottom:8px;'>"
            )
        st.markdown(
            f"<div style='text-align:left; font-weight:bold;'>"
            f"{img_tag}"
            f"<span>{description}</span>"
            f"<span>{meilleur_coup_html}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.space("xxsmall")
