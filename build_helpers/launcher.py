"""
launcher.py — EXE entry point for Bullseye Fintech NSE EOD Dashboard.

ROOT CAUSE OF v2 BUG (infinite loop / 90-second timeout)
─────────────────────────────────────────────────────────
In a PyInstaller frozen build sys.executable points to BullseyeNSE.exe
itself — NOT to a Python interpreter.  The v2 code called:

    subprocess.Popen([sys.executable, "-m", "streamlit", "run", app_py])

…which simply re-launched the EXE, which ran launcher.py again, which
spawned another copy, and so on infinitely.  Streamlit never started, the
port never opened, and the 90-second poll fired in every copy.

SECOND BUG (app_v2.py not found)
──────────────────────────────────
v2 resolved app_v2.py via sys._MEIPASS (_internal/).  But the .spec file
places app_v2.py at DestDir "." — the same folder as the EXE, not inside
_internal.  The path was always wrong in a frozen build.

v3 FIX
──────
1. Use multiprocessing.Process instead of subprocess.  With freeze_support()
   called first in __main__, PyInstaller correctly routes child processes to
   _streamlit_worker() instead of re-entering main().  No standalone
   python.exe is needed or looked for.

2. Resolve app_v2.py from os.path.dirname(sys.executable) — the EXE's own
   folder — where the .spec actually places it.

v4 BUG ("Serving static content from the Node dev server" / 404 on port 8501)
──────────────────────────────────────────────────────────────────────────────
Streamlit decides whether to activate development mode (Node dev server,
frontend on port 3000) by evaluating this at config-load time:

    developmentMode = not os.path.exists(
        os.path.join(os.path.dirname(streamlit.config.__file__), "static", "index.html")
    )

In a PyInstaller PYZ-archived build, config.__file__ resolves to a path
inside the PYZ archive (e.g. _MEIPASS/streamlit/config.pyc) whose dirname
may not match the extracted _MEIPASS location where collect_data_files()
placed the real static files, so exists() returns False and developmentMode
is forced True — even though the static directory IS present in the bundle.

Because developmentMode is a "hidden" config option, Streamlit's env-var
loader SKIPS it; STREAMLIT_GLOBAL_DEVELOPMENT_MODE has no effect (this is
why v3's env-var approach did not work).

v4 FIX
──────
1. After importing streamlit.config (but before bootstrap.run), call
   _cfg.set_option("global.developmentMode", False) via the Python API.
   This fires after auto-detection and wins regardless of how the default
   was computed.

2. Patch streamlit.web.server.server.STATIC_FILES_PATH to the known-correct
   location in _MEIPASS so the Tornado static handler serves the real files.

3. Config options that DO support env vars (port, headless, XSRF, stats)
   are still set that way — belt-and-suspenders.

CORS / XSRF WARNING FIX
────────────────────────
Setting server.enableCORS=false conflicts with server.enableXsrfProtection=true
(Streamlit overrides CORS back to true and logs a warning).  Disable XSRF
protection instead (safe for a localhost-only app) — then the two settings
no longer conflict.  We do NOT set enableCORS at all.
"""

import multiprocessing
import os
import socket
import sys
import time
import webbrowser


# ── Streamlit static-path patcher ─────────────────────────────────────────────

def _fix_frozen_static_path() -> None:
    """
    In a PyInstaller one-folder build, Streamlit's static assets live at
    _MEIPASS/streamlit/static/.  If Streamlit computed STATIC_FILES_PATH
    from __file__ before the PYZ archive was fully mapped (or the path ended
    up wrong due to the .pyc extension), patch it directly so the Tornado
    static file handler finds the real React build.

    This function is a no-op in a normal (non-frozen) Python environment.
    """
    if not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")):
        return

    from pathlib import Path

    static = Path(sys._MEIPASS) / "streamlit" / "static"
    if not static.exists():
        print(
            f"[launcher] WARNING: streamlit static dir not found at {static}.\n"
            "           The bundle may be missing assets — consider rebuilding.",
            file=sys.stderr,
        )
        return

    try:
        import streamlit.web.server.server as _srv  # noqa: PLC0415

        if hasattr(_srv, "STATIC_FILES_PATH"):
            _srv.STATIC_FILES_PATH = static
            print(f"[launcher] STATIC_FILES_PATH → {static}")
        else:
            # Newer Streamlit versions may use a different attribute name —
            # log candidates so we can add a targeted patch if needed.
            candidates = [a for a in dir(_srv) if "static" in a.lower()]
            print(
                f"[launcher] WARNING: STATIC_FILES_PATH not found in "
                f"streamlit.web.server.server.  Candidates: {candidates}",
                file=sys.stderr,
            )
    except (ImportError, AttributeError) as exc:
        print(f"[launcher] WARNING: could not patch static path: {exc}", file=sys.stderr)


# ── Streamlit worker — runs inside the child process ─────────────────────────

def _streamlit_worker(app_py: str, port: int) -> None:
    """
    Invoked by multiprocessing.Process.  Calls Streamlit's bootstrap directly
    so no external python.exe is required.

    Config is applied in two layers:
      • Environment variables — picked up by most options at config-load time.
      • _cfg.set_option() calls — override hidden options (like developmentMode)
        that env vars cannot reach.
    """
    # ── 1. sys.path ────────────────────────────────────────────────────────────
    app_dir = os.path.dirname(os.path.abspath(app_py))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # ── 2. Env vars (set BEFORE any streamlit import) ──────────────────────────
    # These are read by Streamlit's config loader as soon as the config module
    # is first imported.  They cover the options whose env-var override works.
    os.environ["STREAMLIT_SERVER_PORT"]                   = str(port)
    os.environ["STREAMLIT_SERVER_HEADLESS"]               = "true"
    os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
    # Do NOT set STREAMLIT_SERVER_ENABLE_CORS — disabling XSRF already removes
    # the conflict, and setting CORS=false while XSRF=true triggers a warning.
    os.environ.pop("STREAMLIT_SERVER_ENABLE_CORS", None)
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"]    = "false"

    # ── 3. Config API — force options that env vars cannot override ────────────
    # global.developmentMode is a "hidden" option whose default is computed by
    # Streamlit at config-load time by checking for static/index.html via
    # __file__-relative path resolution.  In a frozen build that check can
    # return False even when the files ARE present (PYZ archive __file__ quirk).
    # Calling set_option() here fires AFTER auto-detection and always wins.
    from streamlit import config as _cfg              # noqa: PLC0415

    _cfg.set_option("global.developmentMode", False)
    _cfg.set_option("server.port",                  port)
    _cfg.set_option("server.headless",              True)
    _cfg.set_option("server.enableXsrfProtection",  False)
    _cfg.set_option("browser.gatherUsageStats",     False)

    # ── 4. Patch STATIC_FILES_PATH for frozen builds ───────────────────────────
    _fix_frozen_static_path()

    # ── 5. Run ─────────────────────────────────────────────────────────────────
    from streamlit.web import bootstrap               # noqa: PLC0415

    bootstrap.run(
        app_py,
        "streamlit run",   # command_line — informational only
        [],                # script args
        {},                # flag_options — empty; all config handled above
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_free_port(preferred: int = 8501) -> int:
    """Return preferred port if free, otherwise any available ephemeral port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _server_ready(port: int, timeout: float = 90.0) -> bool:
    """
    Poll localhost:port until it accepts a TCP connection or timeout expires.
    Returns True when the server is up, False on timeout.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False


def _resolve_app_py() -> str:
    """
    Return the absolute path to app_v2.py.

    PyInstaller 6.x one-folder layout:
        dist/BullseyeNSE/
            BullseyeNSE.exe          <- sys.executable
            _internal/               <- sys._MEIPASS  (all bundled datas live here)
                app_v2.py            <- placed here by spec DestDir "."
                EoD_module.py
                streamlit/
                polars/
                ...

    Datas with destination "." in the spec map to _internal/ in PyInstaller 6.x,
    so sys._MEIPASS is the correct base.  We also probe exe_dir as a fallback
    for older PyInstaller versions that did not use the _internal sub-folder.
    """
    if getattr(sys, "frozen", False):
        exe_dir   = os.path.dirname(sys.executable)
        meipass   = getattr(sys, "_MEIPASS", None)
        for base in filter(None, [meipass, exe_dir]):
            candidate = os.path.join(base, "app_v2.py")
            if os.path.exists(candidate):
                return candidate
        return os.path.join(meipass or exe_dir, "app_v2.py")
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_v2.py")


def _fatal(msg: str) -> None:
    """Show an error dialog on Windows, then exit."""
    print(f"\nERROR: {msg}", file=sys.stderr)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, msg, "Bullseye Fintech — Startup Error", 0x10,  # MB_ICONERROR
            )
        except Exception:
            pass
    sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    app_py = _resolve_app_py()

    if not os.path.exists(app_py):
        _fatal(
            f"app_v2.py not found at:\n  {app_py}\n\n"
            "The installation may be corrupted. Please reinstall."
        )

    port = _find_free_port()
    url  = f"http://localhost:{port}"

    print(f"Starting Bullseye Fintech NSE Dashboard on {url} ...")

    proc = multiprocessing.Process(
        target=_streamlit_worker,
        args=(app_py, port),
        daemon=True,
    )
    proc.start()

    print("Waiting for server to start ...", end="", flush=True)
    ready = _server_ready(port, timeout=90)
    print(" ready!" if ready else " timed out.")

    if not ready:
        proc.terminate()
        proc.join(timeout=5)
        _fatal(
            f"Streamlit did not start within 90 seconds on port {port}.\n\n"
            "Possible causes:\n"
            "  - Antivirus is blocking the child process.\n"
            "  - The bundle is corrupted — try reinstalling.\n\n"
            "If antivirus is the cause, add an exclusion for the install\n"
            "folder and try again."
        )

    webbrowser.open(url)
    print(f"Browser opened at {url}")
    print("Keep this window open while using the app. Close it to stop.")

    try:
        proc.join()
    except KeyboardInterrupt:
        print("\nShutting down ...")
        proc.terminate()
        proc.join(timeout=5)
    finally:
        sys.exit(0)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
