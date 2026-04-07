"""
app_v2.py — NSE EOD Dashboard · Bullseye Fintech © 2024–2026
Theme: Light / Pastel — all surfaces, plots, tables, and chrome are light.
Fonts: Sora (headings/UI) + JetBrains Mono (numbers/data)
"""
import os
import time
import threading
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from EoD_module import (
    AUTO_UPDATE_DEFAULT,
    DATA_DIR,
    Col,
    compute_pivot_points,
    delete_year_data,
    download_year_data,
    eod_csv_path,
    get_available_years,
    get_eod_csv_bytes,
    get_pivot_csv_bytes,
    pivot_csv_path,
    run_auto_update,
)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Bullseye Fintech — NSE EOD",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════
# CSS — Light / Pastel Theme (UPGRADED FONT SIZES & CLEANER PIVOT EDITOR)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ═══════════════════════════════════════════════════════════════════════════
   BASE RESET
   ═══════════════════════════════════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family : 'Sora', sans-serif !important;
    color: #1e2035 !important;
    background-color: #f4f5f9 !important;
    font-size: 16px !important;
}
.stApp { background-color: #f4f5f9 !important; font-size: 16px !important; }

/* Force ALL text dark unless a component-specific rule overrides it */
p, span, label, div, li, h1, h2, h3, h4, h5, h6,
strong, em, small, code, pre, blockquote {
    color: #1e2035 !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {
    background-color: #eef0f8 !important;
    border-right: 1px solid #d4d7e8 !important;
    font-size: 1rem !important;
}
[data-testid="stSidebar"] * { color: #1e2035 !important; }
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #3949ab !important;
    font-size: 1.1rem !important; font-weight: 600;
    letter-spacing: 0.10em; text-transform: uppercase;
    margin-top: 1.2rem; margin-bottom: 0.3rem;
    border-bottom: 1px solid #c5cae9; padding-bottom: 4px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ALL WIDGET LABELS
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stDateInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label,
[data-testid="stToggle"] label,
[data-testid="stSlider"] label,
[data-testid="stTextInput"] label {
    color: #5e6180 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SELECT / MULTISELECT  — control face + dropdown overlay
   ═══════════════════════════════════════════════════════════════════════════ */
[data-baseweb="select"],
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div,
[data-baseweb="select"] input {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e2035 !important;
    border-color: #c5cae9 !important;
    font-size: 1.05rem !important;
}
[data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"],
[data-baseweb="select"] span {
    color: #1e2035 !important;
    font-size: 1.05rem !important;
}
[data-baseweb="select"] svg { fill: #5e6180 !important; }

[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] ul,
[data-baseweb="menu"],
[data-baseweb="menu"] ul {
    background-color: #ffffff !important;
    background: #ffffff !important;
    border: 1px solid #c5cae9 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 16px rgba(57,73,171,0.10) !important;
}
[data-baseweb="menu"] li,
[data-baseweb="menu"] [role="option"],
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"] {
    background-color: #ffffff !important;
    color: #1e2035 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 1.05rem !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] [role="option"]:hover {
    background-color: #e8eaf6 !important;
    color: #3949ab !important;
}
[data-baseweb="menu"] [aria-selected="true"],
[data-baseweb="popover"] [aria-selected="true"] {
    background-color: #e8eaf6 !important;
    color: #3949ab !important;
}
[data-baseweb="tag"] {
    background-color: #e8eaf6 !important;
    border-color: #c5cae9 !important;
    color: #3949ab !important;
    font-size: 0.95rem !important;
}
[data-baseweb="tag"] span { color: #3949ab !important; }
[data-baseweb="tag"] svg  { fill: #3949ab !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   DATE INPUT — control face + calendar popover
   ═══════════════════════════════════════════════════════════════════════════ */
[data-baseweb="input"],
[data-baseweb="input"] > div,
[data-baseweb="input"] input,
[data-testid="stDateInput"] input,
[data-testid="stDateInput"] > div > div {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e2035 !important;
    border-color: #c5cae9 !important;
    font-size: 1.05rem !important;
}
[data-baseweb="calendar"],
[data-baseweb="datepicker"],
[data-baseweb="calendar"] > div,
[data-baseweb="datepicker"] > div {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e2035 !important;
    border: 1px solid #c5cae9 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 20px rgba(57,73,171,0.12) !important;
}
[data-baseweb="calendar"] [role="heading"],
[data-baseweb="calendar"] button[aria-label],
[data-baseweb="calendar"] [data-baseweb="typography"],
[data-baseweb="calendar"] span,
[data-baseweb="calendar"] div {
    background-color: transparent !important;
    color: #1e2035 !important;
}
[data-baseweb="calendar"] button {
    background-color: #eef0f8 !important;
    color: #3949ab !important;
    border-radius: 6px !important;
    border: none !important;
}
[data-baseweb="calendar"] button:hover {
    background-color: #c5cae9 !important;
}
[data-baseweb="calendar"] [role="gridcell"] div,
[data-baseweb="calendar"] [role="gridcell"] button {
    color: #1e2035 !important;
    background-color: transparent !important;
    border-radius: 6px !important;
}
[data-baseweb="calendar"] [aria-current="date"] div,
[data-baseweb="calendar"] [data-today="true"] div {
    border: 1.5px solid #3949ab !important;
    color: #3949ab !important;
}
[data-baseweb="calendar"] [aria-selected="true"] div,
[data-baseweb="calendar"] [data-selected="true"] div {
    background-color: #3949ab !important;
    color: #ffffff !important;
}
[data-baseweb="calendar"] [role="columnheader"] div {
    color: #5e6180 !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   NUMBER INPUT — stepper +/- buttons
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stNumberInput"] {
    position: relative;
}
[data-testid="stNumberInput"] input {
    background: #ffffff !important;
    color: #1e2035 !important;
    border-color: #c5cae9 !important;
    border-width: 1.5px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    padding: 8px 48px 8px 10px !important;
    min-height: 42px !important;
}
[data-testid="stNumberInput"] > div > div:last-child,
[data-testid="stNumberInput"] [data-baseweb="button"],
[data-testid="stNumberInput"] button {
    background-color: #e8eaf6 !important;
    background: #e8eaf6 !important;
    color: #3949ab !important;
    border: 1px solid #c5cae9 !important;
    border-radius: 6px !important;
}
[data-testid="stNumberInput"] button:hover {
    background-color: #c5cae9 !important;
}
[data-testid="stNumberInput"] button svg,
[data-testid="stNumberInput"] button span {
    color: #3949ab !important;
    fill: #3949ab !important;
}

.pivot-edit-grid [data-testid="stNumberInput"] input {
    font-size: 1.0rem !important;
    font-weight: 700 !important;
    text-align: right !important;
}
.pivot-edit-grid [data-testid="stNumberInput"] label,
.pivot-edit-grid [data-testid="stTextInput"] label {
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    text-align: center !important;
    display: block !important;
}
[data-testid="stExpander"] [data-testid="stTextInput"] input {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.0rem !important;
    font-weight: 600 !important;
    text-align: right !important;
    background: #ffffff !important;
    color: #1e2035 !important;
    border-color: #c5cae9 !important;
    border-width: 1.5px !important;
    min-height: 40px !important;
    padding: 6px 12px !important;
}
.pivot-edit-res [data-testid="stTextInput"] input { border-left: 4px solid #e53935 !important; }
.pivot-edit-pp  [data-testid="stTextInput"] input { border-left: 4px solid #e65100 !important; background: #fffde7 !important; }
.pivot-edit-sup [data-testid="stTextInput"] input { border-left: 4px solid #43a047 !important; }
.pivot-edit-res [data-testid="stNumberInput"] input { border-left: 4px solid #e53935 !important; }
.pivot-edit-pp  [data-testid="stNumberInput"] input { border-left: 4px solid #e65100 !important; background: #fffde7 !important; }
.pivot-edit-sup [data-testid="stNumberInput"] input { border-left: 4px solid #43a047 !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   TOGGLE  — styled as a distinct card so it always stands out
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stToggle"],
[data-testid="stSidebar"] [data-testid="stToggle"] {
    background-color: #eef0fb !important;
    border: 2px solid #7986cb !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    margin: 4px 0 8px 0 !important;
    box-shadow: 0 2px 6px rgba(57,73,171,0.15) !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="stToggle"] [role="switch"],
[data-testid="stSidebar"] [data-testid="stToggle"] [role="switch"] {
    background-color: #9e9e9e !important;
    border-color: #9e9e9e !important;
    min-width: 40px !important;
    flex-shrink: 0 !important;
}
[data-testid="stToggle"] [role="switch"][aria-checked="true"],
[data-testid="stSidebar"] [data-testid="stToggle"] [role="switch"][aria-checked="true"] {
    background-color: #3949ab !important;
    border-color: #3949ab !important;
}
[data-testid="stToggle"] [role="switch"] > div,
[data-testid="stSidebar"] [data-testid="stToggle"] [role="switch"] > div {
    background-color: #ffffff !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.30) !important;
}
[data-testid="stToggle"] label,
[data-testid="stToggle"] p,
[data-testid="stSidebar"] [data-testid="stToggle"] label,
[data-testid="stSidebar"] [data-testid="stToggle"] p {
    color: #1e2035 !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    margin-left: 4px !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   RADIO BUTTONS
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stRadio"] label,
[data-testid="stRadio"] p,
[data-testid="stRadio"] span { color: #1e2035 !important; }
[data-baseweb="radio"] [role="radio"] {
    background-color: #ffffff !important;
    border-color: #c5cae9 !important;
}
[data-baseweb="radio"] [role="radio"][aria-checked="true"] {
    background-color: #3949ab !important;
    border-color: #3949ab !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHECKBOX
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stCheckbox"] span,
[data-testid="stCheckbox"] p,
[data-testid="stCheckbox"] label { color: #1e2035 !important; }
[data-baseweb="checkbox"] [role="checkbox"] {
    background-color: #ffffff !important;
    border-color: #c5cae9 !important;
    border-radius: 4px !important;
}
[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"] {
    background-color: #3949ab !important;
    border-color: #3949ab !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ALERTS & NOTIFICATIONS  (success / warning / error / info)
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stAlert"],
[data-testid="stAlert"] > div,
[data-baseweb="notification"],
[data-baseweb="toast"],
div[class*="stAlert"] {
    border-radius: 8px !important;
    border-left-width: 4px !important;
}
[class*="stSuccess"], .stSuccess,
[data-baseweb="notification"][kind="positive"] {
    background-color: #e8f5e9 !important;
    border-color: #66bb6a !important;
}
[class*="stSuccess"] *, .stSuccess *,
[data-baseweb="notification"][kind="positive"] * {
    color: #1b5e20 !important;
}
[class*="stWarning"], .stWarning,
[data-baseweb="notification"][kind="warning"] {
    background-color: #fff8e1 !important;
    border-color: #ffb300 !important;
}
[class*="stWarning"] *, .stWarning *,
[data-baseweb="notification"][kind="warning"] * {
    color: #7a4600 !important;
}
[class*="stError"], .stError,
[data-baseweb="notification"][kind="negative"] {
    background-color: #fce4ec !important;
    border-color: #e57373 !important;
}
[class*="stError"] *, .stError *,
[data-baseweb="notification"][kind="negative"] * {
    color: #880e4f !important;
}
[class*="stInfo"], .stInfo,
[data-baseweb="notification"][kind="info"] {
    background-color: #e3f2fd !important;
    border-color: #42a5f5 !important;
}
[class*="stInfo"] *, .stInfo *,
[data-baseweb="notification"][kind="info"] * {
    color: #0d47a1 !important;
}
[data-testid="stAlert"] svg { fill: currentColor !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   STATUS WIDGET (spinner status blocks)
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stStatusWidget"],
[data-testid="stStatusWidget"] > div,
[data-testid="stStatus"],
[data-testid="stStatus"] > div {
    background-color: #ffffff !important;
    border: 1px solid #c5cae9 !important;
    border-radius: 8px !important;
    color: #1e2035 !important;
    font-size: 1.05rem !important;
}
[data-testid="stStatusWidget"] *,
[data-testid="stStatus"] * { color: #1e2035 !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   BUTTONS (main + sidebar)
   ═══════════════════════════════════════════════════════════════════════════ */
.stButton > button {
    background-color: #e8eaf6 !important;
    color: #3949ab !important;
    border: 1px solid #c5cae9 !important;
    border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    transition: background 0.18s, box-shadow 0.18s;
    min-height: 42px !important;
}
.stButton > button:hover {
    background-color: #c5cae9 !important;
    box-shadow: 0 2px 8px rgba(57,73,171,0.14) !important;
}
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button {
    background-color: #3949ab !important;
    color: #ffffff !important;
    border-color: #3949ab !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #283593 !important;
}
[data-testid="stDownloadButton"] > button {
    background-color: #e0f2f1 !important;
    color: #00695c !important;
    border: 1px solid #b2dfdb !important;
    border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important; font-size: 1.1rem !important;
}
[data-testid="stDownloadButton"] > button:hover { background-color: #b2dfdb !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   KPI CARDS
   ═══════════════════════════════════════════════════════════════════════════ */
.kpi-card {
    background: #ffffff; border: 1px solid #dde1ed; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 6px;
    box-shadow: 0 1px 4px rgba(57,73,171,0.07);
}
.kpi-label {
    font-family: 'Sora', sans-serif; font-size: 0.95rem !important;
    color: #5e6180 !important; letter-spacing: 0.10em;
    text-transform: uppercase; margin-bottom: 4px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace; font-size: 1.6rem !important;
    font-weight: 600; color: #1e2035 !important; line-height: 1.1;
}
.kpi-delta-pos { font-family:'JetBrains Mono',monospace; font-size:0.95rem !important; color:#2e7d32 !important; margin-top:3px; }
.kpi-delta-neg { font-family:'JetBrains Mono',monospace; font-size:0.95rem !important; color:#c62828 !important; margin-top:3px; }
.kpi-delta-neu { font-family:'JetBrains Mono',monospace; font-size:0.95rem !important; color:#5e6180 !important; margin-top:3px; }

/* ═══════════════════════════════════════════════════════════════════════════
   52-WEEK BAR
   ═══════════════════════════════════════════════════════════════════════════ */
.wk52-wrap {
    background: #ffffff; border: 1px solid #dde1ed; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(57,73,171,0.07);
}
.wk52-title { font-family:'Sora',sans-serif; font-size:0.95rem !important; color:#5e6180 !important; letter-spacing:0.10em; text-transform:uppercase; margin-bottom:10px; }
.wk52-bar-outer { background:#e8eaf6; border-radius:6px; height:11px; position:relative; margin:8px 0 4px 0; }
.wk52-bar-fill { background:linear-gradient(90deg,#ef9a9a,#ffe082,#a5d6a7); border-radius:6px; height:11px; position:absolute; left:0; top:0; }
.wk52-marker { position:absolute; top:-5px; width:21px; height:21px; background:#fff; border-radius:50%; transform:translateX(-50%); border:2.5px solid #3949ab; box-shadow:0 0 6px rgba(57,73,171,0.28); }
.wk52-labels { display:flex; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:0.95rem !important; color:#5e6180 !important; margin-top:6px; }
.wk52-cur { font-family:'JetBrains Mono',monospace; font-size:1.05rem !important; color:#3949ab !important; font-weight:600; }

/* ═══════════════════════════════════════════════════════════════════════════
   SECTION TITLE / INFO BOX / BADGES
   ═══════════════════════════════════════════════════════════════════════════ */
.section-title {
    font-family:'Sora',sans-serif; font-size:1.25rem !important;
    color:#5e6180 !important;
    font-weight:700; letter-spacing:0.12em; text-transform:uppercase;
    border-bottom:1.5px solid #c5cae9; padding-bottom:6px; margin:18px 0 12px 0;
}
.info-box {
    background:#e8eaf6; border-left:3px solid #3949ab;
    border-radius:0 8px 8px 0; padding:10px 14px;
    font-size:1.05rem !important; color:#3949ab !important; margin-bottom:12px;
}
.info-box * { color:#3949ab !important; }
.method-badge { display:inline-block; border-radius:5px; padding:2px 9px; margin:1px 3px; font-family:'Sora',sans-serif; font-size:0.92rem !important; font-weight:600; letter-spacing:0.04em; }
.badge-classic   { background:#e8eaf6; color:#3949ab !important; border:1px solid #c5cae9; }
.badge-fibonacci { background:#fff8e1; color:#bf360c !important; border:1px solid #ffe082; }
.badge-woodie    { background:#e8f5e9; color:#1b5e20 !important; border:1px solid #a5d6a7; }
.badge-camarilla { background:#f3e5f5; color:#4a148c !important; border:1px solid #ce93d8; }

/* ═══════════════════════════════════════════════════════════════════════════
   PIVOT MATRIX TABLE
   ═══════════════════════════════════════════════════════════════════════════ */
.pivot-matrix-wrap {
    border-radius: 10px; overflow: hidden;
    border: 2px solid #b0b7d4; margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(57,73,171,0.08);
}
.pivot-matrix {
    width: 100%; border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace; font-size: 1.05rem !important;
    background: #ffffff;
}
.pivot-matrix th,
.pivot-matrix td {
    padding: 11px 15px !important; text-align: right;
    border: 1px solid #b0b7d4 !important;
    white-space: nowrap;
}
.pivot-matrix th:first-child, .pivot-matrix td:first-child { text-align: left; min-width: 60px; }
.pivot-matrix td:first-child { color: #3d4060 !important; font-size: 1.0rem !important; font-weight: 600; letter-spacing: 0.06em; }

.pivot-matrix thead tr.method-row th {
    font-family:'Sora',sans-serif; font-size:0.95rem !important;
    letter-spacing:0.12em; text-transform:uppercase;
    padding:11px 15px !important; font-weight:700;
    border-bottom: 2px solid #b0b7d4 !important;
}
.pivot-matrix thead tr.method-row th.th-classic   { color:#3949ab !important; background:#eef0fb; border-bottom:2px solid #7986cb !important; }
.pivot-matrix thead tr.method-row th.th-fibonacci { color:#bf360c !important; background:#fffde7; border-bottom:2px solid #ffb300 !important; }
.pivot-matrix thead tr.method-row th.th-woodie    { color:#1b5e20 !important; background:#f1f8e9; border-bottom:2px solid #66bb6a !important; }
.pivot-matrix thead tr.method-row th.th-camarilla { color:#4a148c !important; background:#f8f0fc; border-bottom:2px solid #ab47bc !important; }
.pivot-matrix thead tr.method-row th.th-label     { color:#3d4060 !important; background:#f4f5f9; }

.pivot-matrix thead tr.sym-row th {
    background:#dde3f0; color:#2d3057 !important;
    font-family:'Sora',sans-serif; font-size:0.95rem !important;
    letter-spacing:0.06em; text-transform:uppercase;
    padding:8px 15px !important; font-weight:700;
    border-bottom: 2px solid #b0b7d4 !important;
}

.pivot-matrix tbody tr.res-row td            { background:#fff0f0; color:#b71c1c !important; }
.pivot-matrix tbody tr.res-row td:first-child { color: #b71c1c !important; font-weight:700; }
.pivot-matrix tbody tr.pp-row  td            { background:#fffde7; color:#e65100 !important; font-weight:700; }
.pivot-matrix tbody tr.pp-row  td:first-child { color:#e65100 !important; }
.pivot-matrix tbody tr.sup-row td            { background:#f0faf0; color:#1b5e20 !important; }
.pivot-matrix tbody tr.sup-row td:first-child { color:#1b5e20 !important; font-weight:700; }
.pivot-matrix tbody tr:hover td              { filter:brightness(0.95); }
.pivot-matrix td.na-val                      { color:#b0b7d4 !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   TABS
   ═══════════════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] { background:#ffffff; border-bottom:2px solid #c5cae9; gap:0; }
.stTabs [data-baseweb="tab"] {
    font-family:'Sora',sans-serif; font-size:1.1rem !important;
    font-weight:500;
    letter-spacing:0.04em; color:#5e6180 !important; padding:12px 28px !important;
    border-bottom:2.5px solid transparent; background:transparent !important;
}
.stTabs [aria-selected="true"] { color:#3949ab !important; border-bottom:2.5px solid #3949ab !important; background:transparent !important; }
.stTabs [data-baseweb="tab-panel"] { background:transparent !important; padding-top:10px !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   DATAFRAME / EXPANDER / MISC
   ═══════════════════════════════════════════════════════════════════════════ */
div[data-testid="stDataFrame"] {
    border-radius:10px; overflow:hidden;
    border:1px solid #b0b7d4 !important;
    box-shadow:0 1px 4px rgba(57,73,171,0.05);
}
.stDataFrame { font-family:'JetBrains Mono',monospace !important; font-size:1.05rem !important; }

[data-testid="stExpander"] {
    background:#ffffff !important; border:1px solid #c5cae9 !important;
    border-radius:10px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p { color:#3949ab !important; font-family:'Sora',sans-serif !important; font-weight:600 !important; font-size:1.05rem !important; }

.stCaption, [data-testid="stCaptionContainer"] { color:#5e6180 !important; font-size:0.95rem !important; }
hr { border-color:#c5cae9 !important; }

[data-testid="stSpinner"] { color:#3949ab !important; }

[data-testid="stNumberInput"] button p,
[data-testid="stNumberInput"] button span:not(:has(svg)),
[data-testid="stNumberInput"] button [data-testid],
[data-testid="stNumberInput"] [data-baseweb="button"] p,
[data-testid="stNumberInput"] [data-baseweb="button"] span:not(:has(svg)) {
    visibility: hidden !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    font-size: 0 !important;
    line-height: 0 !important;
}

.app-header { font-family:'Sora',sans-serif; font-weight:700; font-size:2.2rem !important; color:#1e2035 !important; letter-spacing:-0.01em; }
.app-header span { color:#3949ab !important; }

.dl-log-card {
    margin: 8px 0 4px;
    padding: 12px 14px;
    background: #f8f9ff !important;
    border: 2px solid #c5cae9;
    border-radius: 10px;
    box-shadow: 0 1px 5px rgba(57,73,171,0.10);
    font-family: 'Sora', sans-serif;
    font-size: 1rem !important;
}
.dl-log-card * { color: #1e2035 !important; }
.dl-log-title {
    font-size: 0.9rem !important; font-weight: 700;
    color: #1e2035 !important;
    margin-bottom: 8px; line-height: 1.4;
}
.dl-log-title.success { color: #1b5e20 !important; }
.dl-log-title.partial { color: #e65100 !important; }
.dl-log-prog-wrap {
    background: #dde3f0;
    border-radius: 6px; height: 10px;
    overflow: hidden; margin-bottom: 10px;
}
.dl-log-prog-fill {
    height: 100%; border-radius: 6px;
    transition: width 0.4s ease;
}
.dl-log-prog-fill.success { background: #2e7d32; }
.dl-log-prog-fill.partial { background: #e65100; }
.dl-log-prog-fill.running { background: #3949ab; }
.dl-log-meta {
    font-size: 0.82rem !important; color: #5e6180 !important;
    margin-bottom: 6px; font-weight: 500;
}
.dl-log-entry {
    font-size: 0.82rem !important; color: #3d4060 !important;
    line-height: 1.7; font-family: 'JetBrains Mono', monospace;
}
.dl-log-entry.ok  { color: #2e7d32 !important; }
.dl-log-entry.err { color: #c62828 !important; }
.dl-log-entry.warn { color: #e65100 !important; }

.pivot-method-header {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 0 8px 0;
    border-bottom: 1px solid #e0e4f0;
    margin-bottom: 10px;
}
.pivot-method-label {
    font-family: 'Sora', sans-serif;
    font-size: 1.05rem !important; font-weight: 700;
    color: #5e6180 !important;
    text-transform: uppercase; letter-spacing: 0.08em;
}

[style*="background-color: rgb(14"],
[style*="background-color: rgb(18"],
[style*="background-color: rgb(22"],
[style*="background-color: rgb(26"],
[style*="background: rgb(14"],
[style*="background: rgb(18"],
[style*="background: rgb(22"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e2035 !important;
}
</style>
""",
unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# KEYBOARD FIX
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<script>
(function() {
    var _ALL_ARROWS  = new Set(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight']);
    var _UPDOWN      = new Set(['ArrowUp','ArrowDown']);
    var _LEFTRIGHT   = new Set(['ArrowLeft','ArrowRight']);

    document.addEventListener('keydown', function(e) {
        if (!e.target) return;
        var tag  = e.target.tagName;
        var type = (e.target.type || '').toLowerCase();

        if (tag === 'INPUT' && (type === 'text' || type === 'number' || type === 'search' || type === '')) {
            if (_ALL_ARROWS.has(e.key)) {
                e.stopImmediatePropagation();
                if (type === 'number' && _UPDOWN.has(e.key)) {
                    e.preventDefault();
                }
            }
        }
    }, true);

    document.addEventListener('wheel', function(e) {
        if (e.target && e.target.type === 'number') {
            e.stopImmediatePropagation();
            e.preventDefault();
        }
    }, {capture: true, passive: false});
})();
</script>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS — colours tuned for a light background
# ═══════════════════════════════════════════════════════════════════════════
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#fafbff",
    font=dict(family="Sora, sans-serif", color="#3d4060", size=13),
    xaxis=dict(gridcolor="#c5cae9", zeroline=False, color="#3d4060",
               tickfont=dict(color="#3d4060", size=12),
               title_font=dict(color="#1e2035", size=13)),
    yaxis=dict(gridcolor="#c5cae9", zeroline=False, color="#3d4060",
               tickfont=dict(color="#3d4060", size=12),
               title_font=dict(color="#1e2035", size=13)),
    margin=dict(l=10, r=10, t=40, b=10),
    hovermode="x unified",
)
_METHOD_LEGEND = dict(bgcolor="#ffffff", bordercolor="#dde1ed", borderwidth=1)
METHOD_COLORS = {
    "Classic": {
        "pp":  "#3949ab",
        "r": ["#e53935", "#c62828", "#b71c1c"],
        "s": ["#43a047", "#2e7d32", "#1b5e20"],
    },
    "Fibonacci": {
        "pp":  "#f57c00",
        "r": ["#ffb300", "#fb8c00", "#e65100"],
        "s": ["#26a69a", "#00897b", "#00695c"],
    },
    "Woodie": {
        "pp":  "#2e7d32",
        "r": ["#ef5350", "#e53935", "#c62828"],
        "s": ["#29b6f6", "#039be5", "#0277bd"],
    },
    "Camarilla": {
        "pp":  "#7b1fa2",
        "r": ["#ec407a", "#e91e63", "#c2185b", "#880e4f"],
        "s": ["#7e57c2", "#5e35b1", "#4527a0", "#311b92"],
    },
}
PRICE_LINE_COLORS = [
    "#3949ab", "#e65100", "#2e7d32", "#7b1fa2",
    "#00838f", "#ad1457", "#1565c0", "#4e342e",
]
METHOD_COLS = {
    "Classic":   (Col.P_CLASSIC, [Col.CL_R1, Col.CL_R2, Col.CL_R3], [Col.CL_S1, Col.CL_S2, Col.CL_S3]),
    "Fibonacci": (Col.P_CLASSIC, [Col.FIB_R1, Col.FIB_R2, Col.FIB_R3], [Col.FIB_S1, Col.FIB_S2, Col.FIB_S3]),
    "Woodie":    (Col.P_WOODIE, [Col.WD_R1, Col.WD_R2], [Col.WD_S1, Col.WD_S2]),
    "Camarilla": (Col.P_CAM, [Col.CAM_R1, Col.CAM_R2, Col.CAM_R3, Col.CAM_R4],
                  [Col.CAM_S1, Col.CAM_S2, Col.CAM_S3, Col.CAM_S4]),
}
ALL_METHODS = ["Classic", "Fibonacci", "Woodie", "Camarilla"]

# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADERS (cached)
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")
    df.columns = [c.strip().upper() for c in df.columns]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            df["DATE"] = pd.to_datetime(df["DATE"], format=fmt)
            break
        except (ValueError, TypeError):
            continue
    num_cols = [
        Col.OPEN, Col.HIGH, Col.LOW, Col.CLOSE, Col.PREV_CLOSE,
        Col.NET_TRDQTY, Col.NET_TRDVAL, Col.HI_52, Col.LO_52,
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "", regex=False).str.strip(),
                errors="coerce",
            )
    return df.sort_values([Col.SYMBOL, Col.CATEGORY, "DATE"]).reset_index(drop=True)

@st.cache_data(show_spinner=False)
def load_pivots(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")
    df.columns = [c.strip().upper() for c in df.columns]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            df["DATE"] = pd.to_datetime(df["DATE"], format=fmt)
            break
        except (ValueError, TypeError):
            continue
    return df

# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def _safe_default(options: list, candidates: list) -> list:
    option_set = set(options)
    valid = [c for c in candidates if c in option_set]
    return valid if valid else (options[:1] if options else [])

def _fmt(v, decimals: int = 2) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:,.{decimals}f}"

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📈 Bullseye Fintech")
    st.markdown("### NSE EOD Dashboard")
    st.markdown("### ⚙️ Settings")
    st.markdown(
        '<div style="background:#3949ab;border-radius:8px;padding:2px 0 0 0;margin-bottom:2px;">'
        '<div style="background:#eef0fb;border:2px solid #3949ab;border-radius:7px;padding:8px 12px;">'
        '<span style="font-size:0.82rem;font-weight:700;letter-spacing:0.10em;'
        'text-transform:uppercase;color:#3949ab;">⚙ Auto-update on launch</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    auto_update = st.checkbox(
        "Enable auto-update",
        value=st.session_state.get("auto_update_enabled", AUTO_UPDATE_DEFAULT),
        help="Automatically fetch previous trading day's data when the app starts.",
        key="auto_update_checkbox",
    )
    st.session_state.auto_update_enabled = auto_update

    st.markdown("### 🗄️ Data")
    available_years = get_available_years()
    if available_years:
        st.markdown("**Available years — click to load:**")
        year_btn_cols = st.columns(min(len(available_years), 4))
        for i, yr in enumerate(available_years):
            with year_btn_cols[i % len(year_btn_cols)]:
                if st.button(f"📊 {yr}", key=f"yr_btn_{yr}", use_container_width=True):
                    st.session_state.selected_year = yr
                    st.session_state.auto_update_done = True
                    st.rerun()
        st.success(f"✓ {len(available_years)} year(s) on disk", icon="✅")
    else:
        st.info("No data yet. Download below.")

    sel_yr_for_export = st.session_state.get("selected_year", None)
    if sel_yr_for_export:
        st.markdown("**Export loaded data:**")
        _eod_bytes = get_eod_csv_bytes(sel_yr_for_export)
        if _eod_bytes:
            st.download_button(
                label=f"⬇ EOD data {sel_yr_for_export}",
                data=_eod_bytes,
                file_name=f"NSE_EOD_{sel_yr_for_export}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        _piv_bytes = get_pivot_csv_bytes(sel_yr_for_export)
        if _piv_bytes:
            st.download_button(
                label=f"⬇ Pivot points {sel_yr_for_export}",
                data=_piv_bytes,
                file_name=f"NSE_Pivots_{sel_yr_for_export}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("### 📥 Download from NSE")
    current_year = datetime.now().year
    year_options = list(range(2000, current_year + 1))

    download_mode = st.selectbox(
        "Download mode",
        ["Single Year", "Multiple Years", "Date Range", "All Downloaded"],
        key="dl_mode",
        label_visibility="visible",
    )

    selected_years = []
    dl_date_from = dl_date_to = None

    if download_mode == "Single Year":
        selected_years = [
            st.selectbox(
                "Year", year_options,
                index=year_options.index(current_year),
                key="dl_single",
            )
        ]
    elif download_mode == "Multiple Years":
        selected_years = st.multiselect(
            "Years", year_options, default=[current_year], key="dl_multi"
        )
    elif download_mode == "Date Range":
        st.caption("📅 Pick a date range — all years spanning the range will be downloaded.")
        _today = datetime.now().date()
        _jan1 = _today.replace(month=1, day=1)

        dl_date_from = st.date_input(
            "From date",
            value=_jan1,
            min_value=datetime(2000, 1, 1).date(),
            max_value=_today,
            key="dl_date_from",
            help="Start date for the data download range",
            format="DD/MM/YYYY",
        )
        dl_date_to = st.date_input(
            "To date",
            value=_today,
            min_value=datetime(2000, 1, 1).date(),
            max_value=_today,
            key="dl_date_to",
            help="End date for the data download range",
            format="DD/MM/YYYY",
        )

        if dl_date_from > dl_date_to:
            st.error("⚠️ 'From' date must be before 'To' date.")
            selected_years = []
        else:
            dl_date_to = min(dl_date_to, _today)
            selected_years = list(range(dl_date_from.year, dl_date_to.year + 1))
            st.caption(f"Will download {len(selected_years)} year(s): {selected_years[0]}–{selected_years[-1]}")
            if current_year in selected_years:
                st.warning(
                    "⚠️ **Current year detected**: Only trading dates up to **today** will be downloaded.  "
                    "Future dates in this year do not exist yet and will be skipped automatically."
                )
    else:
        selected_years = available_years
        st.caption(f"Will re-process {len(available_years)} year(s) on disk.")

    force_dl = st.checkbox("Force re-download (overwrite)", value=False, key="dl_force")
    incr_dl = st.checkbox("Incremental (new dates only)", value=True, key="dl_incr")

    if st.button("🚀 Start Download", type="primary", use_container_width=True):
        if not selected_years:
            st.warning("Select at least one year.")
        else:
            valid_years = []
            for yr in selected_years:
                if yr > current_year:
                    st.warning(f"⏭️ Skipping year {yr} (future year)")
                elif yr == current_year and download_mode == "Date Range" and dl_date_from:
                    if dl_date_from <= datetime.now().date():
                        valid_years.append(yr)
                    else:
                        st.warning(f"⏭️ Skipping {yr}: start date is in the future")
                else:
                    valid_years.append(yr)

            if not valid_years:
                st.error("No valid years to download. Adjust your date range.")
            else:
                total = len(valid_years)

                from datetime import date as _date
                def _est_dates(yrs):
                    n = 0
                    for y in yrs:
                        if y == current_year:
                            elapsed = (_date.today() - _date(y, 1, 1)).days
                            n += max(1, int(elapsed * 252 / 365))
                        else:
                            n += 252
                    return n
                est_dates = _est_dates(valid_years)

                st.session_state["dl_log"]       = []
                st.session_state["dl_total"]      = total
                st.session_state["dl_est_dates"]  = est_dates
                st.session_state["dl_ok"]         = 0
                st.session_state["dl_fail"]       = 0

                prog_ph = st.empty()

                def _draw_prog_pct(pct_float, yr_label, ok, fail, est_d, finished=False):
                    pct = max(0, min(100, int(pct_float)))
                    bar_color = "#2e7d32" if finished and fail == 0 else "#e65100" if finished and fail > 0 else "#3949ab"
                    pct_color = "#2e7d32" if finished and fail == 0 else "#e65100" if finished and fail > 0 else "#3949ab"
                    if finished:
                        status_line = f"✅ {ok}/{total} years · ~{est_d:,} trading dates" if fail == 0 else f"⚠ {ok} ok · {fail} failed / {total}"
                    else:
                        status_line = f"Downloading {yr_label}… · {ok + fail}/{total} years done · ~{est_d:,} dates"
                    prog_ph.markdown(
                        f'<div style="background:#f0f2ff;border:1.5px solid #c5cae9;border-radius:10px;'
                        f'padding:12px 14px;margin:6px 0;">'
                        f'<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:8px;">'
                        f'<span style="font-family:JetBrains Mono,monospace;font-size:1.8rem;'
                        f'font-weight:800;color:{pct_color};">{pct}%</span>'
                        f'<span style="font-size:0.82rem;color:#5e6180;">{status_line}</span>'
                        f'</div>'
                        f'<div style="background:#dde3f0;border-radius:99px;height:14px;overflow:hidden;">'
                        f'<div style="width:{pct}%;height:100%;background:{bar_color};border-radius:99px;"></div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                import queue as _queue

                _result_box: list = [None]

                _draw_prog_pct(0, valid_years[0], 0, 0, est_dates)

                for idx, yr in enumerate(valid_years):
                    yr_est = (252 if yr < current_year else
                              max(1, int((_date.today() - _date(yr, 1, 1)).days * 252 / 365)))
                    yr_est_secs = max(4.0, yr_est * 0.05)

                    _result_box[0] = None

                    # --- Thread-safe message queue ----------------------------
                    # The worker thread ONLY puts strings into this queue.
                    # The main Streamlit thread drains the queue and renders them.
                    # This avoids "missing ScriptRunContext" errors that arise when
                    # Streamlit widget calls (st.write / _s.write) are made from a
                    # background thread.
                    _msg_queue: _queue.Queue = _queue.Queue()
                    _cb_count = [0]  # mutable counter read on main thread only

                    def _make_cb(q):
                        def _cb(msg):
                            q.put(msg)
                        return _cb

                    cb = _make_cb(_msg_queue)

                    def _run_download(year_arg, force_arg, incr_arg, cb_arg, box):
                        try:
                            result = download_year_data(
                                year_arg,
                                force_redownload=force_arg,
                                incremental=incr_arg,
                                progress_callback=cb_arg,
                            )
                        except Exception as exc:
                            result = (False, str(exc))
                        box[0] = result

                    dl_thread = threading.Thread(
                        target=_run_download,
                        args=(yr, force_dl, incr_dl, cb, _result_box),
                        daemon=True,
                    )

                    with st.status(f"Downloading {yr}…", expanded=True) as _s:
                        dl_thread.start()

                        t_start = time.monotonic()
                        last_pct = idx / total * 100
                        while dl_thread.is_alive():
                            # Drain all queued messages and write them on the
                            # main thread where Streamlit context is available.
                            while not _msg_queue.empty():
                                try:
                                    line = _msg_queue.get_nowait()
                                    _s.write(line)
                                    _cb_count[0] += 1
                                except _queue.Empty:
                                    break

                            elapsed = time.monotonic() - t_start
                            time_frac = 1.0 - 2.0 ** (-elapsed / max(yr_est_secs / 3, 1.0))
                            time_based_pct = (idx + time_frac * 0.95) / total * 100
                            cb_frac = min(_cb_count[0] / max(yr_est, 1), 0.98)
                            cb_pct = (idx + cb_frac) / total * 100
                            display_pct = max(last_pct, min(time_based_pct, cb_pct if _cb_count[0] > 0 else time_based_pct))
                            last_pct = display_pct
                            _draw_prog_pct(
                                display_pct, yr,
                                st.session_state["dl_ok"], st.session_state["dl_fail"],
                                est_dates,
                            )
                            time.sleep(0.25)

                        dl_thread.join()

                        # Flush any remaining messages after thread exits
                        while not _msg_queue.empty():
                            try:
                                _s.write(_msg_queue.get_nowait())
                            except _queue.Empty:
                                break

                        ok, msg = _result_box[0]

                        if ok:
                            _s.update(label=f"✅ {yr} downloaded", state="complete")
                            st.session_state["dl_ok"] += 1
                            st.session_state["dl_log"].append(("ok", f"{yr}: downloaded successfully"))
                            with st.status(f"Computing pivots for {yr}…"):
                                p_ok, p_msg = compute_pivot_points(yr)
                                (st.success if p_ok else st.warning)(p_msg)
                                if not p_ok:
                                    st.session_state["dl_log"].append(("warn", f"{yr}: pivot — {p_msg}"))
                        else:
                            _s.update(label=f"❌ {yr} failed", state="error")
                            st.session_state["dl_fail"] += 1
                            st.session_state["dl_log"].append(("err", f"{yr}: {msg}"))
                            st.error(msg)
                        time.sleep(0.3)

                _draw_prog_pct(100, "", st.session_state["dl_ok"], st.session_state["dl_fail"], est_dates, finished=True)
                st.session_state["dl_pct"] = 100
                st.cache_data.clear()
                st.session_state.auto_update_done = True
                st.rerun()

# =========================
# SIDEBAR CONTROLS
# =========================
with st.sidebar:

    # ---- Download Log Section ----
    if st.session_state.get("dl_log"):
        ok_c = st.session_state.get("dl_ok", 0)
        fail_c = st.session_state.get("dl_fail", 0)
        tot_c = st.session_state.get("dl_total", 0)
        est_d = st.session_state.get("dl_est_dates", 0)

        pct = int(ok_c / tot_c * 100) if tot_c > 0 else 100
        bar_c = "#2e7d32" if fail_c == 0 else "#e65100"
        pct_c = "#2e7d32" if fail_c == 0 else "#e65100"

        summ = (
            f"✅ {ok_c}/{tot_c} years · ~{est_d:,} trading dates"
            if fail_c == 0
            else f"⚠ {ok_c} ok · {fail_c} failed / {tot_c}"
        )

        log_rows = " ".join(
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.82rem;'
            f'line-height:1.8;color:{"#2e7d32" if k=="ok" else "#c62828" if k=="err" else "#e65100"};">'
            f'{"✅" if k=="ok" else "❌" if k=="err" else "⚠"} {ln}</div>'
            for k, ln in st.session_state["dl_log"]
        )

        st.markdown(
            f'<div style="background:#f0f2ff;border:1.5px solid #c5cae9;border-radius:10px;'
            f'padding:12px 14px;margin:6px 0;">'
            f'<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:8px;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.8rem;'
            f'font-weight:800;color:{pct_c};">{pct}%</span>'
            f'<span style="font-size:0.82rem;color:#5e6180;">{summ}</span>'
            f'</div>'
            f'<div style="background:#dde3f0;border-radius:99px;height:14px;overflow:hidden;margin-bottom:10px;">'
            f'<div style="width:{pct}%;height:100%;background:{bar_c};border-radius:99px;"></div>'
            f'</div>'
            f'{log_rows}'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.button("✖ Clear log", key="clear_dl_log", use_container_width=True):
            for k in ("dl_log", "dl_ok", "dl_fail", "dl_total", "dl_est_dates", "dl_pct"):
                st.session_state.pop(k, None)
            st.rerun()

    # ---- Delete Data Section ----
    st.markdown("### 🗑️ Delete Data")

    if available_years:
        del_yr = st.selectbox("Year to delete", available_years, key="del_yr")

        if st.button("🗑️ Delete", type="secondary", use_container_width=True, key="del_btn"):
            ok, msg = delete_year_data(del_yr)
            (st.success if ok else st.error)(msg)

            if ok:
                st.cache_data.clear()
                time.sleep(0.8)
                st.rerun()
    else:
        st.caption("Nothing to delete.")

    st.markdown("---")

    st.markdown(
        f"<span style='font-family:JetBrains Mono,monospace;font-size:0.72rem;"
        f"color:#8b8fa8;word-break:break-all;'>📁 {DATA_DIR}</span>",
        unsafe_allow_html=True,
    )
# ═══════════════════════════════════════════════════════════════════════════
# AUTO-UPDATE
# ═══════════════════════════════════════════════════════════════════════════
if "auto_update_done" not in st.session_state:
    st.session_state.auto_update_done = False
if st.session_state.get("auto_update_enabled", False) and not st.session_state.auto_update_done:
    with st.sidebar:
        with st.status("🔄 Auto-updating…", expanded=True) as _au:
            import queue as _queue
            _au_queue: _queue.Queue = _queue.Queue()
            _au_result: list = [None]

            def _au_cb(msg):
                _au_queue.put(msg)

            def _au_worker():
                _au_result[0] = run_auto_update(progress_callback=_au_cb)

            _au_thread = threading.Thread(target=_au_worker, daemon=True)
            _au_thread.start()
            while _au_thread.is_alive():
                while not _au_queue.empty():
                    try:
                        _au.write(_au_queue.get_nowait())
                    except _queue.Empty:
                        break
                time.sleep(0.25)
            _au_thread.join()
            # Flush remaining messages
            while not _au_queue.empty():
                try:
                    _au.write(_au_queue.get_nowait())
                except _queue.Empty:
                    break
            ok, msg = _au_result[0]
            _au.update(
                label="✅ Up to date" if ok else "⚠ Auto-update failed",
                state="complete" if ok else "error",
            )
            if not ok:
                st.warning(msg)
            st.session_state.auto_update_done = True
            st.cache_data.clear()

# ═══════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════
df_raw = None
available_years = get_available_years()
if "selected_year" not in st.session_state and available_years:
    st.session_state.selected_year = available_years[-1]
    st.rerun()
if "selected_year" in st.session_state:
    year = st.session_state.selected_year
    _eod_path = eod_csv_path(year)
    if os.path.exists(_eod_path):
        with st.spinner(f"Loading {year} data…"):
            df_raw = load_data(_eod_path)
        st.sidebar.success(f"✅ {len(df_raw):,} rows — {year}", icon="✅")
    else:
        st.sidebar.error(f"No file for {year}. Download it first.", icon="⚠️")

if df_raw is None:
    st.markdown(
        '<h1 class="app-header">📈 Bullseye Fintech <span>— NSE EOD Dashboard</span></h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-size:1.15rem;color:#5e6180;margin-top:16px;">Open the sidebar (≡ top-left) and use <strong>Download from NSE</strong> to get started.</p>',
        unsafe_allow_html=True,
    )
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL FILTER BAR
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🔍 Filters</div>', unsafe_allow_html=True)
fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 1.2, 1.2, 1.2])
with fc1:
    all_cats = sorted(df_raw[Col.CATEGORY].dropna().unique().tolist())
    sel_cats = st.multiselect(
        "Category", all_cats,
        default=all_cats[:1] if all_cats else [],
        key="g_cat",
    )
    if not sel_cats:
        sel_cats = all_cats
with fc2:
    sym_pool = df_raw[df_raw[Col.CATEGORY].isin(sel_cats)]
    all_symbols = sorted(sym_pool[Col.SYMBOL].dropna().unique().tolist())
    default_syms = _safe_default(all_symbols, st.session_state.get("g_sym_prev", all_symbols[:1]))
    sel_symbols = st.multiselect(
        "Symbol", all_symbols,
        default=default_syms,
        key="g_sym",
    )
    st.session_state["g_sym_prev"] = sel_symbols
    if not sel_symbols:
        sel_symbols = all_symbols[:1] if all_symbols else []
min_date = df_raw["DATE"].min().date()
max_date = df_raw["DATE"].max().date()
import datetime as _dt_mod
_CALENDAR_MIN = _dt_mod.date(2000, 1, 1)
_CALENDAR_MAX = _dt_mod.date.today()
with fc3:
    date_from = st.date_input(
        "📅 From",
        value=min_date,
        min_value=_CALENDAR_MIN,
        max_value=_CALENDAR_MAX,
        key="g_from",
        help="Click to open calendar and pick a start date",
        format="DD/MM/YYYY",
    )
with fc4:
    date_to = st.date_input(
        "📅 To",
        value=max_date,
        min_value=_CALENDAR_MIN,
        max_value=_CALENDAR_MAX,
        key="g_to",
        help="Click to open calendar and pick an end date",
        format="DD/MM/YYYY",
    )
with fc5:
    preset = st.selectbox(
        "Quick range",
        ["Custom", "Last 30 days", "Last 90 days", "Last 6 months", "YTD", "Full year"],
        key="g_preset",
        label_visibility="visible",
    )
    if preset != "Custom":
        import datetime as _dt
        _today = max_date
        if preset == "Last 30 days":
            _new_from = _today - _dt.timedelta(days=30)
        elif preset == "Last 90 days":
            _new_from = _today - _dt.timedelta(days=90)
        elif preset == "Last 6 months":
            _new_from = _today - _dt.timedelta(days=182)
        elif preset == "YTD":
            _new_from = _today.replace(month=1, day=1)
        else:
            _new_from = min_date
        date_from = max(_new_from, min_date)
        date_to = _today
        if date_from > date_to:
            st.error("⚠️ 'From' date must not be after 'To' date. Swapping values.")
            date_from, date_to = date_to, date_from

df_filtered = df_raw[
    (df_raw[Col.CATEGORY].isin(sel_cats)) &
    (df_raw[Col.SYMBOL].isin(sel_symbols)) &
    (df_raw["DATE"].dt.date >= date_from) &
    (df_raw["DATE"].dt.date <= date_to)
].sort_values("DATE").reset_index(drop=True)

if df_filtered.empty:
    st.warning("No data for the selected filters. Adjust your selection.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["📊 OHLCV Summary", "🎯 Pivot Points"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — OHLCV
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    if len(sel_symbols) > 1:
        detail_sym = st.selectbox("Detail view:", sel_symbols, key="t1_detail")
    else:
        detail_sym = sel_symbols[0] if sel_symbols else None

    if not detail_sym:
        st.info("Select at least one symbol in the global filters above.")
        st.stop()

    df_sym = df_filtered[df_filtered[Col.SYMBOL] == detail_sym].copy()
    if df_sym.empty:
        st.warning(f"No data for {detail_sym} in the selected filters.")
        st.stop()

    latest = df_sym.iloc[-1]

    show_kpi = st.checkbox("Show KPI cards", value=True, key="t1_kpi")
    if show_kpi:
        dt_str = latest["DATE"].strftime("%d %b %Y") if pd.notna(latest["DATE"]) else "Latest"
        st.markdown(f'<div class="section-title">Latest Session — {dt_str}</div>', unsafe_allow_html=True)
        k1, k2, k3, k4, k5, k6 = st.columns(6)

        def _kpi(col, label: str, value: str, delta=None, delta_pct=None):
            if delta is not None:
                if delta > 0:
                    d_cls, d_txt = "kpi-delta-pos", f"▲ {delta:,.2f}"
                elif delta < 0:
                    d_cls, d_txt = "kpi-delta-neg", f"▼ {abs(delta):,.2f}"
                else:
                    d_cls, d_txt = "kpi-delta-neu", "━ 0.00"
                if delta_pct is not None and delta != 0:
                    d_txt += f" ({abs(delta_pct):.2f}%)"
                delta_html = f'<div class="{d_cls}">{d_txt}</div>'
            else:
                delta_html = ""
            col.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div>'
                f'{delta_html}</div>',
                unsafe_allow_html=True,
            )

        cl = latest.get(Col.CLOSE, np.nan)
        prev = latest.get(Col.PREV_CLOSE, np.nan)
        chg = cl - prev if pd.notna(cl) and pd.notna(prev) else np.nan
        chgp = (chg / prev * 100) if pd.notna(chg) and prev != 0 else np.nan

        _kpi(k1, "Open", _fmt(latest.get(Col.OPEN)))
        _kpi(k2, "High", _fmt(latest.get(Col.HIGH)))
        _kpi(k3, "Low", _fmt(latest.get(Col.LOW)))
        _kpi(k4, "Close", _fmt(cl), chg, chgp)
        _kpi(k5, "Prev Close", _fmt(prev))
        _kpi(k6, "Volume", _fmt(latest.get(Col.NET_TRDQTY), 0))

    show_52 = st.checkbox("Show 52-week range", value=True, key="t1_52")
    if show_52:
        hi52 = latest.get(Col.HI_52, np.nan)
        lo52 = latest.get(Col.LO_52, np.nan)
        cur = latest.get(Col.CLOSE, np.nan)
        if pd.notna(hi52) and pd.notna(lo52) and pd.notna(cur) and (hi52 - lo52) > 0:
            pct = (cur - lo52) / (hi52 - lo52) * 100
            st.markdown(
                f'<div class="wk52-wrap">'
                f'<div class="wk52-title">52-Week Range</div>'
                f'<div class="wk52-cur">Current: {cur:,.2f}</div>'
                f'<div class="wk52-bar-outer">'
                f'  <div class="wk52-bar-fill" style="width:{pct:.1f}%"></div>'
                f'  <div class="wk52-marker" style="left:{pct:.1f}%"></div>'
                f'</div>'
                f'<div class="wk52-labels"><span>{lo52:,.2f}</span><span>{hi52:,.2f}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">Chart</div>', unsafe_allow_html=True)
    ch_c1, ch_c2 = st.columns([2, 3])
    with ch_c1:
        chart_type = st.selectbox("Type", ["Candlestick", "Line (Close)", "OHLC Bar"], key="t1_ctype")
    with ch_c2:
        overlays = st.multiselect(
            "Overlays",
            ["Volume", "20-Day MA", "50-Day MA", "Bollinger Bands"],
            default=["Volume"],
            key="t1_overlays",
        )

    show_vol = "Volume" in overlays
    show_m20 = "20-Day MA" in overlays
    show_m50 = "50-Day MA" in overlays
    show_bb = "Bollinger Bands" in overlays

    rows = 2 if show_vol else 1
    row_heights = [0.7, 0.3] if show_vol else [1.0]

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)

    x = df_sym["DATE"]
    op = df_sym.get(Col.OPEN, None)
    hi = df_sym.get(Col.HIGH, None)
    lo = df_sym.get(Col.LOW, None)
    cl = df_sym.get(Col.CLOSE, None)

    if chart_type == "Candlestick" and all(v is not None for v in [op, hi, lo, cl]):
        fig.add_trace(go.Candlestick(
            x=x, open=op, high=hi, low=lo, close=cl,
            name=detail_sym,
            increasing_line_color="#2e7d32", decreasing_line_color="#c62828",
            increasing_fillcolor="#a5d6a7", decreasing_fillcolor="#ef9a9a",
            legendgroup="price",
        ), row=1, col=1)
    elif chart_type == "OHLC Bar" and all(v is not None for v in [op, hi, lo, cl]):
        fig.add_trace(go.Ohlc(
            x=x, open=op, high=hi, low=lo, close=cl,
            name=detail_sym,
            increasing_line_color="#2e7d32", decreasing_line_color="#c62828",
            legendgroup="price",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=x, y=cl, name=detail_sym,
            line=dict(color="#3949ab", width=2), mode="lines", legendgroup="price",
        ), row=1, col=1)

    if show_m20 and cl is not None:
        fig.add_trace(go.Scatter(
            x=x, y=cl.rolling(20).mean(), name="MA 20",
            line=dict(color="#e65100", width=1.5, dash="dot"), mode="lines",
        ), row=1, col=1)

    if show_m50 and cl is not None:
        fig.add_trace(go.Scatter(
            x=x, y=cl.rolling(50).mean(), name="MA 50",
            line=dict(color="#7b1fa2", width=1.5, dash="dot"), mode="lines",
        ), row=1, col=1)

    if show_bb and cl is not None:
        bb_mid = cl.rolling(20).mean()
        bb_std = cl.rolling(20).std()
        bb_up = bb_mid + 2 * bb_std
        bb_dn = bb_mid - 2 * bb_std
        fig.add_trace(go.Scatter(
            x=x, y=bb_up, name="BB Upper",
            line=dict(color="#3949ab", width=1, dash="dash"), mode="lines",
            legendgroup="bb",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=x, y=bb_dn, name="BB Lower",
            line=dict(color="#3949ab", width=1, dash="dash"), mode="lines",
            fill="tonexty", fillcolor="rgba(57,73,171,0.06)",
            legendgroup="bb", showlegend=False,
        ), row=1, col=1)

    if show_vol and Col.NET_TRDQTY in df_sym.columns:
        pv = df_sym[Col.PREV_CLOSE] if Col.PREV_CLOSE in df_sym.columns else df_sym[Col.CLOSE].shift(1)
        pv = pv.where(pd.notna(pv), df_sym[Col.CLOSE].shift(1))
        colors_vol = [
            "#a5d6a7" if (c >= p) else "#ef9a9a"
            for c, p in zip(df_sym[Col.CLOSE].fillna(0), pv.fillna(0))
        ]
        fig.add_trace(go.Bar(
            x=x, y=df_sym[Col.NET_TRDQTY], name="Volume",
            marker_color=colors_vol, opacity=0.80, legendgroup="vol",
        ), row=2, col=1)

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=f"{detail_sym} — {chart_type}", font=dict(size=14, color="#1e2035")),
        xaxis_rangeslider_visible=False,
        height=620 if show_vol else 500,
        legend=dict(
            **_METHOD_LEGEND,
            orientation="h",
            x=0, xanchor="left",
            y=-0.12, yanchor="top",
            font=dict(size=11, color="#5e6180"),
            tracegroupgap=6,
            itemwidth=40,
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#c5cae9", color="#3d4060", tickfont=dict(color="#3d4060", size=12))
    fig.update_yaxes(showgrid=True, gridcolor="#c5cae9", color="#3d4060", tickfont=dict(color="#3d4060", size=12))
    st.plotly_chart(fig, use_container_width=True)

    n_rows_sym = len(df_sym)
    warn_parts = []
    if show_m20 and n_rows_sym < 20:
        warn_parts.append(f"• <b>20-Day MA</b> — needs ≥ 20 sessions ({n_rows_sym} available)")
    if show_m50 and n_rows_sym < 50:
        warn_parts.append(f"• <b>50-Day MA</b> — needs ≥ 50 sessions ({n_rows_sym} available)")
    if show_bb and n_rows_sym < 20:
        warn_parts.append(f"• <b>Bollinger Bands</b> — needs ≥ 20 sessions ({n_rows_sym} available)")
    if warn_parts:
        st.markdown(
            f'<div class="info-box">⚠️ Some overlays not visible — insufficient data:<br>'
            f'{"<br>".join(warn_parts)}<br>'
            f'<span style="color:#8b8fa8;font-size:0.88rem;">Widen the date range to see them.</span></div>',
            unsafe_allow_html=True,
        )

    if st.checkbox("Show raw data table", value=False, key="t1_raw"):
        disp_cols = [c for c in [
            "DATE", Col.OPEN, Col.HIGH, Col.LOW, Col.CLOSE,
            Col.PREV_CLOSE, Col.NET_TRDQTY, Col.NET_TRDVAL,
        ] if c in df_sym.columns]
        st.dataframe(
            df_sym[disp_cols].sort_values("DATE", ascending=False).reset_index(drop=True),
            use_container_width=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — PIVOT POINTS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    year = st.session_state.get("selected_year", datetime.now().year)
    _piv_path = pivot_csv_path(year)
    if not os.path.exists(_piv_path):
        st.info(
            f"No pivot data for {year}. "
            "Open the sidebar → Download from NSE → Start Download."
        )
        st.stop()
    df_piv_all = load_pivots(_piv_path)

    t2c1, t2c2, t2c3 = st.columns([3, 2, 2])

    with t2c1:
        pivot_methods = st.multiselect(
            "Pivot methods",
            ALL_METHODS,
            default=["Classic"],
            key="t2_methods",
        )
        if not pivot_methods:
            pivot_methods = ["Classic"]

    with t2c2:
        n_levels = int(st.selectbox(
            "R/S levels",
            options=[1, 2, 3, 4],
            index=1,
            key="t2_levels",
            help="Number of Resistance and Support levels shown (1–4). Woodie max=2, others max=3 or 4.",
        ))

    with t2c3:
        _piv_syms_all = sorted(df_piv_all[Col.SYMBOL].dropna().unique().tolist()) if Col.SYMBOL in df_piv_all.columns else []
        _valid_syms = _safe_default(_piv_syms_all, sel_symbols)
        _date_pool = sorted(
            df_piv_all[df_piv_all[Col.SYMBOL].isin(_valid_syms)]["DATE"].dt.date.unique()
        ) if _valid_syms and not df_piv_all.empty else []

        if _date_pool:
            sel_piv_date = st.selectbox(
                "Session date",
                _date_pool,
                index=len(_date_pool) - 1,
                key="t2_date",
            )
        else:
            st.warning("No pivot dates available for selected symbols.")
            st.stop()

    comp_symbols = _valid_syms
    if not comp_symbols:
        st.info("No pivot data for the selected symbols. Try a different symbol.")
        st.stop()

    piv_rows: dict = {}
    for sym in comp_symbols:
        _r = df_piv_all[
            (df_piv_all[Col.SYMBOL] == sym) &
            (df_piv_all["DATE"].dt.date == sel_piv_date)
        ]
        piv_rows[sym] = _r.iloc[0] if not _r.empty else None

    # ── Editable Pivot Values ──────────────────────────────────────────────────
    _exp_key = "pivot_edit_open"
    if _exp_key not in st.session_state:
        st.session_state[_exp_key] = False

    _btn_label = "🔼 Close Pivot Editor" if st.session_state[_exp_key] else "✏️ Open Pivot Editor (Customize Fib/Cam Levels)"
    if st.button(_btn_label, key="pivot_edit_toggle", use_container_width=True, type="secondary"):
        st.session_state[_exp_key] = not st.session_state[_exp_key]
        st.rerun()

    pivot_overrides: dict = {}

    if "fib_f1" not in st.session_state: st.session_state["fib_f1"] = "0.382"
    if "fib_f2" not in st.session_state: st.session_state["fib_f2"] = "0.618"
    if "fib_f3" not in st.session_state: st.session_state["fib_f3"] = "1.000"
    if "cam_k"  not in st.session_state: st.session_state["cam_k"]  = "1.1"

    def _get_prev_ohlc(sym: str) -> tuple:
        _df = df_raw[df_raw[Col.SYMBOL] == sym].copy()
        _df = _df[_df["DATE"].dt.date < sel_piv_date].sort_values("DATE")
        if _df.empty:
            return np.nan, np.nan, np.nan, np.nan
        _last = _df.iloc[-1]
        H = float(_last.get(Col.HIGH,  np.nan)) if pd.notna(_last.get(Col.HIGH))  else np.nan
        L = float(_last.get(Col.LOW,   np.nan)) if pd.notna(_last.get(Col.LOW))   else np.nan
        C = float(_last.get(Col.CLOSE, np.nan)) if pd.notna(_last.get(Col.CLOSE)) else np.nan
        R = (H - L) if pd.notna(H) and pd.notna(L) else np.nan
        return H, L, C, R

    def _recompute_fibonacci(sym: str, f1: float, f2: float, f3: float) -> dict:
        row = piv_rows.get(sym)
        pp_col, r_cols, s_cols = METHOD_COLS["Fibonacci"]
        PP = float(row.get(pp_col, np.nan)) if (row is not None and pd.notna(row.get(pp_col, np.nan))) else np.nan
        _, _, _, R = _get_prev_ohlc(sym)
        out = {pp_col: PP}
        for j, (rc, sc, ratio) in enumerate(zip(r_cols, s_cols, [f1, f2, f3])):
            out[rc] = PP + ratio * R if pd.notna(PP) and pd.notna(R) else np.nan
            out[sc] = PP - ratio * R if pd.notna(PP) and pd.notna(R) else np.nan
        return out

    def _recompute_camarilla(sym: str, k: float) -> dict:
        _, _, C, R = _get_prev_ohlc(sym)
        pp_col, r_cols, s_cols = METHOD_COLS["Camarilla"]
        row = piv_rows.get(sym)
        PP = float(row.get(pp_col, np.nan)) if (row is not None and pd.notna(row.get(pp_col, np.nan))) else np.nan
        divisors = [12, 6, 4, 2]
        out = {pp_col: PP}
        for j, (rc, sc) in enumerate(zip(r_cols, s_cols)):
            div = divisors[j] if j < len(divisors) else 1
            out[rc] = C + R * k / div if pd.notna(C) and pd.notna(R) else np.nan
            out[sc] = C - R * k / div if pd.notna(C) and pd.notna(R) else np.nan
        return out

    def _safe_float(s, default):
        try:
            return float(str(s).replace(",", "").strip())
        except (ValueError, AttributeError):
            return default

    _fib_computed: dict = {}
    _cam_computed: dict = {}

    if st.session_state[_exp_key]:
        with st.container(border=True):
            st.markdown("### ⚙️ Pivot Level Customization")
            st.info("📌 **Classic & Woodie** use fixed formulas. **Fibonacci & Camarilla** can be tuned below. Changes apply instantly to the chart & table.", icon="💡")

            fib_cols = st.columns(3)
            cam_col = st.columns([1, 2])

            # Fibonacci Multipliers
            with fib_cols[0]:
                st.session_state["fib_f1"] = st.text_input("f1 (R1/S1)", value=st.session_state["fib_f1"], key="fib_f1_inp", help="Default: 0.382")
            with fib_cols[1]:
                st.session_state["fib_f2"] = st.text_input("f2 (R2/S2)", value=st.session_state["fib_f2"], key="fib_f2_inp", help="Default: 0.618")
            with fib_cols[2]:
                st.session_state["fib_f3"] = st.text_input("f3 (R3/S3)", value=st.session_state["fib_f3"], key="fib_f3_inp", help="Default: 1.000")

            # Camarilla Constant
            with cam_col[0]:
                st.session_state["cam_k"] = st.text_input("k Constant", value=st.session_state["cam_k"], key="cam_k_inp", help="Default: 1.1")
            with cam_col[1]:
                st.markdown('<div style="margin-top:36px; color:#5e6180; font-size:0.95rem;">Applied as Prev Close ± (Range × k) / [12, 6, 4, 2]</div>', unsafe_allow_html=True)

            # Re-parse after edits
            _fib_f1 = _safe_float(st.session_state["fib_f1"], 0.382)
            _fib_f2 = _safe_float(st.session_state["fib_f2"], 0.618)
            _fib_f3 = _safe_float(st.session_state["fib_f3"], 1.000)
            _cam_k  = _safe_float(st.session_state["cam_k"], 1.1)

            for _sym in comp_symbols:
                if "Fibonacci" in pivot_methods:
                    _fib_computed[_sym] = _recompute_fibonacci(_sym, _fib_f1, _fib_f2, _fib_f3)
                if "Camarilla" in pivot_methods:
                    _cam_computed[_sym] = _recompute_camarilla(_sym, _cam_k)

            st.divider()

            # Read-only Classic & Woodie display
            _ro_methods = [m for m in pivot_methods if m in ("Classic", "Woodie")]
            if _ro_methods:
                st.markdown("#### 📊 Fixed Pivot Values (Read-Only)")
                ro_grid = st.columns(len(_ro_methods))
                for mi, method in enumerate(_ro_methods):
                    with ro_grid[mi]:
                        border_color = "#3949ab" if method == "Classic" else "#1b5e20"
                        bg_color = "#eef0fb" if method == "Classic" else "#e8f5e9"
                        st.markdown(
                            f'<div class="info-box" style="margin:0; border-left-color:{border_color}; background:{bg_color};">{method}</div>',
                            unsafe_allow_html=True
                        )
                        html_vals = '<table style="width:100%; border-collapse:collapse; font-family:JetBrains Mono; font-size:0.95rem; margin-top:6px;">'
                        for sym in comp_symbols:
                            row = piv_rows.get(sym)
                            pp_col, r_cols, s_cols = METHOD_COLS[method]
                            html_vals += f'<tr><td style="padding:4px 8px; border-bottom:1px solid #e0e4f0; font-weight:600;">{sym}</td>'
                            for lbl, col_key in [("PP", pp_col)] + [(f"R{j+1}", r_cols[j]) for j in range(min(n_levels, len(r_cols)))] + [(f"S{j+1}", s_cols[j]) for j in range(min(n_levels, len(s_cols)))]:
                                v = row.get(col_key, np.nan) if row is not None else np.nan
                                fmt_v = f"{v:,.2f}" if pd.notna(v) else "—"
                                html_vals += f'<td style="text-align:right; padding:4px 8px; border-bottom:1px solid #e0e4f0;">{fmt_v}</td>'
                            html_vals += '</tr>'
                        html_vals += '</table>'
                        st.markdown(html_vals, unsafe_allow_html=True)
            st.divider()
    else:
        # Recompute even when editor is closed, using saved session state values
        _fib_f1 = _safe_float(st.session_state.get("fib_f1", "0.382"), 0.382)
        _fib_f2 = _safe_float(st.session_state.get("fib_f2", "0.618"), 0.618)
        _fib_f3 = _safe_float(st.session_state.get("fib_f3", "1.000"), 1.000)
        _cam_k  = _safe_float(st.session_state.get("cam_k",  "1.1"),   1.1)
        for _sym in comp_symbols:
            if "Fibonacci" in pivot_methods:
                _fib_computed[_sym] = _recompute_fibonacci(_sym, _fib_f1, _fib_f2, _fib_f3)
            if "Camarilla" in pivot_methods:
                _cam_computed[_sym] = _recompute_camarilla(_sym, _cam_k)

    def _cell_val(sym: str, method: str, col_key: str) -> float:
        if method == "Fibonacci" and sym in _fib_computed:
            v = _fib_computed[sym].get(col_key, np.nan)
            return float(v) if pd.notna(v) else np.nan
        if method == "Camarilla" and sym in _cam_computed:
            v = _cam_computed[sym].get(col_key, np.nan)
            return float(v) if pd.notna(v) else np.nan
        row = piv_rows.get(sym)
        if row is None:
            return np.nan
        v = row.get(col_key, np.nan)
        return float(v) if pd.notna(v) else np.nan

    # ── CONSOLIDATED PIVOT TABLE ───────────────────────────────────────────────
    st.markdown(f'<div class="section-title">Pivot Levels — {sel_piv_date}</div>', unsafe_allow_html=True)

    n_sym = len(comp_symbols)

    def _td(v: float, cls: str = "") -> str:
        if np.isnan(v):
            return '<td class="na-val">—</td>'
        cls_attr = f' class="{cls}"' if cls else ""
        return f'<td{cls_attr}>{v:,.2f}</td>'

    method_class = {
        "Classic": "th-classic", "Fibonacci": "th-fibonacci",
        "Woodie": "th-woodie", "Camarilla": "th-camarilla",
    }

    thead = '<thead>'
    thead += '<tr class="method-row">'
    thead += '<th class="th-label">Level</th>'
    for m in pivot_methods:
        css = method_class.get(m, "")
        thead += f'<th class="{css}" colspan="{n_sym}">{m}</th>'
    thead += '</tr>'

    thead += '<tr class="sym-row"><th></th>'
    for _m in pivot_methods:
        for sym in comp_symbols:
            thead += f'<th>{sym}</th>'
    thead += '</tr></thead>'

    tbody = '<tbody>'

    def _r_indices(method: str) -> list:
        _, r_cols, _ = METHOD_COLS[method]
        return list(range(1, min(n_levels, len(r_cols)) + 1))

    def _s_indices(method: str) -> list:
        _, _, s_cols = METHOD_COLS[method]
        return list(range(1, min(n_levels, len(s_cols)) + 1))

    all_r_idx = sorted(set(i for m in pivot_methods for i in _r_indices(m)), reverse=True)
    all_s_idx = sorted(set(i for m in pivot_methods for i in _s_indices(m)))

    for i in all_r_idx:
        tbody += '<tr class="res-row">'
        tbody += f'<td>R{i}</td>'
        for m in pivot_methods:
            _, r_cols, _ = METHOD_COLS[m]
            for sym in comp_symbols:
                if i <= len(r_cols):
                    tbody += _td(_cell_val(sym, m, r_cols[i - 1]))
                else:
                    tbody += '<td class="na-val">—</td>'
        tbody += '</tr>'

    tbody += '<tr class="pp-row"><td>PP</td>'
    for m in pivot_methods:
        pp_col, _, _ = METHOD_COLS[m]
        for sym in comp_symbols:
            tbody += _td(_cell_val(sym, m, pp_col))
    tbody += '</tr>'

    for i in all_s_idx:
        tbody += '<tr class="sup-row">'
        tbody += f'<td>S{i}</td>'
        for m in pivot_methods:
            _, _, s_cols = METHOD_COLS[m]
            for sym in comp_symbols:
                if i <= len(s_cols):
                    tbody += _td(_cell_val(sym, m, s_cols[i - 1]))
                else:
                    tbody += '<td class="na-val">—</td>'
        tbody += '</tr>'

    tbody += '</tbody>'

    st.markdown(
        f'<div class="pivot-matrix-wrap"><table class="pivot-matrix">{thead}{tbody}</table></div>',
        unsafe_allow_html=True,
    )

    # ── Pivot + Price Chart ────────────────────────────────────────────────────
    show_piv_chart = st.checkbox("Overlay pivot levels on price chart", value=True, key="t2_chart")

    if show_piv_chart:
        st.markdown('<div class="section-title">Price Chart with Pivot Levels</div>', unsafe_allow_html=True)
        fig2 = go.Figure()

        for si, sym in enumerate(comp_symbols):
            df_sym_p = df_raw[df_raw[Col.SYMBOL] == sym].copy()
            df_sym_p = df_sym_p[
                (df_sym_p["DATE"].dt.date >= date_from) &
                (df_sym_p["DATE"].dt.date <= date_to)
            ].sort_values("DATE").reset_index(drop=True)
            if not df_sym_p.empty and Col.CLOSE in df_sym_p.columns:
                fig2.add_trace(go.Scatter(
                    x=df_sym_p["DATE"],
                    y=df_sym_p[Col.CLOSE],
                    name=f"{sym} Price",
                    legendgroup="price",
                    legendgrouptitle_text="Price",
                    showlegend=True,
                    line=dict(color=PRICE_LINE_COLORS[si % len(PRICE_LINE_COLORS)], width=2),
                    mode="lines",
                    hovertemplate=f"<b>{sym}</b><br>%{{x|%Y-%m-%d}}<br>₹%{{y:,.2f}}<extra></extra>",
                ))

        x_range = [pd.Timestamp(date_from), pd.Timestamp(date_to)]
        _rs_legend_shown: set = set()

        for si, sym in enumerate(comp_symbols):
            row = piv_rows.get(sym)
            if row is None:
                continue

            sym_prefix = f"[{sym}]  " if n_sym > 1 else ""

            for mi, method in enumerate(pivot_methods):
                pp_col, r_cols, s_cols = METHOD_COLS[method]
                mc = METHOD_COLORS[method]
                grp = f"{sym}_{method}" if n_sym > 1 else method

                pp_v = _cell_val(sym, method, pp_col)
                if not np.isnan(pp_v):
                    fig2.add_trace(go.Scatter(
                        x=x_range, y=[pp_v, pp_v],
                        name=f"{sym_prefix}{method} PP",
                        legendgroup=grp,
                        legendgrouptitle_text=f"{sym_prefix}{method}",
                        showlegend=True,
                        line=dict(color=mc["pp"], width=2, dash="dash"),
                        mode="lines",
                        hovertemplate=f"<b>{sym} {method} PP</b>: ₹%{{y:,.2f}}<extra></extra>",
                    ))

                for j, rc in enumerate(r_cols[:n_levels]):
                    v = _cell_val(sym, method, rc)
                    if not np.isnan(v):
                        legend_key = f"{method}_R{j+1}"
                        show_leg = legend_key not in _rs_legend_shown
                        if show_leg:
                            _rs_legend_shown.add(legend_key)
                        fig2.add_trace(go.Scatter(
                            x=x_range, y=[v, v],
                            name=f"R{j+1}",
                            legendgroup=grp,
                            showlegend=show_leg,
                            line=dict(color=mc["r"][j % len(mc["r"])], width=1.5, dash="dot"),
                            mode="lines",
                            hovertemplate=f"<b>{sym} {method} R{j+1}</b>: ₹%{{y:,.2f}}<extra></extra>",
                        ))

                for j, sc in enumerate(s_cols[:n_levels]):
                    v = _cell_val(sym, method, sc)
                    if not np.isnan(v):
                        legend_key = f"{method}_S{j+1}"
                        show_leg = legend_key not in _rs_legend_shown
                        if show_leg:
                            _rs_legend_shown.add(legend_key)
                        fig2.add_trace(go.Scatter(
                            x=x_range, y=[v, v],
                            name=f"S{j+1}",
                            legendgroup=grp,
                            showlegend=show_leg,
                            line=dict(color=mc["s"][j % len(mc["s"])], width=1.5, dash="dot"),
                            mode="lines",
                            hovertemplate=f"<b>{sym} {method} S{j+1}</b>: ₹%{{y:,.2f}}<extra></extra>",
                        ))

        syms_lbl = ", ".join(comp_symbols)
        meth_lbl = " + ".join(pivot_methods)
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text=f"{syms_lbl} — {meth_lbl} | {sel_piv_date}", font=dict(size=14, color="#1e2035")),
            height=580,
            legend=dict(
                **_METHOD_LEGEND,
                orientation="h",
                x=0, xanchor="left",
                y=-0.15, yanchor="top",
                font=dict(size=11, color="#5e6180"),
                tracegroupgap=8,
                groupclick="toggleitem",
                itemwidth=40,
            ),
        )
        fig2.update_xaxes(showgrid=True, gridcolor="#c5cae9", color="#3d4060", tickfont=dict(color="#3d4060", size=12))
        fig2.update_yaxes(showgrid=True, gridcolor="#c5cae9", color="#3d4060", tickfont=dict(color="#3d4060", size=12))
        st.plotly_chart(fig2, use_container_width=True)

    if st.checkbox("Show full pivot data table", value=False, key="t2_raw"):
        disp_pivot_cols = ["DATE", Col.SYMBOL, Col.CATEGORY]
        for m in pivot_methods:
            pp_col, r_cols, s_cols = METHOD_COLS[m]
            disp_pivot_cols.append(pp_col)
            disp_pivot_cols += r_cols[:n_levels]
            disp_pivot_cols += s_cols[:n_levels]
        disp_pivot_cols = list(dict.fromkeys(disp_pivot_cols))

        df_piv_disp = df_piv_all[df_piv_all[Col.SYMBOL].isin(comp_symbols)].copy()
        df_piv_disp = df_piv_disp[
            (df_piv_disp["DATE"].dt.date >= date_from) &
            (df_piv_disp["DATE"].dt.date <= date_to)
        ]
        cols_to_show = [c for c in disp_pivot_cols if c in df_piv_disp.columns]
        st.dataframe(
            df_piv_disp[cols_to_show].sort_values("DATE", ascending=False).reset_index(drop=True),
            use_container_width=True,
        )
