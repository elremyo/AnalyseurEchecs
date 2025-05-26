import chess.pgn
import chess.polyglot
import chess.svg
import io
import base64
import streamlit as st

from utils.display import *
from utils.eval_utils import *
from stockfish import Stockfish

def load_pgn(pgn: str) -> chess.pgn.Game:
    """Charge un objet Game à partir d'un texte PGN."""
    try:
        pgn_io = io.StringIO(pgn)
        game = chess.pgn.read_game(pgn_io)

        if not any(game.mainline_moves()):
            st.error("Le PGN fourni est invalide ou vide.")
        return game
    except Exception as e:
        raise e

def is_theoretical_move(board, move, book_path):
    try:
        with chess.polyglot.open_reader(book_path) as reader:
            entries = list(reader.find_all(board))
            theoretical_moves = [entry.move for entry in entries]
            return move in theoretical_moves
    except FileNotFoundError:
        return False

def analyze_game(pgn: str, user_depth: int, stockfish_path: str, book_path: str):
    """Analyse une partie PGN et retourne la liste des coups annotés."""
    game = load_pgn(pgn)
    board = chess.Board()
    analysis = []
    white_player = game.headers.get("White", "Blanc")
    black_player = game.headers.get("Black", "Noir")

    stockfish = Stockfish(path=stockfish_path, depth=user_depth)
    stockfish.update_engine_parameters({"Skill Level": 20})  # Optionnel mais utile

    moves = list(game.mainline_moves())
    total_moves = len(moves)
    progress_bar = st.progress(0, text="Préparation de l'analyse")

    for idx, move in enumerate(moves):
        # État avant le coup
        stockfish.set_fen_position(board.fen())
        eval_before = stockfish.get_evaluation()

        # Test coup théorique
        is_theo = False
        if book_path:
            is_theo = is_theoretical_move(board, move, book_path)
        
        # On joue le coup réel
        board.push(move)
        stockfish.set_fen_position(board.fen())
        eval_after = stockfish.get_evaluation()

        # Calcul du delta
        delta = convert_eval_to_cp(eval_after) - convert_eval_to_cp(eval_before)

        best_move = stockfish.get_best_move()
        is_best = (best_move == move.uci())

        # Attribution de la qualité
        quality = get_quality(delta, is_best, is_theo)

        # Ajout à l'analyse
        analysis.append({
            "coup": move.uci(),
            "qualité": quality,
            "eval": convert_eval_to_cp(eval_after),
            "raw_eval": eval_after,
            "best_move": best_move,
            "is_best": is_best,
            "is_theoretical": is_theo
        })

        # Mise à jour de la barre de progression
        percent = int(((idx + 1) / total_moves) * 100)
        progress_bar.progress((idx + 1) / total_moves, text=f"Analyse en cours {idx + 1}/{total_moves} ({percent}%)")

    progress_bar.empty()  # Retire la barre à la fin

    return analysis, white_player, black_player


def render_svg(board: chess.Board, flipped: bool = False):
    """Affiche un SVG dans Streamlit, retourné si flipped=True."""
    svg = chess.svg.board(board, flipped=flipped)
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    st.write(html, unsafe_allow_html=True)