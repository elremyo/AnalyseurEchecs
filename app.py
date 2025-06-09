import streamlit as st
import chess


from engine.analysis import *
from utils.display import *
from utils.session import *
from utils.display import *
from utils.assets import stockfish_path, book_path, can_use_clipboard
from utils.debug_pgn_samples import *
from utils.gif_images import *



set_page_style()
init_session_state()

st.header("Road to 1000 ELO", anchor=False)


col_pgn, col_board, col_datas = st.columns(spec=[2,5,3], gap="small", border=True)

with col_pgn:

    if st.button("Options",
                key="open_parameters",
                help="Ouvrir les paramètres de l'analyseur",
                icon=":material/settings:",
                type="secondary"
                ):
        open_parameters()

    # Sélecteur de partie d'exemple
    sample_labels = []
    for idx, pgn in enumerate(sample_games):
        # On extrait les noms des joueurs et la date pour l'affichage
        lines = pgn.strip().splitlines()
        white = next((l.split('"')[1] for l in lines if l.startswith('[White ')), f"White {idx+1}")
        black = next((l.split('"')[1] for l in lines if l.startswith('[Black ')), f"Black {idx+1}")
        date = next((l.split('"')[1] for l in lines if l.startswith('[Date ')), "")
        sample_labels.append(f"{white} vs {black} ({date})")

    selected_idx = st.selectbox(
        "Sélectionner une partie d'exemple",
        options=list(range(len(sample_games))),
        format_func=lambda i: sample_labels[i],
        key="sample_game_select"
    )

    selected_pgn = sample_games[selected_idx].strip()
    if st.session_state.get("pgn_last", "") != selected_pgn:
        st.session_state.pgn_last = selected_pgn

    if can_use_clipboard():
        import pyperclip
        clipboard_content = pyperclip.paste()
        if clipboard_content and isinstance(clipboard_content, str) and clipboard_content.strip().startswith("[Event"):
            pgn_clipboard = clipboard_content.strip()
        else:
            pgn_clipboard = ""
    else:
        pgn_clipboard = ""

    with st.popover("Coller le PGN à analyser",use_container_width=True):
        pgn_text = st.text_area(
            "PGN de la partie :",
            placeholder="Collez ici le PGN de la partie",
            height=420,
            value=st.session_state.get("pgn_last", pgn_clipboard)
        )    
    if st.button("Analyser",
                 disabled=not pgn_text.strip(),
                 type="primary",
                 icon=":material/monitoring:",
                 use_container_width=True):
        analysis, white_name, black_name = analyze_game(pgn_text, st.session_state.user_depth, stockfish_path,book_path)
        st.session_state.analysis = analysis
        st.session_state.white_name = white_name
        st.session_state.black_name = black_name
        st.session_state.pgn_last = pgn_text
        st.session_state.move_index = 0

    if st.session_state.analysis:
        st.divider()
        display_game_result()
        display_quality_table()
    else:
        st.divider()
        st.subheader("✨ Coller un PGN pour commencer l'analyse", anchor=False)
        st.markdown(
            "Vous pouvez copier un PGN depuis [Chess.com](https://www.chess.com/) ou [Lichess.org](https://lichess.org/) et le coller ici pour l'analyser.",
            unsafe_allow_html=True
        )
        with st.expander("Comment copier un PGN ?", expanded=False, icon=":material/help:"):
            st.markdown(
                "1. Ouvrez la partie sur Chess.com ou Lichess.org.\n"
                "2. Cliquez sur le bouton **Partager** ou **Exporter**.\n"
                "3. Sélectionnez l'option **Copier le PGN**.\n"
                "4. Collez-le dans le champ ci-dessus."
            )


        st.session_state.analysis = None
        st.session_state.white_name = None
        st.session_state.black_name = None
        st.session_state.pgn_last = None



with col_board:

    if st.session_state.analysis:
        try:
            pgn_to_use = st.session_state.get("pgn_last", pgn_text)
            game=load_pgn(pgn_to_use)
            board = chess.Board()
            moves = [move for move in game.mainline_moves()]
            max_index = len(moves)

            # Initialisation de l'index du coup courant
            if "move_index" not in st.session_state:
                st.session_state.move_index = 0

            render_navigation_buttons(max_index)
            
            # Limite l'index dans les bornes
            st.session_state.move_index = max(0, min(st.session_state.move_index, max_index))

            # Applique les coups jusqu'à l'index courant
            for move in moves[:st.session_state.move_index]:
                board.push(move)

            last_move = moves[st.session_state.move_index - 1] if st.session_state.move_index > 0 else None
            
            # Synchronisation slider <-> move_index
            if "move_index_slider" in st.session_state:
                slider_value = st.session_state.move_index_slider - 1
                # On ne synchronise QUE si le slider a changé depuis le dernier run
                if st.session_state.get("_last_slider_value", None) != slider_value:
                    st.session_state.move_index = slider_value
                st.session_state._last_slider_value = slider_value

            render_eval_bar()
            render_board(board, last_move=last_move, flipped=st.session_state.board_flipped)

        except Exception as e:
            st.error(f"Erreur pendant l'analyse : {e}")
    else:
        #Afficher un échiquier vide
        render_board(board=chess.Board())

 

with col_datas:
    if st.session_state.analysis:
        # Afficher le sélecteur de coups
        slider_value = display_moves_slider(max_index)

        # Synchronisation slider <-> move_index
        if "move_index_slider" in st.session_state:
            slider_value = st.session_state.move_index_slider - 1
            # Si le slider a changé, on pilote move_index
            if st.session_state.get("_last_slider_value", None) != slider_value:
                st.session_state.move_index = slider_value
            # Sinon, on pilote le slider avec move_index
            elif st.session_state.move_index != slider_value:
                st.session_state.move_index_slider = st.session_state.move_index + 1
            st.session_state._last_slider_value = st.session_state.move_index_slider - 1

        # Afficher l'histogramme
        display_graph(current_index=max(0, st.session_state.get("move_index", 0) - 1))
        # Afficher le coup joué et le meilleur coup
        display_move_description()
        display_moves_recap()
