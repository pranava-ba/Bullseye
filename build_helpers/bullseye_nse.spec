# bullseye_nse.spec
# PyInstaller spec file for Bullseye Fintech — NSE EOD Dashboard
#
# Build with:
#   pyinstaller bullseye_nse.spec
#
# CHANGES from v2
# ────────────────
# 1. launcher.py uses multiprocessing.Process — added multiprocessing hidden
#    imports and streamlit.web.bootstrap.
# 2. copy_metadata() added for every package that calls
#    importlib.metadata.version() at import time.  Without the .dist-info
#    folders in the bundle those calls raise PackageNotFoundError and crash
#    the child process before Streamlit even starts.

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

# ── Collect Streamlit static assets ───────────────────────────────────────────
streamlit_datas = collect_data_files("streamlit", include_py_files=False)

# ── Collect pandas_market_calendars exchange data ─────────────────────────────
pmc_datas = collect_data_files("pandas_market_calendars")

# ── Collect plotly static assets ──────────────────────────────────────────────
plotly_datas = collect_data_files("plotly")

# ── Collect polars shared libraries ───────────────────────────────────────────
polars_datas = collect_data_files("polars")

# ── Copy .dist-info metadata directories ──────────────────────────────────────
# Several packages call importlib.metadata.version("<pkg>") at import time.
# Without the .dist-info folder bundled, that raises PackageNotFoundError and
# kills the child process before Streamlit starts.
#
# copy_metadata() raises PackageNotFoundError at *build* time if a package is
# listed but not installed (e.g. "validators" is an optional dep that may be
# absent). _safe_meta() silently skips missing packages so the build succeeds
# regardless of which optional deps are present in the build environment.

def _safe_meta(pkg):
    try:
        return copy_metadata(pkg)
    except Exception:
        return []

pkg_metadata = (
    _safe_meta("streamlit")
    + _safe_meta("altair")
    + _safe_meta("pydeck")
    + _safe_meta("validators")
    + _safe_meta("click")
    + _safe_meta("rich")
    + _safe_meta("packaging")
    + _safe_meta("requests")
    + _safe_meta("pandas")
    + _safe_meta("numpy")
    + _safe_meta("plotly")
    + _safe_meta("polars")
    + _safe_meta("pandas_market_calendars")
    + _safe_meta("exchange_calendars")
    + _safe_meta("pytz")
    + _safe_meta("tornado")
    + _safe_meta("watchdog")
    + _safe_meta("gitpython")
    + _safe_meta("tzdata")
)

all_datas = streamlit_datas + pmc_datas + plotly_datas + polars_datas + pkg_metadata

# ── Hidden imports that PyInstaller misses ────────────────────────────────────
hidden_imports = [
    # Streamlit internals
    "streamlit",
    "streamlit.web",
    "streamlit.web.cli",
    "streamlit.web.bootstrap",
    "streamlit.runtime",
    "streamlit.runtime.scriptrunner",
    "streamlit.runtime.caching",
    "streamlit.components.v1",

    # multiprocessing — needed for freeze_support() + Process in launcher
    "multiprocessing",
    "multiprocessing.spawn",
    "multiprocessing.forkserver",
    "multiprocessing.popen_spawn_win32",

    # Polars (Rust extension — must be explicitly listed)
    "polars",
    "polars._typing",

    # pandas_market_calendars & dependencies
    "pandas_market_calendars",
    "exchange_calendars",
    "pytz",
    "toolz",
    "multipledispatch",

    # plotly
    "plotly",
    "plotly.graph_objects",
    "plotly.subplots",

    # Standard extras that Streamlit needs at runtime
    "altair",
    "packaging",
    "click",
    "tornado",
    "watchdog",
    "gitpython",
    "pydeck",
    "rich",
    "validators",
    "tzdata",
]

hidden_imports += collect_submodules("streamlit")
hidden_imports += collect_submodules("pandas_market_calendars")
hidden_imports += collect_submodules("exchange_calendars")

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=all_datas + [
        # app_v2.py and EoD_module.py go to "." = _internal/ in PyInstaller 6.x.
        # launcher.py finds them via sys._MEIPASS (which points to _internal/).
        ("app_v2.py",     "."),
        ("EoD_module.py", "."),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "scipy",
        "sklearn",
        "IPython",
        "notebook",
        "pytest",
        "unittest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BullseyeNSE",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    # icon="icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BullseyeNSE",
)
