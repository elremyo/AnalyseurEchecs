import os
import streamlit as st
import textwrap
import base64


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

def img_to_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

def render_quality_table(recap, white, black, quality_colors, quality_images):
    """Affiche un tableau d'analyse des coups avec alignement parfait."""
    table_html = textwrap.dedent(f"""
    <style>
        table, thead, tbody, th, td, tr {{
            border: none !important;
            outline: none !important;
        }}
    </style>
    <table style='max-width:100%; border-collapse: collapse; table-layout: fixed; margin:auto;'>
        <thead>
            <tr>
                <th style='text-align:left; width:30%; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'></th>
                <th style='text-align:center; width:25%; font-weight:bold; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'>{white}</th>
                <th style='width:10%; font-size:12px;'></th>
                <th style='text-align:center; width:25%; font-weight:bold; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'>{black}</th>
            </tr>
        </thead>
        <tbody>
""")


    for qualite, row in recap.iterrows():
        color = quality_colors.get(qualite, "black")
        value_white = row[white]
        value_black = row[black]
        img_path = quality_images.get(qualite)

        if img_path and os.path.exists(img_path):
            img_b64 = img_to_base64(img_path)
            img_tag = (
                f"<img src='data:image/png;base64,{img_b64}' "
                f"style='display:block; margin:auto; width:24px; height:24px; height:auto;'>"
            )
        else:
            img_tag = ""

        table_html += textwrap.dedent(f"""
            <tr>
                <td style='text-align:left; color:{color}; font-weight:bold; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; border:none;'>{qualite}</td>
                <td style='text-align:center; color:{color}; border:none;'>{value_white}</td>
                <td style='text-align:center; border:none;'>{img_tag}</td>
                <td style='text-align:center; color:{color}; border:none;'>{value_black}</td>
            </tr>
        """)

    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)