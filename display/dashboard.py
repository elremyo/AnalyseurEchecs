"""Dashboard principal — données réelles depuis le cache Chess.com."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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

_MIN_GAMES_OPENING = 1   # seuil pour afficher une famille d'ouverture
_ROLLING_WINDOW    = 20  # fenêtre du win rate glissant


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


# ---------------------------------------------------------------------------
# Composants
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
        st.caption(
            f"Dernière sync : {dt.strftime('%d/%m/%Y à %Hh%M')} · "
            f"username Chess.com : `{username}`"
        )


def _render_filters(df: pd.DataFrame) -> tuple[Optional[int], Optional[str]]:
    """Affiche les filtres période + mode de jeu. Retourne (period_days, game_type)."""
    col_period, col_mode = st.columns([3, 2], gap="large")

    with col_period:
        period_label = st.segmented_control(
            "Période",
            options=list(_PERIOD_OPTIONS.keys()),
            default="3 mois",
            key="dashboard_period_filter",
        )
    period_days = _PERIOD_OPTIONS.get(period_label or "3 mois")

    with col_mode:
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
    """4 métriques : parties, ELO + delta, win rate blanc, win rate noir."""
    total  = len(df)
    wins   = (df["user_result"] == "win").sum()
    draws  = (df["user_result"] == "draw").sum()
    losses = (df["user_result"] == "loss").sum()

    df_w = df[df["user_color"] == "white"]
    df_b = df[df["user_color"] == "black"]
    wr_white = round((df_w["user_result"] == "win").sum() / len(df_w) * 100, 1) if len(df_w) else 0
    wr_black = round((df_b["user_result"] == "win").sum() / len(df_b) * 100, 1) if len(df_b) else 0

    # ELO delta : dernier - premier dans la période (tri chronologique)
    df_elo = df[df["user_elo"] > 0].sort_values("date_parsed")
    elo_current = int(df_elo.iloc[-1]["user_elo"]) if not df_elo.empty else None
    elo_delta   = int(df_elo.iloc[-1]["user_elo"] - df_elo.iloc[0]["user_elo"]) if len(df_elo) >= 2 else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Parties jouées", total, f"{wins}V · {draws}N · {losses}D", delta_color="off", delta_arrow="off")
    if elo_current is not None:
        delta_str = f"{elo_delta:+d}" if elo_delta is not None else None
        c2.metric("ELO actuel", elo_current, f' {delta_str} sur la période')
    else:
        c2.metric("ELO actuel", "—", delta_color="off", delta_arrow="off")
    c3.metric("Win rate ⬜ Blancs", f"{wr_white}%", f"{len(df_w)} parties", delta_color="off", delta_arrow ="off")
    c4.metric("Win rate ⬛ Noirs",  f"{wr_black}%", f"{len(df_b)} parties", delta_color="off", delta_arrow ="off")


def _render_openings(df: pd.DataFrame):
    """Tableau des familles d'ouvertures : parties, W% total, W% blancs, W% noirs."""
    st.subheader("Ouvertures", anchor=False, help=f"Répartition des familles d'ouvertures jouées (minimum de {_MIN_GAMES_OPENING} parties jouées)")

    df_eco = df[df["eco"] != ""].copy()
    if df_eco.empty:
        st.caption("Pas de données d'ouvertures disponibles.")
        return

    def _wr(subset: pd.DataFrame) -> float:
        if subset.empty:
            return float("nan")
        return round((subset["user_result"] == "win").sum() / len(subset) * 100, 1)

    rows = []
    for family, grp in df_eco.groupby("eco_family"):
        if len(grp) < _MIN_GAMES_OPENING:
            continue
        grp_w = grp[grp["user_color"] == "white"]
        grp_b = grp[grp["user_color"] == "black"]
        rows.append({
            "Ouverture":    family,
            "Parties":      len(grp),
            "W% total":     _wr(grp),
            "W% ⬜":        _wr(grp_w),
            "W% ⬛":        _wr(grp_b),
        })

    if not rows:
        st.info(f"Pas assez de parties par famille (minimum {_MIN_GAMES_OPENING}).")
        return

    table = (
        pd.DataFrame(rows)
        .sort_values("Parties", ascending=False)
        .reset_index(drop=True)
    )

    def _color_wr(val):
        if pd.isna(val):
            return "color: gray"
        if val >= 55:
            return "color: #739552; font-weight: bold"
        if val >= 45:
            return "color: #d4a017"
        return "color: #c0392b"

    styled = (
        table.style
        .applymap(_color_wr, subset=["W% total", "W% ⬜", "W% ⬛"])
        .format({"W% total": "{:.1f}%", "W% ⬜": "{:.1f}%", "W% ⬛": "{:.1f}%"}, na_rep="—")
        .set_properties(**{"text-align": "center"}, subset=["Parties", "W% total", "W% ⬜", "W% ⬛"])
        .set_properties(**{"text-align": "left"}, subset=["Ouverture"])
    )
    st.dataframe(styled, width='stretch', hide_index=True, height=min(80 + len(table) * 35, 420))


def _render_elo_chart(df: pd.DataFrame):
    """Courbe ELO sur la période."""
    st.subheader("Évolution ELO", anchor=False)
    df_filtered = df[df["user_elo"] > 0].sort_values("date_parsed")
    if df_filtered.empty:
        st.caption("Pas de données ELO disponibles.")
        return

    df_daily = df_filtered.groupby("date_parsed").last().reset_index()
    min_elo, max_elo = df_daily["user_elo"].min(), df_daily["user_elo"].max()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily["date_parsed"],
        y=df_daily["user_elo"],
        mode="lines+markers",
        marker=dict(size=4, color="#739552"),
        line=dict(color="#739552", width=2),
        fill="tozeroy",
        fillcolor="rgba(115, 149, 82, 0.2)",
        hovertemplate="%{x|%d/%m/%Y}<br>ELO : %{y}<extra></extra>",
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            showline=False,
            range=[min_elo - 30, max_elo + 30],
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def _render_rolling_winrate(df: pd.DataFrame):
    """Win rate glissant sur les N dernières parties (ordre chronologique)."""
    st.subheader(f"Win rate glissant ({_ROLLING_WINDOW} parties)", anchor=False)

    df_chron = df.sort_values("date_parsed").reset_index(drop=True)
    if len(df_chron) < 5:
        st.caption("Pas assez de parties pour afficher le win rate glissant.")
        return

    df_chron["win_bin"] = (df_chron["user_result"] == "win").astype(int)
    df_chron["rolling_wr"] = (
        df_chron["win_bin"]
        .rolling(window=_ROLLING_WINDOW, min_periods=5)
        .mean() * 100
    )

    df_plot = df_chron.dropna(subset=["rolling_wr"])

    fig = go.Figure()
    # Zone de référence à 50%
    fig.add_hrect(y0=50, y1=100, fillcolor="rgba(115,149,82,0.06)", line_width=0)
    fig.add_hline(y=50, line=dict(color="gray", width=1, dash="dot"))
    fig.add_trace(go.Scatter(
        x=list(range(len(df_plot))),
        y=df_plot["rolling_wr"],
        mode="lines",
        line=dict(color="#739552", width=2),
        fill="tonexty",
        fillcolor="rgba(115,149,82,0.15)",
        hovertemplate="Partie %{x}<br>Win rate : %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(
            showgrid=False,
            range=[0, 100],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def _render_recent_games_expander(df: pd.DataFrame):
    """Tableau des parties récentes dans un expander discret."""
    with st.expander("Parties récentes", expanded=False, icon=":material/table:"):
        display = df.copy()
        display["Date"]       = display["date_parsed"].dt.strftime("%d/%m/%Y")
        display["Couleur"]    = display["user_color"].map({"white": "⬜", "black": "⬛"})
        display["Résultat"]   = display["user_result"].map({"win": "✅", "loss": "❌", "draw": "🟰"})
        display["Adversaire"] = display["opponent"] + " (" + display["opponent_elo"].astype(str) + ")"
        display["ELO"]        = display["user_elo"]
        display["Ouverture"]  = display["eco"].apply(lambda x: get_opening_name(x) if x else "—")

        st.dataframe(
            display[["Date", "Couleur", "Résultat", "Adversaire", "ELO", "Ouverture"]],
            width='stretch',
            hide_index=True,
            height=320,
        )


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

    df_full = _to_df(games)

    # ── Filtres ──────────────────────────────────────────────────────────────
    period_days, game_type = _render_filters(df_full)
    df = _apply_filters(df_full, period_days, game_type)

    if df.empty:
        label = f"{period_days} derniers jours" if period_days else "toute la période"
        st.info(f"Aucune partie en **{game_type}** sur {label}.")
        return

    st.divider()

    # ── Métriques ─────────────────────────────────────────────────────────────
    _render_metrics(df)

    # ── Corps principal ───────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        _render_openings(df)

    with col_right:
        _render_elo_chart(df)
        _render_rolling_winrate(df)

    # ── Parties récentes (discret) ────────────────────────────────────────────
    _render_recent_games_expander(df)