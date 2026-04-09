import streamlit as st
from callbacks.navigation_callbacks import NavigationCallbacks


def render_navigation_buttons(max_index):
    with st.container(horizontal=True):
        st.button("", 
                 icon=":material/swap_vert:",
                 help = "Retourner l'échiquier",
                 width='stretch',
                 key="flip_board",
                 on_click=NavigationCallbacks.flip_board)            
        st.button("",
                 icon=":material/first_page:",
                 help = "Premier coup",
                 width='stretch',
                 key="first_move",
                 on_click=lambda: NavigationCallbacks.go_to_first_move(max_index))
        st.button("",
                 icon=":material/chevron_left:",
                 help = "Coup précédent",
                 width='stretch',
                 key="prev_move",
                 on_click=lambda: NavigationCallbacks.go_to_prev_move(max_index))
        st.button("",
                 icon=":material/chevron_right:",
                 help = "Coup suivant",
                 width='stretch',
                 key="next_move",
                 on_click=lambda: NavigationCallbacks.go_to_next_move(max_index))
        st.button("",
                 icon=":material/last_page:",
                 help = "Dernier coup",
                 width='stretch',
                 key="last_move",
                 on_click=lambda: NavigationCallbacks.go_to_last_move(max_index))
