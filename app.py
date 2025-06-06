import streamlit as st
import chess
import pyperclip


from engine.analysis import *
from utils.display import *
from utils.session import *
from utils.display import *
from utils.assets import stockfish_path, book_path, can_use_clipboard


set_page_style()
init_session_state()

st.header("Road to 1000 ELO", anchor=False)


if st.button("Options",
            key="open_parameters",
            help="Ouvrir les paramètres de l'analyseur",
            icon=":material/settings:",
            type="secondary"
            ):
    open_parameters()

#DEBUG
pgn_exemple = """[Event "Live Chess"]
[Site "Chess.com"]
[Date "2025.05.29"]
[Round "?"]
[White "ElRemyo"]
[Black "PauloDomingues"]
[Result "0-1"]
[TimeControl "300+5"]
[WhiteElo "794"]
[BlackElo "840"]
[Termination "PauloDomingues a gagné par échec et mat"]
[Link "https://www.chess.com/game/138993809152"]

1. d4 Nf6 2. Bf4 d5 3. Nf3 g6 4. e3 Bg7 5. Bd3 Bg4 6. h3 Bxf3 7. Qxf3 e6 8. Nd2
O-O 9. c4 c6 10. c5 Nbd7 11. Bg5 Qa5 12. b3 Rab8 13. Bf4 Rbc8 14. a3 Qc3 15. Ke2
Nh5 16. Bh2 Rfe8 17. Rhc1 Qa5 18. b4 Qd8 19. Bd6 b6 20. Ba6 Ra8 21. Bb7 bxc5 22.
Bxa8 Qxa8 23. bxc5 Ndf6 24. Rab1 Ne4 25. Nxe4 dxe4 26. Qxe4 Nf6 27. Qd3 Bf8 28.
Rb4 Bxd6 29. cxd6 Rd8 30. Rcb1 Kg7 31. f3 Nd5 32. Rb7 Nb6 33. Rb4 Qxb7 34. a4
Qd7 35. a5 Nd5 36. Rb3 Qxd6 37. e4 Nf4+ 38. Ke3 Nxd3 39. Rxd3 Qc7 40. Ra3 c5 41.
Rc3 Qxa5 42. Rxc5 Qa3+ 43. Kf4 Rxd4 44. g4 Qxc5 45. h4 Qc7+ 46. Ke3 Rc4 47. h5
Rc3+ 48. Kd4 Qc4+ 49. Ke5 f6+ 50. Kf4 e5+ 51. Kg3 Qd3 52. h6+ Kxh6 53. Kh4 g5+
54. Kh3 Qxf3+ 55. Kh2 Rc2+ 56. Kg1 Qd1# 0-1 """



col_pgn, col_board, col_datas = st.columns(spec=[2,5,3], gap="small", border=True)

with col_pgn:

    if st.button("Debug : PGN d'exemple", key="copy_example_pgn", icon=":material/content_copy:"):
        pyperclip.copy(pgn_exemple)
        st.toast("PGN d'exemple copié dans le presse-papiers !",icon="✅")
        st.rerun()

    if can_use_clipboard():
        clipboard_content = pyperclip.paste()
        if clipboard_content and isinstance(clipboard_content, str) and clipboard_content.strip().startswith("[Event"):
            pgn_clipboard = clipboard_content.strip()
        else:
            pgn_clipboard = ""
    else:
        pgn_clipboard = ""
        st.warning("Le presse-papiers n'est pas accessible. Veuillez coller le PGN manuellement.", icon="⚠️")

    with st.popover("Coller le PGN à analyser",
                    use_container_width=True,
                    help="Si un PGN est copié dans le presse papier, il est automatiquement utilisé."):
        pgn_text = st.text_area("PGN de la partie :", placeholder="Collez ici le PGN de la partie", height=420, value=pgn_clipboard)
    
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
        display_quality_table()



with col_board:
    if st.session_state.analysis:
        try:
            game=load_pgn(pgn_text)
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
            
            col_bar, col_board2 = st.columns([1, 6], gap="small", border=False)
            with col_bar:
                render_eval_bar()
            with col_board2:
                render_board(board, last_move=last_move, flipped=st.session_state.board_flipped)

        except Exception as e:
            st.error(f"Erreur pendant l'analyse : {e}")
    else:
        #Afficher un échiquier vide
        render_board(board=chess.Board())

 

with col_datas:
    if st.session_state.analysis:
        #Afficher l'histogramme
        display_graph(current_index=max(0, st.session_state.get("move_index", 0) - 1))

        #Afficher le coup joué et le meilleur coup
        display_move_description()

        display_moves_recap()
