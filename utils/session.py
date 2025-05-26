import streamlit as st

def init_session_state():
    defaults = {
        "analysis": None,
        "pgn_last": "",
        "white_name": "Blanc",
        "black_name": "Noir",
        "board_flipped": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
