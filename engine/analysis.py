import io
import os
import re
import chess
import chess.pgn
import chess.polyglot
import streamlit as st

from utils.eval_utils import convert_eval_to_cp, get_quality, compute_move_accuracy
from constants import (
    MAX_MAINLINE_HALFMOVES,
    MAX_PGN_CHARACTERS,
    DEFAULT_SKILL_LEVEL,
    DEFAULT_HASH,
    DEFAULT_MINIMUM_THINKING_TIME,
    DEFAULT_THREADS
)
from stockfish import Stockfish
from domain.analyzed_move import AnalyzedMove

# Regex pattern for score parsing - compiled once at module level
_SCORE_RE = re.compile(r"score (cp|mate) (-?\d+)")


class InvalidPgnError(ValueError):
    """PGN illisible, vide ou sans ligne principale."""


def _parse_eval_from_info_line(info_line: str, white_to_move: bool) -> dict:
    """Reconstruit le dict d'éval au format get_evaluation() depuis la dernière ligne info."""
    if not info_line or not info_line.strip():
        return {"type": "cp", "value": 0}
    matches = list(_SCORE_RE.finditer(info_line))
    if not matches:
        return {"type": "cp", "value": 0}
    typ, val_s = matches[-1].group(1), matches[-1].group(2)
    val = int(val_s)
    compare = 1 if white_to_move else -1
    return {"type": typ, "value": val * compare}


def _eval_from_top_move(entry: dict) -> dict:
    """Une entrée get_top_moves() -> raw_eval pour convert_eval_to_cp / get_quality."""
    if entry.get("Mate") is not None:
        return {"type": "mate", "value": int(entry["Mate"])}
    if entry.get("Centipawn") is not None:
        return {"type": "cp", "value": int(entry["Centipawn"])}
    return {"type": "cp", "value": 0}


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

@st.cache_resource
def _get_stockfish_engine(_stockfish_path: str) -> Stockfish:
    """Retourne une instance Stockfish mutualisée via cache."""
    stockfish = Stockfish(path=_stockfish_path)
    stockfish.update_engine_parameters(
        {
            "Skill Level": DEFAULT_SKILL_LEVEL,
            "Threads": DEFAULT_THREADS,
            "Hash": DEFAULT_HASH,
            "Minimum Thinking Time": DEFAULT_MINIMUM_THINKING_TIME,
        }
    )
    return stockfish


def _setup_stockfish(user_depth: int, stockfish_path: str) -> Stockfish:
    """Configure et retourne une instance Stockfish avec la profondeur demandée."""
    stockfish = _get_stockfish_engine(stockfish_path)
    stockfish.set_depth(user_depth)
    return stockfish


def _open_book(book_path: str):
    """Ouvre le livre d'ouvertures polyglot et retourne le reader."""
    if not book_path:
        return None
    try:
        return chess.polyglot.open_reader(book_path)
    except FileNotFoundError:
        return None


def _get_stockfish_result(stockfish: Stockfish, board: chess.Board, compute_threats: bool) -> dict:
    """Récupère les résultats Stockfish pour une position donnée.
    
    Returns:
        dict: Contient 'best_move', 'best_move_san', 'eval', 'threats' (si compute_threats)
    """
    white_to_move = board.turn == chess.WHITE
    
    if compute_threats:
        top_moves = stockfish.get_top_moves(2)
        if top_moves:
            best_move = top_moves[0]["Move"]
            eval_result = _eval_from_top_move(top_moves[0])
            threats = [
                m["Move"]
                for m in top_moves
                if m.get("Move") and m.get("Move") != best_move
            ][:1]
        else:
            best_move = None
            eval_result = {"type": "cp", "value": 0}
            threats = []
    else:
        best_move = stockfish.get_best_move()
        info = stockfish.info or ""
        if _SCORE_RE.search(info):
            eval_result = _parse_eval_from_info_line(info, white_to_move)
        else:
            eval_result = stockfish.get_evaluation()
        threats = []
    
    best_move_san = ""
    if best_move:
        try:
            best_move_san = board.san(chess.Move.from_uci(best_move))
        except ValueError:
            best_move_san = "Non spécifié"
    
    return {
        "best_move": best_move,
        "best_move_san": best_move_san,
        "eval": eval_result,
        "threats": threats
    }


def _build_analyzed_move_from_results(board: chess.Board, move: chess.Move, 
                                     prev_result: dict, curr_result: dict, 
                                     book_reader, move_index: int) -> AnalyzedMove:
    """Construit un AnalyzedMove à partir des résultats précalculés."""
    # Vérifier si le coup est théorique
    is_theo = False
    if book_reader:
        is_theo = is_theoretical_move(board, move, book_reader)
    
    move_san = board.san(move)
    
    # Calcul du delta
    delta = convert_eval_to_cp(curr_result["eval"]) - convert_eval_to_cp(prev_result["eval"])
    
    is_best = (prev_result["best_move"] == move.uci())
    
    # Attribution de la qualité
    quality = get_quality(
        delta=delta,
        is_best=is_best,
        is_theoretical=is_theo,
        prev_eval=prev_result["eval"],
        curr_eval=curr_result["eval"],
        prev_cp=convert_eval_to_cp(prev_result["eval"]),
        curr_cp=convert_eval_to_cp(curr_result["eval"])
    )
    
    side = "white" if move_index % 2 == 0 else "black"
    accuracy = compute_move_accuracy(prev_result["eval"], curr_result["eval"], side)

    return AnalyzedMove(
        coup=move_san,
        quality=quality,
        eval=convert_eval_to_cp(curr_result["eval"]),
        raw_eval=curr_result["eval"],
        best_move=prev_result["best_move_san"],
        best_move_uci=prev_result["best_move"],
        is_best=is_best,
        is_theoretical=is_theo,
        threats=curr_result["threats"],
        accuracy=accuracy,
    )


def _analyze_single_move(board, stockfish, move, book_reader, compute_threats: bool, move_index: int) -> AnalyzedMove:
    """Analyse un seul coup et retourne un AnalyzedMove."""
    # Une seule recherche avant le coup : get_best_move remplit .info avec le score final.
    stockfish.set_fen_position(board.fen(), send_ucinewgame_token=(move_index == 0))
    white_before = board.turn == chess.WHITE
    best_move = stockfish.get_best_move()
    info_before = stockfish.info or ""
    if _SCORE_RE.search(info_before):
        eval_before = _parse_eval_from_info_line(info_before, white_before)
    else:
        eval_before = stockfish.get_evaluation()

    best_move_san = board.san(chess.Move.from_uci(best_move)) if best_move else "Non spécifié"

    is_theo = False
    if book_reader:
        is_theo = is_theoretical_move(board, move, book_reader)

    move_san = board.san(move)

    board.push(move)
    stockfish.set_fen_position(board.fen(), send_ucinewgame_token=False)

    if compute_threats:
        top_moves = stockfish.get_top_moves(2)
        if top_moves:
            eval_after = _eval_from_top_move(top_moves[0])
            threats = [
                m["Move"]
                for m in top_moves
                if m.get("Move") and m.get("Move") != best_move
            ][:1]
        else:
            eval_after = {"type": "cp", "value": 0}
            threats = []
    else:
        _ = stockfish.get_best_move()
        info_after = stockfish.info or ""
        if _SCORE_RE.search(info_after):
            eval_after = _parse_eval_from_info_line(
                info_after, board.turn == chess.WHITE
            )
        else:
            eval_after = stockfish.get_evaluation()
        threats = []

    # Calcul du delta
    delta = convert_eval_to_cp(eval_after) - convert_eval_to_cp(eval_before)

    is_best = (best_move == move.uci())

    # Attribution de la quality
    quality = get_quality(
        delta=delta,
        is_best=is_best,
        is_theoretical=is_theo,
        prev_eval=eval_before,
        curr_eval=eval_after,
        prev_cp=convert_eval_to_cp(eval_before),
        curr_cp=convert_eval_to_cp(eval_after)
    )

    # Retourne l'analyse du coup
    return AnalyzedMove(
        coup=move_san,
        quality=quality,
        eval=convert_eval_to_cp(eval_after),
        raw_eval=eval_after,
        best_move=best_move_san,
        best_move_uci=best_move,
        is_best=is_best,
        is_theoretical=is_theo,
        threats=threats
    )


def analyze_game(
    pgn: str,
    user_depth: int,
    stockfish_path: str,
    book_path: str,
    *,
    compute_threats: bool = False,
    progress_callback=None,
):
    """Analyse une partie PGN et retourne la liste des coups annotés.

    Optimisée pour n'appeler Stockfish qu'une fois par position au lieu de deux.
    Gain : -50% temps d'analyse (compute_threats=False) ou -33% (compute_threats=True).
    
    Si compute_threats est False, n'appelle pas get_top_moves (flèches menaces désactivées).
    """
    if len(pgn) > MAX_PGN_CHARACTERS:
        raise InvalidPgnError(
            f"PGN trop volumineux (max {MAX_PGN_CHARACTERS:,} caractères)."
        )
    game = load_pgn(pgn)
    board = chess.Board()
    analysis = []
    def _header_player_name(raw, fallback: str) -> str:
        if raw is None:
            return fallback
        s = str(raw).strip()
        if not s or s == "?":
            return fallback
        return s

    white_player = _header_player_name(game.headers.get("White"), "Blanc")
    black_player = _header_player_name(game.headers.get("Black"), "Noir")

    stockfish = _setup_stockfish(user_depth, stockfish_path)

    moves = list(game.mainline_moves())
    if len(moves) > MAX_MAINLINE_HALFMOVES:
        raise InvalidPgnError(
            f"Partie trop longue (max {MAX_MAINLINE_HALFMOVES} demi-coups)."
        )
    total_moves = len(moves)
    
    # Callback de progression initial
    if progress_callback:
        progress_callback(0, total_moves, "Préparation de l'analyse")

    # Ouverture du livre des coups théoriques
    book_reader = _open_book(book_path)

    # Évaluation initiale (position de départ)
    stockfish.set_fen_position(board.fen(), send_ucinewgame_token=True)
    prev_result = _get_stockfish_result(stockfish, board, compute_threats)
    
    for idx, move in enumerate(moves):
        # Analyser le coup avec prev_result (position avant) et curr_result (position après)
        board.push(move)
        
        # Évaluer la position APRÈS le coup (deviendra prev_result au prochain tour)
        stockfish.set_fen_position(board.fen(), send_ucinewgame_token=False)
        curr_result = _get_stockfish_result(stockfish, board, compute_threats)
        
        # Revenir en arrière pour construire l'analyse avec la bonne position
        board.pop()
        
        analyzed_move = _build_analyzed_move_from_results(board, move, prev_result, curr_result, book_reader, idx)
        analysis.append(analyzed_move)
        
        # Avancer pour le prochain tour
        board.push(move)
        prev_result = curr_result

        # Mise à jour de la progression
        if progress_callback:
            percent = int(((idx + 1) / total_moves) * 100)
            progress_callback(idx + 1, total_moves, f"Analyse en cours {idx + 1}/{total_moves} ({percent}%)")

    # Fermeture du livre des coups théoriques
    if book_reader:
        book_reader.close()

    return analysis, white_player, black_player


def find_key_moments(analysis, threshold=500, min_gap_between_moments=2, winner=None):
    determinants = []
    critiques = []
    prev_eval = None

    for idx, move_info in enumerate(analysis):
        curr_eval = move_info.eval
        curr_raw_eval = move_info.raw_eval

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
                next_eval = analysis[idx + 1].eval
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
