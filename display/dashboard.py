"""Dashboard principal — données réelles depuis le cache Chess.com."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from utils.chesscom_api import fetch_recent_games
from utils.chesscom_cache import init_db, get_cached_games, get_last_sync, upsert_games, update_sync_log
from utils.eco_openings import get_opening_name, get_opening_family
from utils.time_control import classify_time_control, GAME_TYPES


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_PERIOD_OPTIONS = {
    "7 jours":  7,
    "30 jours": 30,
    "3 mois":   90,
    "1 an":     365,
    "Tout":     None,
}

_MIN_GAMES_OPENING  = 1   # seuil pour afficher une famille d'ouverture
_MIN_GAMES_RELIABLE = 4   # seuil pour considérer un W% statistiquement fiable
_ROLLING_WINDOW     = 20  # fenêtre du win rate glissant


# ---------------------------------------------------------------------------
# Sync & chargement
# ---------------------------------------------------------------------------

def _sync(username: str) -> tuple[int, str]:
    try:
        games = fetch_recent_games(username, months=3)
        new_count = upsert_games(games)
        update_sync_log(username)
        return new_count, ""
    except Exception as exc:
        return 0, str(exc)


def _to_df(games: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(games)
    if df.empty:
        return df
    df["user_elo"] = df.apply(
        lambda r: r["white_elo"] if r["user_color"] == "white" else r["black_elo"], axis=1
    )
    df["opponent"] = df.apply(
        lambda r: r["black"] if r["user_color"] == "white" else r["white"], axis=1
    )
    df["opponent_elo"] = df.apply(
        lambda r: r["black_elo"] if r["user_color"] == "white" else r["white_elo"], axis=1
    )
    df["date_parsed"] = pd.to_datetime(df["date"], format="%Y.%m.%d", errors="coerce")
    df["eco_family"]  = df["eco"].apply(get_opening_family)
    df["eco_name"]    = df["eco"].apply(lambda x: get_opening_name(x) if x else "")
    df["game_type"]   = df["time_control"].apply(classify_time_control)
    return df.sort_values("date_parsed", ascending=False).reset_index(drop=True)


def _apply_filters(df: pd.DataFrame, period_days: Optional[int], game_type: Optional[str]) -> pd.DataFrame:
    if df.empty:
        return df
    if period_days is not None:
        cutoff = pd.Timestamp(datetime.now() - timedelta(days=period_days))
        df = df[df["date_parsed"] >= cutoff]
    if game_type:
        df = df[df["game_type"] == game_type]
    return df.reset_index(drop=True)

def render_games_bar(total: int, wins: int, draws: int, losses: int, color_filter: str = "all") -> None:
    """Affiche le résumé des parties jouées avec des barres horizontales. 
    Args:
        total: Nombre total de parties
        wins: Nombre de victoires
        draws: Nombre de nuls
        losses: Nombre de défaites
        color_filter: Couleur des parties (all, white, black)
    """
    if total == 0:
        st.markdown("**0** parties")
        return
    
    # Calcul des pourcentages
    win_pct = wins / total * 100
    draw_pct = draws / total * 100
    loss_pct = losses / total * 100
    
    with st.container(horizontal=True, width="content"):
        filter_text = {
            "all": "Tout",
            "white": "⬜ Blanc", 
            "black": "⬛ Noir"
        }.get(color_filter, "Tout")
        st.markdown(f"**{filter_text}**")

        st.markdown(f"**{total}** parties")
    
    # Barre horizontale composite avec HTML personnalisé pour avoir des barres collées et colorées correctement
    bar_html = f"""
    <div style="display: flex; width: 100%; height: 12px; border-radius: 6px; overflow: hidden; margin: 4px 0;">
        <div style="background-color: #739552; width: {win_pct}%; height: 100%;"></div>
        <div style="background-color: #5a5a5a; width: {draw_pct}%; height: 100%;"></div>
        <div style="background-color: #c0392b; width: {loss_pct}%; height: 100%;"></div>
    </div>
    """
    st.markdown(bar_html, unsafe_allow_html=True)
    # Ligne avec les nombres absolus en dessous
    col_wins_count, col_draws_count, col_losses_count = st.columns(3)
    with col_wins_count:
        st.markdown(f":green[{wins} victoire{'s' if wins > 1 else ''} - **{win_pct:.0f}%**]")
    with col_draws_count:
        st.markdown(f":grey[{draws} nulle{'s' if draws > 1 else ''} - **{draw_pct:.0f}%**]")
    with col_losses_count:
        st.markdown(f":red[{losses} défaite{'s' if losses > 1 else ''} - **{loss_pct:.0f}%**]")
# ---------------------------------------------------------------------------
# Helpers ouvertures
# ---------------------------------------------------------------------------

def _build_opening_stats(df: pd.DataFrame, group_by: str) -> pd.DataFrame:
    """Construit le DataFrame de stats par ouverture pour une couleur donnée."""
    df_eco = df[df["eco"] != ""].copy()
    if df_eco.empty:
        return pd.DataFrame()

    rows = []
    for name, grp in df_eco.groupby(group_by):
        if len(grp) < _MIN_GAMES_OPENING:
            continue
        wins   = (grp["user_result"] == "win").sum()
        draws  = (grp["user_result"] == "draw").sum()
        losses = (grp["user_result"] == "loss").sum()
        total  = len(grp)
        wr = round(wins / total * 100, 1)
        rows.append({
            "name":    name,
            "total":   total,
            "wins":    int(wins),
            "draws":   int(draws),
            "losses":  int(losses),
            "wr":      wr,
            "reliable": total >= _MIN_GAMES_RELIABLE,
        })

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values("total", ascending=False)
        .reset_index(drop=True)
    )


def _render_opening_chart(stats: pd.DataFrame, title: str):
    """Bar chart horizontal V/N/D par ouverture, trié par nombre de parties."""
    if stats.empty:
        st.caption("Pas de données.")
        return

    st.markdown(f"**{title}**")

    names  = stats["name"].tolist()
    wins   = stats["wins"].tolist()
    draws  = stats["draws"].tolist()
    losses = stats["losses"].tolist()
    totals = stats["total"].tolist()
    wrs    = stats["wr"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Victoires", y=names, x=wins, orientation="h",
        marker_color="#739552",
        text=[f"{w}V" if w > 0 else "" for w in wins],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=11, color="white"),
        hovertemplate="%{y}<br>Victoires : %{x}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Nulles", y=names, x=draws, orientation="h",
        marker_color="#5a5a5a",
        text=[f"{d}N" if d > 0 else "" for d in draws],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=11, color="white"),
        hovertemplate="%{y}<br>Nulles : %{x}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Défaites", y=names, x=losses, orientation="h",
        marker_color="#c0392b",
        text=[f"{l}D" if l > 0 else "" for l in losses],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=11, color="white"),
        hovertemplate="%{y}<br>Défaites : %{x}<extra></extra>",
    ))

    # Annotations W% à droite des barres
    annotations = []
    for i, (total, wr, reliable) in enumerate(zip(totals, wrs, stats["reliable"].tolist())):
        color  = "#739552" if wr >= 55 else ("#d4a017" if wr >= 45 else "#c0392b")
        suffix = "" if reliable else " ⚠"
        annotations.append(dict(
            x=total + 0.3, y=i,
            text=f"<b>{wr:.0f}%{suffix}</b>",
            font=dict(size=11, color=color),
            showarrow=False, xanchor="left",
        ))

    chart_h = max(140, len(names) * 38)
    fig.update_layout(
        barmode="stack",
        height=chart_h,
        margin=dict(l=0, r=60, t=4, b=0),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                   range=[0, max(totals) * 1.25]),
        yaxis=dict(showgrid=False, zeroline=False, autorange="reversed",
                   tickfont=dict(size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=10)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=annotations,
        showlegend=True,
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def _render_forces_faiblesses(stats: pd.DataFrame):
    """Affiche les meilleures et pires ouvertures parmi celles avec assez de parties."""
    reliable = stats[stats["reliable"]].copy()
    if reliable.empty:
        st.caption(f"⚠️ Aucune ouverture avec {_MIN_GAMES_RELIABLE}+ parties sur cette période.")
        return

    best  = reliable.nlargest(2, "wr")
    worst = reliable.nsmallest(2, "wr")

    col_b, col_w = st.columns(2)
    with col_b:
        st.markdown("💪 **Forces**")
        for _, row in best.iterrows():
            color = "#739552"
            st.markdown(
                f"<span style='color:{color};font-weight:bold'>{row['wr']:.0f}%</span> "
                f"{row['name']} <span style='color:gray;font-size:12px'>({row['total']} parties)</span>",
                unsafe_allow_html=True,
            )
    with col_w:
        st.markdown("⚠️ **À travailler**")
        for _, row in worst.iterrows():
            color = "#c0392b"
            st.markdown(
                f"<span style='color:{color};font-weight:bold'>{row['wr']:.0f}%</span> "
                f"{row['name']} <span style='color:gray;font-size:12px'>({row['total']} parties)</span>",
                unsafe_allow_html=True,
            )


def _render_openings_section(df: pd.DataFrame):
    """Section complète ouvertures avec onglets Blancs/Noirs et niveau de détail."""
    detail_col, _ = st.columns([2, 3])
    with detail_col:
        detail = st.segmented_control(
            "Niveau de détail",
            options=["Famille ECO", "Ouverture exacte"],
            default="Famille ECO",
            key="opening_detail_level",
        )
    group_by = "eco_family" if detail == "Famille ECO" else "eco_name"

    tab_all, tab_white, tab_black = st.tabs(["Toutes", "⬜ Blancs", "⬛ Noirs"])

    with tab_all:
        stats_all = _build_opening_stats(df, group_by)
        if stats_all.empty:
            st.caption("Pas de données d'ouvertures disponibles.")
        else:
            _render_forces_faiblesses(stats_all)
            st.divider()
            _render_opening_chart(stats_all, "Bilan par ouverture — Toutes couleurs")

    with tab_white:
        df_w   = df[df["user_color"] == "white"]
        stats_w = _build_opening_stats(df_w, group_by)
        if stats_w.empty:
            st.caption("Pas de parties avec les Blancs sur cette période.")
        else:
            _render_forces_faiblesses(stats_w)
            st.divider()
            _render_opening_chart(stats_w, "Bilan par ouverture — Blancs")

    with tab_black:
        df_b   = df[df["user_color"] == "black"]
        stats_b = _build_opening_stats(df_b, group_by)
        if stats_b.empty:
            st.caption("Pas de parties avec les Noirs sur cette période.")
        else:
            _render_forces_faiblesses(stats_b)
            st.divider()
            _render_opening_chart(stats_b, "Bilan par ouverture — Noirs")

# ---------------------------------------------------------------------------
# Composants existants
# ---------------------------------------------------------------------------

def _render_header(username: str):
    with st.container(horizontal = True, vertical_alignment = "center"):

        if st.button("Rafraîchir", type="tertiary", width="content", icon=":material/refresh:", key="dashboard_refresh"):
            with st.spinner("Récupération des parties Chess.com…"):
                new_count, error = _sync(username)
            if error:
                st.toast(f"Erreur lors de la synchronisation : {error}", icon="❌")
            elif new_count == 0:
                st.toast("Aucune nouvelle partie depuis la dernière sync.", icon="ℹ️")
            else:
                st.toast(f"{new_count} nouvelle(s) partie(s) importée(s).", icon="✅")
            st.rerun()

        last_sync = get_last_sync(username)
        if last_sync:
            dt = datetime.fromisoformat(last_sync)
            st.caption(
                f"Dernière sync : {dt.strftime('%d/%m/%Y à %Hh%M')} · "
                f"username Chess.com : `{username}`"
            )


def _render_filters(df: pd.DataFrame) -> tuple[Optional[int], Optional[str]]:
    
    with st.container(horizontal=True):
        period_label = st.segmented_control(
            "Période",
            options=list(_PERIOD_OPTIONS.keys()),
            default="3 mois",
            key="dashboard_period_filter",
        )
        period_days = _PERIOD_OPTIONS.get(period_label or "3 mois")

        available_types = [t for t in GAME_TYPES if t in df["game_type"].unique()]
        default_type = df["game_type"].value_counts().idxmax() if available_types else None
        default_idx  = available_types.index(default_type) if default_type in available_types else 0
        game_type = st.segmented_control(
            "Mode de jeu",
            options=available_types,
                default=available_types[default_idx] if available_types else None,
                key="dashboard_game_type_filter",
            )
    return period_days, game_type


def _render_metrics(df: pd.DataFrame):

    # Barres de statistiques globales
    total  = len(df)
    wins   = (df["user_result"] == "win").sum()
    draws  = (df["user_result"] == "draw").sum()
    losses = (df["user_result"] == "loss").sum()
    render_games_bar(total, wins, draws, losses, "all")

    # Barres de statistiques pour les Blancs
    df_w = df[df["user_color"] == "white"]
    wins_w = (df_w["user_result"] == "win").sum()
    draws_w = (df_w["user_result"] == "draw").sum()
    losses_w = (df_w["user_result"] == "loss").sum()
    render_games_bar(len(df_w), wins_w, draws_w, losses_w, "white")   
    
    # Barres de statistiques pour les Noirs
    df_b = df[df["user_color"] == "black"]
    wins_b = (df_b["user_result"] == "win").sum()
    draws_b = (df_b["user_result"] == "draw").sum()
    losses_b = (df_b["user_result"] == "loss").sum()
    render_games_bar(len(df_b), wins_b, draws_b, losses_b, "black")




def _render_elo_chart(df: pd.DataFrame):

    # ELO actuel
    df_elo = df[df["user_elo"] > 0].sort_values("date_parsed")
    elo_current = int(df_elo.iloc[-1]["user_elo"]) if not df_elo.empty else None
    elo_delta   = int(df_elo.iloc[-1]["user_elo"] - df_elo.iloc[0]["user_elo"]) if len(df_elo) >= 2 else None
    if elo_current is not None:
        delta_str = f"{elo_delta:+d}" if elo_delta is not None else None
        color = "green" if elo_delta >= 0 else "red"
        delta_colored = f":{color}-badge[{delta_str}]"

        with st.container(horizontal=True, width="content", vertical_alignment="center"):
            st.subheader(f"ELO : **{elo_current}**", anchor=False)
            st.markdown(f":{color}-badge[{delta_str} sur la période]")
    else:
        st.caption("ELO actuel non disponible.")


    df_filtered = df[df["user_elo"] > 0].sort_values("date_parsed")
    if df_filtered.empty:
        st.caption("Évolution ELO non disponible.")
        return

    df_daily = df_filtered.groupby("date_parsed").last().reset_index()
    min_elo, max_elo = df_daily["user_elo"].min(), df_daily["user_elo"].max()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily["date_parsed"], y=df_daily["user_elo"],
        mode="lines+markers",
        marker=dict(size=4, color="#739552"),
        line=dict(color="#739552", width=2),
        fill="tozeroy", fillcolor="rgba(115, 149, 82, 0.2)",
        hovertemplate="%{x|%d/%m/%Y}<br>ELO : %{y}<extra></extra>",
    ))
    fig.update_layout(
        height=180, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)",
                   showline=False, range=[min_elo - 20, max_elo + 20]),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def _render_rolling_winrate(df: pd.DataFrame):

    df_chron = df.sort_values("date_parsed").reset_index(drop=True)
    if len(df_chron) < 5:
        st.caption("Pas assez de parties pour afficher le win rate glissant.")
        return
    else:
        with st.container(horizontal=True, width="content", vertical_alignment="bottom"):
            st.subheader(f"Win rate glissant", anchor=False, help=f"Moyenne glissante de vos victoires. Fenêtre de 5 à 20 parties selon votre historique.")
            with st.popover(" ", icon=":material/settings:", type="tertiary", help="Paramètres de la fenêtre glissante"):
                st.markdown('Fenêtre de calcul')

                st.markdown(':gray[:small[**10 :** réaction rapide  \n**20 :** équilibre  \n**40 :** tendance fond  \n**80 :** analyse long terme]]')
                rolling_window = st.select_slider(
                    "Fenêtre de calcul",
                    options=[10, 20, 40, 80],
                    value=st.session_state.get("rolling_window", _ROLLING_WINDOW),
                    format_func=lambda x: f"{x} parties" if x != 80 else f"{x} parties (max)",
                    key="rolling_window_slider",
                    label_visibility="collapsed"
                )
                
                if st.button("Appliquer", key="apply_rolling_window"):
                    st.session_state.rolling_window = rolling_window
                    st.rerun()

    # Récupérer la fenêtre de calcul (par défaut _ROLLING_WINDOW si non définie)
    rolling_window = st.session_state.get("rolling_window", _ROLLING_WINDOW)
    
    df_chron["win_bin"]    = (df_chron["user_result"] == "win").astype(int)
    df_chron["rolling_wr"] = (
        df_chron["win_bin"].rolling(window=rolling_window, min_periods=5).mean() * 100
    )
    df_plot = df_chron.dropna(subset=["rolling_wr"])

    fig = go.Figure()
    fig.add_hrect(y0=50, y1=100, fillcolor="rgba(115,149,82,0.06)", line_width=0)
    fig.add_hline(y=50, line=dict(color="gray", width=1, dash="dot"))    
    fig.add_trace(go.Scatter(
        x=list(range(5, 5 + len(df_plot))), y=df_plot["rolling_wr"],
        mode="lines", line=dict(color="#739552", width=2),
        fill="tonexty", fillcolor="rgba(115,149,82,0.15)",
        text=df_plot["date_parsed"].dt.strftime("%d/%m/%Y"),
        hovertemplate="Partie %{x}<br>Date : %{text}<br>Win rate : %{y:.1f}%<extra></extra> ",
    ))
    fig.update_layout(
        height=180, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, range=[df_plot["rolling_wr"].min()-5, df_plot["rolling_wr"].max()+5], ticksuffix="%", tickfont=dict(size=10)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def _render_recent_games(df: pd.DataFrame, analysis_callbacks) -> None:

    from utils.chesscom_cache import get_analyzed_game_ids

    def _analyze_game(pgn: str) -> None:
        st.session_state.pgn_text_input = pgn
        analysis_callbacks.on_analyze_click()

    game_ids      = df.head(20)["game_id"].astype(str).tolist()
    analyzed_ids  = get_analyzed_game_ids(game_ids)

    col_size = [1, 0.9, 0.9, 2.5, 0.5, 3, 0.6]

    with st.container(border=True):
        st.subheader("Parties récentes (20)", anchor=False)

        h = st.columns(col_size, vertical_alignment="center")
        for col, label in zip(h, ["Date", "Couleur", "Résultat", "Adversaire", "ELO", "Ouverture", "Analyser"]):
            col.caption(f"**{label}**")

        for _, row in df.head(20).iterrows():
            date_str     = row["date_parsed"].strftime("%d/%m/%Y") if pd.notna(row["date_parsed"]) else "—"
            color_icon   = "⬜" if row["user_color"] == "white" else "⬛"
            result_icon  = {"win": "✅", "loss": "❌", "draw": "🟰"}.get(row["user_result"], "?")
            opponent_str = f"{row['opponent']} ({row['opponent_elo']})"
            elo_str      = str(int(row["user_elo"])) if row["user_elo"] > 0 else "—"
            opening_str  = get_opening_name(row["eco"]) if row["eco"] else "—"
            pgn          = row.get("pgn", "")
            gid          = str(row.get("game_id", ""))
            is_cached    = gid in analyzed_ids

            c = st.columns(col_size, vertical_alignment="center")
            c[0].markdown(date_str)
            c[1].markdown(color_icon)
            c[2].markdown(result_icon)
            c[3].markdown(opponent_str)
            c[4].markdown(elo_str)
            c[5].markdown(opening_str)
            if pgn:
                c[6].button(
                    "",
                    icon=":material/bolt:" if is_cached else ":material/monitoring:",
                    key=f"analyze_{gid}",
                    type="secondary",
                    help="⚡ En cache — chargement instantané" if is_cached else "Analyser avec Stockfish",
                    on_click=_analyze_game,
                    args=(pgn,),
                )


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def render_dashboard(analysis_callbacks):
    username = st.session_state.get("username", "Joueur")
    init_db()

    _render_header(username)

    games = get_cached_games(username)
    if not games:
        st.info(
            f"Aucune partie en cache. Cliquez sur **Rafraîchir** pour importer "
            f"vos parties Chess.com (username configuré : `{username}`).\n\n"
            f"Assurez-vous que la variable d'environnement `STREAMLIT_USER` correspond "
            f"à votre pseudo Chess.com."
        )
        return

    df_full = _to_df(games)

    # ── Filtres ──────────────────────────────────────────────────────────────
    period_days, game_type = _render_filters(df_full)
    df = _apply_filters(df_full, period_days, game_type)

    if df.empty:
        label = f"{period_days} derniers jours" if period_days else "toute la période"
        st.info(f"Aucune partie en **{game_type}** sur {label}.")
        return
    st.divider()


        


    # ── Corps principal ───────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        # ── Métriques ─────────────────────────────────────────────────────────────
        _render_metrics(df)
        st.subheader("Ouvertures", anchor=False)
        _render_openings_section(df)

    with col_right:
        _render_elo_chart(df)
        _render_rolling_winrate(df)

    st.divider()

    # ── Parties récentes (discret) ────────────────────────────────────────────
    _render_recent_games(df, analysis_callbacks)