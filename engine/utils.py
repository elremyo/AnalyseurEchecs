def convert_eval_to_cp(e):
    if e["type"] == "cp":
        return e["value"]
    elif e["type"] == "mate":
        return 1500 if e["value"] > 0 else -1500
    return 0

def get_quality(delta, eval_type_before, eval_type_after):
    if eval_type_after == "mate" and eval_type_before != "mate":
        return "Brillant"
    
    delta_abs = abs(delta)
    if delta_abs == 0:
        return "Meilleur"
    elif delta_abs < 20:
        return "Excellent"
    elif delta_abs < 50:
        return "Bon"
    elif delta_abs < 150:
        return "Imprécision"
    elif delta_abs < 300:
        return "Erreur"
    else:
        return "Gaffe"

def format_eval(e):
    if e["type"] == "cp":
        val = round(e["value"] / 100, 2)
        return f"+{val}" if val > 0 else f"{val}"
    elif e["type"] == "mate":
        return f"M{e['value']}" if e["value"] > 0 else f"-M{abs(e['value'])}"
    return "?"
