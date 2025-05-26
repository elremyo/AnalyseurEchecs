import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import base64

from utils.eval_utils import format_eval
from assets import *





def set_page_style():
    """Applique le style global de la page."""
    st.set_page_config(layout="wide",page_icon="♟️")
    st.header("Analyseur de parties d'échecs", anchor=False)
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
    meilleur_coup_data = st.session_state.analysis[analysis_index-1]

    meilleur_coup = meilleur_coup_data.get("best_move", "Non spécifié")
    coup_joué = coup_data.get("coup", "Inconnu")
    qualite = coup_data.get("qualité", "Non précisée")
    eval_cp = coup_data.get("eval", "N/A")
    est_theorique = "Oui" if coup_data.get("is_theoretical", False) else "Non"
    est_meilleur = "Oui" if coup_data.get("is_best", False) else "Non"

    with st.container(border=True):
        if est_theorique == "Oui":
            st.write(f"{coup_joué} est un coup théorique")
        elif qualite == "Excellent" or qualite == "Bon":
            st.write(f"{coup_joué} est un {qualite.lower()} coup")
        elif qualite == "Imprécision" or qualite == "Erreur" or qualite == "Gaffe":
            st.write(f"{coup_joué} est une {qualite.lower()}")
        elif qualite == "Meilleur":
            st.write(f"{coup_joué} est le meilleur coup")
        if est_theorique != "Oui" and est_meilleur != "Oui" and analysis_index>0:
            st.markdown(f"**:green[{meilleur_coup}]** est le meilleur coup")

    with st.container(border=True):
        st.markdown(f"""
        **Analyse du coup {move_index} :**
        - Coup joué : `{coup_joué}`
        - Meilleur coup suggéré : `{meilleur_coup}`
        - Qualité : **{qualite}**
        - Évaluation (cp) : `{eval_cp}`
        - Coup théorique : {est_theorique}
        """)





def display_graph(current_index=None):
        if st.session_state.analysis:
            evals = [coup["eval"] for coup in st.session_state.analysis]
            formatted_labels = [format_eval(coup["raw_eval"]) for coup in st.session_state.analysis]
            min_val = min(evals) - 100

            fig = go.Figure()

            # Première trace : ligne blanche invisible au niveau de `min_val` pour générer une "zone remplie"
            fig.add_trace(go.Scatter(
                x=list(range(len(evals))),
                y=[min_val] * len(evals),
                mode='lines',
                line=dict(color='white'),
                fill=None,
                showlegend=False,
                hoverinfo="skip"
            ))

            # Deuxième trace : ligne des évaluations avec remplissage vers le bas jusqu'à la trace précédente
            fig.add_trace(go.Scatter(
                x=list(range(len(evals))),
                y=evals,
                mode='lines',
                line=dict(color='white'),
                fill='tonexty',
                fillcolor='white',
                showlegend=False,
                text=[f"Coup {i+1}: {label}" for i, label in enumerate(formatted_labels)],
                hovertemplate="%{text}<extra></extra>"
            ))

            # Ligne grise horizontale à y=0 pour référence
            fig.add_shape(
                type="line",
                x0=0,
                y0=0,
                x1=len(evals)-1,
                y1=0,
                line=dict(color="gray", width=1),
                layer="above"
            )

            # Ligne rouge verticale indiquant le coup actuellement sélectionné (si fourni)
            if current_index is not None:
                fig.add_shape(
                    type="line",
                    x0=current_index,
                    y0=min_val,
                    x1=current_index,
                    y1=max(evals),
                    line=dict(color="red", width=2),
                    layer="above"
                )


            fig.update_layout(
                height=90,
                margin=dict(l=0, r=0, t=0, b=0),
                dragmode=False,
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, showline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, showline=False)
            )

            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def display_quality_table():
    assets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

    quality_images = {
    "Théorique": os.path.join(assets_path, "theorique.png"),
    "Gaffe": os.path.join(assets_path, "gaffe.png"),
    "Erreur": os.path.join(assets_path, "erreur.png"),
    "Imprécision": os.path.join(assets_path, "imprecision.png"),
    "Bon": os.path.join(assets_path, "bon.png"),
    "Excellent": os.path.join(assets_path, "excellent.png"),
    "Meilleur": os.path.join(assets_path, "meilleur.png"),
    "Critique": os.path.join(assets_path, "tres_bon.png"),
    "Brillant": os.path.join(assets_path, "brillant.png")
    }

    quality_colors = {
    "Théorique": "#a88764",
    "Gaffe": "#c93233",
    "Erreur": "#dc8c2a",
    "Imprécision": "#e8b443",
    "Bon": "#78af8b",
    "Excellent": "#67ac49",
    "Meilleur": "#98bc49",
    "Critique": "#4c8caf",
    "Brillant": "#1baa9b"
    }

    df = pd.DataFrame(st.session_state.analysis)
    white = st.session_state.white_name
    black = st.session_state.black_name
    df["joueur"] = [white if i % 2 == 0 else black for i in range(len(df))]
    recap = (
        df.groupby(["qualité", "joueur"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[white, black], fill_value=0)
        .reindex(index=[
            #"Brillant", 
            #"Critique", 
            "Meilleur", "Excellent", "Bon",
            "Imprécision", "Erreur", "Gaffe", "Théorique"
        ], fill_value=0)
        )

    col_quality,col_white,col_image,col_black = st.columns([3,2,1,2],border=False)
    with col_quality:
        pass        
    with col_white:
        st.markdown(f"**{white}**")        
    with col_image:
        pass
    with col_black:
        st.markdown(f"**{black}**")        


    for qualite, row in recap.iterrows():
        color = quality_colors.get(qualite, "black")
        value_white = row[white]
        value_black = row[black]
        img_path = quality_images.get(qualite)

        col_quality,col_white,col_image,col_black = st.columns([3,2,1,2],border=False)
        with col_quality:
            st.markdown(f"<span style='color:{color}; font-weight:bold'>{qualite}</span>", unsafe_allow_html=True)
        with col_white:
            st.markdown(
            f"<div style='text-align:center'><span style='color:{color}; font-weight:bold'>{value_white}</span></div>",
            unsafe_allow_html=True
        )        
        with col_image:
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<img src='data:image/png;base64,{img_b64}' style='height:24px; max-width:24px; display:inline-block;'>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        with col_black:
            st.markdown(
            f"<div style='text-align:center'><span style='color:{color}; font-weight:bold'>{value_black}</span></div>",
            unsafe_allow_html=True
        )
