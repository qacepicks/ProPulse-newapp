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
# CUSTOM CSS (MOBILE FRIENDLY + FIXED)
# ==========================================
logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:56px;height:56px;border-radius:12px;">' if logo_b64 else '<div class="brand-logo-fallback">PP</div>'

st.markdown(
    f"""
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
    #MainMenu,footer,header {{visibility:hidden;}}

    /* Sidebar */
    [data-testid="stSidebar"] {{
      background:var(--surface-dark);
      border-right:2px solid var(--primary-color);
      overflow-y:auto;
    }}
    [data-testid="stSidebar"] * {{color:var(--text-secondary)!important;}}
    [data-testid="stSidebar"] label {{
      font-weight:700;font-size:12px;text-transform:uppercase;
      letter-spacing:1px;margin-bottom:6px;
    }}

    /* Mobile dropdown fix */
    @media (max-width:768px) {{
      [data-testid="stSidebar"] {{
        width:100vw!important;border-right:none!important;
        border-bottom:2px solid var(--primary-color)!important;
      }}
      [data-testid="stSidebar"] .stRadio>div {{
        display:flex!important;flex-direction:column!important;
        align-items:flex-start!important;gap:.5rem!important;
        overflow:visible!important;
      }}
      [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] input,
      [data-testid="stSidebar"] select {{
        visibility:visible!important;opacity:1!important;
        pointer-events:auto!important;
      }}
      [data-testid="stSidebar"] .stRadio {{
        z-index:99!important;position:relative!important;
      }}
    }}

    /* Header */
    .main-header {{
      background:linear-gradient(135deg,var(--surface-dark),var(--background-dark));
      border-bottom:2px solid var(--primary-color);
      padding:1.5rem 1rem;box-shadow:0 8px 24px rgba(0,0,0,.4);
    }}
    .brand-container {{
      display:flex;align-items:center;justify-content:space-between;
      gap:1rem;flex-wrap:wrap;
    }}
    .brand-logo-fallback {{
      width:56px;height:56px;
      background:linear-gradient(135deg,var(--primary-color),var(--primary-dark));
      border-radius:12px;display:flex;align-items:center;justify-content:center;
      font-weight:900;font-size:26px;color:white;
    }}
    .brand-title {{
      font-size:28px;font-weight:900;
      background:linear-gradient(135deg,var(--primary-color),var(--primary-light));
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    }}
    .brand-subtitle {{font-size:13px;color:var(--text-muted);}}
    .status-badge {{
      background:#065F46;border:2px solid var(--success);
      color:var(--success);padding:6px 12px;border-radius:8px;
      font-size:12px;font-weight:700;
    }}

    /* Inputs */
    .stTextInput input,.stNumberInput input,.stSelectbox select {{
      background:var(--surface-dark);
      border:2px solid var(--border-color);
      border-radius:10px;color:var(--text-primary);
      padding:12px 14px;font-size:15px;
    }}

    /* Dark theme fix for date input */
    [data-testid="stDateInput"] input {{
      background-color: var(--surface-dark) !important;
      border: 2px solid var(--border-color) !important;
      color: var(--text-primary) !important;
      border-radius: 10px !important;
      padding: 10px 12px !important;
      font-size: 15px !important;
    }}
    [data-testid="stDateInput"] label {{
      font-weight: 700 !important;font-size: 12px !important;
      text-transform: uppercase !important;letter-spacing: 1px !important;
      margin-bottom: 6px !important;color: var(--text-secondary) !important;
    }}
    [data-testid="stDateInput"] input:hover,
    [data-testid="stDateInput"] input:focus {{
      border-color: var(--primary-color) !important;
      box-shadow: 0 0 8px rgba(255, 140, 66, 0.4) !important;
      transition: 0.25s ease-in-out !important;
    }}
    .stDateInput [role="dialog"], .stDateInput [data-baseweb="calendar"] {{
      background-color: var(--surface-dark) !important;
      color: var(--text-primary) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 10px !important;
    }}
    .stDateInput [role="dialog"] * {{color: var(--text-primary) !important;}}

    /* Buttons */
    .stButton>button {{
      width:100%;background:linear-gradient(135deg,var(--primary-color),var(--primary-dark));
      border-radius:10px;padding:14px 24px;font-weight:800;text-transform:uppercase;
      box-shadow:0 6px 20px rgba(255,140,66,0.4);
    }}
    .stButton>button:hover {{
      transform:translateY(-2px);
      box-shadow:0 8px 28px rgba(255,140,66,0.6);
    }}

    /* Metric Cards */
    .metric-grid {{
      display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
      gap:16px;margin:24px 0;
    }}
    .metric-card {{
      background:var(--surface-dark);border-radius:12px;
      border:1.5px solid var(--border-color);
      padding:18px;transition:.3s;
    }}
    .metric-card:hover {{
      border-color:var(--primary-color);transform:translateY(-3px);
    }}
    .metric-value {{
      font-size:28px;font-weight:900;color:var(--text-primary);
    }}

    /* Footer */
    .footer {{
      text-align:center;padding:30px 0;font-size:13px;color:var(--text-muted);
      border-top:1px solid var(--border-color);margin-top:40px;
    }}
    .footer strong {{color:var(--primary-color)!important;}}

    /* Mobile Tweaks */
    @media(max-width:768px) {{
      .brand-title {{font-size:22px;}}
      .metric-grid {{grid-template-columns:1fr;}}
      .stAppViewContainer {{padding:0 .5rem!important;}}
      .stButton>button {{font-size:14px;padding:12px 20px;}}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

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
