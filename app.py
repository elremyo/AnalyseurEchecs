import streamlit as st
import chess.pgn
from stockfish import Stockfish
import io
import pandas as pd
import plotly.graph_objects as go
import os

os.system("chmod +x ./bin/stockfish")

stockfish_path = "./bin/stockfish"
stockfish = Stockfish(path=stockfish_path, depth=15)


# Fonction pour analyser la partie PGN
def analyze_game(pgn_text):
    # Simuler un fichier avec le texte PGN
    pgn_io = io.StringIO(pgn_text)
    
    # Charger le PGN de la partie
    game = chess.pgn.read_game(pgn_io)
    board = chess.Board()
    analysis = []

    # Analyser chaque coup
    for move in game.mainline_moves():
        stockfish.set_fen_position(board.fen())
        best_move = stockfish.get_best_move()
        eval_before = stockfish.get_evaluation()

        board.push(move)
        stockfish.set_fen_position(board.fen())
        eval_after = stockfish.get_evaluation()

        delta = eval_after['value'] - eval_before['value'] if eval_after['type'] == 'cp' else 0

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
            "eval": eval_after['value'],
        })
    return analysis



# Interface Streamlit
st.title("Analyseur de parties d'échecs")

# Section d'import de la partie PGN
st.header("Importez votre partie")
pgn_text = st.text_area("Collez ici le PGN de la partie")

if pgn_text:
    # Analyser la partie
    analysis = analyze_game(pgn_text)

    # Afficher les résultats sous forme de tableau
    st.header("Analyse des coups")
    analysis_df = pd.DataFrame(analysis)
    st.write(analysis_df)

    # Afficher l'histogramme
    st.header("Évolution de l'avantage")
    evals = [coup["eval"] for coup in analysis]
    min_val = min(evals) - 100

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
        hoverinfo="skip"
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
    

    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar': False,"staticPlot": True})