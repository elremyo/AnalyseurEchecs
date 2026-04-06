import streamlit as st
from typing import Dict, Any, List

from utils.image_utils import load_quality_images_b64
from utils.safe_html import escape_html

def display_all_moves_recap() -> None:
    if not st.session_state.analysis_result or not st.session_state.analysis_result.analysis:
        st.write("Aucun récapitulatif disponible.")
        return

    analysis = st.session_state.analysis_result.analysis
    current_move_index = st.session_state.move_index
    
    # Charger les images une seule fois
    images_b64 = load_quality_images_b64()

    def go_to_move(idx: int) -> None:
        st.session_state.move_index = idx

    with st.container(border=False, height=400):
        for i in range(0, len(analysis), 2):
            # Vérifier si cette ligne contient le coup actuel
            is_current_line = (i == current_move_index) or (i + 1 == current_move_index)
            

            
            with st.container():
                col_num_coup,col_qual_blanc,col_coup_blanc,col_qual_noir,col_coup_noir = st.columns([1, 3, 1, 3, 1],vertical_alignment="center")
                move_number = i // 2 + 1

                with col_num_coup:
                    st.caption(f"{move_number}.")

                quality_w = analysis[i].quality
                coup_w = analysis[i].coup
                img_b64 = images_b64.get(quality_w)

                with col_qual_blanc:
                    # Vérifier si c'est le coup actuel
                    is_current_move = (i == current_move_index)
                    
                    img_w_tag = ""
                    if img_b64:
                        img_w_tag = (
                            f"<img src='data:image/png;base64,{img_b64}' "
                            f"style='height:20px;vertical-align:middle;margin-right:6px;'>"
                        )
                    
                    # Appliquer un style surligné si c'est le coup actuel
                    if is_current_move:
                        st.markdown(
                            f"{img_w_tag}"
                            f"**:green-badge[{escape_html(coup_w)}]**",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"{img_w_tag}"
                            f"{escape_html(coup_w)}",
                            unsafe_allow_html=True,
                        )
                with col_coup_blanc:
                    st.button(
                        ":material/search:",
                        key=f"move_w_{i}",
                        help=f"Aller au coup",
                        on_click=go_to_move,
                        args=(i + 1,),
                        width='stretch',
                        type="tertiary"
                    )


            # Coup noir
                if i + 1 < len(analysis):
                    quality_b = analysis[i + 1].quality
                    coup_b = analysis[i + 1].coup
                    img_b64 = images_b64.get(quality_b)
                    with col_qual_noir:
                        # Vérifier si c'est le coup actuel
                        is_current_move = (i + 1 == current_move_index)
                        
                        img_b_tag = ""
                        if img_b64:
                            img_b_tag = (
                                f"<img src='data:image/png;base64,{img_b64}' "
                                f"style='height:20px;vertical-align:middle;margin-right:6px;'>"
                            )
                        
                        # Appliquer un style surligné si c'est le coup actuel
                        if is_current_move:
                            st.markdown(
                                f"{img_b_tag}"
                                f"**:green-badge[{escape_html(coup_b)}]**",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f"{img_b_tag}"
                                f"{escape_html(coup_b)}",
                                unsafe_allow_html=True,
                            )
                    with col_coup_noir:
                        st.button(
                            ":material/search:",
                            key=f"move_n_{i+1}",
                            help=f"Aller au coup",
                            on_click=go_to_move,
                            args=(i + 2,),
                            width='stretch',
                            type="tertiary"
                        )
