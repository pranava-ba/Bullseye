# Bullseye
NSE trade analysis 
---
# Bullseye Fintech NSE EOD — Build & Packaging Instructions

> **Target:** Windows 10/11 x64 · Python 3.11+ · Inno Setup 6+

---

## Files in this package

| File | Purpose |
|------|---------|
| `app_v2.py` | Main Streamlit dashboard (bug-fixed) |
| `EoD_module.py` | Data-download & pivot-computation module |
| `launcher.py` | Entry-point: starts Streamlit, opens browser |
| `requirements.txt` | Python dependencies |
| `build_app.spec` | PyInstaller spec (controls bundling) |
| `BullseyeNSE_Installer.iss` | Inno Setup installer script |

---

## Step 0 — Prerequisites

1. **Python 3.11 or 3.12** (64-bit) — [python.org](https://www.python.org/downloads/)
2. **Inno Setup 6** — already installed ✓
3. A dedicated virtual environment is **strongly recommended**.

```
python -m venv .venv
.venv\Scripts\activate
```

---

## Step 1 — Install dependencies

```
pip install -r requirements.txt
pip install pyinstaller
```

> If you see `UPX not found` warnings during the PyInstaller build, that is fine — UPX is optional. The build will succeed without it.

---

## Step 2 — (Optional) Create an icon

Place a `icon.ico` file in the same folder as `build_app.spec`.  
If you skip this, remove or comment out the `icon="icon.ico"` line in `build_app.spec` and the `; SetupIconFile=icon.ico` line in the `.iss` file.

---

## Step 3 — Build with PyInstaller

Make sure your virtual environment is active, then run:

```
pyinstaller build_app.spec --clean
```

PyInstaller will create:

```
dist/
└── BullseyeNSE/          ← entire self-contained app lives here
    ├── BullseyeNSE.exe
    ├── app_v2.py
    ├── EoD_module.py
    └── ... (hundreds of support files)
```

### Smoke-test before packaging

```
dist\BullseyeNSE\BullseyeNSE.exe
```

The app should open in your default browser within ~10 seconds.

---

## Step 4 — Compile the Inno Setup installer

1. Open **Inno Setup Compiler** (from the Start Menu).
2. Click **File → Open** and select `BullseyeNSE_Installer.iss`.
3. Verify the `#define SourceDir` path at the top of the `.iss` file matches your `dist\BullseyeNSE` folder. Adjust if needed.
4. Press **F9** (or **Build → Compile**).

The output installer will be written to:

```
installer_output\
└── BullseyeNSE_Setup_v3.0.exe
```

Distribute this single `.exe` to end-users.

---

## Step 5 — Installer behaviour for end-users

- **No admin rights required** by default (`PrivilegesRequired=lowest`).
- Default install location: `%LocalAppData%\Programs\BullseyeFintech\NSE_EOD\`
- Optional Desktop and Start Menu shortcuts are created.
- The app is launchable immediately after install (checkbox on last wizard page).
- Uninstaller is registered in **Add/Remove Programs**.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'EoD_module'`
Make sure `EoD_module.py` is listed in the `datas` list inside `build_app.spec` **and** is present in the same directory as `launcher.py` when running PyInstaller.

### Browser does not open automatically
The launcher polls for 30 seconds. If Streamlit takes longer on first run (cold start), open `http://127.0.0.1:8501` manually.

### `streamlit` command not found inside the bundle
The launcher uses `sys.executable -m streamlit` instead of the bare `streamlit` command, so it always uses the bundled Python — this is already handled in `launcher.py`.

### Large installer size
Streamlit bundles many assets. Typical uncompressed size is 300–500 MB; the compressed installer is usually 100–200 MB. This is expected.

### `upx` compression errors
If UPX causes issues, open `build_app.spec` and set `upx=False` in both the `EXE` and `COLLECT` blocks.

---

## Re-building after code changes

Only steps 3 and 4 need to be repeated:

```
pyinstaller build_app.spec --clean
# then re-compile in Inno Setup
```

---

## Version bumping

1. Update the version string in `app_v2.py` docstring.
2. Change `#define AppVersion` in `BullseyeNSE_Installer.iss`.
3. Re-run steps 3 and 4.
