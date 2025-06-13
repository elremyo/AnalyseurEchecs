import base64
import chess.svg
import streamlit as st
from streamlit_avatar import avatar

from display.style import *
from display.navigation import *
from display.moves_info import *
from display.constants import board_size, quality_images, quality_board_colors

def display_players_name_for_board(color="white", height=50):

    white_name = st.session_state.white_name
    black_name = st.session_state.black_name
    white_elo = st.session_state.pgn_last.split("[WhiteElo \"")[1].split("\"]")[0] if "[WhiteElo \"" in st.session_state.pgn_last else "ELO?"
    black_elo = st.session_state.pgn_last.split("[BlackElo \"")[1].split("\"]")[0] if "[BlackElo \"" in st.session_state.pgn_last else "ELO?"


    if "analysis" not in st.session_state or not st.session_state.analysis:
        return
    if color == "white":
        with st.container(border=False,height=height):
            avatar([{
                "url": "https://raw.githubusercontent.com/elremyo/chess-assets/refs/heads/main/white_king.png",
                "size": 35,
                "title": f"{white_name}",
                "caption": f"({white_elo})",
                "key": "avatar1",
            }])
            #st.markdown(f"◻️ {white_name} :grey[({white_elo})]")
    elif color == "black":
        with st.container(border=False,height=height):
            avatar([{
                "url": "https://raw.githubusercontent.com/elremyo/chess-assets/refs/heads/main/black_king.png",
                "size": 35,
                "title": f"{black_name}",
                "caption": f"({black_elo})",
                "key": "avatar1",
            }])
            #st.markdown(f"◼️ {black_name} :grey[({black_elo})]")
    else:
        st.error("Couleur non reconnue. Utilisez 'white' ou 'black'.")
    
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

    if st.session_state.analysis:
        if flipped:
            display_players_name_for_board("white")
        else:
            display_players_name_for_board("black")
    
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    st.write(html, unsafe_allow_html=True)

    if st.session_state.analysis:
        if flipped:
            display_players_name_for_board("black")
        else:
            display_players_name_for_board("white")


