"""
PropPulse+ v2025.3 — Professional NBA Prop Analyzer
Modern betting interface with dark theme
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
from contextlib import redirect_stdout

# Import your model
import prop_ev as pe

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="PropPulse+ | NBA Props",
    page_icon="🏀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# CUSTOM CSS - Modern Betting UI
# ==========================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0A0E27 0%, #1A1F3A 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Header Logo */
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    
    .logo-text {
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
        margin-bottom: 0;
    }
    
    .tagline {
        color: #8B92B0;
        font-size: 14px;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* Input Section */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: white;
        padding: 12px;
        font-size: 15px;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Labels */
    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label {
        color: #B4B8CC !important;
        font-weight: 600;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 16px;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Result Cards */
    .result-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        backdrop-filter: blur(10px);
    }
    
    .player-header {
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin-bottom: 8px;
    }
    
    .stat-line {
        color: #8B92B0;
        font-size: 15px;
        margin-bottom: 20px;
    }
    
    /* Metric Grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }
    
    .metric-box {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    
    .metric-label {
        color: #8B92B0;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    .metric-value {
        color: white;
        font-size: 24px;
        font-weight: 700;
    }
    
    .metric-delta {
        font-size: 13px;
        margin-top: 4px;
        font-weight: 500;
    }
    
    /* EV Badge */
    .ev-badge {
        display: inline-block;
        padding: 12px 24px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 18px;
        margin: 16px 0;
    }
    
    .ev-positive {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    .ev-negative {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
    }
    
    /* Info Pills */
    .info-pill {
        display: inline-block;
        background: rgba(102, 126, 234, 0.15);
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 6px 14px;
        border-radius: 20px;
        color: #667eea;
        font-size: 13px;
        font-weight: 600;
        margin: 4px;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
        margin: 2rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #8B92B0;
        padding: 2rem 0;
        font-size: 13px;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="logo-text">PropPulse+</div>
    <div class="tagline">AI-Powered NBA Player Prop Analytics</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# INPUT FORM
# ==========================================
with st.form("prop_analyzer"):
    # Player Input
    player = st.text_input(
        "Player Name",
        placeholder="e.g., LeBron James",
        help="Enter the full player name"
    )
    
    # Stat and Line
    col1, col2 = st.columns(2)
    with col1:
        stat = st.selectbox(
            "Stat Category",
            ["PTS", "REB", "AST", "REB+AST", "PRA", "FG3M"],
            help="Select the prop type"
        )
    
    with col2:
        line = st.number_input(
            "Line",
            min_value=0.0,
            max_value=100.0,
            value=25.5,
            step=0.5,
            help="The sportsbook line"
        )
    
    # Odds and Submit
    col3, col4 = st.columns([2, 1])
    with col3:
        odds = st.number_input(
            "Odds (American)",
            value=-110,
            step=5,
            help="Enter American odds (e.g., -110 or +150)"
        )
    
    with col4:
        st.write("")  # Spacing
        st.write("")  # Spacing
        submit = st.form_submit_button("🔍 Analyze Prop")

# ==========================================
# ANALYSIS LOGIC
# ==========================================
if submit:
    if not player.strip():
        st.error("⚠️ Please enter a player name")
        st.stop()
    
    # Load settings
    settings = pe.load_settings()
    
    with st.spinner(f"🏀 Analyzing {player}'s {stat} projection..."):
        try:
            # Capture model output
            buf = io.StringIO()
            with redirect_stdout(buf):
                result = pe.analyze_single_prop(
                    player=player,
                    stat=stat,
                    line=line,
                    odds=int(odds),
                    settings=settings
                )
            
            if not result:
                st.error("❌ Unable to analyze this prop. Player data may be unavailable.")
                st.stop()
            
            # Extract results
            p_model = result['p_model']
            p_book = result['p_book']
            ev = result['ev']
            projection = result['projection']
            n_games = result['n_games']
            opponent = result.get('opponent', 'N/A')
            position = result.get('position', 'N/A')
            dvp_mult = result.get('dvp_mult', 1.0)
            
            # Calculate metrics
            edge = (p_model - p_book) * 100
            ev_cents = ev * 100
            recommendation = "OVER" if projection > line else "UNDER"
            
            # ==========================================
            # RESULTS DISPLAY
            # ==========================================
            
            # Player Header Card
            st.markdown(f"""
            <div class="result-card">
                <div class="player-header">{player}</div>
                <div class="stat-line">
                    {stat} • Line: {line} • Odds: {odds:+d}
                </div>
                
                <div style="margin: 16px 0;">
                    <span class="info-pill">📍 {position} vs {opponent}</span>
                    <span class="info-pill">📊 {n_games} games analyzed</span>
                    <span class="info-pill">🎯 DvP: {dvp_mult:.3f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Main Metrics
            st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
            
            # Projection
            proj_delta = projection - line
            proj_color = "#11998e" if proj_delta > 0 else "#eb3349"
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Projection</div>
                <div class="metric-value" style="color: {proj_color};">{projection:.1f}</div>
                <div class="metric-delta" style="color: {proj_color};">
                    {proj_delta:+.1f} vs line
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Model Probability
            edge_color = "#11998e" if edge > 0 else "#eb3349"
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Model Prob</div>
                <div class="metric-value">{p_model * 100:.1f}%</div>
                <div class="metric-delta" style="color: {edge_color};">
                    {edge:+.1f}% edge
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Book Probability
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Book Prob</div>
                <div class="metric-value">{p_book * 100:.1f}%</div>
                <div class="metric-delta" style="color: #8B92B0;">
                    Implied odds
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Expected Value Badge
            ev_class = "ev-positive" if ev_cents > 0 else "ev-negative"
            ev_emoji = "📈" if ev_cents > 0 else "📉"
            st.markdown(f"""
            <div style="text-align: center; margin: 24px 0;">
                <div class="{ev_class} ev-badge">
                    {ev_emoji} EV: {ev_cents:+.1f}¢ per $1
                </div>
                <div style="color: #8B92B0; margin-top: 12px; font-size: 15px;">
                    <strong style="color: white;">Recommendation:</strong> {recommendation}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Detailed Breakdown
            with st.expander("📊 Detailed Analysis", expanded=False):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown(f"""
                    **Model Details:**
                    - Games Analyzed: {n_games}
                    - Standard Deviation: Calculated
                    - L20 Weighted: Yes
                    - DvP Adjusted: {dvp_mult:.3f}
                    """)
                
                with detail_col2:
                    st.markdown(f"""
                    **Context:**
                    - Position: {position}
                    - Opponent: {opponent}
                    - Edge: {edge:+.2f}%
                    - EV per $100: ${ev * 100:.2f}
                    """)
            
            # Model Log
            model_output = buf.getvalue()
            if model_output:
                with st.expander("🔧 Model Debug Log", expanded=False):
                    st.code(model_output, language="text")
        
        except Exception as e:
            st.error(f"❌ Analysis Error: {str(e)}")
            import traceback
            with st.expander("Show Error Details"):
                st.code(traceback.format_exc())

# ==========================================
# FOOTER
# ==========================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(f"""
<div class="footer">
    PropPulse+ v2025.3 | L20-Weighted Model with FantasyPros DvP<br>
    Built with ❤️ for sharper betting decisions
</div>
""", unsafe_allow_html=True)