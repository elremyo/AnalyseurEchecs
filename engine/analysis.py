import chess.pgn
import io
from .utils import convert_eval_to_cp, get_quality
from stockfish import Stockfish

def analyze_game(pgn_text, user_depth, stockfish_path):
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)
    if game is None:
        raise ValueError("Le PGN fourni est invalide ou vide.")

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
