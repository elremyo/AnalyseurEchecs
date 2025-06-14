import math

def convert_eval_to_cp(e):
    if e["type"] == "cp":
        return e["value"]
    elif e["type"] == "mate":
        return 1200 if e["value"] >= 0 else -1200
    return 0

def get_quality(delta, is_best, is_theoretical, prev_eval, curr_eval, prev_cp, curr_cp):
    if is_best and not is_theoretical:
        return "Meilleur"
    if is_theoretical:
        return "Théorique"

    # Mate cases
    if prev_eval["type"] == "cp" and curr_eval["type"] == "mate":
        if curr_eval["value"] > 0:
            return "Meilleur"
        elif curr_eval["value"] >= -2:
            return "Gaffe"
        elif curr_eval["value"] >= -5:
            return "Erreur"
        else:
            return "Imprécision"
    if prev_eval["type"] == "mate" and curr_eval["type"] == "cp":
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
    if prev_eval["type"] == "mate" and curr_eval["type"] == "mate":
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

    # Centipawn cases
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

def format_eval(e):
    if e["type"] == "cp":
        val = round(e["value"] / 100, 2)
        return f"+{val}" if val > 0 else f"{val}"
    elif e["type"] == "mate":
        return f"M{e['value']}" if e["value"] > 0 else f"-M{abs(e['value'])}"
    return "?"

def get_win_chance(cp):
    cp = max(min(cp, 1000), -1000)
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)

def get_winner(pgn: str):
    """
    Retourne 'white', 'black', 'draw' ou None selon le résultat du PGN.
    """
    import re
    # Recherche la balise [Result "..."] ou la dernière occurrence dans le texte
    m = re.search(r'\[Result\s+"([^"]+)"\]', pgn)
    if m:
        result = m.group(1)
    else:
        m = re.findall(r'(1-0|0-1|1/2-1/2|½-½)', pgn)
        if m:
            result = m[-1]
        else:
            result = "?"

    if result == "1-0":
        return "white"
    elif result == "0-1":
        return "black"
    elif result in ("1/2-1/2", "½-½"):
        return "draw"
    else:
        return None