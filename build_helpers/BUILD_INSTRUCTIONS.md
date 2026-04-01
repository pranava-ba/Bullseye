# Building the Bullseye Fintech NSE EOD Dashboard EXE

> **Platform**: Windows 10/11 (64-bit)  
> **Python**: 3.11 recommended (3.10 minimum, 3.12 works but test carefully)  
> **Time**: ~10–20 minutes for first build

---

## File Overview

| File | Purpose |
|---|---|
| `app_v2.py` | Streamlit front-end (main app) |
| `EoD_module.py` | NSE download, processing & pivot engine |
| `launcher.py` | EXE entry point — boots Streamlit & opens browser |
| `requirements.txt` | Python package dependencies |
| `bullseye_nse.spec` | PyInstaller build specification |
| `bullseye_nse.iss` | Inno Setup installer script (optional) |

---

## Step 1 — Set Up a Clean Python Environment

```powershell
# Create and activate a dedicated virtual environment
python -m venv .venv
.venv\Scripts\activate

# Upgrade pip to latest
python -m pip install --upgrade pip
```

---

## Step 2 — Install Dependencies

```powershell
pip install -r requirements.txt

# Install PyInstaller separately (not listed in requirements.txt to
# keep the runtime requirements clean)
pip install pyinstaller==6.6.0
```

> **Optional**: Install UPX for smaller binaries.  
> Download from https://upx.github.io/ and add to your `PATH`.  
> If UPX is absent PyInstaller will warn but the build will still succeed.

---

## Step 3 — Prepare Project Directory

Place all files in the **same folder**:

```
project/
├── app_v2.py
├── EoD_module.py
├── launcher.py
├── requirements.txt
├── bullseye_nse.spec
├── bullseye_nse.iss     ← optional (Inno Setup installer)
└── icon.ico             ← optional (32×32 or 256×256 Windows icon)
```

> If you have no `icon.ico`, remove the `icon="icon.ico"` line from
> `bullseye_nse.spec` and the `SetupIconFile` line from `bullseye_nse.iss`
> before building.

---

## Step 4 — Build the EXE

```powershell
# Make sure you are in the project folder and the venv is active
cd path\to\project
pyinstaller bullseye_nse.spec
```

PyInstaller will:
1. Analyse all imports.
2. Bundle Python, your code, Streamlit, Polars, plotly, etc.
3. Write the output to `dist\BullseyeNSE\`.

The EXE to distribute is `dist\BullseyeNSE\BullseyeNSE.exe`.

### Expected build output

```
dist\
└── BullseyeNSE\
    ├── BullseyeNSE.exe   ← launcher
    ├── app_v2.py
    ├── EoD_module.py
    ├── _internal\        ← bundled Python runtime + packages
    │   ├── streamlit\
    │   ├── polars\
    │   └── ...
    └── ...
```

---

## Step 5 — Test the Build

```powershell
# Double-click or run from PowerShell:
.\dist\BullseyeNSE\BullseyeNSE.exe
```

A browser tab should open at `http://localhost:8501` (or another free port)
within 5–10 seconds.

### Common test checklist

- [ ] App loads without Python errors in the terminal.
- [ ] Sidebar shows "No data yet. Download below."
- [ ] Select "Single Year → 2024" and click **Start Download** — data downloads.
- [ ] After download, pivot computation runs without errors.
- [ ] Charts render correctly.
- [ ] Export (CSV download) buttons work.

---

## Step 6 — Create the Installer (Optional)

Install **Inno Setup 6** from https://jrsoftware.org/isinfo.php then:

```powershell
# Compile the installer
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" bullseye_nse.iss
```

The output installer will appear in `installer_output\BullseyeNSE_Setup_2.0.0.exe`.

Users simply run the installer — no Python required on their machine.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'streamlit'` inside the EXE

Add any missing module to the `hiddenimports` list in `bullseye_nse.spec` then
rebuild.

### `OSError: [Errno 98] Address already in use`

Port 8501 is taken. The launcher automatically falls back to a free port — wait
for the browser to open at the correct URL shown in the console.

### `Pattern 'pd...' not found in ZIP` warning

This is a **known NSE archive behaviour** fixed in `EoD_module.py` (case-
insensitive match). If it still appears after applying the fixed files, the ZIP
for that date truly has no PD file (e.g. a Saturday that slipped into the
calendar). The date is safely skipped.

### `ValueError: CATEGORY length mismatch`

NSE changed their PD file format. Open a GitHub issue with the filename that
failed — the `process_file()` parser may need updating for the new layout.

### Antivirus flags the EXE

This is common with PyInstaller bundles (false positive). Sign the EXE with a
code-signing certificate to eliminate the warning, or submit the file to your
AV vendor for whitelisting.

### Build is very large (>400 MB)

This is expected — Streamlit, Polars, and plotly are all bundled. Use UPX
(Step 2) to reduce size by ~30 %. Alternatively, create a one-file build by
changing `EXE(..., exclude_binaries=True)` to `exclude_binaries=False` and
adding `a.binaries, a.datas` back into the `EXE()` call — but one-file builds
are slower to start (they self-extract each launch).

---

## Rebuild After Code Changes

```powershell
# Clean previous build artifacts first
Remove-Item -Recurse -Force build, dist

# Rebuild
pyinstaller bullseye_nse.spec
```

---

## Distributing to End Users

1. Zip the `dist\BullseyeNSE\` folder **or** share the Inno Setup installer.
2. Users extract and run `BullseyeNSE.exe` — no Python or pip needed.
3. Data is stored in `%APPDATA%\BullseyeFintech\NSE_Dashboard\data\` so it
   survives app updates.

---

*Bullseye Fintech © 2024–2026*
