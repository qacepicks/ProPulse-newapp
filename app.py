"""
PropPulse+ v2025.6 — Professional NBA Prop Analyzer
Mobile-Optimized Modern UI | Advanced Analytics | Responsive Sidebar
"""

import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime, timedelta
import io
from contextlib import redirect_stdout
import plotly.graph_objects as go
import plotly.express as px

# Import model
try:
    import prop_ev as pe
except ImportError as e:
    st.error(f"❌ Failed to import prop_ev.py: {e}")
    st.stop()

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="PropPulse+ | NBA Props",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# LOGO HANDLING
# ==========================================
def get_logo_base64():
    logo_path = "proppulse_logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ==========================================
# CUSTOM CSS (MOBILE FRIENDLY)
# ==========================================
logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:56px;height:56px;border-radius:12px;">' if logo_b64 else '<div class="brand-logo-fallback">PP</div>'

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
:root {{
  --primary-color:#FF8C42;--primary-dark:#E67A33;--primary-light:#FFB380;
  --background-dark:#0B0F19;--surface-dark:#1F2937;--text-primary:#F9FAFB;
  --text-secondary:#E5E7EB;--text-muted:#9CA3AF;--success:#10B981;
  --warning:#F59E0B;--danger:#EF4444;--border-color:#374151;
}}
.stApp {{
  background:var(--background-dark);
  font-family:'Inter',sans-serif;color:var(--text-secondary);
  overflow-x:hidden!important;
}}
#MainMenu,footer,header{{visibility:hidden;}}

/* Sidebar */
[data-testid="stSidebar"]{{
  background:var(--surface-dark);
  border-right:2px solid var(--primary-color);
  overflow-y:auto;
}}
[data-testid="stSidebar"] *{{color:var(--text-secondary)!important;}}
[data-testid="stSidebar"] label{{
  font-weight:700;font-size:12px;text-transform:uppercase;
  letter-spacing:1px;margin-bottom:6px;
}}
/* Mobile dropdown fix */
@media (max-width:768px){{
  [data-testid="stSidebar"]{{width:100vw!important;border-right:none!important;
  border-bottom:2px solid var(--primary-color)!important;}}
  [data-testid="stSidebar"] .stRadio>div{{display:flex!important;
  flex-direction:column!important;align-items:flex-start!important;
  gap:.5rem!important;overflow:visible!important;}}
  [data-testid="stSidebar"] label,[data-testid="stSidebar"] input,[data-testid="stSidebar"] select{{
    visibility:visible!important;opacity:1!important;pointer-events:auto!important;
  }}
  [data-testid="stSidebar"] .stRadio{{z-index:99!important;position:relative!important;}}
}}

/* Header */
.main-header {{
  background:linear-gradient(135deg,var(--surface-dark),var(--background-dark));
  border-bottom:2px solid var(--primary-color);
  padding:1.5rem 1rem;box-shadow:0 8px 24px rgba(0,0,0,.4);
}}
.brand-container{{display:flex;align-items:center;justify-content:space-between;
  gap:1rem;flex-wrap:wrap;}}
.brand-logo-fallback{{width:56px;height:56px;background:linear-gradient(135deg,var(--primary-color),var(--primary-dark));
  border-radius:12px;display:flex;align-items:center;justify-content:center;
  font-weight:900;font-size:26px;color:white;}}
.brand-title{{font-size:28px;font-weight:900;background:linear-gradient(135deg,var(--primary-color),var(--primary-light));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.brand-subtitle{{font-size:13px;color:var(--text-muted);}}
.status-badge{{background:#065F46;border:2px solid var(--success);
  color:var(--success);padding:6px 12px;border-radius:8px;font-size:12px;font-weight:700;}}

/* Inputs + Buttons */
.stTextInput input,.stNumberInput input,.stSelectbox select{
  background:var(--surface-dark);border:2px solid var(--border-color);
  border-radius:10px;color:var(--text-primary);padding:12px 14px;font-size:15px;
}

/* Dark theme fix for Streamlit date input */
[data-testid="stDateInput"] input {
  background-color: var(--surface-dark) !important;
  border: 2px solid var(--border-color) !important;
  color: var(--text-primary) !important;
  border-radius: 10px !important;
  padding: 10px 12px !important;
  font-size: 15px !important;
}

[data-testid="stDateInput"] label {
  font-weight: 700 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  margin-bottom: 6px !important;
  color: var(--text-secondary) !important;
}

/* Focus & hover glow for date input */
[data-testid="stDateInput"] input:hover,
[data-testid="stDateInput"] input:focus {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 8px rgba(255, 140, 66, 0.4) !important;
  outline: none !important;
  transition: 0.25s ease-in-out !important;
}

/* Calendar popup dark theme */
.stDateInput [role="dialog"], .stDateInput [data-baseweb="calendar"] {
  background-color: var(--surface-dark) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: 10px !important;
}
.stDateInput [role="dialog"] * {
  color: var(--text-primary) !important;
}

/* Buttons */
.stButton>button{
  width:100%;background:linear-gradient(135deg,var(--primary-color),var(--primary-dark));
  border-radius:10px;padding:14px 24px;font-weight:800;text-transform:uppercase;
  box-shadow:0 6px 20px rgba(255,140,66,0.4);
}

.stButton>button:hover{{transform:translateY(-2px);
  box-shadow:0 8px 28px rgba(255,140,66,0.6);}}

/* Metric Cards */
.metric-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
  gap:16px;margin:24px 0;}}
.metric-card{{background:var(--surface-dark);border-radius:12px;border:1.5px solid var(--border-color);
  padding:18px;transition:.3s;}}
.metric-card:hover{{border-color:var(--primary-color);transform:translateY(-3px);}}
.metric-value{{font-size:28px;font-weight:900;color:var(--text-primary);}}

/* Footer */
.footer{{text-align:center;padding:30px 0;font-size:13px;color:var(--text-muted);
  border-top:1px solid var(--border-color);margin-top:40px;}}
.footer strong{{color:var(--primary-color)!important;}}

/* Mobile Tweaks */
@media(max-width:768px){{
  .brand-title{{font-size:22px;}}
  .metric-grid{{grid-template-columns:1fr;}}
  .stAppViewContainer{{padding:0 .5rem!important;}}
  .stButton>button{{font-size:14px;padding:12px 20px;}}
  .ev-container{{padding:24px;}}
}}
</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================
st.markdown(f"""
<div class="main-header">
  <div class="brand-container">
    {logo_html}
    <div class="brand-text">
      <div class="brand-title">PropPulse+</div>
      <div class="brand-subtitle">Advanced NBA Player Prop Analytics Platform</div>
    </div>
    <div class="status-badge">LIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR SETTINGS
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Analysis Settings")
    st.markdown("---")

    default_date = datetime.now()
    analysis_date = st.date_input(
        "Analysis Date",
        value=default_date,
        min_value=datetime.now() - timedelta(days=7),
        max_value=datetime.now() + timedelta(days=7),
        help="Select the date for opponent/schedule lookup."
    )

    if analysis_date.strftime("%Y-%m-%d") != datetime.now().strftime("%Y-%m-%d"):
        st.caption(f"⚠️ Using custom date: {analysis_date.strftime('%b %d, %Y')}")

    st.markdown("---")
    mode = st.radio(
        "Select Analysis Mode",
        ["🎯 Single Prop Analysis", "📊 Batch Manual Entry", "📁 CSV Import"],
        index=0
    )

    st.markdown("---")
    with st.expander("🔧 Advanced Settings"):
        debug_mode = st.checkbox("Enable Debug Mode", value=True)
        show_charts = st.checkbox("Show Visualizations", value=True)
        confidence_threshold = st.slider("Min Confidence", 0.0, 1.0, 0.5, 0.05)

    st.markdown("---")
    st.caption("**PropPulse+ v2025.6**")
    st.caption("L20-Weighted Projection Model")
    st.caption("Integrated FantasyPros DvP")
    st.caption("Built for Professional Bettors")

# ==========================================
# MODE 1: SINGLE PROP ANALYSIS
# ==========================================
if mode == "🎯 Single Prop Analysis":
    with st.form("prop_analyzer"):
        st.markdown("### 📋 Enter Prop Details")

        col1, col2 = st.columns([2, 1])
        player = col1.text_input("Player Name", placeholder="LeBron James")
        stat = col2.selectbox(
            "Stat Category",
            ["PTS", "REB", "AST", "REB+AST", "PRA", "P+R", "P+A", "FG3M"]
        )

        # NEW: Date picker moved inside form
        col_date = st.columns([1])[0]
        analysis_date = col_date.date_input(
            "📅 Analysis Date",
            value=datetime.now(),
            min_value=datetime.now() - timedelta(days=7),
            max_value=datetime.now() + timedelta(days=7),
            help="Select the date for opponent/schedule lookup."
        )

        col3, col4 = st.columns(2)
        line = col3.number_input("Line", 0.0, 100.0, 25.5, 0.5)
        odds = col4.number_input("Odds (American)", value=-110, step=5)

        st.markdown("---")
        submit = st.form_submit_button("🔍 ANALYZE PROP", use_container_width=True)


    if submit:
        if not player.strip():
            st.error("⚠️ Please enter a player name")
            st.stop()

        try:
            settings = pe.load_settings()
        except Exception as e:
            st.error(f"❌ Failed to load settings: {e}")
            st.stop()

        analysis_date_str = analysis_date.strftime("%Y-%m-%d")
        st.info(f"📅 Analyzing for date: **{analysis_date_str}**")

        with st.spinner(f"🏀 Analyzing {player}'s {stat} projection..."):
            try:
                settings['analysis_date'] = analysis_date_str
                buf = io.StringIO()
                with redirect_stdout(buf):
                    result = pe.analyze_single_prop(
                        player, stat, line, int(odds),
                        settings=settings, debug_mode=debug_mode)
                model_output = buf.getvalue()
                if not result:
                    st.error("❌ Unable to analyze this prop.")
                    st.stop()
            except Exception as e:
                st.error(f"❌ Analysis Error: {e}")
                st.stop()

        # Display results
        p_model = result['p_model']
        p_book = result['p_book']
        ev = result['ev']
        projection = result['projection']
        n_games = result['n_games']
        opponent = result.get('opponent', 'N/A')
        position = result.get('position', 'N/A')
        dvp_mult = result.get('dvp_mult', 1.0)
        confidence = result.get('confidence', 0.0)
        grade = result.get('grade', 'N/A')

        edge = (p_model - p_book) * 100
        ev_cents = ev * 100
        recommendation = "OVER" if projection > line else "UNDER"

        st.success("✅ Analysis Complete!")

        # Metric cards
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f"<div class='metric-card'><div class='metric-value'>{projection:.1f}</div><div>Model Projection</div></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='metric-card'><div class='metric-value'>{ev_cents:+.1f}¢</div><div>Expected Value</div></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='metric-card'><div class='metric-value'>{edge:+.1f}%</div><div>Model Edge</div></div>", unsafe_allow_html=True)
        col4.markdown(f"<div class='metric-card'><div class='metric-value'>{confidence:.2f}</div><div>Confidence</div></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        ev_class = "ev-positive" if ev > 0 else "ev-negative"
        rec_text = f"BET {recommendation}" if ev > 0 else "FADE THIS PROP"
        st.markdown(f"<div class='ev-container'><div class='ev-badge {ev_class}'>{ev_cents:+.1f}¢ EV</div><div class='recommendation'>{rec_text}</div></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        col1.markdown(f"**Model Prob:** {p_model*100:.1f}%  \n**Book Prob:** {p_book*100:.1f}%  \n**Line:** {line}  \n**Odds:** {odds}")
        col2.markdown(f"**Opponent:** {opponent}  \n**Position:** {position}  \n**DvP Multiplier:** {dvp_mult:.3f}  \n**Sample Size:** {n_games}")

        if show_charts:
            st.markdown("---")
            st.markdown("### 📈 Visual Analysis")
            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure(data=[go.Bar(name='Model', x=['Model', 'Sportsbook'], y=[p_model*100, p_book*100],
                                             marker_color=['#FF8C42', '#6B7280'])])
                fig.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=ev_cents, title={'text': "EV (¢)"},
                                             gauge={'axis': {'range': [-20, 20]}, 'bar': {'color': "#FF8C42"}}))
                fig.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig, use_container_width=True)

        if debug_mode and model_output:
            with st.expander("🔧 Debug Log"):
                st.code(model_output)

# ==========================================
# MODE 2: BATCH MANUAL ENTRY
# ==========================================
elif mode == "📊 Batch Manual Entry":
    st.markdown("### 📊 Batch Manual Entry")
    n_props = st.number_input("Number of props", 1, 20, 3)
    manual_entries = []
    for i in range(int(n_props)):
        col1, col2, col3, col4 = st.columns(4)
        player = col1.text_input(f"Player", key=f"player_{i}")
        stat = col2.selectbox(f"Stat", ["PTS", "REB", "AST", "PRA", "FG3M"], key=f"stat_{i}")
        line = col3.number_input(f"Line", 0.0, 100.0, 20.0, key=f"line_{i}")
        odds = col4.text_input(f"Odds", "-110", key=f"odds_{i}")
        if player.strip():
            manual_entries.append({"player": player, "stat": stat, "line": line, "odds": odds})

    if st.button("🚀 ANALYZE BATCH", use_container_width=True):
        if not manual_entries:
            st.error("⚠️ Please enter at least one valid player.")
            st.stop()
        settings = pe.load_settings()
        settings['analysis_date'] = analysis_date.strftime("%Y-%m-%d")
        results = []
        for entry in manual_entries:
            try:
                res = pe.analyze_single_prop(entry["player"], entry["stat"], float(entry["line"]), int(entry["odds"]), settings)
                if res: results.append(res)
            except Exception as e:
                st.warning(f"⚠️ Skipped {entry['player']}: {e}")
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("💾 Download Results CSV", csv, "batch_results.csv", use_container_width=True)

# ==========================================
# MODE 3: CSV IMPORT
# ==========================================
else:
    st.markdown("### 📁 CSV Import")
    uploaded = st.file_uploader("Upload CSV", type=['csv'])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df, use_container_width=True)
        if st.button("🚀 ANALYZE CSV DATA", use_container_width=True):
            settings = pe.load_settings()
            settings['analysis_date'] = analysis_date.strftime("%Y-%m-%d")
            results = []
            for idx, row in df.iterrows():
                try:
                    res = pe.analyze_single_prop(row['player'], row['stat'], float(row['line']), int(row['odds']), settings)
                    if res: results.append(res)
                except Exception as e:
                    st.warning(f"⚠️ {row['player']}: {e}")
            if results:
                df2 = pd.DataFrame(results)
                st.dataframe(df2, use_container_width=True)
                csv = df2.to_csv(index=False).encode('utf-8')
                st.download_button("💾 Download Results CSV", csv, "results.csv", use_container_width=True)

# ==========================================
# FOOTER (QacePicks Edition)
# ==========================================
st.markdown("""
<div class="footer">
  <strong>PropPulse+ v2025.6</strong> — Engineered & Curated by <strong style="color:#FF8C42;">QacePicks</strong><br>
  Data-Calibrated • Matchup-Weighted • Built for Professional Bettors<br><br>
  <em>⚠️ For entertainment and educational purposes only. Bet responsibly.</em>
</div>
""", unsafe_allow_html=True)
