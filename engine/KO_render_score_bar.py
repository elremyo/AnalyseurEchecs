#Progress bar générée par IA. Fonctionne à peu près mais ne retourne pas les bonnes valeur. A reprendre.

#à utiliser dans le app.py : 
    #current_analysis = st.session_state.analysis[st.session_state.move_index]
    #current_score = current_analysis.get("raw_eval", None)
    #orientation = "black" if st.session_state.get("board_flipped") else "white"
    #render_eval_bar(current_score, orientation=orientation)




def get_win_chance(cp):
    cp = max(min(cp, 1000), -1000)
    return 100 / (1 + math.exp(-0.004 * cp))

def render_eval_bar(score, orientation="white", height=400):

    if score is None:
        st.write("Pas d'évaluation")
        return

    # Gestion score
    if score["type"] == "mate":
        progress = 100 if score["value"] > 0 else 0
        display_score = f"#{abs(score['value'])}"
    else:  # centipawn
        progress = get_win_chance(score["value"])
        sign = "+" if score["value"] > 0 else ""
        display_score = f"{sign}{score['value'] / 100:.2f}"

    white_pct = progress
    black_pct = 100 - white_pct

    # En fonction de qui est en bas (orientation)
    if orientation == "white":
        top_color = "#4a4a4a"  # noir en haut
        bottom_color = "#e0e0e0"  # blanc en bas
        top_pct = black_pct
        bottom_pct = white_pct
    else:
        top_color = "#e0e0e0"  # blanc en haut
        bottom_color = "#4a4a4a"  # noir en bas
        top_pct = white_pct
        bottom_pct = black_pct

    bar_html = f"""
    <div style='
        width: 30px;
        height: {height}px;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 0 6px rgba(0,0,0,0.2);
        display: flex;
        flex-direction: column;
    '>
        <div style='height: {top_pct}%; background-color: {top_color};'></div>
        <div style='height: {bottom_pct}%; background-color: {bottom_color}; 
                    display: flex; align-items: center; justify-content: center; 
                    font-family: monospace; font-size: 11px; font-weight: bold; color: #222;'>
            {display_score}
        </div>
    </div>
    """

    st.markdown(bar_html, unsafe_allow_html=True)