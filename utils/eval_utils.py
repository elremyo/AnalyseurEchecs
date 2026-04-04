import math
from typing import Optional, Dict, Any

def convert_eval_to_cp(e: Dict[str, Any]) -> int:
    if e["type"] == "cp":
        return e["value"]
    elif e["type"] == "mate":
        return 1200 if e["value"] >= 0 else -1200
    return 0

def _quality_cp_to_mate(curr_eval: dict) -> str:
    """Évalue la qualité d'une transition de centipawns à mate."""
    if curr_eval["value"] > 0:
        return "Meilleur"
    elif curr_eval["value"] >= -2:
        return "Gaffe"
    elif curr_eval["value"] >= -5:
        return "Erreur"
    else:
        return "Imprécision"

def _quality_mate_to_cp(prev_cp: int, curr_cp: int) -> str:
    """Évalue la qualité d'une transition de mate à centipawns."""
    if prev_cp < 0 and curr_cp < 0:
        return "Meilleur"
    elif curr_cp >= 400:
        return "Bon"
    elif curr_cp >= 150:
        return "Imprécision"
    elif curr_cp >= -100:
        return "Erreur"
    else:
        return "Gaffe"

def _quality_mate_to_mate(prev_cp: int, curr_cp: int) -> str:
    """Évalue la qualité d'une transition de mate à mate."""
    if prev_cp > 0:
        if curr_cp <= -4:
            return "Erreur"
        elif curr_cp < 0:
            return "Gaffe"
        elif curr_cp < prev_cp:
            return "Meilleur"
        elif curr_cp <= prev_cp + 2:
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
    if delta_abs < 10:
        return "Meilleur"
    if delta_abs < 40:
        return "Excellent"
    elif delta_abs < 80:
        return "Bon"
    elif delta_abs < 200:
        return "Imprécision"
    elif delta_abs < 400:
        return "Erreur"
    else:
        # Si la position reste gagnante malgré la gaffe, on peut rétrograder à "Bon"
        if curr_cp >= 600 or (prev_cp <= -600 and prev_eval["type"] == "cp" and curr_eval["type"] == "cp"):
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
    cp = max(min(cp, 1000), -1000)
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)