import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from engine.analysis import analyze_game
from engine.utils import format_eval

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
    st.subheader("Importez votre partie")
    pgn_text = st.text_area("Saisir le PGN", placeholder="Collez ici le PGN de la partie", height=68, label_visibility="collapsed")
    user_depth = st.slider("Profondeur d'analyse", min_value=5, max_value=20, value=16)
    
    if st.button("Analyser", disabled=not pgn_text.strip()):
        analysis, white_name, black_name = analyze_game(pgn_text, user_depth, stockfish_path)
        st.session_state.analysis = analysis
        st.session_state.white_name = white_name
        st.session_state.black_name = black_name
        st.session_state.pgn_last = pgn_text

with col2:
    st.subheader("Analyse des coups")

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

        st.dataframe(recap)
        st.write(df)

with col3:
    st.subheader("Évolution de l'avantage")

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

        if st.button("Balloooooon !"):
            st.balloons()
