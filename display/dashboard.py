import streamlit as st
import pandas as pd
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

def render_dashboard():
    """Render the dashboard page with placeholder data"""
    st.header("📊 Tableau de bord", anchor=False)
    
    # Generate placeholder data
    recent_games = generate_recent_games_data()
    metrics = generate_metrics_data()
    
    # Layout: metrics cards at top
    render_metrics_cards(metrics)
    
    # Two columns layout
    col_games, col_charts = st.columns([3, 2], gap="medium")
    
    with col_games:
        render_recent_games_table(recent_games)
    
    with col_charts:
        render_win_rate_chart()
        render_opening_family_chart()

def generate_recent_games_data() -> List[Dict[str, Any]]:
    """Generate placeholder data for recent games"""
    games = []
    players = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    openings = ["Italian Game", "Sicilian Defense", "French Defense", "Ruy Lopez", "Queen's Gambit"]
    
    for i in range(20):
        white = random.choice(players)
        black = random.choice([p for p in players if p != white])
        result = random.choice(["1-0", "0-1", "1/2-1/2"])
        opening = random.choice(openings)
        accuracy = round(random.uniform(60, 95), 1)
        date = datetime.now() - timedelta(days=random.randint(0, 30))
        
        games.append({
            "Date": date.strftime("%d/%m/%Y"),
            "Blanc": white,
            "Noir": black,
            "Résultat": result,
            "Ouverture": opening,
            "Précision": f"{accuracy}%",
            "Durée": f"{random.randint(5, 60)} min"
        })
    
    return games

def generate_metrics_data() -> Dict[str, float]:
    """Generate placeholder metrics"""
    return {
        "accuracy_moyenne": round(random.uniform(70, 85), 1),
        "win_rate_blanc": round(random.uniform(35, 55), 1),
        "win_rate_noir": round(random.uniform(35, 55), 1),
        "total_parties": 20,
        "parties_ce_mois": 8
    }

def render_metrics_cards(metrics: Dict[str, float]):
    """Render metrics cards at the top of dashboard"""
    col1, col2, col3, col4 = st.columns(4, gap="small")
    
    with col1:
        st.metric(
            label="🎯 Précision moyenne",
            value=f"{metrics['accuracy_moyenne']}%",
            delta=f"+{random.uniform(1, 5):.1f}% vs mois dernier"
        )
    
    with col2:
        st.metric(
            label="⚪ Win rate (Blanc)",
            value=f"{metrics['win_rate_blanc']}%",
            delta=f"+{random.uniform(0, 3):.1f}%"
        )
    
    with col3:
        st.metric(
            label="⚫ Win rate (Noir)",
            value=f"{metrics['win_rate_noir']}%",
            delta=f"{random.uniform(-2, 2):.1f}%"
        )
    
    with col4:
        st.metric(
            label="📈 Parties ce mois",
            value=metrics['parties_ce_mois'],
            delta=f"+{random.randint(1, 5)} vs mois dernier"
        )

def render_recent_games_table(games: List[Dict[str, Any]]):
    """Render table of recent games"""
    st.subheader("🕹️ 20 dernières parties", anchor=False)
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(games)
    
    # Style the result column
    def color_result(val):
        if val == "1-0":
            return "background-color: rgba(34, 197, 94, 0.2); color: black"
        elif val == "0-1":
            return "background-color: rgba(239, 68, 68, 0.2); color: black"
        else:
            return "background-color: rgba(251, 191, 36, 0.2); color: black"
    
    styled_df = df.style.applymap(color_result, subset=['Résultat'])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )

def render_win_rate_chart():
    """Render win rate chart"""
    st.subheader("📊 Taux de victoire", anchor=False)
    
    # Generate placeholder data
    data = {
        'Type': ['Victoires (Blanc)', 'Victoires (Noir)', 'Nulles'],
        'Pourcentage': [45, 38, 17]
    }
    
    fig = px.pie(
        data,
        values='Pourcentage',
        names='Type',
        color_discrete_map={
            'Victoires (Blanc)': '#ffffff',
            'Victoires (Noir)': '#000000',
            'Nulles': '#808080'
        }
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='#000000', width=2))
    )
    
    fig.update_layout(
        height=300,
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_opening_family_chart():
    """Render opening family win rate chart"""
    st.subheader("🏆 Win rate par famille d'ouverture", anchor=False)
    
    # Generate placeholder data for openings with ≥3 games
    openings_data = [
        {'Ouverture': 'Italienne', 'Parties': 5, 'Win Rate': 60},
        {'Ouverture': 'Sicilienne', 'Parties': 4, 'Win Rate': 50},
        {'Ouverture': 'Française', 'Parties': 3, 'Win Rate': 33},
        {'Ouverture': 'Ruy Lopez', 'Parties': 3, 'Win Rate': 67},
        {'Ouverture': 'Gambit Dame', 'Parties': 5, 'Win Rate': 40}
    ]
    
    df = pd.DataFrame(openings_data)
    
    # Create horizontal bar chart
    fig = px.bar(
        df,
        x='Win Rate',
        y='Ouverture',
        orientation='h',
        text='Win Rate',
        color='Win Rate',
        color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'],
        range_color=[0, 100]
    )
    
    fig.update_traces(
        texttemplate='%{text}%',
        textposition='outside'
    )
    
    fig.update_layout(
        height=300,
        margin=dict(t=0, b=0, l=0, r=0),
        xaxis_title="Win Rate (%)",
        yaxis_title="",
        coloraxis_showscale=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
