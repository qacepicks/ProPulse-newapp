"""
PropPulse+ v2025.6 — Professional NBA Prop Analyzer
Mobile-Optimized UI | Blue–Red Theme | Responsive & Sidebar User-Controlled
"""

import os, io, base64
from datetime import datetime, timedelta
from contextlib import redirect_stdout

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ============
# Model import
# ============
try:
    import prop_ev as pe
except ImportError as e:
    st.error(f"❌ Failed to import prop_ev.py: {e}")
    st.stop()

# =============
# Page settings
# =============
st.set_page_config(
    page_title="PropPulse+ | NBA Props",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"   # user can open/close — we don't force it
)

# =========
# Logo util
# =========
def _logo_b64():
    path = "proppulse_logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = _logo_b64()
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" style="width:56px;height:56px;border-radius:12px;">'
    if logo_b64 else
    '<div class="brand-logo-fallback">PP</div>'
)

# ======================
# Global color variables
# ======================
# Primary = Blue, Accent = Red
PRIMARY = "#2563EB"     # blue-600
PRIMARY_DARK = "#1E40AF"
PRIMARY_LIGHT = "#60A5FA"
ACCENT = "#EF4444"      # red-500
ACCENT_DARK = "#B91C1C"
TEXT_PRIMARY = "#F9FAFB"
TEXT_SECONDARY = "#E5E7EB"
TEXT_MUTED = "#9CA3AF"
SURFACE = "#111827"     # gray-900
SURFACE_2 = "#1F2937"   # gray-800
BORDER = "#374151"      # gray-700

# =========
# Global CSS
# =========
st.markdown(
f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {{
  --primary:{PRIMARY};
  --primary-dark:{PRIMARY_DARK};
  --primary-light:{PRIMARY_LIGHT};
  --accent:{ACCENT};
  --accent-dark:{ACCENT_DARK};
  --bg:{SURFACE};
  --surface:{SURFACE_2};
  --text:{TEXT_PRIMARY};
  --text-2:{TEXT_SECONDARY};
  --muted:{TEXT_MUTED};
  --border:{BORDER};
}}

.stApp {{
  background: var(--bg);
  font-family: 'Inter', sans-serif;
  color: var(--text-2);
  overflow-x: hidden !important;
}}
#MainMenu, footer, header {{ visibility: hidden; }}

/* Sidebar (user can open/close; we only style it) */
[data-testid="stSidebar"] {{
  background: var(--surface);
  border-right: 2px solid var(--primary);
  overflow-y: auto;
}}
[data-testid="stSidebar"] * {{ color: var(--text-2) !important; }}
[data-testid="stSidebar"] label {{
  font-weight: 700; font-size: 12px; text-transform: uppercase;
  letter-spacing: 1px; margin-bottom: 6px;
}}

/* Header */
.main-header {{
  background: linear-gradient(135deg, var(--surface), var(--bg));
  border-bottom: 2px solid var(--primary);
  padding: 1.2rem 1rem; box-shadow: 0 8px 24px rgba(0,0,0,.4);
}}
.brand-container {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }}
.brand-logo-fallback {{
  width: 56px; height: 56px; background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 12px; display: flex; align-items: center; justify-content: center;
  font-weight: 900; font-size: 26px; color: white;
}}
.brand-title {{
  font-size: 28px; font-weight: 900;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.brand-subtitle {{ font-size: 13px; color: var(--muted); }}
.status-badge {{
  background: rgba(16, 185, 129, .12); border: 2px solid #10B981; color: #10B981;
  padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 700;
}}

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox select {{
  background: var(--surface); border: 2px solid var(--border);
  border-radius: 10px; color: var(--text); padding: 12px 14px; font-size: 15px;
}}
.stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {{
  border-color: var(--primary);
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.35);
  outline: none;
}}

/* Date input (dark themed) */
[data-testid="stDateInput"] input {{
  background-color: var(--surface) !important;
  border: 2px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
  padding: 10px 12px !important;
  font-size: 15px !important;
}}
[data-testid="stDateInput"] label {{
  font-weight: 700 !important; font-size: 12px !important; text-transform: uppercase !important;
  letter-spacing: 1px !important; margin-bottom: 6px !important; color: var(--text-2) !important;
}}
[data-testid="stDateInput"] input:hover, [data-testid="stDateInput"] input:focus {{
  border-color: var(--primary) !important;
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.35) !important;
  outline: none !important; transition: 0.25s ease-in-out !important;
}}

/* Buttons */
.stButton>button {{
  width: 100%;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 10px; padding: 14px 24px; font-weight: 800; text-transform: uppercase;
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
  color: white;
}}
.stButton>button:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(239, 68, 68, 0.45);
}}

/* Metric cards */
.metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 24px 0; }}
.metric-card {{
  background: var(--surface); border-radius: 12px; border: 1.5px solid var(--border);
  padding: 18px; transition: .3s;
}}
.metric-card:hover {{ border-color: var(--primary); transform: translateY(-3px); }}
.metric-value {{ font-size: 28px; font-weight: 900; color: var(--text); }}

/* EV badge strip */
.ev-container {{
  margin-top: 12px; background: linear-gradient(135deg, rgba(37,99,235,.08), rgba(239,68,68,.08));
  border: 1px solid var(--border); border-radius: 12px; padding: 16px;
}}
.ev-badge {{ display: inline-block; font-weight: 900; padding: 6px 10px; border-radius: 8px; margin-right: 10px; }}
.ev-positive {{ background: rgba(16, 185, 129, .15); color: #10B981; border: 1px solid #10B981; }}
.ev-negative {{ background: rgba(239, 68, 68, .15); color: var(--accent); border: 1px solid var(--accent); }}
.recommendation {{ display: inline-block; font-weight: 800; color: var(--text-2); }}

/* Footer */
.footer {{
  text-align:center; padding:30px 0; font-size:13px; color: var(--muted);
  border-top:1px solid var(--border); margin-top:40px;
}}
.footer strong {{ color: var(--primary) !important; }}

/* Mobile tweaks */
@media (max-width: 768px) {{
  .brand-title {{ font-size: 22px; }}
  .metric-grid {{ grid-template-columns: 1fr; }}
  .stAppViewContainer {{ padding: 0 .5rem !important; }}
  .stButton>button {{ font-size: 14px; padding: 12px 20px; }}
  .ev-container {{ padding: 16px; }}
}}
</style>
""",
    unsafe_allow_html=True
)

# ======
# Header
# ======
st.markdown(
    f"""
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
""",
    unsafe_allow_html=True,
)

# =================
# Sidebar (controls)
# =================
with st.sidebar:
    st.markdown("### ⚙️ Analysis Settings")
    st.markdown("---")

    mode = st.radio(
        "Select Analysis Mode",
        ["🎯 Single Prop Analysis", "📊 Batch Manual Entry", "📁 CSV Import"],
        index=0,
    )

    st.markdown("---")
    with st.expander("🔧 Advanced Settings"):
        debug_mode = st.checkbox("Enable Debug Mode", value=True)
        show_charts = st.checkbox("Show Visualizations", value=True)
        confidence_threshold = st.slider("Min Confidence", 0.0, 1.0, 0.5, 0.05)

    st.markdown("---")
    st.caption("**PropPulse+ v2025.6** — Blue–Red theme")
    st.caption("L20-Weighted Projection • FantasyPros DvP")
    st.caption("Built for Professional Bettors")

# =================================================
# Mode 1 — Single Prop (date picker moved into form)
# =================================================
if mode == "🎯 Single Prop Analysis":
    with st.form("prop_analyzer"):
        st.markdown("### 📋 Enter Prop Details")

        c1, c2 = st.columns([2, 1])
        player = c1.text_input("Player Name", placeholder="LeBron James")
        stat = c2.selectbox(
            "Stat Category",
            ["PTS", "REB", "AST", "REB+AST", "PRA", "P+R", "P+A", "FG3M"]
        )

        # Date picker INSIDE form
        cdate = st.columns([1])[0]
        analysis_date = cdate.date_input(
            "📅 Analysis Date",
            value=datetime.now(),
            min_value=datetime.now() - timedelta(days=7),
            max_value=datetime.now() + timedelta(days=7),
            help="Select the date for opponent/schedule lookup."
        )

        c3, c4 = st.columns(2)
        line = c3.number_input("Line", 0.0, 100.0, 25.5, 0.5)
        odds = c4.number_input("Odds (American)", value=-110, step=5)

        st.markdown("---")
        submitted = st.form_submit_button("🔍 ANALYZE PROP", use_container_width=True)

    if submitted:
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
                settings["analysis_date"] = analysis_date_str
                buf = io.StringIO()
                with redirect_stdout(buf):
                    result = pe.analyze_single_prop(
                        player, stat, float(line), int(odds),
                        settings=settings, debug_mode=debug_mode
                    )
                debug_text = buf.getvalue()
                if not result:
                    st.error("❌ Unable to analyze this prop.")
                    st.stop()
            except Exception as e:
                st.error(f"❌ Analysis Error: {e}")
                st.stop()

        # ----- Display
        p_model = result["p_model"]
        p_book = result["p_book"]
        ev = result["ev"]
        projection = result["projection"]
        n_games = result["n_games"]
        opponent = result.get("opponent", "N/A")
        position = result.get("position", "N/A")
        dvp_mult = result.get("dvp_mult", 1.0)
        confidence = result.get("confidence", 0.0)
        grade = result.get("grade", "N/A")

        edge = (p_model - p_book) * 100
        ev_cents = ev * 100
        recommendation = "OVER" if projection > line else "UNDER"

        st.success("✅ Analysis Complete!")

        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.markdown(f"<div class='metric-card'><div class='metric-value'>{projection:.1f}</div><div>Model Projection</div></div>", unsafe_allow_html=True)
        mc2.markdown(f"<div class='metric-card'><div class='metric-value'>{ev_cents:+.1f}¢</div><div>Expected Value</div></div>", unsafe_allow_html=True)
        mc3.markdown(f"<div class='metric-card'><div class='metric-value'>{edge:+.1f}%</div><div>Model Edge</div></div>", unsafe_allow_html=True)
        mc4.markdown(f"<div class='metric-card'><div class='metric-value'>{confidence:.2f}</div><div>Confidence</div></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        ev_class = "ev-positive" if ev > 0 else "ev-negative"
        rec_text = f"BET {recommendation}" if ev > 0 else "FADE THIS PROP"
        st.markdown(
            f"<div class='ev-container'><span class='ev-badge {ev_class}'>{ev_cents:+.1f}¢ EV</span>"
            f"<span class='recommendation'>{rec_text}</span></div>",
            unsafe_allow_html=True
        )

        cL, cR = st.columns(2)
        cL.markdown(f"**Model Prob:** {p_model*100:.1f}%  \n**Book Prob:** {p_book*100:.1f}%  \n**Line:** {line}  \n**Odds:** {odds}")
        cR.markdown(f"**Opponent:** {opponent}  \n**Position:** {position}  \n**DvP Multiplier:** {dvp_mult:.3f}  \n**Sample Size:** {n_games}")

        if show_charts:
            st.markdown("---")
            st.markdown("### 📈 Visual Analysis")
            g1, g2 = st.columns(2)
            with g1:
                fig = go.Figure(
                    data=[go.Bar(name='Model', x=['Model', 'Sportsbook'], y=[p_model*100, p_book*100])]
                )
                fig.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig2 = go.Figure(go.Indicator(
                    mode="gauge+number", value=ev_cents, title={'text': "EV (¢)"},
                    gauge={'axis': {'range': [-20, 20]}}
                ))
                fig2.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig2, use_container_width=True)

        if debug_mode and debug_text:
            with st.expander("🔧 Debug Log"):
                st.code(debug_text)

# =========================
# Mode 2 — Batch (manual)
# =========================
elif mode == "📊 Batch Manual Entry":
    st.markdown("### 📊 Batch Manual Entry")
    n_props = st.number_input("Number of props", 1, 20, 3)
    manual_entries = []
    for i in range(int(n_props)):
        c1, c2, c3, c4 = st.columns(4)
        p = c1.text_input("Player", key=f"player_{i}")
        s = c2.selectbox("Stat", ["PTS", "REB", "AST", "PRA", "FG3M"], key=f"stat_{i}")
        ln = c3.number_input("Line", 0.0, 100.0, 20.0, key=f"line_{i}")
        od = c4.text_input("Odds", "-110", key=f"odds_{i}")
        if p.strip():
            manual_entries.append({"player": p, "stat": s, "line": ln, "odds": od})

    if st.button("🚀 ANALYZE BATCH", use_container_width=True):
        if not manual_entries:
            st.error("⚠️ Please enter at least one valid player.")
            st.stop()
        settings = pe.load_settings()
        settings["analysis_date"] = datetime.now().strftime("%Y-%m-%d")  # batch defaults to today
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
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("💾 Download Results CSV", csv, "batch_results.csv", use_container_width=True)

# =====================
# Mode 3 — CSV Import
# =====================
else:
    st.markdown("### 📁 CSV Import")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df, use_container_width=True)
        if st.button("🚀 ANALYZE CSV DATA", use_container_width=True):
            settings = pe.load_settings()
            settings["analysis_date"] = datetime.now().strftime("%Y-%m-%d")
            results = []
            for _, row in df.iterrows():
                try:
                    res = pe.analyze_single_prop(row["player"], row["stat"], float(row["line"]), int(row["odds"]), settings)
                    if res: results.append(res)
                except Exception as e:
                    st.warning(f"⚠️ {row.get('player','(unknown)')}: {e}")
            if results:
                df2 = pd.DataFrame(results)
                st.dataframe(df2, use_container_width=True)
                csv = df2.to_csv(index=False).encode("utf-8")
                st.download_button("💾 Download Results CSV", csv, "results.csv", use_container_width=True)

# ======
# Footer
# ======
st.markdown(
    """
<div class="footer">
  <strong>PropPulse+ v2025.6</strong> — Engineered &amp; Curated by <strong style="color:#2563EB;">QacePicks</strong><br>
  Data-Calibrated • Matchup-Weighted • Built for Professional Bettors<br><br>
  <em>⚠️ For entertainment and educational purposes only. Bet responsibly.</em>
</div>
""",
    unsafe_allow_html=True,
)
