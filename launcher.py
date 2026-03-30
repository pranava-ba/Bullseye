"""
launcher.py — Entry point for the BullseyeNSE exe.

Starts Streamlit on a free port, waits for it to be ready,
then opens the browser automatically.
"""

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser


def _find_free_port(start: int = 8501) -> int:
    """Return the first available TCP port starting from `start`."""
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start  # fall back; Streamlit will error if truly none free


def _wait_and_open(url: str, timeout: float = 30.0) -> None:
    """Poll until the server responds, then open the browser."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            webbrowser.open(url)
            return
        except Exception:
            time.sleep(0.5)
    # Open anyway after timeout — Streamlit may still be starting
    webbrowser.open(url)


def main() -> None:
    # Resolve paths whether running from source or frozen bundle
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_dir, "app_v2.py")
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"

    cmd = [
        sys.executable,
        "-m", "streamlit", "run",
        app_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--browser.gatherUsageStats", "false",
    ]

    # Launch Streamlit as a child process
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=base_dir,
    )

    # Open browser in a background thread so we don't block
    threading.Thread(target=_wait_and_open, args=(url,), daemon=True).start()

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
