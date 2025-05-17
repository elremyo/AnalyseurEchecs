import streamlit as st
from engine.analysis import *
from engine.utils import *
import chess
import os


set_page_style()

# Chemin vers Stockfish à adapter si besoin
stockfish_path = "C:/Program Files (x86)/stockfish/stockfish-windows-x86-64-avx2.exe"

ASSETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
book_path = os.path.join(ASSETS_PATH, "performance.bin")

# Session state init
init_session_state()


col1, col2, col3 = st.columns(spec=[3,5,4], gap="small", border=True)

with col1:
    pgn_text = st.text_area("PGN de la partie :", placeholder="Collez ici le PGN de la partie", height=120)
    user_depth = st.slider("Profondeur d'analyse", min_value=5, max_value=20, value=16)
    
    if st.button("Analyser", disabled=not pgn_text.strip()):
        analysis, white_name, black_name = analyze_game(pgn_text, user_depth, stockfish_path,book_path)
        st.session_state.analysis = analysis
        st.session_state.white_name = white_name
        st.session_state.black_name = black_name
        st.session_state.pgn_last = pgn_text

with col2:
    if st.session_state.analysis:
        try:
            game=load_pgn(pgn_text)
            board = chess.Board()
            moves = [move for move in game.mainline_moves()]
            mv = st.slider("Coup",min_value=0,max_value=len(moves),value=0)
            for move in moves[0:mv]:
                board.push(move)
            render_svg(chess.svg.board(board))
        except ValueError as e:
            st.error(f"Erreur lors du chargement du PGN : {e}")

with col3:
    st.write("Graphe de la partie")
        
    display_graph()



    with st.container(border=False):
        if st.session_state.analysis:
            display_quality_table()
