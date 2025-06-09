import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import base64
import chess.svg
import re

from utils.eval_utils import *
from assets import *
from utils.session import *

board_size = 800 #in pixels



assets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
quality_images = {
"Théorique": os.path.join(assets_path, "theorique.png"),
"Gaffe": os.path.join(assets_path, "gaffe.png"),
"Erreur": os.path.join(assets_path, "erreur.png"),
"Imprécision": os.path.join(assets_path, "imprecision.png"),
"Bon": os.path.join(assets_path, "bon.png"),
"Excellent": os.path.join(assets_path, "excellent.png"),
"Meilleur": os.path.join(assets_path, "meilleur.png"),
"Critique": os.path.join(assets_path, "tres_bon.png"),
"Brillant": os.path.join(assets_path, "brillant.png")
}
quality_colors = {
"Théorique": "#a88764",
"Gaffe": "#c93233",
"Erreur": "#dc8c2a",
"Imprécision": "#e8b443",
"Bon": "#78af8b",
"Excellent": "#67ac49",
"Meilleur": "#98bc49",
"Critique": "#4c8caf",
"Brillant": "#1baa9b"
}

quality_board_colors = {
"Théorique":( "#ccb08c","#ae8763"),
"Gaffe":("#df8973","#c0604a"),
"Erreur":( "#e9b373","#cc8a49"),
"Imprécision":( "#f2cd7f", "#d4a456"),
"Bon": ("#c4c49f","#a79c77"),
"Excellent": ("#c5ca80","#a8a257"),
"Meilleur": ("#c5ca80","#a8a257"),
"Critique":("#a7b2b2", "#8a8a8a"),
"Brillant":("#1baa9b", "#1baa9b")  
}


def set_page_style():
    """Applique le style global de la page."""
    st.set_page_config(
        page_title="ChessBot",
        layout="wide",
        page_icon="♟️",
        initial_sidebar_state ="expanded",
        menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
        }
        )
    st.markdown(
        """
        <style>
        html, body, .main, .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            margin-left: 1rem !important;
            margin-right: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def open_parameters():
    @st.dialog(title="Options")
    def dialog():
        user_depth = st.slider("Profondeur d'analyse", min_value=10, max_value=20, value=10, step=1)
        st.session_state.user_depth = user_depth

        show_best_arrow = st.toggle("Afficher la meilleure alternative", value=st.session_state.get("show_best_arrow", True))
        st.session_state.show_best_arrow = show_best_arrow

        show_threat_arrows = st.toggle("Afficher la meilleure continuation", value=st.session_state.get("show_threat_arrows", False))
        st.session_state.show_threat_arrows = show_threat_arrows

    dialog()


def render_navigation_buttons(max_index):
    col_flip, col_first, col_prev, col_next, col_last = st.columns(5)
    with col_flip:
        if st.button("", 
                     icon=":material/swap_vert:",
                     use_container_width=True,
                     key="flip_board"):
            st.session_state.board_flipped = not st.session_state.board_flipped            
    with col_first:
        if st.button("",
                     icon=":material/first_page:",
                     help = "Premier coup",
                     use_container_width=True,
                     key="first_move") and st.session_state.move_index > 0:
            st.session_state.move_index = 0
    with col_prev:
        if st.button("",
                     icon=":material/chevron_left:",
                     help = "Coup précédent",
                     use_container_width=True,
                     key="prev_move") and st.session_state.move_index > 0:
            st.session_state.move_index -= 1
    with col_next:
        if st.button("",
                     icon=":material/chevron_right:",
                     help = "Coup suivant",
                     use_container_width=True,
                     key="next_move") and st.session_state.move_index < max_index:
            st.session_state.move_index += 1
    with col_last:
        if st.button("",
                     icon=":material/last_page:",
                     help = "Dernier coup",
                     use_container_width=True,
                     key="last_move") and st.session_state.move_index < max_index:
            st.session_state.move_index = max_index

def display_moves_slider(max_index):
    if "analysis" not in st.session_state or not st.session_state.analysis:
        return

    if max_index == 0:
        return

    st.slider(
        "Sélectionnez un coup",
        min_value=0,
        max_value=max_index - 1,
        key="move_index",  # <-- Lier le slider à la session_state
        step=1,
        label_visibility="collapsed"
    )


def inject_quality_on_square(svg, square, quality_path, flipped=False):

    #Magic numbers found by trial and error
    marging_coordinates = 10
    square_size = 45.7

    file = chess.square_file(square)
    rank = chess.square_rank(square)

    if not flipped:
        x = (file + 1) * square_size
        y = (7-rank)*square_size
    else:
        x = (8-file)*square_size
        y = rank*square_size

    with open(quality_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    quality_size = int(20)
    quality_x = marging_coordinates + x - quality_size/2
    quality_y = marging_coordinates + 2 + y - quality_size/2

    img_tag = (
        f'<image href="data:image/png;base64,{img_b64}" '
        f'x="{quality_x}" y="{quality_y}" width="{quality_size}" height="{quality_size}" />'
    )

    if "</svg>" in svg:
        svg = svg.replace("</svg>", img_tag + "</svg>")
    else:
        svg += img_tag
    return svg


def render_board(board, last_move=None, flipped=False):
    move_index = st.session_state.get("move_index", 0)

    arrows = []

    # Ajout des flèches selon les options
    if (
        move_index > 0
        and "analysis" in st.session_state
        and st.session_state.analysis
    ):

        coup_data = st.session_state.analysis[move_index - 1]
        qualite = coup_data.get("qualité", "Non précisée")
        # Flèche pour le meilleur coup si le coup joué n'est ni théorique ni le meilleur
        if (
            st.session_state.get("show_best_arrow", True)
            and qualite not in ("Théorique", "Meilleur")
            and "best_move" in coup_data
            and coup_data.get("best_move_uci")
        ):
            best_move_uci = coup_data["best_move_uci"]

            try:
                best_move = chess.Move.from_uci(best_move_uci)
                arrows.append(
                    chess.svg.Arrow(
                        best_move.from_square,
                        best_move.to_square,
                        color="#98bc499e" 
                    )
                )
            except Exception:
                pass

        # Flèches pour les menaces
        if (
            st.session_state.get("show_threat_arrows", True)
            and "threats" in coup_data
        ):
            for threat_uci in coup_data["threats"]:
                try:
                    threat_move = chess.Move.from_uci(threat_uci)
                    arrows.append(
                        chess.svg.Arrow(
                            threat_move.from_square,
                            threat_move.to_square,
                            color="#c02424b9" 
                        )
                    )
                except Exception:
                    pass


    if move_index == 0 or "analysis" not in st.session_state or not st.session_state.analysis:
        qualite = "Non précisée"
        light_color, dark_color = "#ffffff", "#FFFFFF"
        quality_path = None
    else:
        analysis_index = move_index - 1
        coup_data = st.session_state.analysis[analysis_index]
        qualite = coup_data.get("qualité", "Non précisée")
        light_color, dark_color = quality_board_colors.get(qualite, ("#ff0000", "#000000"))
        quality_path = quality_images.get(qualite)

    svg = chess.svg.board(
        board,
        lastmove=last_move,
        flipped=flipped,
        colors={
            "square light": "#ebecd0",
            "square dark": "#739552",
            "arrow": "#ff0000",
            "square light lastmove": light_color,
            "square dark lastmove": dark_color,
        },
        size=board_size,
        coordinates=True,
        arrows=arrows
    )

    # Ajoute l'icône sur la case cible du dernier coup joué
    if last_move and quality_path:
        svg = inject_quality_on_square(svg, last_move.to_square, quality_path, flipped)

    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    st.write(html, unsafe_allow_html=True)


def display_move_description():
    if "analysis" not in st.session_state or not st.session_state.analysis:
        st.write("Aucune analyse disponible.")
        return

    move_index = st.session_state.get("move_index", 0)

    if move_index == 0:
        return

    analysis_index = move_index - 1

    if analysis_index >= len(st.session_state.analysis):
        st.warning("Aucune analyse disponible pour ce coup.")
        return

    coup_data = st.session_state.analysis[analysis_index]
    meilleur_coup = coup_data.get("best_move", "Non spécifié")
    coup_joué = coup_data.get("coup", "Inconnu")
    qualite = coup_data.get("qualité", "Non précisée")
    img_path = quality_images.get(qualite)
    est_theorique = "Oui" if coup_data.get("is_theoretical", False) else "Non"
    est_meilleur = "Oui" if coup_data.get("is_best", False) else "Non"
    color_best = quality_colors.get("Meilleur", "black")

    color_coup = quality_colors.get(qualite, "black")

    if est_theorique == "Oui":
        description = f"<span style='color:{color_coup};'>{coup_joué} est un coup théorique</span>"
    elif qualite == "Excellent" or qualite == "Bon":
        description = f"<span style='color:{color_coup};'>{coup_joué} est un {qualite.lower()} coup</span>"
    elif qualite == "Imprécision" or qualite == "Erreur" or qualite == "Gaffe":
        description = f"<span style='color:{color_coup};'>{coup_joué} est une {qualite.lower()}</span>"
    elif qualite == "Meilleur":
        description = f"<span style='color:{color_coup};'>{coup_joué} est le meilleur coup</span>"

    meilleur_coup_html = ""
    if est_theorique != "Oui" and est_meilleur != "Oui" and qualite!="Meilleur" and analysis_index > 0:
        meilleur_coup_html = f"<div style='margin-top:8px; color:{color_best}; font-weight:bold;'>{meilleur_coup} est le meilleur coup</div>"


    
    with st.container(border=True):
        with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
                st.markdown(
                    f"<div style='text-align:left; font-weight:bold;'>"
                    f"<img src='data:image/png;base64,{img_b64}' style='height:24px; max-width:24px; display:inline-block;margin-right:8px;margin-bottom:8px;'>"
                    f"<span>{description}</span> "
                    f"{meilleur_coup_html}"
                    f"</div>",
                    unsafe_allow_html=True
                )


def display_graph(current_index=None):
    if st.session_state.analysis:
        y_min, y_max = -1300, 1300

        def eval_to_y(i, coup):
            raw = coup.get("raw_eval", {"type": "cp", "value": coup.get("eval", 0)})
            if raw["type"] == "mate":
                if raw["value"] > 0:
                    return y_max
                elif raw["value"] < 0:
                    return y_min
                else:  # M0, il faut déterminer qui a maté
                    # On regarde le coup précédent pour savoir le signe du mat
                    prev_eval = None
                    for prev_coup in reversed(st.session_state.analysis[:i]):
                        prev_raw = prev_coup.get("raw_eval", {})
                        if prev_raw.get("type") == "mate" and prev_raw.get("value") != 0:
                            prev_eval = prev_raw["value"]
                            break
                    if prev_eval is not None and prev_eval > 0:
                        return y_max
                    else:
                        return y_min
            return max(min(raw.get("value", 0), y_max), y_min)

        evals = [eval_to_y(i, coup) for i, coup in enumerate(st.session_state.analysis)]
        formatted_labels = [format_eval(coup["raw_eval"]) for coup in st.session_state.analysis]

        fig = go.Figure()
        # Première trace : ligne blanche invisible au niveau de `min_val` pour générer une "zone remplie"
        fig.add_trace(go.Scatter(
            x=list(range(len(evals))),
            y=[y_min] * len(evals),
            mode='lines',
            line=dict(color="#252423", width=0),
            fill=None,
            showlegend=False,
            hoverinfo="skip"
        ))
        # Deuxième trace : ligne des évaluations avec remplissage vers le bas jusqu'à la trace précédente
        fig.add_trace(go.Scatter(
            x=list(range(len(evals))),
            y=evals,
            mode='lines',
            line=dict(color='blue', width=0),
            fill='tonexty',
            fillcolor='white',
            showlegend=False,
            text=[f"Coup {i+1}: {label}" for i, label in enumerate(formatted_labels)],
            hovertemplate="%{text}<extra></extra>"
        ))
        # Ligne grise horizontale à y=0 pour référence
        fig.add_shape(
            type="line",
            x0=0,
            y0=0,
            x1=len(evals)-1,
            y1=0,
            line=dict(color="gray", width=2),
            layer="above"
        )
        # Ligne verticale indiquant le coup actuellement sélectionné (si fourni)
        if current_index is not None and current_index < len(evals):
            qualite = st.session_state.analysis[current_index].get("qualité", "Meilleur")
            color = quality_colors.get(qualite, "#739552")

            fig.add_shape(
                type="line",
                x0=current_index,
                y0=y_min,
                x1=current_index,
                y1=y_max,
                line=dict(color=color, width=2),
                layer="above"
            )
        fig.update_layout(
            height=90,
            margin=dict(l=0, r=0, t=0, b=0),
            dragmode=False,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, showline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, showline=False),
            plot_bgcolor="#252423"
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})



def display_quality_table():

    df = pd.DataFrame(st.session_state.analysis)
    white_name = st.session_state.white_name
    black_name = st.session_state.black_name
    white_elo = st.session_state.pgn_last.split("[WhiteElo \"")[1].split("\"]")[0] if "[WhiteElo \"" in st.session_state.pgn_last else "ELO?"
    black_elo = st.session_state.pgn_last.split("[BlackElo \"")[1].split("\"]")[0] if "[BlackElo \"" in st.session_state.pgn_last else "ELO?"

    df["joueur"] = [white_name if i % 2 == 0 else black_name for i in range(len(df))]
    recap = (
        df.groupby(["qualité", "joueur"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[white_name, black_name], fill_value=0)
        .reindex(index=[
            #"Brillant", 
            #"Critique", 
            "Meilleur", "Excellent", "Bon",
            "Imprécision", "Erreur", "Gaffe", "Théorique"
        ], fill_value=0)
        )

    col_quality,col_white,col_image,col_black = st.columns([3,2,1,2],border=False,vertical_alignment="bottom")
    with col_quality:
        pass        
    with col_white:
        st.markdown(f"◻️**{white_name}** :small[:grey[({white_elo})]]")
        
    with col_image:
        pass
    with col_black:
        st.markdown(f"◼️**{black_name}** \n :small[:grey[({black_elo})]]")    


    for qualite, row in recap.iterrows():
        color = quality_colors.get(qualite, "black")
        value_white = row[white_name]
        value_black = row[black_name]
        img_path = quality_images.get(qualite)

        col_quality,col_white,col_image,col_black = st.columns([3,2,1,2],border=False)
        with col_quality:
            st.markdown(f"<span style='color:{color}; font-weight:bold'>{qualite}</span>", unsafe_allow_html=True)
        with col_white:
            st.markdown(
            f"<div style='text-align:center'><span style='color:{color}; font-weight:bold'>{value_white}</span></div>",
            unsafe_allow_html=True
        )        
        with col_image:
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<img src='data:image/png;base64,{img_b64}' style='height:24px; max-width:24px; display:inline-block;'>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        with col_black:
            st.markdown(
            f"<div style='text-align:center'><span style='color:{color}; font-weight:bold'>{value_black}</span></div>",
            unsafe_allow_html=True
        )

def display_moves_recap():
    if "analysis" not in st.session_state or not st.session_state.analysis:
        st.write("Aucun récapitulatif disponible.")
        return

    analysis = st.session_state.analysis

    def go_to_move(idx):
        st.session_state.move_index = idx

    with st.container(border=False,height=400):
        for i in range(0, len(analysis), 2):
            col_num_coup,col_qual_blanc,col_coup_blanc,col_qual_noir,col_coup_noir = st.columns([1, 3, 1, 3, 1],vertical_alignment="center")
            move_number = i // 2 + 1

            with col_num_coup:
                st.markdown(f"&nbsp;:small[{move_number}].",unsafe_allow_html=True)

            qualite_w = analysis[i].get("qualité", "Non précisée")
            img_w = quality_images.get(qualite_w)
            coup_w = analysis[i].get("coup", "")
            with open(img_w, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            with col_qual_blanc:
                st.markdown(
                    f"<img src='data:image/png;base64,{img_b64}' style='height:20px;vertical-align:middle;margin-right:6px;'>"
                    f"<span style='font-family:monospace;font-size:16px'>{coup_w}</span>",
                    unsafe_allow_html=True
                )
            with col_coup_blanc:
                st.button(
                    ":material/search:",
                    key=f"move_w_{i}",
                    help=f"Aller au coup",
                    on_click=go_to_move,
                    args=(i + 1,),
                    use_container_width=True,
                    type="tertiary"
                )


            # Coup noir
            if i + 1 < len(analysis):
                qualite_b = analysis[i + 1].get("qualité", "Non précisée")
                img_b = quality_images.get(qualite_b)
                coup_b = analysis[i + 1].get("coup", "")
                with open(img_b, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")
                with col_qual_noir:
                    st.markdown(
                        f"<img src='data:image/png;base64,{img_b64}' style='height:20px;vertical-align:middle;margin-right:6px;'>"
                        f"<span style='font-family:monospace;font-size:16px'>{coup_b}</span>",
                        unsafe_allow_html=True
                    )
                with col_coup_noir:
                    st.button(
                        ":material/search:",
                        key=f"move_n_{i+1}",
                        help=f"Aller au coup",
                        on_click=go_to_move,
                        args=(i + 2,),
                        use_container_width=True,
                        type="tertiary"
                    )




def render_eval_bar():
    if not st.session_state.analysis:
        return

    move_index = st.session_state.get("move_index", 0)
    if move_index == 0:
        cp = 0
        eval_text = "0.0"
        white_win_chance = 50
        black_win_chance = 50
    else:
        coup = st.session_state.analysis[move_index - 1]
        cp = coup["eval"]
        raw_eval = coup.get("raw_eval", {"type": "cp", "value": cp})

        # Fonction locale pour formatage positif sans signe
        def format_eval_bar(e):
            if e["type"] == "cp":
                val = abs(round(e["value"] / 100, 1))
                return f"{val}"
            elif e["type"] == "mate":
                return f"M{abs(e['value'])}"
            return "?"

        eval_text = format_eval_bar(raw_eval)

        # Gestion spéciale du mat
        if raw_eval["type"] == "mate":
            if raw_eval["value"] > 0:
                white_win_chance = 100
                black_win_chance = 0
            elif raw_eval["value"] < 0:
                white_win_chance = 0
                black_win_chance = 100
            else:  # M0, il faut déterminer qui a maté
                prev_eval = None
                for prev_coup in reversed(st.session_state.analysis[:move_index-1]):
                    prev_raw = prev_coup.get("raw_eval", {})
                    if prev_raw.get("type") == "mate" and prev_raw.get("value") != 0:
                        prev_eval = prev_raw["value"]
                        break
                if prev_eval is not None and prev_eval > 0:
                    white_win_chance = 100
                    black_win_chance = 0
                else:
                    white_win_chance = 0
                    black_win_chance = 100
        else:
            white_win_chance = get_win_chance(cp)
            black_win_chance = 100 - white_win_chance

    fig = go.Figure()
    flipped = st.session_state.get("board_flipped", False)

    # Ajoute toujours les traces dans le même ordre : Blancs puis Noirs
    fig.add_trace(go.Bar(
        y=["Évaluation"],
        x=[white_win_chance],
        orientation='h',
        marker_color="#ffffff",
        hoverinfo="skip",
        showlegend=False,
        name="Blancs",
        text=[eval_text if white_win_chance > 50 else ""],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=16, family="Source Sans Pro, sans-serif", color="black"),
    ))
    fig.add_trace(go.Bar(
        y=["Évaluation"],
        x=[black_win_chance],
        orientation='h',
        marker_color="#232325",
        hoverinfo="skip",
        showlegend=False,
        name="Noirs",
        text=[eval_text if black_win_chance > 50 else ""],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=16, family="Source Sans Pro, sans-serif", color="white"),
    ))


    flipped = st.session_state.get("board_flipped", False)

    fig.update_layout(
        barmode='stack',
        height=48,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            range=[100, 0] if flipped else [0, 100],  # <-- Ici on inverse le range
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Ajoute ce bloc pour limiter la hauteur du conteneur
    st.markdown(
        f"""
        <style>
        .eval-bar-container {{
            max-height: 400px;
            overflow: hidden;
        }}
        </style>
        <div class="eval-bar-container">
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

def display_game_result():
    if "pgn_last" not in st.session_state or not st.session_state.pgn_last:
        return
    
    pgn = st.session_state.pgn_last

    # Résultat : recherche la balise [Result "..."] ou la ligne "1-0", "0-1", "1/2-1/2"
    result = None
    m = re.search(r'\[Result\s+"([^"]+)"\]', pgn)
    if m:
        result = m.group(1)
    else:
        # Fallback : cherche la dernière occurrence de 1-0, 0-1, 1/2-1/2 dans le texte
        m = re.findall(r'(1-0|0-1|1/2-1/2)', pgn)
        if m:
            result = m[-1]
        else:
            result = "?"

    if result == "1-0":
        winner_color = "⬜"
    elif result == "0-1":
        winner_color = "⬛"
    elif result in ("1/2-1/2", "½-½"):
        winner_color = "🟰"
    else:
        winner_color = "❓"

    # Affichage de la terminaison
    termination = None
    is_chesscom = "chess.com" in pgn.lower()
    m = re.search(r'\[Termination\s+"([^"]+)"\]', pgn)
    if is_chesscom and m:
        termination = m.group(1)
    else:
        # Pour tout le reste (lichess, parties historiques, etc.), on reconstruit à partir du résultat
        if result == "1-0":
            termination = "Victoire des Blancs"
        elif result == "0-1":
            termination = "Victoire des Noirs"
        elif result in ("1/2-1/2", "½-½"):
            termination = "Partie nulle"
        else:
            termination = "Résultat inconnu"

    # Lien Chess.com ou Lichess
    link = None
    m = re.search(r'\[Link\s+"([^"]+)"\]', pgn)
    if m:
        link = m.group(1)
    else:
        # Lichess Site "https://lichess.org/FLYtItYV"] ou [GameId "FLYtItYV"]: [
        m = re.search(r'\[Site\s+"(https?://lichess\.org/[\w\d]+)"\]', pgn)
        if m:
            link = m.group(1)
        else:
            m = re.search(r'\[GameId\s+"([\w\d]+)"\]', pgn)
            if m:
                link = f"https://lichess.org/{m.group(1)}"
    
    with st.container(border=False):
        st.markdown(f"{winner_color}**{termination}**", unsafe_allow_html=False)
        if link:
            st.page_link(label=":blue[Lien de la partie]", page=link, use_container_width=True, icon=":material/open_in_new:")
