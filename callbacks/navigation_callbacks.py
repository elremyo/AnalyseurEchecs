import streamlit as st


class NavigationCallbacks:
    """Callbacks Streamlit pour la navigation dans les coups d'une partie."""
    
    @staticmethod
    def flip_board() -> None:
        """Inverse l'orientation de l'échiquier."""
        st.session_state.board_flipped = not st.session_state.board_flipped
    
    @staticmethod
    def go_to_first_move(max_index: int) -> None:
        """Va au premier coup de la partie."""
        if st.session_state.move_index > 0:
            st.session_state.move_index = 0
    
    @staticmethod
    def go_to_prev_move(max_index: int) -> None:
        """Va au coup précédent."""
        if st.session_state.move_index > 0:
            st.session_state.move_index -= 1
    
    @staticmethod
    def go_to_next_move(max_index: int) -> None:
        """Va au coup suivant."""
        if st.session_state.move_index < max_index:
            st.session_state.move_index += 1
    
    @staticmethod
    def go_to_last_move(max_index: int) -> None:
        """Va au dernier coup de la partie."""
        if st.session_state.move_index < max_index:
            st.session_state.move_index = max_index
    
    @staticmethod
    def on_slider_change() -> None:
        """Gère le changement de valeur du slider de navigation."""
        st.session_state.move_index = st.session_state.move_index_slider - 1
