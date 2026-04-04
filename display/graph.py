import streamlit as st
import plotly.graph_objects as go
from utils.eval_utils import format_eval, get_win_chance, convert_eval_to_cp
from display.constants import quality_colors



def render_score_bar():
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
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)



def render_moves_graph(current_index=None):
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
            quality = st.session_state.analysis[current_index].get("qualité", "Meilleur")
            color = quality_colors.get(quality, "#739552")

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
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

