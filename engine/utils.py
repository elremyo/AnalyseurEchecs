import os
import streamlit as st
import textwrap
import base64
import plotly.graph_objects as go
import pandas as pd

ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

def init_session_state():
    """Initialise les variables de session si besoin."""
    defaults = {
        "analysis": None,
        "pgn_last": "",
        "white_name": "Blanc",
        "black_name": "Noir",
        "board_flipped": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def set_page_style():
    """Applique le style global de la page."""
    st.set_page_config(layout="wide")
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

def convert_eval_to_cp(e):
    if e["type"] == "cp":
        return e["value"]
    elif e["type"] == "mate":
        return 1500 if e["value"] > 0 else -1500
    return 0

def get_quality(delta, eval_type_before, eval_type_after, is_best,is_theoretical):
    #if eval_type_after == "mate" and eval_type_before != "mate":
    #    return "Brillant"
    if is_best:
        return "Meilleur"
    if is_theoretical:
        return "Théorique"


    delta_abs = abs(delta)
    if delta_abs < 10:
        return "Meilleur"
    if delta_abs < 40:
        return "Excellent"
    elif delta_abs < 50:
        return "Bon"
    elif delta_abs < 150:
        return "Imprécision"
    elif delta_abs < 300:
        return "Erreur"
    else:
        return "Gaffe"


def format_eval(e):
    if e["type"] == "cp":
        val = round(e["value"] / 100, 2)
        return f"+{val}" if val > 0 else f"{val}"
    elif e["type"] == "mate":
        return f"M{e['value']}" if e["value"] > 0 else f"-M{abs(e['value'])}"
    return "?"

def img_to_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

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
    quality_images = {
    "Théorique": os.path.join(ASSETS_PATH, "theorique.png"),
    "Gaffe": os.path.join(ASSETS_PATH, "gaffe.png"),
    "Erreur": os.path.join(ASSETS_PATH, "erreur.png"),
    "Imprécision": os.path.join(ASSETS_PATH, "imprecision.png"),
    "Bon": os.path.join(ASSETS_PATH, "bon.png"),
    "Excellent": os.path.join(ASSETS_PATH, "excellent.png"),
    "Meilleur": os.path.join(ASSETS_PATH, "meilleur.png"),
    "Critique": os.path.join(ASSETS_PATH, "tres_bon.png"),
    "Brillant": os.path.join(ASSETS_PATH, "brillant.png")
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
            "Critique", "Meilleur", "Excellent", "Bon",
            "Imprécision", "Erreur", "Gaffe", "Théorique"
        ], fill_value=0)
        )

 
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