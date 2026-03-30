# build_app.spec
# PyInstaller spec for Bullseye Fintech NSE EOD Dashboard
#
# Usage:
#   pyinstaller build_app.spec
#
# This bundles Streamlit + the app into a single-folder dist.

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_all

block_cipher = None

# Collect all Streamlit static assets and data files
streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all("streamlit")
plotly_datas, plotly_binaries, plotly_hiddenimports = collect_all("plotly")

datas = (
    streamlit_datas
    + plotly_datas
    + [
        ("app_v2.py",    "."),
        ("EoD_module.py", "."),
        ("launcher.py",  "."),
    ]
)

hiddenimports = (
    streamlit_hiddenimports
    + plotly_hiddenimports
    + [
        "streamlit.runtime.scriptrunner.magic_funcs",
        "streamlit.web.cli",
        "pandas",
        "numpy",
        "plotly.graph_objs",
        "plotly.subplots",
        "requests",
        "EoD_module",
    ]
)

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=streamlit_binaries + plotly_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "PIL"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,           # no console window; launcher manages its own
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico",         # replace with your .ico path or remove line
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BullseyeNSE",
)
