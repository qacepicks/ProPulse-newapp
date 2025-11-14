#!/usr/bin/env python3
"""
PropPulse+ v2025.6 — Professional NBA Prop Analyzer
Mobile-Optimized Modern UI | Blue–Red Theme | Icon Tab Navigation
"""

import os
import io
import base64
from datetime import datetime
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
    initial_sidebar_state="collapsed",
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

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* Centered icon tabs */
        .stTabs [data-baseweb="tab-list"] {
            justify-content: center;
            gap: 0.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px !important;
            padding: 0.3rem 0.9rem !important;
            background: rgba(15,23,42,0.9);
            border: 1px solid rgba(148,163,184,0.35);
            font-size: 0.9rem;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3b82f6, #ef4444) !important;
            border: none !important;
            color: #f9fafb !important;
        }

        /* Sidebar styling (minimal) */
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

        h1, h2, h3, h4 {
            color: var(--text-primary);
            letter-spacing: 0.03em;
        }

        .pulse-gradient {
            background: radial-gradient(circle at top left,
                rgba(59,130,246,0.30) 0,
                transparent 45%),
                radial-gradient(circle at top right,
                rgba(239,68,68,0.30) 0,
                transparent 45%);
            border-radius: 18px;
            border: 1px solid rgba(148,163,184,0.25);
            padding: 1.1rem 1.4rem;
            box-shadow: 0 18px 40px rgba(15,23,42,0.8);
        }

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

        .stDataFrame, .stTable {
            border-radius: 14px;
            overflow: hidden;
        }

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
                padding-left: 0.7rem;
                padding-right: 0.7rem;
            }
            h1 {
                font-size: 1.35rem;
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
                         style="width:70px;height:auto;border-radius:14px;
                                border:1px solid rgba(148,163,184,0.4);" />
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
                            Data-Driven Player Prop Analyzer
                        </span>
                        <span style="font-size:0.85rem;color:#9ca3af;">
                            Calibrated projections · Matchup signals · True EV detection
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


def run_single_prop(player, stat, line, odds, debug_mode=True):
    settings = safe_load_settings()
    try:
        if hasattr(pe, "analyze_single_prop"):
            return pe.analyze_single_prop(
                player=player,
                stat=stat,
                line=line,
                odds=odds,
                settings=settings,
                debug_mode=debug_mode,
            )

        # Fallback: CLI-style if model only prints
        buf = io.StringIO()
        with redirect_stdout(buf):
            if hasattr(pe, "main"):
                pe.main()
        return {"raw_output": buf.getvalue()}
    except Exception as e:
        st.error(f"❌ Error while running model: {e}")
        return None


def run_batch_from_df(df_input, debug_mode=True):
    settings = safe_load_settings()
    try:
        # Preferred: dedicated batch helper in prop_ev
        if hasattr(pe, "batch_analyze_props"):
            # Normalize column names
            cols_lower = {c.lower(): c for c in df_input.columns}
            props_list = []
            for _, row in df_input.iterrows():
                def get_val(*names, default=None):
                    for n in names:
                        c = cols_lower.get(n.lower())
                        if c and c in row and pd.notna(row[c]):
                            return row[c]
                    return default

                player = get_val("player")
                stat = get_val("stat")
                line = get_val("line")
                odds = get_val("odds")

                if not player or not stat or line is None or odds is None:
                    continue

                props_list.append(
                    {
                        "player": str(player),
                        "stat": str(stat),
                        "line": float(line),
                        "odds": str(odds),
                    }
                )

            if not props_list:
                st.error("No valid props found in input.")
                return None

            return pe.batch_analyze_props(props_list, settings)

        # Secondary: analyze_batch_df if your model provides it
        if hasattr(pe, "analyze_batch_df"):
            return pe.analyze_batch_df(df_input, settings=settings, debug_mode=debug_mode)

        # Legacy fallback: analyze_batch
        if hasattr(pe, "analyze_batch"):
            return pe.analyze_batch(df_input, settings=settings, debug_mode=debug_mode)

        st.warning("⚠️ Batch function not found in prop_ev.py (expected batch_analyze_props / analyze_batch_df / analyze_batch).")
        return None
    except Exception as e:
        st.error(f"❌ Error while running batch analysis: {e}")
        return None

# ===============================
# 📊 SINGLE PROP UI
# ===============================
def single_prop_view():
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

            debug_mode = st.checkbox("Enable debug mode", value=True)

        with c2:
            st.markdown("##### Quick notes")
            st.write(
                "The model blends recent form, matchup context, and calibrated probability logic to highlight "
                "where a number may be mispriced. Probabilities are tuned toward realistic NBA scoring "
                "distributions rather than simple hit-rate chasing."
            )
            st.caption("Tip: Alternate lines are supported — adjust the line to see how the edge moves.")

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

    # Normalize into DataFrame
    if isinstance(result, dict):
        df_res = pd.DataFrame([result])
    elif isinstance(result, pd.DataFrame):
        df_res = result.copy()
    else:
        st.write(result)
        return

    # Extract keys defensively based on prop_ev.py’s schema
    def get_first(df, *names, default=None):
        for n in names:
            if n in df.columns:
                val = df[n].iloc[0]
                return val
        return default

    proj = get_first(df_res, "projection", "Projection")
    direction = get_first(df_res, "direction", "Direction", default="")
    ev_cents = get_first(df_res, "EV¢", "EVc", "EV", default=None)
    if ev_cents is None:
        ev_float = get_first(df_res, "ev", "EV", default=None)
        ev_cents = ev_float * 100 if ev_float is not None else None

    model_prob = get_first(df_res, "p_model", "Model Prob", "Model_Prob")
    book_prob = get_first(df_res, "p_book", "Book Prob", "Book_Prob")
    confidence = get_first(df_res, "confidence", "Confidence")
    opponent = get_first(df_res, "opponent", "Opponent", default="–")
    position = get_first(df_res, "position", "Position", default="–")
    dvp_mult = get_first(df_res, "dvp_mult", "DvP Mult", "DvP_Mult")

    st.markdown("#### 📈 Model Snapshot")

    m1, m2, m3, m4 = st.columns(4)

    # Projection card
    with m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Projection</div>', unsafe_allow_html=True)
        proj_str = f"{proj:.2f}" if proj is not None else "–"
        st.markdown(
            f'<div class="metric-value">{proj_str}</div>',
            unsafe_allow_html=True,
        )
        dir_text = direction if direction else "No lean"
        st.markdown(
            f'<div class="metric-sub">Line {line:.1f} · {dir_text}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # EV card
    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Expected Value</div>', unsafe_allow_html=True)
        ev_str = f"{ev_cents:+.1f}¢" if ev_cents is not None else "–"
        st.markdown(
            f'<div class="metric-value">{ev_str}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="metric-sub">Per $1 stake</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Model vs Book
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
        st.markdown("</div>", unsafe_allow_html=True)

    # Context card
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
            try:
                matchup_bits.append(f"DvP {float(dvp_mult):.2f}×")
            except Exception:
                pass
        sub_text = " · ".join(matchup_bits) if matchup_bits else "No matchup data"
        st.markdown(
            f'<div class="metric-value">{conf_str}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="metric-sub">{sub_text}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### 🔬 Full Result Row")
    st.dataframe(df_res, use_container_width=True)

    # Optional distribution if your model ever adds it
    if "Distribution" in df_res.columns and isinstance(
        df_res["Distribution"].iloc[0], (list, tuple, np.ndarray)
    ):
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
    st.markdown("### 🧺 Batch Analyzer")

    mode = st.radio(
        "Batch input mode",
        ["Manual entry", "Upload CSV"],
        horizontal=True,
    )

    debug_mode = st.checkbox("Enable debug mode for batch", value=True)

    # ---------- Manual entry ----------
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
            elif isinstance(df_results, list):
                df_results = pd.DataFrame(df_results)

            st.markdown("#### 📊 Batch results")
            st.dataframe(df_results, use_container_width=True)

            # Try to sort by EV
            ev_col = None
            for cand in ["EV¢", "EV", "ev"]:
                if cand in df_results.columns:
                    ev_col = cand
                    break

            if ev_col:
                df_sort = df_results.copy()
                with pd.option_context("mode.use_inf_as_na", True):
                    df_sort[ev_col] = (
                        df_sort[ev_col]
                        .astype(str)
                        .str.replace("+", "", regex=False)
                        .str.replace("¢", "", regex=False)
                    )
                    df_sort[ev_col] = pd.to_numeric(df_sort[ev_col], errors="coerce")

                try:
                    df_sort = df_sort.sort_values(by=ev_col, ascending=False)
                    st.markdown("##### 🔝 Highest EV props")
                    st.dataframe(df_sort.head(25), use_container_width=True)
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

    # ---------- CSV upload ----------
    else:
        st.markdown("#### 📂 Upload CSV")
        st.caption(
            "Expected columns (case-insensitive): `Player`, `Stat`, `Line`, `Odds`."
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
                elif isinstance(df_results, list):
                    df_results = pd.DataFrame(df_results)

                st.markdown("#### 📊 Batch results")
                st.dataframe(df_results, use_container_width=True)

                ev_col = None
                for cand in ["EV¢", "EV", "ev"]:
                    if cand in df_results.columns:
                        ev_col = cand
                        break

                if ev_col:
                    df_sort = df_results.copy()
                    with pd.option_context("mode.use_inf_as_na", True):
                        df_sort[ev_col] = (
                            df_sort[ev_col]
                            .astype(str)
                            .str.replace("+", "", regex=False)
                            .str.replace("¢", "", regex=False)
                        )
                        df_sort[ev_col] = pd.to_numeric(df_sort[ev_col], errors="coerce")

                    try:
                        df_sort = df_sort.sort_values(by=ev_col, ascending=False)
                        st.markdown("##### 🔝 Highest EV props")
                        st.dataframe(df_sort.head(25), use_container_width=True)
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
    st.markdown("### 📡 Live EV Board (Google Sheets)")

    st.caption(
        "Pulls directly from your live Google Sheet so visitors can see the current EV board "
        "without downloading files."
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

    important_cols = [
        c for c in df_sheet.columns
        if c.lower() in ["player", "stat", "line", "projection", "ev", "ev¢", "direction", "confidence"]
    ]

    if important_cols:
        st.markdown("#### 🔝 Top EV snapshot")
        preview = df_sheet.copy()
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
    st.markdown("### ℹ️ About PropPulse+")

    st.write(
        "PropPulse+ is a calibrated NBA player prop engine built to surface edges, not vibes. "
        "It blends recent form, season-long context, defense-vs-position signals, and matchup-aware logic "
        "to help identify where a line may be mispriced."
    )

    st.write(
        "Under the hood, the `prop_ev.py` model handles projections, distribution shaping, and expected value "
        "calculations. This front-end is tuned for both mobile and desktop so you can scan slates, test single "
        "props, and review your live EV board from anywhere."
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
# 🧭 OPTIONAL SIDEBAR (MINIMAL)
# ===============================
with st.sidebar:
    st.markdown("### 🏀 PropPulse+")
    st.caption("QacePicks · PropPulse+ v2025.6")
    st.markdown("---")
    st.caption("Use the main tabs above the content to switch between tools.")

# ===============================
# 🚀 MAIN LAYOUT — HEADER + ICON TABS
# ===============================
render_header()

tab_single, tab_batch, tab_live, tab_about = st.tabs(
    ["🎯 Single Prop", "🧺 Batch Mode", "📡 Live EV Sheet", "ℹ️ About"]
)

with tab_single:
    single_prop_view()

with tab_batch:
    batch_mode_view()

with tab_live:
    live_sheet_view()

with tab_about:
    about_view()
