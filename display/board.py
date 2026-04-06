import base64
from typing import Optional
from utils.image_utils import load_quality_images_b64
from utils.safe_html import escape_html
import chess
import chess.svg
import streamlit as st
from streamlit_avatar import avatar

from constants import (
    BOARD_SIZE,
    QUALITY_IMAGES,
    QUALITY_BOARD_COLORS,
    SQUARE_SIZE_PX,
    BOARD_MARGIN_PX,
    QUALITY_ICON_SIZE,
    BOARD_COLORS
)

def display_players_name_for_board(color: str = "white", height: int = 30) -> None:

    analysis_result = st.session_state.analysis_result
    white_name = analysis_result.white_name
    black_name = analysis_result.black_name
    
    # Utiliser les métadonnées PGN depuis analysis_result
    pgn_meta = analysis_result.pgn_meta
    white_elo = pgn_meta.white_elo
    black_elo = pgn_meta.black_elo


    if not st.session_state.analysis_result or not st.session_state.analysis_result.analysis:
        return
    if color == "white":
        with st.container(border=False,height=height):
            #nom et elo du joueur blanc
            st.markdown(f"⬜ **{escape_html(white_name)}**  :gray[:small[{white_elo}]]")
    elif color == "black":
        with st.container(border=False,height=height):
            #nom et elo du joueur noir
            st.markdown(f"⬛ **{escape_html(black_name)}** :gray[:small[{black_elo}]]")

    else:
        st.error("Couleur non reconnue. Utilisez 'white' ou 'black'.")
    
def inject_quality_on_square(svg: str, square: chess.Square, quality: str, images_b64: dict[str, str], flipped: bool = False) -> str:

    img_b64 = images_b64[quality]

    # Constants for board rendering
    marging_coordinates = BOARD_MARGIN_PX
    square_size = SQUARE_SIZE_PX

    file = chess.square_file(square)
    rank = chess.square_rank(square)

    if not flipped:
        x = (file + 1) * square_size
        y = (7-rank)*square_size
    else:
        x = (8-file)*square_size
        y = rank*square_size

    
    quality_size = QUALITY_ICON_SIZE
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



def render_board(board: chess.Board, last_move: Optional[chess.Move] = None, flipped: bool = False) -> None:

    move_index = st.session_state.get("move_index", 0)
    images_b64 = load_quality_images_b64()

    arrows = []

    # Ajout des flèches selon les options
    if (
        move_index > 0
        and st.session_state.analysis_result
        and st.session_state.analysis_result.analysis
    ):

        coup_data = st.session_state.analysis_result.analysis[move_index - 1]
        quality = coup_data.quality
        # Flèche pour le meilleur coup si le coup joué n'est ni théorique ni le meilleur
        if (
            st.session_state.get("show_best_arrow", True)
            and quality not in ("Théorique", "Meilleur")
            and coup_data.best_move
            and coup_data.best_move_uci
        ):
            best_move_uci = coup_data.best_move_uci

            try:
                best_move = chess.Move.from_uci(best_move_uci)
                arrows.append(
                    chess.svg.Arrow(
                        best_move.from_square,
                        best_move.to_square,
                        color=BOARD_COLORS["best_arrow"]
                    )
                )
            except Exception:
                pass

        # Flèches pour les menaces
        if (
            st.session_state.get("show_threat_arrows", False)
            and coup_data.threats
        ):
            for threat_uci in coup_data.threats:
                try:
                    threat_move = chess.Move.from_uci(threat_uci)
                    arrows.append(
                        chess.svg.Arrow(
                            threat_move.from_square,
                            threat_move.to_square,
                            color=BOARD_COLORS["threat_arrow"]
                        )
                    )
                except Exception:
                    pass


    if move_index == 0 or not st.session_state.analysis_result or not st.session_state.analysis_result.analysis:
        quality = "Non précisée"
        light_color, dark_color = BOARD_COLORS["default_light"], BOARD_COLORS["default_dark"]
        quality_path = None
    else:
        analysis_index = move_index - 1
        coup_data = st.session_state.analysis_result.analysis[analysis_index]
        quality = coup_data.quality
        light_color, dark_color = QUALITY_BOARD_COLORS.get(quality, (BOARD_COLORS["default_light"], BOARD_COLORS["default_dark"]))
        quality_path = QUALITY_IMAGES.get(quality)

    svg = chess.svg.board(
        board,
        lastmove=last_move,
        flipped=flipped,
        colors={
            "square light": BOARD_COLORS["square_light"],
            "square dark": BOARD_COLORS["square_dark"],
            "arrow": BOARD_COLORS["arrow"],
            "square light lastmove": light_color,
            "square dark lastmove": dark_color,
            "margin": BOARD_COLORS["margin"],
        },
        size=BOARD_SIZE,
        coordinates=True,
        arrows=arrows
    )

    # Ajoute l'icône sur la case cible du dernier coup joué
    if last_move and quality_path:
        svg = inject_quality_on_square(svg, last_move.to_square, quality, images_b64, flipped)

    if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
        if flipped:
            display_players_name_for_board("white")
        else:
            display_players_name_for_board("black")
    
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    st.write(html, unsafe_allow_html=True)

    if st.session_state.analysis_result and st.session_state.analysis_result.analysis:
        if flipped:
            display_players_name_for_board("black")
        else:
            display_players_name_for_board("white")


