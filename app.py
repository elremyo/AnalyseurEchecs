import streamlit as st
import chess.pgn
from stockfish import Stockfish
import io
import pandas as pd
import plotly.graph_objects as go
import os
st.set_page_config(layout="wide")


#os.system("chmod +x ./bin/stockfish")

#stockfish_path = "./bin/stockfish"
stockfish_path = "C:\Program Files (x86)\stockfish\stockfish-windows-x86-64-avx2.exe"


def convert_eval_to_cp(e):
    if e["type"] == "cp":
        return e["value"]
    elif e["type"] == "mate":
        return 1500 if e["value"] > 0 else -1500
    return 0

def get_quality(delta, eval_type_before, eval_type_after):
    # Si on passe d'une éval normale à un mat (ou l'inverse)
    if eval_type_after == "mate" and eval_type_before != "mate":
        return "Brillant"
    
    delta_abs = abs(delta)

    if delta_abs == 0:
        return "Meilleur"
    elif delta_abs < 20:
        return "Excellent"
    elif delta_abs < 50:
        return "Bon"
    elif delta_abs < 150:
        return "Imprécision"
    elif delta_abs < 300:
        return "Erreur"
    else:
        return "Gaffe"


# Fonction pour analyser la partie PGN
def analyze_game(pgn_text,user_depth):
    # Simuler un fichier avec le texte PGN
    pgn_io = io.StringIO(pgn_text)
    
    # Charger le PGN de la partie
    game = chess.pgn.read_game(pgn_io)
    board = chess.Board()
    analysis = []

    white_player = game.headers.get("White", "Blanc")
    black_player = game.headers.get("Black", "Noir")

    stockfish = Stockfish(path=stockfish_path, depth=user_depth)

    # Analyser chaque coup
    for move in game.mainline_moves():
        stockfish.set_fen_position(board.fen())
        best_move = stockfish.get_best_move()
        eval_before = stockfish.get_evaluation()

        board.push(move)
        stockfish.set_fen_position(board.fen())
        eval_after = stockfish.get_evaluation()


        eval_before_cp = convert_eval_to_cp(eval_before)
        eval_after_cp = convert_eval_to_cp(eval_after)

        delta = eval_after_cp - eval_before_cp

        quality = get_quality(
            delta,
            eval_before["type"] if isinstance(eval_before, dict) else "cp",
            eval_after["type"] if isinstance(eval_after, dict) else "cp"
        )



        analysis.append({
            "coup": move.uci(),
            "qualité": quality,
            "eval": eval_after_cp,             # pour le tracé
            "raw_eval": eval_after             # pour l'affichage textuel
        })
    return analysis,white_player,black_player


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
if 'white_name' not in st.session_state:
    st.session_state.white_name = "Blanc"
if 'black_name' not in st.session_state:
    st.session_state.black_name = "Noir"



# Interface Streamlit
st.title("Analyseur de parties d'échecs")


col1, col2, col3 = st.columns(spec=[2,4,3],gap="small",border=True)

with col1:
    # Section d'import de la partie PGN
    st.subheader("Importez votre partie")
    pgn_text = st.text_area("Saisir le PNG",placeholder="Collez ici le PGN de la partie",height=68,label_visibility ="collapsed")
    user_depth = st.slider("Profondeur d'analyse",min_value=5, max_value=20, value=16)
    if st.button("Analyser", disabled=not pgn_text.strip()):
        analysis, white_name, black_name = analyze_game(pgn_text, user_depth)
        st.session_state.analysis = analysis
        st.session_state.white_name = white_name
        st.session_state.black_name = black_name
        st.session_state.pgn_last = pgn_text

        if 'white_name' not in st.session_state:
            st.session_state.white_name = "Blanc"
        if 'black_name' not in st.session_state:
            st.session_state.black_name = "Noir"





with col2:
    st.subheader("Analyse des coups")


    if st.session_state.analysis:
        analysis_df = pd.DataFrame(st.session_state.analysis)

        # Attribuer les joueurs
        white = st.session_state.white_name
        black = st.session_state.black_name
        analysis_df["joueur"] = [white if i % 2 == 0 else black for i in range(len(analysis_df))]

        # Regrouper par joueur et qualité, et compter
        recap = (
            analysis_df
            .groupby(["qualité", "joueur"])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=[st.session_state.white_name, st.session_state.black_name], fill_value=0)
            .reindex(index=[
            "Brillant", "Très bon", "Meilleur", "Excellent", "Bon",
            "Imprécision", "Erreur", "Gaffe"
            ], fill_value=0)
        )

        st.dataframe(recap)


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
