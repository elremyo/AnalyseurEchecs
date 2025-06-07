import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import base64
import chess.svg

from utils.eval_utils import *
from assets import *

board_size = 900 #in pixels



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


def render_board(board, last_move=None, flipped=False):
    move_index = st.session_state.get("move_index", 0)
    if move_index == 0 or "analysis" not in st.session_state or not st.session_state.analysis:
        qualite = "Non précisée"
        light_color, dark_color = "#ffffff", "#FFFFFF"
    else:
        analysis_index = move_index - 1
        coup_data = st.session_state.analysis[analysis_index]
        qualite = coup_data.get("qualité", "Non précisée")
        light_color, dark_color = quality_board_colors.get(qualite, ("#ff0000", "#000000"))

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
    )
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
    eval_cp = coup_data.get("eval", "N/A")
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
    if est_theorique != "Oui" and est_meilleur != "Oui" and analysis_index > 0:
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


    with st.expander("Détail DEBUG"):
        st.markdown(f"""
        **Analyse du coup {move_index} :**
        - Coup joué : `{coup_joué}`
        - Meilleur coup suggéré : `{meilleur_coup}`
        - Qualité : **{qualite}**
        - Évaluation (cp) : `{eval_cp}`
        - Coup théorique : {est_theorique}
        """)

def display_graph(current_index=None):
    if st.session_state.analysis:
        evals = [coup["eval"] for coup in st.session_state.analysis]
        formatted_labels = [format_eval(coup["raw_eval"]) for coup in st.session_state.analysis]
        min_val = min(evals) - 100
        fig = go.Figure()
        # Première trace : ligne blanche invisible au niveau de `min_val` pour générer une "zone remplie"
        fig.add_trace(go.Scatter(
            x=list(range(len(evals))),
            y=[min_val] * len(evals),
            mode='lines',
            line=dict(color='white'),
            fill=None,
            showlegend=False,
            hoverinfo="skip"
        ))
        # Deuxième trace : ligne des évaluations avec remplissage vers le bas jusqu'à la trace précédente
        fig.add_trace(go.Scatter(
            x=list(range(len(evals))),
            y=evals,
            mode='lines',
            line=dict(color='white'),
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
            line=dict(color="gray", width=1),
            layer="above"
        )
        # Ligne verticale indiquant le coup actuellement sélectionné (si fourni)
        if current_index is not None:
            fig.add_shape(
                type="line",
                x0=current_index,
                y0=min_val,
                x1=current_index,
                y1=max(evals),
                line=dict(color="#739552", width=2),
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
    white = st.session_state.white_name
    black = st.session_state.black_name
    df["joueur"] = [white if i % 2 == 0 else black for i in range(len(df))]
    recap = (
        df.groupby(["qualité", "joueur"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[white, black], fill_value=0)
        .reindex(index=[
            #"Brillant", 
            #"Critique", 
            "Meilleur", "Excellent", "Bon",
            "Imprécision", "Erreur", "Gaffe", "Théorique"
        ], fill_value=0)
        )

    col_quality,col_white,col_image,col_black = st.columns([3,2,1,2],border=False)
    with col_quality:
        pass        
    with col_white:
        st.markdown(f"**{white}**")        
    with col_image:
        pass
    with col_black:
        st.markdown(f"**{black}**")        


    for qualite, row in recap.iterrows():
        color = quality_colors.get(qualite, "black")
        value_white = row[white]
        value_black = row[black]
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
            col_num_coup,col_qual_blanc,col_coup_blanc,col_qual_noir,col_coup_noir = st.columns([1, 4, 1, 4, 1],vertical_alignment="center")
            move_number = i // 2 + 1

            with col_num_coup:
                st.markdown(f"{move_number}.")

            # Coup blanc
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
            qualite_b = analysis[i + 0].get("qualité", "Non précisée")
            img_b = quality_images.get(qualite_b)
            coup_b = analysis[i + 0].get("coup", "")
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
    else:
        coup = st.session_state.analysis[move_index - 1]
        cp = coup["eval"]
        raw_eval = coup.get("raw_eval", {"type": "cp", "value": cp})

        # Fonction locale pour formatage positif sans signe
        def format_eval_bar(e):
            if e["type"] == "cp":
                val = abs(round(e["value"] / 100, 2))
                return f"{val}"
            elif e["type"] == "mate":
                return f"M{abs(e['value'])}"
            return "?"

        eval_text = format_eval_bar(raw_eval)

    white_win_chance = get_win_chance(cp)
    black_win_chance = 100 - white_win_chance

    fig = go.Figure()
    flipped = st.session_state.get("board_flipped", False)

    # Toujours ajouter Noir puis Blanc (ordre d'empilement)
    fig.add_trace(go.Bar(
        x=[0],
        y=[white_win_chance],
        marker_color="#ffffff",
        hoverinfo="skip",
        showlegend=False,
        name="Blancs",
        width=[0.35],
        text=[eval_text] if white_win_chance > 50 else [""],
        textfont=dict(size=16, family="Source Sans Pro, sans-serif")
    ))
    fig.add_trace(go.Bar(
        x=[0],
        y=[black_win_chance],
        marker_color="#232325",
        hoverinfo="skip",
        showlegend=False,
        name="Noirs",
        width=[0.35],
        text=[eval_text] if black_win_chance > 50 else [""],
        textfont=dict(size=16, family="Source Sans Pro, sans-serif")
    ))


    fig.update_layout(
        barmode='stack',
        height=board_size,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            range=[-0.5, 0.5]
        ),
        yaxis=dict(
            range=[100, 0] if flipped else [0, 100],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True
        ),
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})
