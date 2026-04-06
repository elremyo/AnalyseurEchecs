import streamlit as st
import plotly.graph_objects as go
from typing import Optional
from utils.eval_utils import format_eval, get_win_chance, convert_eval_to_cp
from constants import QUALITY_COLORS
from callbacks.navigation_callbacks import NavigationCallbacks


def handle_graph_click():
    """Gère le clic sur le graphe d'évaluation pour naviguer au coup."""
    print("handle_graph_click appelé!")  # Debug
    
    # Les données de sélection sont stockées dans st.session_state par Streamlit
    # quand on utilise on_select avec une clé
    widget_state = st.session_state.get('moves_graph', None)
    print(f"widget_state: {widget_state}")  # Debug
    
    if widget_state is None:
        return
    
    # Essayer d'extraire les données de sélection de différentes manières
    selected_data = None
    
    # Cas 1: Les données sont directement dans l'état du widget
    if hasattr(widget_state, 'selection'):
        selected_data = widget_state.selection
    elif isinstance(widget_state, dict) and 'selection' in widget_state:
        selected_data = widget_state['selection']
    elif hasattr(widget_state, 'points'):
        selected_data = widget_state
    elif isinstance(widget_state, dict) and 'points' in widget_state:
        selected_data = widget_state
    
    print(f"selected_data: {selected_data}")  # Debug
    
    if selected_data is None:
        return
    
    # Traiter les données de sélection
    points = None
    
    if hasattr(selected_data, 'points'):
        points = selected_data.points
    elif isinstance(selected_data, dict) and "points" in selected_data:
        points = selected_data["points"]
    elif isinstance(selected_data, list):
        points = selected_data
    
    print(f"points: {points}")  # Debug
    
    # Si on a des points, traiter le premier
    if points and len(points) > 0:
        point = points[0]
        
        # Extraire la coordonnée x
        x_val = None
        if hasattr(point, 'x'):
            x_val = point.x
        elif isinstance(point, dict):
            if "x" in point:
                x_val = point["x"]
            elif "point_number" in point:
                x_val = point["point_number"]
        
        if x_val is not None:
            move_index = int(x_val)
            
            # Calculer le bon index pour move_index
            # move_index = 0 signifie "avant le premier coup"
            # move_index = 1 signifie "après le premier coup" (donc on montre le premier coup)
            # Le graphe montre les coups de 0 à n-1, donc move_index = x_val + 1
            st.session_state.move_index = move_index + 1
            print(f"Nouveau move_index: {st.session_state.move_index}")  # Debug



def render_score_bar() -> None:
    if not st.session_state.analysis_result or not st.session_state.analysis_result.analysis:
        return

    move_index = st.session_state.get("move_index", 0)
    if move_index == 0:
        cp = 0
        eval_text = "0.0"
        white_win_chance = 50
        black_win_chance = 50
    else:
        coup = st.session_state.analysis_result.analysis[move_index - 1]
        cp = coup.eval
        raw_eval = coup.raw_eval

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
                for prev_coup in reversed(st.session_state.analysis_result.analysis[:move_index-1]):
                    prev_raw = prev_coup.raw_eval
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
        marker_color="#000000",
        hoverinfo="skip",
        showlegend=False,
        name="Noirs",
        text=[eval_text if black_win_chance > 50 else ""],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=16, family="Source Sans Pro, sans-serif", color="white"),
    ))

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
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)



def render_moves_graph(current_index: Optional[int] = None) -> None:
    if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
        y_min, y_max = -1300, 1300

        def eval_to_y(i, coup):
            raw = coup.raw_eval
            if raw["type"] == "mate":
                if raw["value"] > 0:
                    return y_max
                elif raw["value"] < 0:
                    return y_min
                else:  # M0, il faut déterminer qui a maté
                    # On regarde le coup précédent pour savoir le signe du mat
                    prev_eval = None
                    for prev_coup in reversed(st.session_state.analysis_result.analysis[:i]):
                        prev_raw = prev_coup.raw_eval
                        if prev_raw.get("type") == "mate" and prev_raw.get("value") != 0:
                            prev_eval = prev_raw["value"]
                            break
                    if prev_eval is not None and prev_eval > 0:
                        return y_max
                    else:
                        return y_min
            return max(min(raw.get("value", 0), y_max), y_min)

        evals = [eval_to_y(i, coup) for i, coup in enumerate(st.session_state.analysis_result.analysis)]
        formatted_labels = [format_eval(coup.raw_eval) for coup in st.session_state.analysis_result.analysis]

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
            mode='lines+markers',
            line=dict(color='blue', width=0),
            marker=dict(size=1, color='blue'),
            fill='tonexty',
            fillcolor='white',
            showlegend=False,
            text=[f"Coup {i+2}: {label}" for i, label in enumerate(formatted_labels)],
            hovertemplate="%{text}<extra></extra>",
            name="Évaluation"
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
            quality = st.session_state.analysis_result.analysis[current_index].quality
            color = QUALITY_COLORS.get(quality, "#739552")

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
            plot_bgcolor="#000000"
        )
        
        # Configuration pour permettre la sélection par clic
        config = {
            'displayModeBar': False
        }
        
        # Utiliser la fonction sans arguments comme callback
        st.plotly_chart(fig, width='stretch', config=config, on_select=handle_graph_click, key="moves_graph")

