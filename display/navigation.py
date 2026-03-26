import streamlit as st


def render_navigation_buttons(max_index):
    col_flip, col_first, col_prev, col_next, col_last = st.columns(5)
    with col_flip:
        if st.button("", 
                     icon=":material/swap_vert:",
                     width='stretch',
                     key="flip_board"):
            st.session_state.board_flipped = not st.session_state.board_flipped            
    with col_first:
        if st.button("",
                     icon=":material/first_page:",
                     help = "Premier coup",
                     width='stretch',
                     key="first_move") and st.session_state.move_index > 0:
            st.session_state.move_index = 0
    with col_prev:
        if st.button("",
                     icon=":material/chevron_left:",
                     help = "Coup précédent",
                     width='stretch',
                     key="prev_move") and st.session_state.move_index > 0:
            st.session_state.move_index -= 1
    with col_next:
        if st.button("",
                     icon=":material/chevron_right:",
                     help = "Coup suivant",
                     width='stretch',
                     key="next_move") and st.session_state.move_index < max_index:
            st.session_state.move_index += 1
    with col_last:
        if st.button("",
                     icon=":material/last_page:",
                     help = "Dernier coup",
                     width='stretch',
                     key="last_move") and st.session_state.move_index < max_index:
            st.session_state.move_index = max_index

def display_moves_slider(max_index):
    if "analysis" not in st.session_state or not st.session_state.analysis:
        return
    if max_index == 0:
        return

    # Le slider suit move_index, mais affiche 1-based
    slider_value = st.slider(
        "Sélectionnez un coup",
        min_value=1,
        max_value=max_index,
        value=st.session_state.get("move_index", 0) + 1,
        step=1,
        label_visibility="collapsed",
        key="move_index_slider"
    )
    return slider_value
