import streamlit as st
import os

def init_session_state():
    defaults = {
        "analysis": None,
        "pgn_last": "",
        "pgn_last_analyzed": "",
        "white_name": "Blanc",
        "black_name": "Noir",
        "board_flipped": False,
        "user_depth": 15,
        "show_best_arrow": True,
        "show_threat_arrows": False,
        "username": os.getenv("CHESSBOT_USERNAME", "Anonymous"),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
