import streamlit as st
import pandas as pd
from typing import Dict, Any, List

from constants import QUALITY_COLORS
from utils.image_utils import load_quality_images_b64
from utils.safe_html import escape_html

def display_total_moves_by_quality() -> None:

    # Utiliser le récap précalculé depuis analysis_result
    analysis_result = st.session_state.analysis_result
    recap = analysis_result.quality_recap
    if recap is None:
        st.write("Aucun récapitulatif de qualité disponible.")
        return
    
    white_name = analysis_result.white_name
    black_name = analysis_result.black_name

    # Charger les images une seule fois
    images_b64 = load_quality_images_b64()
    
    col_quality,col_white,col_image,col_black = st.columns([3,2,1,2],border=False,vertical_alignment="center")
    with col_quality:
        pass        
    with col_white:
        st.markdown(f"<b>{escape_html(white_name)}</b>", unsafe_allow_html=True)

    with col_image:
        pass
    with col_black:
        st.markdown(f"<b>{escape_html(black_name)}</b>", unsafe_allow_html=True)


    for quality, row in recap.iterrows():
        color = QUALITY_COLORS.get(quality, "black")
        value_white = int(row["W"])
        value_black = int(row["B"])

        col_quality,col_white,col_image,col_black = st.columns([3,2,1,2],border=False)
        with col_quality:
            st.markdown(
                f"<span style='color:{escape_html(color)}; font-weight:bold'>{escape_html(quality)}</span>",
                unsafe_allow_html=True,
            )
        with col_white:
            st.markdown(
                f"<div style='text-align:center'><span style='color:{escape_html(color)}; font-weight:bold'>{value_white}</span></div>",
                unsafe_allow_html=True,
            )
        with col_image:
            img_b64 = images_b64.get(quality)
            if img_b64:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<img src='data:image/png;base64,{img_b64}' style='height:24px; max-width:24px; display:inline-block;'>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        with col_black:
            st.markdown(
                f"<div style='text-align:center'><span style='color:{escape_html(color)}; font-weight:bold'>{value_black}</span></div>",
                unsafe_allow_html=True,
            )
