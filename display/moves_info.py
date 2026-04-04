import streamlit as st
import pandas as pd

from display.constants import quality_images, quality_colors
from engine.analysis import find_key_moments
from utils.image_utils import load_quality_images_b64
from utils.safe_html import escape_html


def display_total_moves_by_quality():

    # Utiliser le DataFrame pré-calculé ou le créer si nécessaire
    if "analysis_df" not in st.session_state:
        st.session_state.analysis_df = pd.DataFrame(st.session_state.analysis)
    
    df = st.session_state.analysis_df
    white_name = st.session_state.white_name
    black_name = st.session_state.black_name

 
    # Clés fixes W/B : si les deux noms PGN sont identiques (ex. "?"), pandas aurait
    # deux colonnes du même nom et row[nom] renverrait une Series au lieu d'un entier.
    df["_side"] = ["W" if i % 2 == 0 else "B" for i in range(len(df))]
    recap = (
        df.groupby(["quality", "_side"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["W", "B"], fill_value=0)
        .reindex(index=[
            #"Brillant", 
            #"Critique", 
            "Meilleur", "Excellent", "Bon",
            "Imprécision", "Erreur", "Gaffe", "Théorique"
        ], fill_value=0)
        )
    
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
        color = quality_colors.get(quality, "black")
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
            images_b64 = load_quality_images_b64()
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



def display_move_description():
    if "analysis" not in st.session_state or not st.session_state.analysis:
        st.write("Aucune analyse disponible.")
        return

    move_index = st.session_state.get("move_index", 0)

    if move_index == 0:
        return

    analysis_index = move_index - 1

    if analysis_index >= len(st.session_state.analysis):
        st.warning("Aucune analyse disponible pour ce coup.")
        return

    coup_data = st.session_state.analysis[analysis_index]
    meilleur_coup = coup_data.get("best_move", "Non spécifié")
    coup_joué = coup_data.get("coup", "Inconnu")
    quality = coup_data.get("quality", "Non précisée")
    est_theorique = "Oui" if coup_data.get("is_theoretical", False) else "Non"
    est_meilleur = "Oui" if coup_data.get("is_best", False) else "Non"
    color_best = quality_colors.get("Meilleur", "black")

    color_coup = quality_colors.get(quality, "black")

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


def display_all_moves_recap():
    if "analysis" not in st.session_state or not st.session_state.analysis:
        st.write("Aucun récapitulatif disponible.")
        return

    analysis = st.session_state.analysis

    def go_to_move(idx):
        st.session_state.move_index = idx

    with st.container(border=False, height=400):
        for i in range(0, len(analysis), 2):
            col_num_coup,col_qual_blanc,col_coup_blanc,col_qual_noir,col_coup_noir = st.columns([1, 3, 1, 3, 1],vertical_alignment="center")
            move_number = i // 2 + 1

            with col_num_coup:
                st.markdown(f"&nbsp;:small[{move_number}].", unsafe_allow_html=True)

            quality_w = analysis[i].get("quality", "Non précisée")
            coup_w = analysis[i].get("coup", "")
            images_b64 = load_quality_images_b64()
            img_b64 = images_b64.get(quality_w)

            with col_qual_blanc:
                img_w_tag = ""
                if img_b64:
                    img_w_tag = (
                        f"<img src='data:image/png;base64,{img_b64}' "
                        f"style='height:20px;vertical-align:middle;margin-right:6px;'>"
                    )
                st.markdown(
                    f"{img_w_tag}"
                    f"<span style='font-family:monospace;font-size:16px'>{escape_html(coup_w)}</span>",
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
                quality_b = analysis[i + 1].get("quality", "Non précisée")
                coup_b = analysis[i + 1].get("coup", "")
                images_b64 = load_quality_images_b64()
                img_b64 = images_b64.get(quality_b)
                with col_qual_noir:
                    img_b_tag = ""
                    if img_b64:
                        img_b_tag = (
                            f"<img src='data:image/png;base64,{img_b64}' "
                            f"style='height:20px;vertical-align:middle;margin-right:6px;'>"
                        )
                    st.markdown(
                        f"{img_b_tag}"
                        f"<span style='font-family:monospace;font-size:16px'>{escape_html(coup_b)}</span>",
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


def display_key_moments(winner): 
    analysis = st.session_state.analysis
    username = st.session_state.get("username", "Vous")
    white = st.session_state.get("white_name", "Blanc")

    user_color = "white" if username.lower() == white.lower() else "black"

    key_moments = find_key_moments(
        analysis,
        threshold=500,
        min_gap_between_moments=2,
        winner=winner
    )

    determinants = key_moments["moments_determinants"]
    critiques = key_moments["moments_critiques"]

    def go_to_move(idx):
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
                    f"Coup {idx + 2} ({move_info['coup']}) : "
                    f"{move_info.get('eval', 0) / 100:+.1f}, {move_info['quality']}"
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
                    f"Coup {idx + 2} ({move_info['coup']}) : "
                    f"{move_info.get('eval', 0) / 100:+.1f}, {move_info['quality']}"
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

