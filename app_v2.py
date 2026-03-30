"""
app_v3.py — NSE EOD Dashboard · Bullseye Fintech © 2024–2026

New in this version (v3)
─────────────────────────
NEW  Date Range download mode — pick any from/to dates; years are derived automatically
NEW  Calendar popup date inputs for global date filter (DD/MM/YYYY format)
NEW  Quick date-range presets (Last 30/90 days, Last 6 months, YTD, Full year)
NEW  Date range validation with auto-swap if from > to
NEW  Custom R/S level count via number_input (was slider)
NEW  Editable Pivot Values expander — pre-filled with computed defaults, overridable
     → overrides feed through to both the pivot table and the chart
NEW  Pivot chart legend refactored: grouped by method, one PP entry per group,
     R/S entries shown once per method to avoid clutter; legend placed below chart
NEW  Tab-1 legend moved below chart (horizontal, non-overlapping)

Carried from v2
───────────────
BUG  StreamlitAPIException: default symbols not in pivot options  → fixed
BUG  Duplicate filter UIs  → fixed
BUG  Pivot tables rendered separately per symbol  → ONE consolidated HTML matrix
BUG  Pivot chart used latest pivot row  → uses sel_piv_date row
BUG  Cache not cleared after re-download  → st.cache_data.clear() before st.rerun()
BUG  "All Available" since year 2000  → renamed "All Downloaded"
NEW  Sidebar download/export buttons
NEW  Auto-update default OFF
NEW  Camarilla anchor col updated to P_CAM
"""

import os
import time
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

# ═════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Bullseye Fintech — NSE EOD",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═════════════════════════════════════════════════════════════════════════════
# CSS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #58a6ff;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 1.2rem;
    margin-bottom: 0.3rem;
    border-bottom: 1px solid #30363d;
    padding-bottom: 4px;
}

/* ── KPI cards ───────────────────────────────────────────────────────────── */
.kpi-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 14px 18px; margin-bottom: 6px;
}
.kpi-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    color: #8b949e; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px;
}
.kpi-value {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.35rem;
    font-weight: 600; color: #e6edf3; line-height: 1.1;
}
.kpi-delta-pos { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; color:#3fb950; margin-top:3px; }
.kpi-delta-neg { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; color:#f85149; margin-top:3px; }
.kpi-delta-neu { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; color:#8b949e; margin-top:3px; }

/* ── 52-week bar ─────────────────────────────────────────────────────────── */
.wk52-wrap { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px 20px; margin-bottom:14px; }
.wk52-title { font-family:'IBM Plex Mono',monospace; font-size:0.68rem; color:#8b949e; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px; }
.wk52-bar-outer { background:#30363d; border-radius:4px; height:8px; position:relative; margin:8px 0 4px 0; }
.wk52-bar-fill  { background:linear-gradient(90deg,#f85149,#e3b341,#3fb950); border-radius:4px; height:8px; position:absolute; left:0; top:0; }
.wk52-marker    { position:absolute; top:-4px; width:16px; height:16px; background:#fff; border-radius:50%; transform:translateX(-50%); border:2px solid #58a6ff; box-shadow:0 0 6px #58a6ff88; }
.wk52-labels    { display:flex; justify-content:space-between; font-family:'IBM Plex Mono',monospace; font-size:0.72rem; color:#8b949e; margin-top:6px; }
.wk52-cur       { font-family:'IBM Plex Mono',monospace; font-size:0.8rem; color:#58a6ff; font-weight:600; }

/* ── Section title ───────────────────────────────────────────────────────── */
.section-title {
    font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#8b949e;
    letter-spacing:0.12em; text-transform:uppercase;
    border-bottom:1px solid #30363d; padding-bottom:6px; margin:18px 0 12px 0;
}

/* ── Info box ────────────────────────────────────────────────────────────── */
.info-box {
    background:#161b22; border-left:3px solid #58a6ff;
    border-radius:0 6px 6px 0; padding:10px 14px;
    font-size:0.82rem; color:#8b949e; margin-bottom:12px;
}

/* ── Method badges ───────────────────────────────────────────────────────── */
.method-badge   { display:inline-block; border-radius:4px; padding:2px 8px; margin:1px 3px; font-family:'IBM Plex Mono',monospace; font-size:0.7rem; font-weight:600; }
.badge-classic   { background:rgba(88,166,255,0.15); color:#58a6ff; border:1px solid #58a6ff44; }
.badge-fibonacci { background:rgba(227,179,65,0.15);  color:#e3b341; border:1px solid #e3b34144; }
.badge-woodie    { background:rgba(63,185,80,0.15);   color:#3fb950; border:1px solid #3fb95044; }
.badge-camarilla { background:rgba(188,140,255,0.15); color:#bc8cff; border:1px solid #bc8cff44; }

/* ── Pivot consolidated matrix ───────────────────────────────────────────── */
.pivot-matrix-wrap { border-radius:8px; overflow:hidden; border:1px solid #30363d; margin-bottom:20px; }
.pivot-matrix { width:100%; border-collapse:collapse; font-family:'IBM Plex Mono',monospace; font-size:0.82rem; }
.pivot-matrix th, .pivot-matrix td { padding:8px 14px; text-align:right; border-bottom:1px solid #21262d; white-space:nowrap; }
.pivot-matrix th:first-child, .pivot-matrix td:first-child { text-align:left; min-width:60px; }
.pivot-matrix td:first-child { color:#8b949e; font-size:0.72rem; letter-spacing:0.06em; }

/* Method group header row */
.pivot-matrix thead tr.method-row th {
    background:#161b22; font-size:0.68rem; letter-spacing:0.12em;
    text-transform:uppercase; padding:10px 14px; font-weight:600;
}
.pivot-matrix thead tr.method-row th.th-classic   { color:#58a6ff; border-bottom:2px solid #58a6ff44; }
.pivot-matrix thead tr.method-row th.th-fibonacci { color:#e3b341; border-bottom:2px solid #e3b34144; }
.pivot-matrix thead tr.method-row th.th-woodie    { color:#3fb950; border-bottom:2px solid #3fb95044; }
.pivot-matrix thead tr.method-row th.th-camarilla { color:#bc8cff; border-bottom:2px solid #bc8cff44; }
.pivot-matrix thead tr.method-row th.th-label     { color:#8b949e; border-bottom:2px solid #30363d; }

/* Symbol sub-header row */
.pivot-matrix thead tr.sym-row th {
    background:#21262d; color:#8b949e; font-size:0.68rem;
    letter-spacing:0.06em; text-transform:uppercase; padding:6px 14px;
}

/* Data rows */
.pivot-matrix tbody tr.res-row td { background:#1f1419; color:#f85149; }
.pivot-matrix tbody tr.pp-row  td { background:#1a1a14; color:#e3b341; font-weight:600; }
.pivot-matrix tbody tr.sup-row td { background:#131a14; color:#3fb950; }
.pivot-matrix tbody tr:hover td   { filter:brightness(1.15); }
.pivot-matrix td.na-val { color:#30363d !important; }

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { background:#161b22; border-bottom:1px solid #30363d; gap:0; }
.stTabs [data-baseweb="tab"] {
    font-family:'IBM Plex Mono',monospace; font-size:0.78rem;
    letter-spacing:0.06em; color:#8b949e; padding:10px 24px;
    border-bottom:2px solid transparent;
}
.stTabs [aria-selected="true"] { color:#58a6ff !important; border-bottom:2px solid #58a6ff !important; background:transparent !important; }

div[data-testid="stDataFrame"] { border-radius:8px; overflow:hidden; }
.stDataFrame { font-family:'IBM Plex Mono',monospace !important; font-size:0.8rem; }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═════════════════════════════════════════════════════════════════════════════
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
    font=dict(family="IBM Plex Mono, monospace", color="#8b949e", size=11),
    xaxis=dict(gridcolor="#21262d", zeroline=False),
    yaxis=dict(gridcolor="#21262d", zeroline=False),
    margin=dict(l=10, r=10, t=36, b=10),
    hovermode="x unified",
)

# Base legend style — merged into update_layout calls that customise the legend.
# Kept separate from PLOTLY_LAYOUT to avoid duplicate keyword errors when callers
# pass their own legend=dict(...) alongside **PLOTLY_LAYOUT.
_LEGEND_BASE = dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1)

METHOD_COLORS = {
    "Classic":   {"pp": "#58a6ff", "r": ["#ff7b72", "#f85149", "#c93c37"], "s": ["#56d364", "#3fb950", "#26a641"]},
    "Fibonacci": {"pp": "#e3b341", "r": ["#ffd700", "#e3b341", "#b8912b"], "s": ["#90d4a4", "#7ec89a", "#5faa7d"]},
    "Woodie":    {"pp": "#3fb950", "r": ["#ff9966", "#ff6633", "#cc4422"], "s": ["#66ccff", "#33aaff", "#1188dd"]},
    "Camarilla": {"pp": "#bc8cff", "r": ["#ffaacc", "#ff77aa", "#ee4488", "#cc2266"],
                  "s": ["#aaddff", "#77bbff", "#4499ee", "#1166cc"]},
}

PRICE_LINE_COLORS = [
    "#58a6ff", "#e3b341", "#3fb950", "#bc8cff",
    "#ff7b72", "#ffa657", "#2ea043", "#6e7681",
]

# Use Col from EoD_module as the single source of truth.
# METHOD_COLS maps method name → (pp_col, [r_cols], [s_cols])
# Camarilla now correctly uses P_CAM (prev-close) not P_CLASSIC (BUG-E6 fix)
METHOD_COLS = {
    "Classic":   (Col.P_CLASSIC, [Col.CL_R1,  Col.CL_R2,  Col.CL_R3],            [Col.CL_S1,  Col.CL_S2,  Col.CL_S3]),
    "Fibonacci": (Col.P_CLASSIC, [Col.FIB_R1, Col.FIB_R2, Col.FIB_R3],           [Col.FIB_S1, Col.FIB_S2, Col.FIB_S3]),
    "Woodie":    (Col.P_WOODIE,  [Col.WD_R1,  Col.WD_R2],                         [Col.WD_S1,  Col.WD_S2]),
    "Camarilla": (Col.P_CAM,     [Col.CAM_R1, Col.CAM_R2, Col.CAM_R3, Col.CAM_R4],
                                 [Col.CAM_S1, Col.CAM_S2, Col.CAM_S3, Col.CAM_S4]),
}

ALL_METHODS = ["Classic", "Fibonacci", "Woodie", "Camarilla"]

# ═════════════════════════════════════════════════════════════════════════════
# DATA LOADERS  (cached)
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
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
    df = pd.read_csv(path)
    df.columns = [c.strip().upper() for c in df.columns]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            df["DATE"] = pd.to_datetime(df["DATE"], format=fmt)
            break
        except (ValueError, TypeError):
            continue
    return df


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def _safe_default(options: list, candidates: list) -> list:
    """Return candidates filtered to only those present in options."""
    option_set = set(options)
    valid = [c for c in candidates if c in option_set]
    return valid if valid else (options[:1] if options else [])


def _fmt(v, decimals: int = 2) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:,.{decimals}f}"


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📈 Bullseye Fintech")
    st.markdown("### NSE EOD Dashboard")

    # ── Settings ──────────────────────────────────────────────────────────────
    st.markdown("### ⚙️ Settings")
    auto_update = st.toggle(
        "Auto-update on launch",
        value=st.session_state.get("auto_update_enabled", AUTO_UPDATE_DEFAULT),
        help="Automatically fetch previous trading day's data when the app starts.",
    )
    st.session_state.auto_update_enabled = auto_update

    # ── Data Management ────────────────────────────────────────────────────────
    st.markdown("### 🗄️ Data")
    available_years = get_available_years()
    if available_years:
        st.markdown("**Available years — click to load:**")
        year_btn_cols = st.columns(min(len(available_years), 4))
        for i, yr in enumerate(available_years):
            with year_btn_cols[i % len(year_btn_cols)]:
                if st.button(
                    f"📊 {yr}", key=f"yr_btn_{yr}", use_container_width=True
                ):
                    st.session_state.selected_year = yr
                    st.session_state.auto_update_done = True
                    st.rerun()
        st.success(f"✓ {len(available_years)} year(s) on disk", icon="✅")
    else:
        st.info("No data yet. Download below.")

    # ── Export / Download current data ────────────────────────────────────────
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

    # ── Download from NSE ─────────────────────────────────────────────────────
    st.markdown("### 📥 Download from NSE")
    current_year = datetime.now().year
    year_options = list(range(2000, current_year + 1))

    download_mode = st.radio(
        "Mode",
        ["Single Year", "Multiple Years", "Date Range", "All Downloaded"],
        label_visibility="collapsed",
        key="dl_mode",
    )
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
        _jan1  = _today.replace(month=1, day=1)
        dl_date_from = st.date_input(
            "From date",
            value=_jan1,
            min_value=datetime(2000, 1, 1).date(),
            max_value=_today,
            key="dl_date_from",
            help="Start date for the data download range",
        )
        dl_date_to = st.date_input(
            "To date",
            value=_today,
            min_value=datetime(2000, 1, 1).date(),
            max_value=_today,
            key="dl_date_to",
            help="End date for the data download range",
        )
        if dl_date_from > dl_date_to:
            st.error("⚠️ 'From' date must be before 'To' date.")
            selected_years = []
        else:
            selected_years = list(range(dl_date_from.year, dl_date_to.year + 1))
            st.caption(f"Will download {len(selected_years)} year(s): {selected_years[0]}–{selected_years[-1]}")
    else:
        # BUG-A3 fix: "All Downloaded" = only what's already on disk
        selected_years = available_years
        st.caption(f"Will re-process {len(available_years)} year(s) on disk.")

    force_dl = st.checkbox("Force re-download (overwrite)", value=False, key="dl_force")
    incr_dl  = st.checkbox("Incremental (new dates only)", value=True,  key="dl_incr")

    if st.button("🚀 Start Download", type="primary", use_container_width=True):
        if not selected_years:
            st.warning("Select at least one year.")
        else:
            for yr in selected_years:
                with st.status(f"Downloading {yr}…", expanded=True) as _s:
                    ok, msg = download_year_data(
                        yr,
                        force_redownload=force_dl,
                        incremental=incr_dl,
                        progress_callback=st.write,
                    )
                    if ok:
                        _s.update(label=f"✅ {yr} downloaded", state="complete")
                        with st.status(f"Computing pivots for {yr}…"):
                            p_ok, p_msg = compute_pivot_points(yr)
                            (st.success if p_ok else st.warning)(p_msg)
                    else:
                        _s.update(label=f"❌ {yr} failed", state="error")
                        st.error(msg)
                    time.sleep(0.3)
            # BUG-A2 fix: clear cache so re-downloaded data is loaded fresh
            st.cache_data.clear()
            st.session_state.auto_update_done = True
            st.rerun()

    # ── Delete ────────────────────────────────────────────────────────────────
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

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"<span style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;"
        f"color:#8b949e;word-break:break-all;'>📁 {DATA_DIR}</span>",
        unsafe_allow_html=True,
    )

# ═════════════════════════════════════════════════════════════════════════════
# AUTO-UPDATE
# ═════════════════════════════════════════════════════════════════════════════
if "auto_update_done" not in st.session_state:
    st.session_state.auto_update_done = False

if st.session_state.get("auto_update_enabled", False) and not st.session_state.auto_update_done:
    with st.sidebar:
        with st.status("🔄 Auto-updating…", expanded=True) as _au:
            ok, msg = run_auto_update(progress_callback=st.write)
            _au.update(
                label="✅ Up to date" if ok else "⚠ Auto-update failed",
                state="complete" if ok else "error",
            )
            if not ok:
                st.warning(msg)
    st.session_state.auto_update_done = True
    st.cache_data.clear()

# ═════════════════════════════════════════════════════════════════════════════
# LOAD DATA FOR SELECTED YEAR
# ═════════════════════════════════════════════════════════════════════════════
df_raw = None
available_years = get_available_years()  # refresh after potential download

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

# ── Welcome screen ────────────────────────────────────────────────────────────
if df_raw is None:
    st.markdown("""
## 📈 Bullseye Fintech — NSE EOD Dashboard
Open the **sidebar** (≡ top-left) and use **Download from NSE** to get started.
    """)
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# GLOBAL FILTER BAR
# — one set of filters, shared across both tabs
# — Tab 2 adds ONLY pivot-specific controls (method, levels, date)
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">Filters</div>', unsafe_allow_html=True)

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
    sym_pool     = df_raw[df_raw[Col.CATEGORY].isin(sel_cats)]
    all_symbols  = sorted(sym_pool[Col.SYMBOL].dropna().unique().tolist())
    # BUG FIX: default must be within options
    default_syms = _safe_default(all_symbols, st.session_state.get("g_sym_prev", all_symbols[:1]))
    sel_symbols  = st.multiselect(
        "Symbol", all_symbols,
        default=default_syms,
        key="g_sym",
    )
    st.session_state["g_sym_prev"] = sel_symbols
    if not sel_symbols:
        sel_symbols = all_symbols[:1] if all_symbols else []

min_date = df_raw["DATE"].min().date()
max_date = df_raw["DATE"].max().date()

with fc3:
    date_from = st.date_input(
        "📅 From",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
        key="g_from",
        help="Click to open calendar and pick a start date",
        format="DD/MM/YYYY",
    )

with fc4:
    date_to = st.date_input(
        "📅 To",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
        key="g_to",
        help="Click to open calendar and pick an end date",
        format="DD/MM/YYYY",
    )

with fc5:
    # Quick date-range presets
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
        else:  # Full year
            _new_from = min_date
        date_from = max(_new_from, min_date)
        date_to   = _today

# Validate date range
if date_from > date_to:
    st.error("⚠️ 'From' date must not be after 'To' date. Swapping values.")
    date_from, date_to = date_to, date_from

# Apply global filters
df_filtered = df_raw[
    (df_raw[Col.CATEGORY].isin(sel_cats)) &
    (df_raw[Col.SYMBOL].isin(sel_symbols)) &
    (df_raw["DATE"].dt.date >= date_from) &
    (df_raw["DATE"].dt.date <= date_to)
].sort_values("DATE").reset_index(drop=True)

if df_filtered.empty:
    st.warning("No data for the selected filters. Adjust your selection.")
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["📊  OHLCV Summary", "🎯  Pivot Points"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — OHLCV
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    # Symbol detail selector (only shown when multiple symbols are selected)
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

    # ── KPI cards ──────────────────────────────────────────────────────────────
    show_kpi = st.checkbox("Show KPI cards", value=True, key="t1_kpi")
    if show_kpi:
        dt_str = latest["DATE"].strftime("%d %b %Y") if pd.notna(latest["DATE"]) else "Latest"
        st.markdown(
            f'<div class="section-title">Latest Session — {dt_str}</div>',
            unsafe_allow_html=True,
        )
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

        cl   = latest.get(Col.CLOSE, np.nan)
        prev = latest.get(Col.PREV_CLOSE, np.nan)
        chg  = cl - prev if pd.notna(cl) and pd.notna(prev) else np.nan
        chgp = (chg / prev * 100) if pd.notna(chg) and prev != 0 else np.nan

        _kpi(k1, "Open",       _fmt(latest.get(Col.OPEN)))
        _kpi(k2, "High",       _fmt(latest.get(Col.HIGH)))
        _kpi(k3, "Low",        _fmt(latest.get(Col.LOW)))
        _kpi(k4, "Close",      _fmt(cl),   chg, chgp)
        _kpi(k5, "Prev Close", _fmt(prev))
        _kpi(k6, "Volume",     _fmt(latest.get(Col.NET_TRDQTY), 0))

    # ── 52-week range ──────────────────────────────────────────────────────────
    show_52 = st.checkbox("Show 52-week range", value=True, key="t1_52")
    if show_52:
        hi52 = latest.get(Col.HI_52, np.nan)
        lo52 = latest.get(Col.LO_52, np.nan)
        cur  = latest.get(Col.CLOSE, np.nan)
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

    # ── Price chart ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Chart</div>', unsafe_allow_html=True)
    ch_c1, ch_c2 = st.columns([2, 3])
    with ch_c1:
        chart_type = st.selectbox(
            "Type", ["Candlestick", "Line (Close)", "OHLC Bar"], key="t1_ctype"
        )
    with ch_c2:
        overlays = st.multiselect(
            "Overlays",
            ["Volume", "20-Day MA", "50-Day MA", "Bollinger Bands"],
            default=["Volume"],
            key="t1_overlays",
        )

    show_vol = "Volume"          in overlays
    show_m20 = "20-Day MA"       in overlays
    show_m50 = "50-Day MA"       in overlays
    show_bb  = "Bollinger Bands" in overlays

    rows        = 2 if show_vol else 1
    row_heights = [0.7, 0.3] if show_vol else [1.0]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    x  = df_sym["DATE"]
    op = df_sym.get(Col.OPEN,  None)
    hi = df_sym.get(Col.HIGH,  None)
    lo = df_sym.get(Col.LOW,   None)
    cl = df_sym.get(Col.CLOSE, None)

    if chart_type == "Candlestick" and all(v is not None for v in [op, hi, lo, cl]):
        fig.add_trace(go.Candlestick(
            x=x, open=op, high=hi, low=lo, close=cl,
            name=detail_sym,
            increasing_line_color="#3fb950", decreasing_line_color="#f85149",
            legendgroup="price",
        ), row=1, col=1)
    elif chart_type == "OHLC Bar" and all(v is not None for v in [op, hi, lo, cl]):
        fig.add_trace(go.Ohlc(
            x=x, open=op, high=hi, low=lo, close=cl,
            name=detail_sym,
            increasing_line_color="#3fb950", decreasing_line_color="#f85149",
            legendgroup="price",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=x, y=cl, name=detail_sym,
            line=dict(color="#58a6ff", width=1.5), mode="lines", legendgroup="price",
        ), row=1, col=1)

    if show_m20 and cl is not None:
        fig.add_trace(go.Scatter(
            x=x, y=cl.rolling(20).mean(), name="MA 20",
            line=dict(color="#e3b341", width=1, dash="dot"), mode="lines",
        ), row=1, col=1)

    if show_m50 and cl is not None:
        fig.add_trace(go.Scatter(
            x=x, y=cl.rolling(50).mean(), name="MA 50",
            line=dict(color="#bc8cff", width=1, dash="dot"), mode="lines",
        ), row=1, col=1)

    if show_bb and cl is not None:
        bb_mid = cl.rolling(20).mean()
        bb_std = cl.rolling(20).std()
        bb_up  = bb_mid + 2 * bb_std
        bb_dn  = bb_mid - 2 * bb_std
        fig.add_trace(go.Scatter(
            x=x, y=bb_up, name="BB Upper",
            line=dict(color="#58a6ff", width=0.8, dash="dash"), mode="lines",
            legendgroup="bb",
        ), row=1, col=1)
        # BUG-A10 fix: fill targets BB upper trace explicitly
        fig.add_trace(go.Scatter(
            x=x, y=bb_dn, name="BB Lower",
            line=dict(color="#58a6ff", width=0.8, dash="dash"), mode="lines",
            fill="tonexty", fillcolor="rgba(88,166,255,0.05)",
            legendgroup="bb", showlegend=False,
        ), row=1, col=1)

    if show_vol and Col.NET_TRDQTY in df_sym.columns:
        pv = df_sym[Col.PREV_CLOSE] if Col.PREV_CLOSE in df_sym.columns else df_sym[Col.CLOSE].shift(1)
        pv = pv.where(pd.notna(pv), df_sym[Col.CLOSE].shift(1))  # BUG-A7 fix: per-row fallback
        colors_vol = [
            "#3fb950" if (c >= p) else "#f85149"
            for c, p in zip(df_sym[Col.CLOSE].fillna(0), pv.fillna(0))
        ]
        fig.add_trace(go.Bar(
            x=x, y=df_sym[Col.NET_TRDQTY], name="Volume",
            marker_color=colors_vol, opacity=0.7, legendgroup="vol",
        ), row=2, col=1)

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=f"{detail_sym} — {chart_type}", font=dict(size=13, color="#e6edf3")),
        xaxis_rangeslider_visible=False,
        height=620 if show_vol else 500,
        legend=dict(
            **_LEGEND_BASE,
            orientation="h",
            x=0, xanchor="left",
            y=-0.12, yanchor="top",
            font=dict(size=10),
            tracegroupgap=6,
            itemwidth=40,
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#21262d")
    fig.update_yaxes(showgrid=True, gridcolor="#21262d")
    st.plotly_chart(fig, use_container_width=True)

    # Overlay notes
    n_rows_sym  = len(df_sym)
    warn_parts  = []
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
            f'<span style="color:#8b949e;font-size:0.78rem;">Widen the date range to see them.</span></div>',
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

    # ── Pivot-specific controls (compact, inline — no separate "Comparison Settings") ──
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
        # Custom number of R/S levels: 1–4
        n_levels = st.number_input(
            "R / S levels",
            min_value=1, max_value=4, value=2, step=1,
            key="t2_levels",
            help="Number of Resistance and Support levels shown (1–4). Woodie max=2, others max=3 or 4.",
        )
        n_levels = int(n_levels)

    with t2c3:
        # Symbol pool for pivot tab comes from GLOBAL symbol filter
        # (BUG FIX: intersect with what's in the pivot CSV)
        _piv_syms_all = sorted(df_piv_all[Col.SYMBOL].dropna().unique().tolist()) \
            if Col.SYMBOL in df_piv_all.columns else []
        _valid_syms = _safe_default(_piv_syms_all, sel_symbols)

        # Date selector — filtered to available dates for valid symbols
        _date_pool = sorted(
            df_piv_all[df_piv_all[Col.SYMBOL].isin(_valid_syms)]["DATE"].dt.date.unique()
        ) if _valid_syms and not df_piv_all.empty else []
        # BUG-A8 fix: handle empty _date_pool gracefully
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

    # Symbols to compare — from global filter, guaranteed within pivot options
    comp_symbols = _valid_syms  # already intersected

    if not comp_symbols:
        st.info("No pivot data for the selected symbols. Try a different symbol.")
        st.stop()

    # ── Pre-fetch pivot rows for selected date ─────────────────────────────────
    piv_rows: dict = {}
    for sym in comp_symbols:
        _r = df_piv_all[
            (df_piv_all[Col.SYMBOL] == sym) &
            (df_piv_all["DATE"].dt.date == sel_piv_date)
        ]
        piv_rows[sym] = _r.iloc[0] if not _r.empty else None

    # ── Editable Pivot Values ──────────────────────────────────────────────────
    with st.expander("✏️ Edit Pivot Values (override defaults for chart)", expanded=False):
        st.markdown(
            '<div class="info-box">📌 The fields below are pre-filled with computed defaults. '
            'Edit any value to override it on the chart and table below. '
            'Leave as-is to use the computed value.</div>',
            unsafe_allow_html=True,
        )
        # Build editable overrides keyed by (sym, method, level_key)
        pivot_overrides: dict = {}
        for sym in comp_symbols:
            row = piv_rows.get(sym)
            st.markdown(
                f'<div class="section-title" style="margin-top:10px">{sym}</div>',
                unsafe_allow_html=True,
            )
            for method in pivot_methods:
                pp_col, r_cols, s_cols = METHOD_COLS[method]
                mc_badge = {"Classic": "badge-classic", "Fibonacci": "badge-fibonacci",
                            "Woodie": "badge-woodie", "Camarilla": "badge-camarilla"}.get(method, "")
                st.markdown(
                    f'<span class="method-badge {mc_badge}">{method}</span>',
                    unsafe_allow_html=True,
                )
                # Build level list: R-levels desc, PP, S-levels asc
                levels = []
                for j, rc in enumerate(r_cols[:n_levels]):
                    levels.append((f"R{j+1}", rc))
                levels.append(("PP", pp_col))
                for j, sc in enumerate(s_cols[:n_levels]):
                    levels.append((f"S{j+1}", sc))

                ncols = len(levels)
                edit_cols = st.columns(ncols)
                for ci, (lbl, col_key) in enumerate(levels):
                    default_v = float(row.get(col_key, 0.0)) if (row is not None and pd.notna(row.get(col_key, np.nan))) else 0.0
                    ov_key = f"ov_{sym}_{method}_{col_key}"
                    with edit_cols[ci]:
                        new_val = st.number_input(
                            lbl,
                            value=default_v,
                            step=0.01,
                            format="%.2f",
                            key=ov_key,
                            help=f"Default: {default_v:,.2f}",
                        )
                    pivot_overrides[(sym, method, col_key)] = new_val

    # Helper that checks overrides first
    def _cell_val(sym: str, method: str, col_key: str) -> float:
        ov = pivot_overrides.get((sym, method, col_key))
        if ov is not None:
            return float(ov)
        row = piv_rows.get(sym)
        if row is None:
            return np.nan
        v = row.get(col_key, np.nan)
        return float(v) if pd.notna(v) else np.nan

    # ── CONSOLIDATED PIVOT TABLE ───────────────────────────────────────────────
    st.markdown(
        f'<div class="section-title">Pivot Levels — {sel_piv_date}</div>',
        unsafe_allow_html=True,
    )

    # Build the HTML table
    n_sym = len(comp_symbols)
    n_met = len(pivot_methods)
    total_data_cols = n_sym * n_met

    def _td(v: float, cls: str = "") -> str:
        cls_attr = f' class="{cls}"' if cls else ""
        if np.isnan(v):
            return f'<td class="na-val"{cls_attr.replace(" class=\"na-val\"", "")}>—</td>'
        return f'<td{cls_attr}>{v:,.2f}</td>'

    # ── Build thead ────────────────────────────────────────────────────────────
    method_class = {
        "Classic": "th-classic", "Fibonacci": "th-fibonacci",
        "Woodie": "th-woodie",   "Camarilla": "th-camarilla",
    }

    thead = '<thead>'
    # Row 1: Method group headers
    thead += '<tr class="method-row">'
    thead += '<th class="th-label">Level</th>'
    for m in pivot_methods:
        css = method_class.get(m, "")
        colspan = n_sym
        thead += f'<th class="{css}" colspan="{colspan}">{m}</th>'
    thead += '</tr>'

    # Row 2: Symbol sub-headers (only shown if >1 symbol OR always for clarity)
    thead += '<tr class="sym-row">'
    thead += '<th></th>'
    for _m in pivot_methods:
        for sym in comp_symbols:
            thead += f'<th>{sym}</th>'
    thead += '</tr>'
    thead += '</thead>'

    # ── Build tbody ────────────────────────────────────────────────────────────
    tbody = '<tbody>'

    # Determine actual available R/S per method (cap at n_levels)
    def _r_indices(method: str) -> list:
        _, r_cols, _ = METHOD_COLS[method]
        return list(range(1, min(n_levels, len(r_cols)) + 1))

    def _s_indices(method: str) -> list:
        _, _, s_cols = METHOD_COLS[method]
        return list(range(1, min(n_levels, len(s_cols)) + 1))

    all_r_idx = sorted(
        set(i for m in pivot_methods for i in _r_indices(m)),
        reverse=True
    )
    all_s_idx = sorted(
        set(i for m in pivot_methods for i in _s_indices(m))
    )

    # Resistance rows
    for i in all_r_idx:
        tbody += '<tr class="res-row">'
        tbody += f'<td>R{i}</td>'
        for m in pivot_methods:
            _, r_cols, _ = METHOD_COLS[m]
            for sym in comp_symbols:
                if i <= len(r_cols):
                    v = _cell_val(sym, m, r_cols[i - 1])
                    tbody += _td(v)
                else:
                    tbody += '<td class="na-val">—</td>'
        tbody += '</tr>'

    # PP row
    tbody += '<tr class="pp-row">'
    tbody += '<td>PP</td>'
    for m in pivot_methods:
        pp_col, _, _ = METHOD_COLS[m]
        for sym in comp_symbols:
            v = _cell_val(sym, m, pp_col)
            tbody += _td(v)
    tbody += '</tr>'

    # Support rows
    for i in all_s_idx:
        tbody += '<tr class="sup-row">'
        tbody += f'<td>S{i}</td>'
        for m in pivot_methods:
            _, _, s_cols = METHOD_COLS[m]
            for sym in comp_symbols:
                if i <= len(s_cols):
                    v = _cell_val(sym, m, s_cols[i - 1])
                    tbody += _td(v)
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
        st.markdown(
            '<div class="section-title">Price Chart with Pivot Levels</div>',
            unsafe_allow_html=True,
        )
        fig2 = go.Figure()

        # ── Price lines ────────────────────────────────────────────────────────
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

        # ── Pivot horizontal lines ─────────────────────────────────────────────
        # One legend entry per method (for PP) — R/S lines share the group but
        # are shown as "Rn" / "Sn" only once across all methods to avoid clutter.
        x_range = [pd.Timestamp(date_from), pd.Timestamp(date_to)]
        _rs_legend_shown: set = set()  # track which "R1","S2",… entries already have a legend item

        for si, sym in enumerate(comp_symbols):
            row = piv_rows.get(sym)
            if row is None:
                continue

            sym_prefix = f"[{sym}] " if n_sym > 1 else ""

            for mi, method in enumerate(pivot_methods):
                pp_col, r_cols, s_cols = METHOD_COLS[method]
                mc  = METHOD_COLORS[method]
                grp = f"{sym}_{method}" if n_sym > 1 else method

                # PP — always show in legend as group title entry
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

                # R levels
                for j, rc in enumerate(r_cols[:n_levels]):
                    v = _cell_val(sym, method, rc)
                    if not np.isnan(v):
                        legend_key = f"{method}_R{j+1}"
                        show_leg   = legend_key not in _rs_legend_shown
                        if show_leg:
                            _rs_legend_shown.add(legend_key)
                        fig2.add_trace(go.Scatter(
                            x=x_range, y=[v, v],
                            name=f"R{j+1}",
                            legendgroup=grp,
                            showlegend=show_leg,
                            line=dict(color=mc["r"][j % len(mc["r"])], width=1.2, dash="dot"),
                            mode="lines",
                            hovertemplate=f"<b>{sym} {method} R{j+1}</b>: ₹%{{y:,.2f}}<extra></extra>",
                        ))

                # S levels
                for j, sc in enumerate(s_cols[:n_levels]):
                    v = _cell_val(sym, method, sc)
                    if not np.isnan(v):
                        legend_key = f"{method}_S{j+1}"
                        show_leg   = legend_key not in _rs_legend_shown
                        if show_leg:
                            _rs_legend_shown.add(legend_key)
                        fig2.add_trace(go.Scatter(
                            x=x_range, y=[v, v],
                            name=f"S{j+1}",
                            legendgroup=grp,
                            showlegend=show_leg,
                            line=dict(color=mc["s"][j % len(mc["s"])], width=1.2, dash="dot"),
                            mode="lines",
                            hovertemplate=f"<b>{sym} {method} S{j+1}</b>: ₹%{{y:,.2f}}<extra></extra>",
                        ))

        syms_lbl = ", ".join(comp_symbols)
        meth_lbl = " + ".join(pivot_methods)
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(
                text=f"{syms_lbl} — {meth_lbl} | {sel_piv_date}",
                font=dict(size=13, color="#e6edf3"),
            ),
            height=580,
            legend=dict(
                **_LEGEND_BASE,
                orientation="h",
                x=0, xanchor="left",
                y=-0.15, yanchor="top",
                font=dict(size=10),
                tracegroupgap=8,
                groupclick="toggleitem",
                itemwidth=40,
            ),
        )
        fig2.update_xaxes(showgrid=True, gridcolor="#21262d")
        fig2.update_yaxes(showgrid=True, gridcolor="#21262d")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Optional full data table ───────────────────────────────────────────────
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