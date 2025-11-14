#!/usr/bin/env python3
"""
PropPulse+ v2025.6 — Professional NBA Prop Analyzer
Combined: Analysis Tools + Live Sheets Viewer
Mobile-Optimized UI | Blue–Red Theme | Projection Snapshot Visual
"""

import os
import io
import base64
import re
from datetime import datetime, timedelta, timezone
from contextlib import redirect_stdout

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ===============================
# 🔗 Google Sheets config (Live EV Board)
# ===============================
SHEET_ID = "1SHuoEg331k_dcrgBoc7y8gWbgw1QTKHFJRzzNRqiOnE"
SHEET_GID = "1954146299"
SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export"
    f"?format=csv&gid={SHEET_GID}"
)

# ===============================
# 🔧 Import Model
# ===============================
try:
    import prop_ev as pe
except ImportError as e:
    st.error(f"❌ Failed to import prop_ev.py: {e}")
    st.stop()

# ===============================
# ⚙️ PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PropPulse+ | NBA Props",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===============================
# 🎨 BRANDING — COLORS + CSS
# ===============================
st.markdown("""
<style>
:root {
    --pp-blue: #007bff;
    --pp-red:  #ff2d55;
    --pp-dark: #0c0c0f;
    --pp-card: #16171a;
    --pp-border: #2a2b2f;
    --pp-text: #e6e6e6;
}

html, body, [class*="css"]  {
    color: var(--pp-text) !important;
    background-color: var(--pp-dark) !important;
}

/* Cards */
.pp-card {
    background-color: var(--pp-card);
    padding: 18px;
    border-radius: 14px;
    border: 1px solid var(--pp-border);
}

/* Buttons */
.stButton button {
    background: linear-gradient(90deg, var(--pp-blue), var(--pp-red)) !important;
    border: 0px;
    color: white !important;
    padding: 0.7rem 1.2rem;
    border-radius: 10px;
    font-weight: 600;
}

/* Inputs */
.stTextInput input,
.stNumberInput input,
.stSelectbox select {
    background: var(--pp-card);
    border: 2px solid var(--pp-border);
    border-radius: 10px;
    color: var(--pp-text);
}

/* Footer */
#footer-note {
    text-align: center;
    font-size: 14px;
    margin-top: 40px;
    padding: 12px 0px;
    color: #888;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 🏀 LOGO (if present)
# ===============================
def get_logo_base64():
    logo_path = "proppulse_logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()
if logo_b64:
    st.markdown(
        f'<img src="data:image/png;base64,{logo_b64}" width="140">',
        unsafe_allow_html=True
    )

st.markdown("## **PropPulse+ NBA Prop Analyzer**")
# ===============================
# 📌 SIDEBAR — User Controls
# ===============================
with st.sidebar:
    st.markdown("### ⚙️ PropPulse+ Controls")
    st.markdown("---")

    mode = st.radio(
        "Select Mode",
        ["Single Prop Analyzer", "Batch Analyzer", "Live EV Sheet Viewer"],
        index=0
    )

    st.markdown("---")
    st.markdown("📅 **Date:** Today’s slate auto-detected")
    st.markdown("---")

    st.markdown("""
    <div style='text-align:center;color:#888;font-size:13px;margin-top:40px;'>
        PropPulse+ v2025.6<br>
        Blue-Red Theme · Mobile Optimized
    </div>
    """, unsafe_allow_html=True)

# ===============================
# 🧩 MAIN LAYOUT
# ===============================
st.markdown("")

# Helper: Clean line formatting
def clean_float(value):
    try:
        return float(value)
    except:
        return None

# ===============================
# 🎯 PROJECTION SNAPSHOT — UI Block
# ===============================
def render_projection_snapshot(result):
    """Pretty, mobile-friendly projection visual"""
    if result is None:
        return

    proj = result.get("projection")
    line = result.get("line")
    ev  = result.get("EV¢")
    conf = result.get("confidence")
    opp = result.get("opponent")
    dvp = result.get("dvp_mult")

    st.markdown("### 📈 Model Snapshot")
    container = st.container()
    with container:
        c1, c2, c3 = st.columns(3)

        c1.metric("Projection", f"{proj:.2f}" if proj is not None else "—")
        c2.metric("Line", line)
        c3.metric("EV (¢)", ev)

        st.markdown("")

        st.markdown(
            f"""
            <div class="pp-card">
                <b>Opponent:</b> {opp or "—"}<br>
                <b>DvP Multiplier:</b> {dvp or "—"}<br>
                <b>Confidence Score:</b> {conf or "—"}
            </div>
            """,
            unsafe_allow_html=True
        )
# ==========================================================
# 🔍 SINGLE PROP ANALYZER
# ==========================================================
if mode == "Single Prop Analyzer":
    st.markdown("## 🔍 Single Prop Analyzer")

    # Input form layout
    with st.form("single_form"):
        col1, col2, col3, col4 = st.columns(4)

        player_name = col1.text_input("Player Name")
        stat = col2.selectbox(
            "Stat",
            ["PTS", "REB", "AST", "PRA", "REB+AST", "PTS+REB", "PTS+AST", "FG3M"]
        )
        line = col3.text_input("Line (e.g., 7.5)")
        odds = col4.text_input("Odds (e.g., -110)", "-110")

        debug = st.checkbox("Enable Debug Mode", value=False)

        submitted = st.form_submit_button("🚀 RUN ANALYSIS")

    if submitted:
        if not player_name or not line:
            st.error("⚠️ Please provide both a player name and a line.")
            st.stop()

        settings = pe.load_settings()
        line_val = clean_float(line)

        with st.spinner("🧠 Running full PropPulse+ model…"):
            try:
                result = pe.analyze_single_prop(
                    player=player_name,
                    stat=stat,
                    line=line_val,
                    odds=odds,
                    settings=settings,
                    debug_mode=debug,
                )
            except Exception as e:
                st.error(f"❌ Error while analyzing: {e}")
                st.stop()

        if result:
            render_projection_snapshot(result)
            st.markdown("### 📤 Full Output")
            st.json(result)
        else:
            st.warning("⚠️ No data returned for this player.")
# ==========================================================
# 📦 BATCH ANALYZER
# ==========================================================
if mode == "Batch Analyzer":
    st.markdown("## 📦 Batch Analyzer")

    st.info("Enter multiple props and analyze them all at once.")

    manual_entries = []

    with st.form("batch_form"):
        st.markdown("### ✏️ Enter Props")

        num_rows = st.number_input(
            "Number of props to enter",
            min_value=1, max_value=150, value=5, step=1
        )

        for i in range(num_rows):
            c1, c2, c3, c4 = st.columns(4)
            p = c1.text_input(f"Player {i+1}")
            s = c2.selectbox(
                f"Stat {i+1}",
                ["PTS", "REB", "AST", "PRA", "REB+AST", "PTS+REB", "PTS+AST", "FG3M"],
                key=f"stat_{i}"
            )
            l = c3.text_input(f"Line {i+1}")
            o = c4.text_input(f"Odds {i+1}", "-110")

            if p and l:
                manual_entries.append({
                    "Player": p,
                    "Stat": s,
                    "Line": l,
                    "Odds": o
                })

        submitted = st.form_submit_button("🚀 ANALYZE BATCH")

    if manual_entries:
        df_preview = pd.DataFrame(manual_entries)
        st.subheader("📋 Preview")
        st.dataframe(df_preview, use_container_width=True)

        if submitted:
            st.markdown("### 📊 Batch Results")
            settings = pe.load_settings()
            results = []

            with st.spinner("🧠 Running batch analysis…"):
                for entry in manual_entries:
                    try:
                        res = pe.analyze_single_prop(
                            player=entry["Player"],
                            stat=entry["Stat"],
                            line=clean_float(entry["Line"]),
                            odds=entry["Odds"],
                            settings=settings,
                            debug_mode=False,
                        )
                        if res:
                            results.append(res)
                    except Exception as e:
                        st.error(f"Error analyzing {entry['Player']}: {e}")

            if results:
                df_results = pd.DataFrame(results)
                st.dataframe(df_results, use_container_width=True)
            else:
                st.warning("⚠️ No results produced.")
    else:
        st.info("✏️ Add props above, then click ANALYZE BATCH.")
# ==========================================================
# 📡 LIVE EV SHEET VIEWER
# ==========================================================
if mode == "Live EV Sheet Viewer":
    st.markdown("## 📡 Live EV Sheet Viewer")

    st.info("This pulls directly from your Google Sheets EV board.")

    @st.cache_data(ttl=300)
    def load_live_sheet():
        try:
            df = pd.read_csv(SHEET_CSV_URL)
            return df
        except Exception as e:
            st.error(f"❌ Error loading Google Sheet: {e}")
            return None

    with st.spinner("🔄 Loading live EV board…"):
        df_sheet = load_live_sheet()

    if df_sheet is not None:
        st.success("✅ Live sheet loaded")
        st.dataframe(df_sheet, use_container_width=True)

        # Optional: simple filters for mobile usability
        st.markdown("### 🔍 Quick Filter")
        cols = df_sheet.columns.tolist()
        col_to_filter = st.selectbox("Column", cols)
        filter_val = st.text_input("Search")

        if filter_val:
            df_filtered = df_sheet[df_sheet[col_to_filter].astype(str).str.contains(filter_val, case=False)]
            st.dataframe(df_filtered, use_container_width=True)
# ==========================================================
# 🛠️ UTILITY FUNCTIONS
# ==========================================================

def convert_df_to_csv(df: pd.DataFrame):
    """Convert a dataframe to CSV bytes for download"""
    return df.to_csv(index=False).encode("utf-8")


def render_download_button(df, label="📥 Download CSV", file_name="proppulse_export.csv"):
    """Generic CSV download button"""
    if df is None or df.empty:
        return

    csv_bytes = convert_df_to_csv(df)

    st.download_button(
        label=label,
        data=csv_bytes,
        file_name=file_name,
        mime="text/csv",
        use_container_width=True
    )


# ==========================================================
# 📉 CUSTOM PROJECTION VISUAL — GAIN/LOSS BAR
# ==========================================================

def render_projection_bar(projection, line):
    """Draws a simple horizontal line showing projection vs line"""

    if projection is None or line is None:
        st.info("No projection available.")
        return

    diff = projection - line

    color = "#007bff" if diff >= 0 else "#ff2d55"
    label = "Projected ↑" if diff >= 0 else "Projected ↓"

    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=projection,
            delta={"reference": line, "relative": False},
            number={"font": {"size": 38}},
            title={"text": f"<b>{label}</b><br><span style='font-size:16px'>Line = {line}</span>"}
        )
    )

    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=20, b=0),
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)
# ==========================================================
# 📱 MOBILE OPTIMIZATION — FIXES FOR SMALL SCREENS
# ==========================================================

st.markdown("""
<style>
/* Make inputs full width on mobile */
@media (max-width: 768px) {
    .stTextInput, .stNumberInput, .stSelectbox, .stButton {
        width: 100% !important;
    }

    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Force columns to stack vertically */
    [data-testid="column"] {
        display: block !important;
        width: 100% !important;
    }

    /* Fix dropdown cutoff issue */
    .stSelectbox > div {
        overflow: visible !important;
    }
}
</style>
""", unsafe_allow_html=True)


# ==========================================================
# 🧾 FOOTER — PROPULSE BRANDING
# ==========================================================

st.markdown("""
<div id="footer-note">
    Built with ❤️ by <b>QacePicks</b><br>
    Powered by PropPulse+ · Data-Driven NBA Betting Tools
</div>
""", unsafe_allow_html=True)
# ==========================================================
# 🧩 END OF MAIN APP LOGIC
# ==========================================================

def safe_run():
    """Wrapper to prevent Streamlit from crashing silently."""
    try:
        pass  # All logic is executed above directly in the layout
    except Exception as e:
        st.error(f"Unexpected error in app: {e}")


if __name__ == "__main__":
    safe_run()
