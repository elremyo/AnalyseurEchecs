import chess.pgn
import io
from .utils import convert_eval_to_cp, get_quality
from stockfish import Stockfish
import base64
import streamlit as st

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


def analyze_game(pgn: str, user_depth: int, stockfish_path: str):
    """Analyse une partie PGN et retourne la liste des coups annotés."""
    game = load_pgn(pgn)
    board = chess.Board()
    analysis = []
    white_player = game.headers.get("White", "Blanc")
    black_player = game.headers.get("Black", "Noir")
    stockfish = Stockfish(path=stockfish_path, depth=user_depth)
    for move in game.mainline_moves():
        stockfish.set_fen_position(board.fen())
        eval_before = stockfish.get_evaluation()
        board.push(move)
        stockfish.set_fen_position(board.fen())
        eval_after = stockfish.get_evaluation()
        delta = convert_eval_to_cp(eval_after) - convert_eval_to_cp(eval_before)
        quality = get_quality(delta, eval_before.get("type", "cp"), eval_after.get("type", "cp"))
        analysis.append({
            "coup": move.uci(),
            "qualité": quality,
            "eval": convert_eval_to_cp(eval_after),
            "raw_eval": eval_after
        })
    return analysis, white_player, black_player

def render_svg(svg: str):
    """Affiche un SVG dans Streamlit."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    st.write(html, unsafe_allow_html=True)