"""Dashboard principal — données réelles depuis le cache Chess.com."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import List, Dict, Any

from utils.chesscom_api import fetch_recent_games
from utils.chesscom_cache import init_db, get_cached_games, get_last_sync, upsert_games, update_sync_log
from utils.eco_openings import get_opening_name, get_opening_family



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
    df["eco_family"] = df["eco"].apply(get_opening_family)
    return df.sort_values("date_parsed", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Composants d'affichage
# ---------------------------------------------------------------------------

def _render_header(username: str):
    col_title, col_btn = st.columns([4, 1], vertical_alignment="bottom")
    with col_title:
        st.header("📊 Tableau de bord", anchor=False)
    with col_btn:
        if st.button("🔄 Rafraîchir", type="secondary", width="stretch", key="dashboard_refresh"):
            with st.spinner("Récupération des parties Chess.com…"):
                new_count, error = _sync(username)
            if error:
                st.error(f"Erreur lors de la synchronisation : {error}")
            elif new_count == 0:
                st.info("Aucune nouvelle partie depuis la dernière sync.")
            else:
                st.success(f"{new_count} nouvelle(s) partie(s) importée(s).")
            st.rerun()

    last_sync = get_last_sync(username)
    if last_sync:
        dt = datetime.fromisoformat(last_sync)
        st.caption(f"Dernière sync : {dt.strftime('%d/%m/%Y à %Hh%M')} · username Chess.com : `{username}`")


def _render_metrics(df: pd.DataFrame):
    total = len(df)
    wins  = (df["user_result"] == "win").sum()
    draws = (df["user_result"] == "draw").sum()
    losses = (df["user_result"] == "loss").sum()
    wr_global = round(wins / total * 100, 1) if total else 0

    df_w = df[df["user_color"] == "white"]
    df_b = df[df["user_color"] == "black"]
    wr_white = round((df_w["user_result"] == "win").sum() / len(df_w) * 100, 1) if len(df_w) else 0
    wr_black = round((df_b["user_result"] == "win").sum() / len(df_b) * 100, 1) if len(df_b) else 0
    current_elo = int(df.iloc[0]["user_elo"]) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 Win rate global", f"{wr_global}%", f"{wins}V / {draws}N / {losses}D")
    c2.metric("⬜ Win rate (Blancs)", f"{wr_white}%", f"{len(df_w)} parties")
    c3.metric("⬛ Win rate (Noirs)", f"{wr_black}%", f"{len(df_b)} parties")
    c4.metric("📈 Elo actuel", current_elo, f"{total} parties en cache")


def _render_recent_games(df: pd.DataFrame):
    st.subheader("Parties récentes", anchor=False)
    display = df.copy()
    display["Date"]       = display["date_parsed"].dt.strftime("%d/%m/%Y")
    display["Couleur"]    = display["user_color"].map({"white": "⬜", "black": "⬛"})
    display["Résultat"]   = display["user_result"].map({"win": "✅", "loss": "❌", "draw": "🟰"})
    display["Adversaire"] = display["opponent"] + " (" + display["opponent_elo"].astype(str) + ")"
    display["Elo"]        = display["user_elo"]
    display["Ouverture"]  = display["eco"].apply(lambda x: get_opening_name(x) if x else "Inconnue")

    st.dataframe(
        display[["Date", "Couleur", "Résultat", "Adversaire", "Elo", "Ouverture"]],
        use_container_width=True,
        hide_index=True,
        height=420,
    )


def _render_elo_chart(df: pd.DataFrame):
    st.subheader("Évolution de l'Elo", anchor=False)
    df_filtered = df[df["user_elo"] > 0].copy()
    if df_filtered.empty:
        st.caption("Pas de données Elo disponibles.")
        return

    # Grouper par jour et garder le dernier ELO de chaque journée
    df_daily = df_filtered.sort_values("date_parsed").groupby("date_parsed").last().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily["date_parsed"],
        y=df_daily["user_elo"],
        mode="lines+markers",
        marker=dict(size=4, color="#739552"),
        line=dict(color="#739552", width=2),
        fill="tozeroy",
        fillcolor="rgba(115, 149, 82, 0.3)",
        hovertemplate="%{x|%d/%m/%Y}<br>Elo : %{y}<extra></extra>",
    ))
    # Calculer les limites
    min_elo = df_daily["user_elo"].min()
    max_elo = df_daily["user_elo"].max()
    
    fig.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(
            showgrid=True, 
            gridcolor="rgba(255,255,255,0.08)", 
            showline=False,
            range=[min_elo - 50, max_elo + 50]
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_opening_chart(df: pd.DataFrame):
    st.subheader("Win rate par famille d'ouverture", anchor=False)
    df_eco = df[df["eco"] != ""].copy()
    if df_eco.empty:
        st.caption("Pas de données d'ouvertures disponibles.")
        return

    stats = (
        df_eco.groupby("eco_family")
        .agg(parties=("user_result", "count"), victoires=("user_result", lambda x: (x == "win").sum()))
        .reset_index()
    )
    stats = stats[stats["parties"] >= 3]
    if stats.empty:
        st.caption("Pas assez de parties par famille d'ouverture (minimum 3).")
        return

    stats["win_rate"] = (stats["victoires"] / stats["parties"] * 100).round(1)
    stats = stats.sort_values("win_rate", ascending=True)

    fig = px.bar(
        stats,
        x="win_rate", y="eco_family", orientation="h",
        text="win_rate",
        color="win_rate",
        color_continuous_scale=["#ef4444", "#f59e0b", "#739552"],
        range_color=[0, 100],
        custom_data=["parties"],
    )
    fig.update_traces(
        texttemplate="%{text}%",
        textposition="outside",
        hovertemplate="%{y}<br>Win rate : %{x}%<br>Parties : %{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(title="Win rate (%)", range=[0, 115], showgrid=False),
        yaxis_title="",
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def render_dashboard():
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

    df = _to_df(games)
    _render_metrics(df)

    col_games, col_charts = st.columns([3, 2], gap="medium")
    with col_games:
        _render_recent_games(df)
    with col_charts:
        _render_elo_chart(df)
        _render_opening_chart(df)