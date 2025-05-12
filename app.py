import streamlit as st
import chess.pgn
from stockfish import Stockfish
import io
import pandas as pd

stockfish_path = "C:\Program Files (x86)\stockfish\stockfish-windows-x86-64-avx2.exe"
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
    fig = plot_evaluation_histogram(analysis)
    st.plotly_chart(fig)
    