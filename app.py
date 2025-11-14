#!/usr/bin/env python3
"""
PropPulse+ v2025.6 — Professional NBA Prop Analyzer
Mobile-Optimized Modern UI | Blue–Red Theme | Multi-Tab Interface
"""

import os
import io
import base64
from datetime import datetime, timedelta
from contextlib import redirect_stdout

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ===============================
# 🔗 Google Sheets config (Live EV Board)
# ===============================
SHEET_ID = "1SHuoEg331k_dcrgBoc7y8gWbgw1QTKHFJRzzNRqiOnE"
SHEET_GID = "1954146299"  # your main EV sheet tab
SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export"
    f"?format=csv&gid={SHEET_GID}"
)

# ===============================
# 🧠 Import model
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
# 🎨 GLOBAL STYLING (Blue–Red, Mobile-Friendly)
# ===============================
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --bg-main: #020617;
            --bg-surface: #020617;
            --bg-surface-alt: #020617;
            --accent-blue: #3b82f6;
            --accent-red: #ef4444;
            --accent-purple: #a855f7;
            --text-primary: #f9fafb;
            --text-muted: #9ca3af;
            --border-subtle: #1f2937;
        }

        .main {
            background: radial-gradient(circle at top, #0b1120 0, #020617 55%, #000000 100%);
            color: var(--text-primary);
        }

        /* Remove padding to make space feel tighter on mobile */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background: #020617;
            border-right: 1px solid var(--border-subtle);
        }

        section[data-testid="stSidebar"] .stButton button,
        section[data-testid="stSidebar"] .stSelectbox select,
        section[data-testid="stSidebar"] .stTextInput input,
        section[data-testid="stSidebar"] .stNumberInput input {
            border-radius: 10px;
        }

        /* Titles and headers */
        h1, h2, h3, h4 {
            color: var(--text-primary);
            letter-spacing: 0.03em;
        }

        .pulse-gradient {
            background: radial-gradient(circle at top left,
                rgba(59,130,246,0.35) 0,
                transparent 45%),
                        radial-gradient(circle at top right,
                rgba(239,68,68,0.35) 0,
                transparent 45%);
            border-radius: 18px;
            border: 1px solid rgba(148,163,184,0.25);
            padding: 1.25rem 1.5rem;
        }

        /* Core cards */
        .metric-card {
            background: rgba(15,23,42,0.95);
            border-radius: 16px;
            padding: 1rem 1.2rem;
            border: 1px solid rgba(148,163,184,0.35);
            box-shadow: 0 18px 45px rgba(15,23,42,0.65);
        }

        .metric-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--text-muted);
        }

        .metric-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .metric-sub {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        /* Inputs */
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox select {
            background: rgba(15,23,42,0.95) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 12px !important;
            color: var(--text-primary) !important;
            padding: 10px 12px !important;
            font-size: 0.95rem !important;
        }

        /* Buttons */
        .stButton button {
            border-radius: 999px !important;
            padding: 0.6rem 1.1rem !important;
            border: 1px solid rgba(148,163,184,0.4) !important;
        }

        .primary-btn button {
            background: linear-gradient(135deg, #3b82f6, #ef4444) !important;
            border: none !important;
            font-weight: 600 !important;
        }

        /* Tables */
        .stDataFrame, .stTable {
            border-radius: 14px;
            overflow: hidden;
        }

        /* Footer */
        .footer {
            margin-top: 2rem;
            padding-top: 1.25rem;
            border-top: 1px solid rgba(148,163,184,0.35);
            font-size: 0.8rem;
            color: var(--text-muted);
            text-align: center;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }

            h1 {
                font-size: 1.4rem;
            }

            h2 {
                font-size: 1.1rem;
            }

            .metric-card {
                padding: 0.85rem 0.9rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# ===============================
# 🖼️ LOGO HANDLING
# ===============================
def get_logo_base64():
    logo_path = "proppulse_logo.png"
    if not os.path.exists(logo_path):
        return None
    with open(logo_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_header():
    logo_b64 = get_logo_base64()

    with st.container():
        cols = st.columns([1, 4])
        with cols[0]:
            if logo_b64:
                st.markdown(
                    f"""
                    <img src="data:image/png;base64,{logo_b64}"
                         style="width:70px;height:auto;border-radius:14px;border:1px solid rgba(148,163,184,0.4);" />
                    """,
                    unsafe_allow_html=True,
                )
        with cols[1]:
            st.markdown(
                """
                <div class="pulse-gradient">
                    <div style="font-size:0.80rem;text-transform:uppercase;
                                color:#9ca3af;letter-spacing:0.16em;margin-bottom:0.3rem;">
                        PropPulse+ · NBA Player Prop Engine
                    </div>
                    <div style="display:flex;flex-wrap:wrap;align-items:baseline;gap:0.45rem;">
                        <span style="font-size:1.35rem;font-weight:720;">
                            Data-Calibrated Player Prop Analyzer
                        </span>
                        <span style="font-size:0.85rem;color:#9ca3af;">
                            L20-weighted trends · Matchup-weighted · EV driven
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ===============================
# 🧩 HELPERS FOR MODEL CALLS
# ===============================
def safe_load_settings():
    if hasattr(pe, "load_settings"):
        try:
            return pe.load_settings()
        except Exception as e:
            st.warning(f"⚠️ Could not load settings from prop_ev.py: {e}")
            return {}
    return {}


def run_single_prop(player, stat, line, odds, debug_mode=False):
    settings = safe_load_settings()
    try:
        # preferred API if present
        if hasattr(pe, "analyze_single_prop"):
            return pe.analyze_single_prop(
                player=player,
                stat=stat,
                line=line,
                odds=odds,
                settings=settings,
                debug_mode=debug_mode,
            )

        # fallback: CLI-style call if you had a main() that prints output
        buf = io.StringIO()
        with redirect_stdout(buf):
            if hasattr(pe, "main"):
                pe.main()
        return {"raw_output": buf.getvalue()}
    except Exception as e:
        st.error(f"❌ Error while running model: {e}")
        return None


def run_batch_from_df(df_input, debug_mode=False):
    settings = safe_load_settings()
    try:
        if hasattr(pe, "analyze_batch_df"):
            return pe.analyze_batch_df(df_input, settings=settings, debug_mode=debug_mode)
        elif hasattr(pe, "analyze_batch"):
            return pe.analyze_batch(df_input, settings=settings, debug_mode=debug_mode)
        else:
            st.warning("⚠️ Batch function not found in prop_ev.py. Expected analyze_batch_df or analyze_batch.")
            return None
    except Exception as e:
        st.error(f"❌ Error while running batch analysis: {e}")
        return None


# ===============================
# 📊 SINGLE PROP UI
# ===============================
def single_prop_view():
    render_header()
    st.markdown("### 🎯 Single Prop Analyzer")

    with st.container():
        c1, c2 = st.columns([1.2, 1])

        with c1:
            player = st.text_input("Player name", placeholder="e.g., Cade Cunningham")
            stat = st.selectbox(
                "Stat type",
                ["PTS", "REB", "AST", "PRA", "REB+AST", "PTS+REB", "PTS+AST", "FG3M"],
                index=0,
            )

            left, right = st.columns(2)
            with left:
                line = st.number_input("Line", min_value=0.0, step=0.5, format="%.1f")
            with right:
                odds = st.text_input("Odds (US)", value="-110", help="Enter like -110 or +100")

            debug_mode = st.checkbox("Enable debug mode", value=False)

        with c2:
            st.markdown("##### Quick notes")
            st.write(
                "Use L20-weighted form plus matchup context to see whether the line is soft or sharp. "
                "Model probabilities are calibrated toward realistic NBA distributions, not just raw hit rates."
            )
            st.caption("Tip: Alternate lines work too, just change the line number.")

    st.markdown("---")

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        run = st.button("🚀 Analyze Prop", type="primary", use_container_width=True)

    if not run:
        return

    if not player.strip():
        st.error("Please enter a valid player name.")
        return

    with st.spinner("Running PropPulse+ model…"):
        result = run_single_prop(player, stat, line, odds, debug_mode=debug_mode)

    if result is None:
        return

    # If it's the CLI fallback, just show raw output
    if "raw_output" in result:
        st.code(result["raw_output"], language="text")
        return

    # Normalize into DataFrame for flexibility
    if isinstance(result, dict):
        df_res = pd.DataFrame([result])
    elif isinstance(result, pd.DataFrame):
        df_res = result.copy()
    else:
        st.write(result)
        return

    # Extract key values defensively
    proj = df_res.get("Projection", pd.Series([None])).iloc[0]
    direction = df_res.get("Direction", pd.Series([""])).iloc[0]
    ev_cents = df_res.get("EV", df_res.get("EV¢", pd.Series([None]))).iloc[0]
    model_prob = df_res.get("Model Prob", df_res.get("Model_Prob", pd.Series([None]))).iloc[0]
    book_prob = df_res.get("Book Prob", df_res.get("Book_Prob", pd.Series([None]))).iloc[0]
    confidence = df_res.get("Confidence", pd.Series([None])).iloc[0]
    opponent = df_res.get("Opponent", pd.Series(["–"])).iloc[0]
    position = df_res.get("Position", pd.Series(["–"])).iloc[0]
    dvp_mult = df_res.get("DvP Mult", df_res.get("DvP_Mult", pd.Series([None]))).iloc[0]

    st.markdown("#### 📈 Model Snapshot")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Projection</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-value">{proj if proj is not None else "–"}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="metric-sub">Line {line:.1f} · {direction}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Expected Value</div>', unsafe_allow_html=True)
        ev_str = f"{ev_cents:+.1f}¢" if ev_cents is not None else "–"
        st.markdown(
            f'<div class="metric-value">{ev_str}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="metric-sub">Per $1 exposure</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with m3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Model vs Book</div>', unsafe_allow_html=True)
        if model_prob is not None and book_prob is not None:
            st.markdown(
                f'<div class="metric-value">{model_prob*100:.1f}%</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="metric-sub">Book implied: {book_prob*100:.1f}%</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="metric-value">–</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">No prob data</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with m4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Context</div>', unsafe_allow_html=True)
        conf_str = f"{confidence*100:.0f}%" if confidence is not None else "–"
        matchup_bits = []
        if opponent and opponent != "–":
            matchup_bits.append(f"vs {opponent}")
        if position and position != "–":
            matchup_bits.append(position)
        if dvp_mult is not None:
            matchup_bits.append(f"DvP {dvp_mult:.2f}×")
        sub_text = " · ".join(matchup_bits) if matchup_bits else "No matchup data"
        st.markdown(
            f'<div class="metric-value">{conf_str}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="metric-sub">{sub_text}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### 🔬 Full Result Row")
    st.dataframe(df_res, use_container_width=True)

    if "Distribution" in df_res.columns and isinstance(df_res["Distribution"].iloc[0], (list, tuple, np.ndarray)):
        try:
            dist_vals = np.array(df_res["Distribution"].iloc[0], dtype=float)
            x = np.arange(len(dist_vals))
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x, y=dist_vals))
            fig.update_layout(
                title="Model Distribution (simulated outcomes)",
                xaxis_title=stat,
                yaxis_title="Probability",
                bargap=0.02,
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass


# ===============================
# 📦 BATCH MODE UI
# ===============================
def init_manual_entries():
    if "manual_entries" not in st.session_state:
        st.session_state.manual_entries = []


def add_manual_entry(player, stat, line, odds):
    st.session_state.manual_entries.append(
        {"Player": player, "Stat": stat, "Line": line, "Odds": odds}
    )


def clear_manual_entries():
    st.session_state.manual_entries = []


def batch_mode_view():
    init_manual_entries()
    render_header()
    st.markdown("### 🧺 Batch Analyzer")

    mode = st.radio(
        "Batch input mode",
        ["Manual entry", "Upload CSV"],
        horizontal=True,
    )

    debug_mode = st.checkbox("Enable debug mode for batch", value=False)

    if mode == "Manual entry":
        st.markdown("#### ✏️ Add props manually")

        with st.form("manual_entry_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([1.7, 1, 0.8, 0.8])
            with c1:
                m_player = st.text_input("Player", key="batch_player")
            with c2:
                m_stat = st.selectbox(
                    "Stat",
                    ["PTS", "REB", "AST", "PRA", "REB+AST", "PTS+REB", "PTS+AST", "FG3M"],
                    key="batch_stat",
                )
            with c3:
                m_line = st.number_input("Line", key="batch_line", step=0.5, format="%.1f")
            with c4:
                m_odds = st.text_input("Odds", key="batch_odds", value="-110")

            s1, s2 = st.columns([1, 1])
            with s1:
                submitted = st.form_submit_button("➕ Add to slate", use_container_width=True)
            with s2:
                clear_clicked = st.form_submit_button("🧹 Clear all", use_container_width=True)

        if submitted:
            if not m_player.strip():
                st.error("Please enter a valid player name.")
            else:
                add_manual_entry(m_player, m_stat, m_line, m_odds)
                st.success(f"Added {m_player} {m_stat} {m_line} ({m_odds})")

        if clear_clicked:
            clear_manual_entries()
            st.success("Cleared all manual entries.")

        if st.session_state.manual_entries:
            df_preview = pd.DataFrame(st.session_state.manual_entries)
            st.markdown("#### 📋 Current slate")
            st.dataframe(df_preview, use_container_width=True)
        else:
            st.info("No props added yet. Use the form above to build your slate.")

        if st.button("🚀 Analyze batch", type="primary", use_container_width=True):
            if not st.session_state.manual_entries:
                st.error("Add at least one prop before running the batch.")
                return

            df_input = pd.DataFrame(st.session_state.manual_entries)
            with st.spinner("Running batch model…"):
                df_results = run_batch_from_df(df_input, debug_mode=debug_mode)

            if df_results is None:
                return

            if isinstance(df_results, dict):
                df_results = pd.DataFrame([df_results])

            st.markdown("#### 📊 Batch results")
            st.dataframe(df_results, use_container_width=True)

            if "EV" in df_results.columns or "EV¢" in df_results.columns:
                ev_col = "EV" if "EV" in df_results.columns else "EV¢"
                try:
                    df_sorted = df_results.sort_values(by=ev_col, ascending=False)
                    st.markdown("##### 🔝 Highest EV props")
                    st.dataframe(df_sorted.head(25), use_container_width=True)
                except Exception:
                    pass

            to_download = df_results.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download results as CSV",
                data=to_download,
                file_name=f"proppulse_batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    else:
        st.markdown("#### 📂 Upload CSV")

        st.caption(
            "Expected columns (case-insensitive): "
            "`Player`, `Stat`, `Line`, `Odds`."
        )

        file = st.file_uploader("Upload your slate CSV", type=["csv"])

        if file is not None:
            try:
                df_input = pd.read_csv(file)
            except Exception as e:
                st.error(f"Could not read CSV: {e}")
                return

            st.markdown("#### 📋 Preview")
            st.dataframe(df_input.head(50), use_container_width=True)

            if st.button("🚀 Analyze uploaded slate", type="primary", use_container_width=True):
                with st.spinner("Running batch model…"):
                    df_results = run_batch_from_df(df_input, debug_mode=debug_mode)

                if df_results is None:
                    return

                if isinstance(df_results, dict):
                    df_results = pd.DataFrame([df_results])

                st.markdown("#### 📊 Batch results")
                st.dataframe(df_results, use_container_width=True)

                if "EV" in df_results.columns or "EV¢" in df_results.columns:
                    ev_col = "EV" if "EV" in df_results.columns else "EV¢"
                    try:
                        df_sorted = df_results.sort_values(by=ev_col, ascending=False)
                        st.markdown("##### 🔝 Highest EV props")
                        st.dataframe(df_sorted.head(25), use_container_width=True)
                    except Exception:
                        pass

                to_download = df_results.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download results as CSV",
                    data=to_download,
                    file_name=f"proppulse_batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.info("Upload a CSV file to start batch analysis.")


# ===============================
# 📡 LIVE EV SHEET VIEWER
# ===============================
def live_sheet_view():
    render_header()
    st.markdown("### 📡 Live EV Board (Google Sheets)")

    st.caption(
        "This pulls directly from your live Google Sheet so visitors can see the current EV board "
        "without downloading a file."
    )

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("🔄 Refresh sheet", use_container_width=True):
            st.session_state["_refresh_sheet"] = datetime.now().timestamp()
    with c2:
        st.write("")

    try:
        df_sheet = pd.read_csv(SHEET_CSV_URL)
    except Exception as e:
        st.error(f"Could not load Google Sheet CSV: {e}")
        return

    if df_sheet.empty:
        st.warning("Sheet loaded, but appears to be empty.")
        return

    important_cols = [c for c in df_sheet.columns if c.lower() in
                      ["player", "stat", "line", "projection", "ev", "ev¢", "direction", "confidence"]]
    if important_cols:
        st.markdown("#### 🔝 Top EV snapshot")
        preview = df_sheet.copy()
        # try to sort by EV if present
        ev_col = None
        for candidate in ["EV¢", "EV", "ev", "ev¢"]:
            if candidate in preview.columns:
                ev_col = candidate
                break
        if ev_col:
            with pd.option_context("mode.use_inf_as_na", True):
                preview[ev_col] = (
                    preview[ev_col]
                    .astype(str)
                    .str.replace("+", "", regex=False)
                    .str.replace("¢", "", regex=False)
                )
                preview[ev_col] = pd.to_numeric(preview[ev_col], errors="coerce")
            preview = preview.sort_values(by=ev_col, ascending=False)

        st.dataframe(preview[important_cols].head(50), use_container_width=True)

    st.markdown("#### 🧾 Full sheet")
    st.dataframe(df_sheet, use_container_width=True)


# ===============================
# ℹ️ ABOUT VIEW
# ===============================
def about_view():
    render_header()
    st.markdown("### ℹ️ About PropPulse+")

    st.write(
        "PropPulse+ is your calibrated NBA player prop engine. It combines L20-weighted form, "
        "season-long context, defense-vs-position multipliers, and matchup-aware logic to surface "
        "edges instead of vibes. The goal is not just to chase hit rates, but to lean into spots "
        "where price, role, and matchup all align."
    )

    st.write(
        "This app is wired to your underlying Python model in `prop_ev.py`, which handles the heavy "
        "math for projections, distribution fitting, and expected value calculations. The front-end "
        "is tuned for mobile and desktop so you can scan slates, test single props, and review your "
        "live EV sheet from anywhere."
    )

    st.markdown("---")
    st.markdown(
        """
        <div class="footer">
            Built by <strong>QacePicks</strong> · Powered by <strong>PropPulse+</strong> · v2025.6<br/>
            Data-calibrated · Matchup-weighted · EV-first
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===============================
# 🧭 SIDEBAR NAVIGATION (USER CONTROLLED)
# ===============================
with st.sidebar:
    st.markdown("### 🏀 PropPulse+")
    st.caption("QacePicks · PropPulse+ v2025.6")

    nav = st.radio(
        "Navigation",
        ["Single Prop", "Batch Mode", "Live EV Sheet", "About"],
    )

    st.markdown("---")
    st.caption(
        "Tip: On mobile, you can swipe the sidebar open or closed using the Streamlit toggle "
        "to maximize screen space."
    )


# ===============================
# 🚀 ROUTER
# ===============================
if nav == "Single Prop":
    single_prop_view()
elif nav == "Batch Mode":
    batch_mode_view()
elif nav == "Live EV Sheet":
    live_sheet_view()
else:
    about_view()
