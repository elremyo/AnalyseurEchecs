import streamlit as st
import chess.pgn
from stockfish import Stockfish
import io
import pandas as pd
import plotly.graph_objects as go
import os
st.set_page_config(layout="wide")


hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


#os.system("chmod +x ./bin/stockfish")

#stockfish_path = "./bin/stockfish"
stockfish_path = "C:\Program Files (x86)\stockfish\stockfish-windows-x86-64-avx2.exe"

def convert_eval_to_cp(e):
    if e["type"] == "cp":
        return e["value"]
    elif e["type"] == "mate":
        return 1500 if e["value"] > 0 else -1500
    return 0




# Fonction pour analyser la partie PGN
def analyze_game(pgn_text,user_depth):
    # Simuler un fichier avec le texte PGN
    pgn_io = io.StringIO(pgn_text)
    
    # Charger le PGN de la partie
    game = chess.pgn.read_game(pgn_io)
    board = chess.Board()
    analysis = []

    stockfish = Stockfish(path=stockfish_path, depth=user_depth)

    # Analyser chaque coup
    for move in game.mainline_moves():
        stockfish.set_fen_position(board.fen())
        best_move = stockfish.get_best_move()
        eval_before = stockfish.get_evaluation()

        board.push(move)
        stockfish.set_fen_position(board.fen())
        eval_after = stockfish.get_evaluation()

        #DEBUG
        st.write(eval_after)

        eval_before_cp = convert_eval_to_cp(eval_before)
        eval_after_cp = convert_eval_to_cp(eval_after)

        delta = eval_after_cp - eval_before_cp

        quality = "bon coup"
        if abs(delta) > 50:
            quality = "imprécision"
        if abs(delta) > 150:
            quality = "erreur"
        if abs(delta) > 300:
            quality = "bourde"

        analysis.append({
            "coup": move.uci(),
            "qualité": quality,
            "eval": eval_after_cp,             # pour le tracé
            "raw_eval": eval_after             # pour l'affichage textuel
        })
    return analysis


def format_eval(e):
    if e["type"] == "cp":
        val = round(e["value"] / 100, 2)
        return f"+{val}" if val > 0 else f"{val}"
    elif e["type"] == "mate":
        return f"M{e['value']}" if e["value"] > 0 else f"-M{abs(e['value'])}"
    return "?"


# Session state init
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'pgn_last' not in st.session_state:
    st.session_state.pgn_last = ""


# Interface Streamlit
st.title("Analyseur de parties d'échecs")


col1, col2, col3 = st.columns(spec=[2,4,3],gap="small",border=True)

with col1:
    # Section d'import de la partie PGN
    st.subheader("Importez votre partie")
    pgn_text = st.text_area("Saisir le PNG",placeholder="Collez ici le PGN de la partie",height=68,label_visibility ="collapsed")
    user_depth = st.slider("Profondeur d'analyse",min_value=5, max_value=20, value=16)
    if st.button("Analyser", disabled=not pgn_text.strip()):
        st.session_state.analysis = analyze_game(pgn_text,user_depth)
        st.session_state.pgn_last = pgn_text




with col2:
    st.subheader("Analyse des coups")


    if st.session_state.analysis:
        analysis_df = pd.DataFrame(st.session_state.analysis)
        st.write(analysis_df)


with col3:
    st.subheader("Évolution de l'avantage")
    if st.session_state.analysis:
        evals = [coup["eval"] for coup in st.session_state.analysis]
        min_val = min(evals) - 100

        formatted_labels = [format_eval(coup["raw_eval"]) for coup in st.session_state.analysis]



        fig = go.Figure()

        # Fond blanc jusqu'en bas
        fig.add_trace(go.Scatter(
            x=list(range(len(evals))),
            y=[min_val]*len(evals),
            mode='lines',
            line=dict(color='white'),
            fill=None,
            showlegend=False,
            hoverinfo="skip"
            )
        )

        # Courbe d'évaluation + remplissage
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
        # Ligne y=0 au premier plan
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
            xaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                showline=False,
            ),
            yaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                showline=False,
            )
        )
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar': False,"staticPlot": False})
        if st.button("Balloooooon !"):
            st.balloons()


#DEBUG
st.write("evals")
st.write(evals)
st.write("formatted_labels")
st.write(formatted_labels)
