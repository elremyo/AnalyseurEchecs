import chess.pgn
import chess.polyglot
import io
import streamlit as st

from utils.eval_utils import convert_eval_to_cp, get_quality
from stockfish import Stockfish


class InvalidPgnError(ValueError):
    """PGN illisible, vide ou sans ligne principale."""


def load_pgn(pgn: str) -> chess.pgn.Game:
    """Charge un objet Game à partir d'un texte PGN."""
    if not pgn or not str(pgn).strip():
        raise InvalidPgnError("PGN vide.")
    try:
        game = chess.pgn.read_game(io.StringIO(pgn))
    except Exception as e:
        raise InvalidPgnError(f"PGN illisible : {e}") from e
    if game is None:
        raise InvalidPgnError("PGN illisible (aucune partie reconnue).")
    if not any(game.mainline_moves()):
        raise InvalidPgnError("PGN invalide ou sans coups sur la ligne principale.")
    return game


@st.cache_data
def get_moves_from_pgn(pgn_text: str) -> list[chess.Move]:
    """Parse le PGN et retourne la liste des coups. Résultat mis en cache par PGN."""
    if not pgn_text or not str(pgn_text).strip():
        raise InvalidPgnError("Aucun PGN à afficher.")
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_text))
    except Exception as e:
        raise InvalidPgnError(f"PGN illisible : {e}") from e
    if game is None:
        raise InvalidPgnError("PGN illisible (aucune partie reconnue).")
    moves = list(game.mainline_moves())
    if not moves:
        raise InvalidPgnError("PGN sans coups sur la ligne principale.")
    return moves

def is_theoretical_move(board, move, reader):
    try:
        entries = list(reader.find_all(board))
        theoretical_moves = [entry.move for entry in entries]
        return move in theoretical_moves
    except Exception:
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
    caption_placeholder = st.empty()
    caption_placeholder.caption("Si l'analyse est trop longue, vous pouvez diminuer la profondeur d'analyse dans les options.")

    #Ouverture du livre des coups théoriques
    book_reader = None
    if book_path:
        try:
            book_reader = chess.polyglot.open_reader(book_path)
        except FileNotFoundError:
            book_reader = None

    for idx, move in enumerate(moves):
        # État avant le coup
        stockfish.set_fen_position(board.fen())
        eval_before = stockfish.get_evaluation()
        best_move = stockfish.get_best_move()
        best_move_san = board.san(chess.Move.from_uci(best_move)) if best_move else "Non spécifié"

        # Test coup théorique
        is_theo = False
        if book_reader:
            is_theo = is_theoretical_move(board, move, book_reader)

        move_san = board.san(move)

        # On joue le coup réel
        board.push(move)
        stockfish.set_fen_position(board.fen())
        eval_after = stockfish.get_evaluation()

        #Ajout du calcul des menaces
        threats = []
        top_moves = stockfish.get_top_moves(2)
        threats = [m['Move'] for m in top_moves if m['Move'] != best_move][:1]

        # Calcul du delta
        delta = convert_eval_to_cp(eval_after) - convert_eval_to_cp(eval_before)

        is_best = (best_move == move.uci())

        # Attribution de la qualité
        quality = get_quality(
            delta=delta,
            is_best=is_best,
            is_theoretical=is_theo,
            prev_eval=eval_before,
            curr_eval=eval_after,
            prev_cp=convert_eval_to_cp(eval_before),
            curr_cp=convert_eval_to_cp(eval_after)
        )

        # Ajout à l'analyse
        analysis.append({
            "coup": move_san,
            "qualité": quality,
            "eval": convert_eval_to_cp(eval_after),
            "raw_eval": eval_after,
            "best_move": best_move_san,
            "best_move_uci": best_move, 
            "is_best": is_best,
            "is_theoretical": is_theo,
            "threats": threats
        })

        # Mise à jour de la barre de progression
        percent = int(((idx + 1) / total_moves) * 100)
        progress_bar.progress((idx + 1) / total_moves, text=f"Analyse en cours {idx + 1}/{total_moves} ({percent}%)")

    progress_bar.empty()  
    caption_placeholder.empty()

    #Fermeture du livre des coups théoriques
    if book_reader:
        book_reader.close()

    return analysis, white_player, black_player


def find_key_moments(analysis, threshold=500, min_gap_between_moments=2, winner=None):
    determinants = []
    critiques = []
    prev_eval = None

    for idx, move_info in enumerate(analysis):
        curr_eval = move_info.get("eval", 0)
        curr_raw_eval = move_info.get("raw_eval", {})

        # Ne pas considérer un coup qui mène directement au mat
        if curr_raw_eval.get("type") == "mate" and curr_raw_eval.get("value") == 0:
            prev_eval = curr_eval
            continue

        if prev_eval is not None:
            delta = curr_eval - prev_eval
            abs_delta = abs(delta)

            # sustained_change vérifie que le changement d'évaluation est durable, 
            # pour éviter de signaler des variations temporaires corrigées immédiatement après
            sustained_change = True
            if idx + 1 < len(analysis):
                next_eval = analysis[idx + 1].get("eval", curr_eval)
                delta_next = next_eval - curr_eval
                if abs(delta_next) > abs_delta * 0.5:
                    sustained_change = False

            # Blunder extrême même s'il est corrigé ensuite
            is_extreme_blunder = abs_delta > threshold * 2.5 or (prev_eval > 600 and curr_eval < -400)

            is_blunder = (
                (curr_eval * prev_eval < 0 and abs_delta > threshold)
                or (abs(prev_eval) < threshold / 2 and abs(curr_eval) > threshold)
                or (abs_delta > threshold * 1.5)
                or is_extreme_blunder
            ) 

            if is_blunder and (sustained_change or is_extreme_blunder):
                if winner:
                    winning_eval_sign = 1 if winner == "white" else -1
                    # Si l'erreur va à l'encontre du résultat final => critique
                    if curr_eval * winning_eval_sign > 0:
                        determinants.append(idx)
                    else:
                        critiques.append(idx)
                else:
                    determinants.append(idx)

        prev_eval = curr_eval

    def filter_moments(moment_list):
        filtered = []
        for i in range(len(moment_list)):
            if i == 0 or moment_list[i] - filtered[-1] >= min_gap_between_moments:
                filtered.append(moment_list[i])
        return filtered

    return {
        "moments_determinants": filter_moments(determinants),
        "moments_critiques": filter_moments(critiques)
    }
