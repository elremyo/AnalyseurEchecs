import math
from typing import Optional, Dict, Any
from constants import (
    EVAL_THRESHOLDS,
    CP_MIN,
    CP_MAX,
    WIN_CHANCE_FACTOR,
    MATE_VALUE
)

def convert_eval_to_cp(e: Dict[str, Any]) -> int:
    if e["type"] == "cp":
        return e["value"]
    elif e["type"] == "mate":
        return MATE_VALUE if e["value"] >= 0 else -MATE_VALUE
    return 0

def _quality_cp_to_mate(curr_eval: dict) -> str:
    """Évalue la qualité d'une transition de centipawns à mate."""
    if curr_eval["value"] > 0:
        return "Meilleur"
    elif curr_eval["value"] >= EVAL_THRESHOLDS["MATE_IN_NEGATIVE"]:
        return "Gaffe"
    elif curr_eval["value"] >= EVAL_THRESHOLDS["MATE_IN_NEGATIVE_BIG"]:
        return "Erreur"
    else:
        return "Imprécision"

def _quality_mate_to_cp(prev_cp: int, curr_cp: int) -> str:
    """Évalue la qualité d'une transition de mate à centipawns."""
    if prev_cp < 0 and curr_cp < 0:
        return "Meilleur"
    elif curr_cp >= EVAL_THRESHOLDS["GOOD_CP_THRESHOLD"]:
        return "Bon"
    elif curr_cp >= EVAL_THRESHOLDS["GOOD_CP_LOWER"]:
        return "Imprécision"
    elif curr_cp >= EVAL_THRESHOLDS["ERROR_CP_UPPER"]:
        return "Erreur"
    else:
        return "Gaffe"

def _quality_mate_to_mate(prev_cp: int, curr_cp: int) -> str:
    """Évalue la qualité d'une transition de mate à mate."""
    if prev_cp > 0:
        if curr_cp <= EVAL_THRESHOLDS["MATE_IN_POSITIVE"]:
            return "Erreur"
        elif curr_cp < 0:
            return "Gaffe"
        elif curr_cp < prev_cp:
            return "Meilleur"
        elif curr_cp <= prev_cp + EVAL_THRESHOLDS["MATE_IN_SAME"]:
            return "Excellent"
        else:
            return "Bon"
    else:
        if curr_cp == prev_cp:
            return "Meilleur"
        else:
            return "Bon"

def _quality_cp_to_cp(delta: int, prev_cp: int, curr_cp: int, prev_eval: dict, curr_eval: dict) -> str:
    """Évalue la qualité d'une transition de centipawns à centipawns."""
    delta_abs = abs(delta)
    if delta_abs < EVAL_THRESHOLDS["BEST_MOVE"]:
        return "Meilleur"
    if delta_abs < EVAL_THRESHOLDS["EXCELLENT_MOVE"]:
        return "Excellent"
    elif delta_abs < EVAL_THRESHOLDS["GOOD_MOVE"]:
        return "Bon"
    elif delta_abs < EVAL_THRESHOLDS["INACCURATE_MOVE"]:
        return "Imprécision"
    elif delta_abs < EVAL_THRESHOLDS["MISTAKE_MOVE"]:
        return "Erreur"
    else:
        # Si la position reste gagnante malgré la gaffe, on peut rétrograder à "Bon"
        if curr_cp >= EVAL_THRESHOLDS["WINNING_THRESHOLD"] or (prev_cp <= EVAL_THRESHOLDS["LOSING_THRESHOLD"] and prev_eval["type"] == "cp" and curr_eval["type"] == "cp"):
            return "Bon"
        return "Gaffe"

def get_quality(delta: int, is_best: bool, is_theoretical: bool, prev_eval: Dict[str, Any], curr_eval: Dict[str, Any], prev_cp: int, curr_cp: int) -> str:
    """Dispatch principal qui délègue aux fonctions spécialisées selon le type de transition."""
    if is_best and not is_theoretical:
        return "Meilleur"
    if is_theoretical:
        return "Théorique"
    
    # Dispatch selon le type de transition
    if prev_eval["type"] == "cp" and curr_eval["type"] == "mate":
        return _quality_cp_to_mate(curr_eval)
    elif prev_eval["type"] == "mate" and curr_eval["type"] == "cp":
        return _quality_mate_to_cp(prev_cp, curr_cp)
    elif prev_eval["type"] == "mate" and curr_eval["type"] == "mate":
        return _quality_mate_to_mate(prev_cp, curr_cp)
    else:  # cp to cp
        return _quality_cp_to_cp(delta, prev_cp, curr_cp, prev_eval, curr_eval)

def format_eval(e: Dict[str, Any]) -> str:
    if e["type"] == "cp":
        val = round(e["value"] / 100, 2)
        return f"+{val}" if val > 0 else f"{val}"
    elif e["type"] == "mate":
        return f"M{e['value']}" if e["value"] > 0 else f"-M{abs(e['value'])}"
    return "?"

def get_win_chance(cp: int) -> float:
    cp = max(min(cp, CP_MAX), CP_MIN)
    return 50 + 50 * (2 / (1 + math.exp(-WIN_CHANCE_FACTOR * cp)) - 1)


def compute_move_accuracy(
    prev_eval: Dict[str, Any],
    curr_eval: Dict[str, Any],
    side: str,
) -> float:
    """
    Accuracy d'un coup selon la perte de win% du joueur qui vient de jouer.
    Formule Chess.com : 103.1668 * exp(-0.04354 * loss) - 3.1669, clampé [0, 100].
    """
    prev_cp = convert_eval_to_cp(prev_eval)
    curr_cp = convert_eval_to_cp(curr_eval)
    wp_before = get_win_chance(prev_cp)
    wp_after  = get_win_chance(curr_cp)

    # Perte de win% du côté qui vient de jouer (toujours >= 0 si coup bon)
    if side == "white":
        win_pct_loss = max(0.0, wp_before - wp_after)
    else:
        win_pct_loss = max(0.0, wp_after - wp_before)

    raw = 103.1668 * math.exp(-0.04354 * win_pct_loss) - 3.1669
    return max(0.0, min(100.0, raw))