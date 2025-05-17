import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from engine.analysis import *
from engine.utils import *

ASSETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Chemin vers Stockfish à adapter si besoin
stockfish_path = "C:/Program Files (x86)/stockfish/stockfish-windows-x86-64-avx2.exe"

st.set_page_config(layout="wide")
st.title("Analyseur de parties d'échecs")

# Session state init
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'pgn_last' not in st.session_state:
    st.session_state.pgn_last = ""
if 'white_name' not in st.session_state:
    st.session_state.white_name = "Blanc"
if 'black_name' not in st.session_state:
    st.session_state.black_name = "Noir"

col1, col2, col3 = st.columns(spec=[2,4,3], gap="small", border=True)

with col1:
    pgn_text = st.text_area("PGN de la partie :", placeholder="Collez ici le PGN de la partie", height=86)
    user_depth = st.slider("Profondeur d'analyse", min_value=5, max_value=20, value=16)
    
    if st.button("Analyser", disabled=not pgn_text.strip()):
        analysis, white_name, black_name = analyze_game(pgn_text, user_depth, stockfish_path)
        st.session_state.analysis = analysis
        st.session_state.white_name = white_name
        st.session_state.black_name = black_name
        st.session_state.pgn_last = pgn_text


quality_colors = {
    "Gaffe": "#c93233",
    "Erreur": "#dc8c2a",
    "Imprécision": "#e8b443",
    "Bon": "#78af8b",
    "Excellent": "#67ac49",
    "Meilleur": "#98bc49",
    "Très bon": "#4c8caf",
    "Brillant": "#1baa9b"
}

quality_images = {
    "Gaffe": os.path.join(ASSETS_PATH, "gaffe.png"),
    "Erreur": os.path.join(ASSETS_PATH, "erreur.png"),
    "Imprécision": os.path.join(ASSETS_PATH, "imprecision.png"),
    "Bon": os.path.join(ASSETS_PATH, "bon.png"),
    "Excellent": os.path.join(ASSETS_PATH, "excellent.png"),
    "Meilleur": os.path.join(ASSETS_PATH, "meilleur.png"),
    "Très bon": os.path.join(ASSETS_PATH, "tres_bon.png"),
    "Brillant": os.path.join(ASSETS_PATH, "brillant.png")
}
with col2:
    if st.session_state.analysis:
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
                "Brillant", "Très bon", "Meilleur", "Excellent", "Bon",
                "Imprécision", "Erreur", "Gaffe"
            ], fill_value=0)
        )

        with st.container(border=True):
            render_quality_table(recap, white, black, quality_colors, quality_images)

        st.write(df)

with col3:
    st.write("Graphe de la partie")
    if st.session_state.analysis:
        evals = [coup["eval"] for coup in st.session_state.analysis]
        formatted_labels = [format_eval(coup["raw_eval"]) for coup in st.session_state.analysis]
        min_val = min(evals) - 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=list(range(len(evals))),
            y=[min_val] * len(evals),
            mode='lines',
            line=dict(color='white'),
            fill=None,
            showlegend=False,
            hoverinfo="skip"
        ))

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

        fig.add_shape(
            type="line",
            x0=0,
            y0=0,
            x1=len(evals)-1,
            y1=0,
            line=dict(color="gray", width=1),
            layer="above"
        )

        fig.update_layout(
            height=80,
            margin=dict(l=0, r=0, t=0, b=0),
            dragmode=False,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, showline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, showline=False)
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
