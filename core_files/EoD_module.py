"""
EoD_module.py  ·  NSE End-of-Day Data Downloader & Processor
Bullseye Fintech © 2024–2026
Rebuild v3 — ground-up rewrite.
All fixes and improvements cross-referenced to the Deep Analysis document.
Fixes applied
─────────────
BUG-E1  Two-digit year + filename date validation (day/month range checks)
BUG-E2  URL year-slice fragility guarded by datetime parsing
BUG-E3  CATEGORY length validated before assignment (raises descriptive error)
BUG-E4  Session cookie priming before bulk downloads + re-prime on 403
BUG-E5  Retry with exponential backoff (3 attempts, 2/4/8 s)
BUG-E6  Camarilla PP renamed P_CAM = prev-close C (not P_CLASSIC)
BUG-E7  Column names defined as class constants (Col) — single source of truth
BUG-E8  Holiday-aware auto-update (consults CUE_DATE CSV, not just weekdays)
BUG-E9  Atomic CSV write via tmp→rename
BUG-E10 Per-year temp directories eliminate cross-year file contamination
BUG-E11 delete_year_data also cleans partial PD files from per-year temp dir
BUG-E12 get_nse_trading_days raises RuntimeError with helpful message
BUG-E13 Skip future dates during download to prevent 404 loops (NEW)
Improvements applied
────────────────────
I-P3  Full Polars pipeline (process_file, consolidation, pivots, helpers)
I-P4  Parallel downloads via ThreadPoolExecutor (configurable workers)
I-R1  NSE session priming (GET homepage before bulk download + periodic refresh)
I-R2  Retry with exponential backoff on transient network errors
I-R3  Atomic CSV write (write .tmp → os.replace to final path)
I-R4  Per-year temp directories for extraction
I-R5  Holiday-aware auto-update (consults trading calendar)
I-R6  CATEGORY length assertion before assignment
I-C1  Col dataclass as shared column-name schema
I-C2  Full type annotations throughout
I-D1  Filename date validation (day 1-31, month 1-12)
I-D2  Consistent YYYY-MM-DD date format in both CSVs
I-D3  Camarilla anchor renamed P_CAM (prev close)
F6    Sidebar download helpers returning in-memory bytes for st.download_button
F7    Incremental / append-only download mode
New defaults
────────────
AUTO_UPDATE_DEFAULT = False   ← auto-update is OFF by default
"""
# ── Standard library ─────────────────────────────────────────────────────────
import io
import logging
import os
import re
import sys
import threading
import time
import warnings
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

# ── Third-party ───────────────────────────────────────────────────────────────
import polars as pl
import requests
from pandas_market_calendars import get_calendar

# ═════════════════════════════════════════════════════════════════════════════
# COLUMN-NAME SCHEMA  (I-C1 / BUG-X1)
# Import this class in app.py to eliminate hardcoded column-name strings.
# ═════════════════════════════════════════════════════════════════════════════
class Col:
    """Single source of truth for every column name used across all CSVs.

    BUG-FIX: All column names use clean strings without trailing spaces.
    The NSE PD files have headers like 'SYMBOL ' (with trailing space); these
    are stripped by the normalisation step (c.strip().upper()) in every loader.
    Having trailing spaces in these constants caused silent column-lookup
    failures in Polars/pandas pipelines.
    """
    # ── Raw EoD fields ────────────────────────────────────────────────────────
    SECURITY   = "SECURITY"
    SYMBOL     = "SYMBOL"
    CATEGORY   = "CATEGORY"
    DATE       = "DATE"
    OPEN       = "OPEN_PRICE"
    HIGH       = "HIGH_PRICE"
    LOW        = "LOW_PRICE"
    CLOSE      = "CLOSE_PRICE"
    PREV_CLOSE = "PREV_CL_PR"
    NET_TRDVAL = "NET_TRDVAL"
    NET_TRDQTY = "NET_TRDQTY"
    HI_52      = "HI_52_WK"
    LO_52      = "LO_52_WK"

    # ── Classic pivot ─────────────────────────────────────────────────────────
    P_CLASSIC  = "P_CLASSIC"
    CL_R1 = "CL_R1";  CL_R2 = "CL_R2";  CL_R3 = "CL_R3"
    CL_S1 = "CL_S1";  CL_S2 = "CL_S2";  CL_S3 = "CL_S3"

    # ── Fibonacci pivot ───────────────────────────────────────────────────────
    FIB_R1 = "FIB_R1"; FIB_R2 = "FIB_R2"; FIB_R3 = "FIB_R3"
    FIB_S1 = "FIB_S1"; FIB_S2 = "FIB_S2"; FIB_S3 = "FIB_S3"

    # ── Woodie pivot ──────────────────────────────────────────────────────────
    P_WOODIE = "P_WOODIE"
    WD_R1 = "WD_R1"; WD_R2 = "WD_R2"
    WD_S1 = "WD_S1"; WD_S2 = "WD_S2"

    # ── Camarilla pivot  (anchor = prev close, NOT a PP average — BUG-E6) ─────
    P_CAM  = "P_CAM"    # = previous-day close (the true Camarilla anchor)
    CAM_R1 = "CAM_R1";  CAM_R2 = "CAM_R2"
    CAM_R3 = "CAM_R3";  CAM_R4 = "CAM_R4"
    CAM_S1 = "CAM_S1";  CAM_S2 = "CAM_S2"
    CAM_S3 = "CAM_S3";  CAM_S4 = "CAM_S4"

    # ── Convenience lists for bulk operations ─────────────────────────────────
    PRICE_COLS: Tuple[str, ...] = (
        "HIGH_PRICE", "LOW_PRICE", "CLOSE_PRICE",
        "OPEN_PRICE", "PREV_CL_PR", "NET_TRDVAL", "NET_TRDQTY",
    )

    PIVOT_FINAL_COLS: Tuple[str, ...] = (
        "DATE", "CATEGORY", "SYMBOL",
        # Classic
        "P_CLASSIC",
        "CL_R1", "CL_R2", "CL_R3",
        "CL_S1", "CL_S2", "CL_S3",
        # Fibonacci
        "FIB_R1", "FIB_R2", "FIB_R3",
        "FIB_S1", "FIB_S2", "FIB_S3",
        # Woodie
        "P_WOODIE",
        "WD_R1", "WD_R2", "WD_S1", "WD_S2",
        # Camarilla
        "P_CAM",
        "CAM_R1", "CAM_R2", "CAM_R3", "CAM_R4",
        "CAM_S1", "CAM_S2", "CAM_S3", "CAM_S4",
    )

# ═════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═════════════════════════════════════════════════════════════════════════════
def _get_log_path() -> str:
    """Return a writable log-file path in frozen / development mode."""
    if getattr(sys, "frozen", False) and os.name == "nt":
        base = os.environ.get("APPDATA", os.path.dirname(sys.executable))
        log_dir = os.path.join(base, "BullseyeFintech", "NSE_Dashboard")
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "bullseye.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(_get_log_path(), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=FutureWarning)

# ═════════════════════════════════════════════════════════════════════════════
# PATH HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def get_data_dir() -> str:
    """Return a portable, writable data directory (frozen-app & dev-mode safe)."""
    if getattr(sys, "frozen", False):
        if os.name == "nt":
            appdata = os.environ.get("APPDATA", os.path.dirname(sys.executable))
            base = os.path.join(appdata, "BullseyeFintech", "NSE_Dashboard", "data")
        else:
            base = os.path.join(os.path.dirname(sys.executable), "data")
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(base, exist_ok=True)
    return base

DATA_DIR: str = get_data_dir()

def eod_csv_path(year: int) -> str:
    return os.path.join(DATA_DIR, f"EOD_DATA_FOR_ANALYSIS_{year}.csv")

def pivot_csv_path(year: int) -> str:
    return os.path.join(DATA_DIR, f"pivots_output{year}.csv")

def cue_date_path(year: int) -> str:
    return os.path.join(DATA_DIR, f"CUE_DATE_{year}.csv")

def _year_temp_dir(year: int) -> str:
    """Per-year temp extraction folder (I-R4 / BUG-E10)."""
    p = os.path.join(DATA_DIR, "nse_eod_data_files", str(year))
    os.makedirs(p, exist_ok=True)
    return p

# ═════════════════════════════════════════════════════════════════════════════
# HTTP SESSION  (I-R1 / BUG-E4 — session cookie priming)
# ═════════════════════════════════════════════════════════════════════════════
_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.nseindia.com/",
}

SESSION: requests.Session = requests.Session()
SESSION.headers.update(_HEADERS)

_session_lock = threading.Lock()
_last_prime_time = 0.0
_PRIME_INTERVAL = 300  # re-prime every 5 minutes during long downloads

def _prime_session(force: bool = False) -> None:
    """
    GET the NSE homepage to acquire a valid session cookie.
    Skipped if a prime happened within _PRIME_INTERVAL seconds,
    unless force is True (called on first 403 to recover).
    """
    global _last_prime_time
    now = time.monotonic()
    if not force and (now - _last_prime_time) < _PRIME_INTERVAL:
        return
    with _session_lock:
        try:
            r = SESSION.get("https://www.nseindia.com/", timeout=15)
            _last_prime_time = time.monotonic()
            log.info("NSE session primed (HTTP %s)", r.status_code)
        except Exception as exc:
            log.warning("Session prime failed: %s", exc)

# ═════════════════════════════════════════════════════════════════════════════
# TRADING CALENDAR
# ═════════════════════════════════════════════════════════════════════════════
def get_nse_trading_days(year: int) -> List[str]:
    """
    Return all NSE trading days for year as DD-MM-YYYY strings.
    Raises
    ------
    RuntimeError with a descriptive message if the calendar cannot be
    fetched (BUG-E12 fix).
    """
    try:
        cal = get_calendar("NSE")
        schedule = cal.valid_days(
            start_date=f"{year}-01-01",
            end_date=f"{year}-12-31",
        )
        return [s.strftime("%d-%m-%Y") for s in schedule]
    except Exception as exc:
        raise RuntimeError(
            f"Could not fetch NSE trading calendar for {year}. "
            f"Ensure pandas_market_calendars is up-to-date. Detail: {exc}"
        ) from exc

def save_trading_days_to_csv(trading_days: List[str], year: int) -> str:
    """Persist the trading-day list for year using Polars."""
    path = cue_date_path(year)
    pl.DataFrame({"details": trading_days}).write_csv(path)
    return path

def _load_trading_days(year: int) -> List[str]:
    """Load calendar from disk or fetch + save if missing."""
    path = cue_date_path(year)
    if not os.path.exists(path):
        days = get_nse_trading_days(year)
        save_trading_days_to_csv(days, year)
        return days
    return pl.read_csv(path)["details"].to_list()

# ═════════════════════════════════════════════════════════════════════════════
# SINGLE-DATE DOWNLOAD  (I-R2 / BUG-E4, BUG-E5 — retry + backoff)
# ═════════════════════════════════════════════════════════════════════════════
_MAX_RETRIES = 3
_RETRY_DELAYS = (2, 4, 8)  # seconds between attempts

def _tdate_to_pdtag(tdate: str) -> str:
    """
    Convert DD-MM-YYYY → DDMMYY tag used in NSE archive URLs.
    Validates the input length before slicing (BUG-E2).
    """
    parts = tdate.split("-")
    if len(parts) != 3 or any(len(p) == 0 for p in parts):
        raise ValueError(f"Unexpected date string format: '{tdate}'")
    day, month, year_full = parts[0], parts[1], parts[2]
    return day + month + year_full[-2:]

def _download_one(
    tdate: str,
    temp_dir: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Optional[bool]:
    """
    Download and extract the bhavcopy ZIP for one trading date.
    Returns True on success, None on any unrecoverable failure.
    Skips future dates and gracefully handles 404 (missing file).
    """
    # ── Skip future dates ───────────────────────────────────────────────────
    try:
        parsed_date = datetime.strptime(tdate, "%d-%m-%Y").date()
        if parsed_date > datetime.now().date():
            if progress_callback:
                progress_callback(f"  ⏭️ Skipping future date {tdate}")
            return None
    except ValueError:
        log.warning("Skipping %s: invalid date format", tdate)
        return None

    try:
        pd_tag = _tdate_to_pdtag(tdate)
    except ValueError as exc:
        log.warning("Skipping %s: %s", tdate, exc)
        return None

    url = f"https://archives.nseindia.com/archives/equities/bhavcopy/pr/PR{pd_tag}.zip"
    zip_path = os.path.join(temp_dir, f"pd_{os.getpid()}_{threading.get_ident()}.zip")

    # ── Retry loop with exponential backoff (BUG-E5 / I-R2) ───────────────
    _prime_session()
    last_exc: Optional[Exception] = None
    for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
        try:
            resp = SESSION.get(url, timeout=30)

            # 403 = stale cookie → re-prime once and retry immediately
            if resp.status_code == 403:
                log.info("403 on %s (attempt %d) – re-priming session…", tdate, attempt)
                _prime_session(force=True)
                time.sleep(1)
                resp = SESSION.get(url, timeout=30)

            # 404 = file genuinely doesn't exist → stop, don't retry
            if resp.status_code == 404:
                if progress_callback:
                    progress_callback(f"  ⚠️ No data for {tdate} (404) — skipping")
                return None

            resp.raise_for_status()

            with open(zip_path, "wb") as f:
                f.write(resp.content)
            break  # success — exit retry loop

        except requests.RequestException as exc:
            last_exc = exc
            log.warning("Download failed for %s (attempt %d/%d): %s",
                        tdate, attempt, _MAX_RETRIES, exc)
            if delay is not None:
                if progress_callback:
                    progress_callback(f"  ↻ Retry {attempt}/{_MAX_RETRIES} for {tdate} in {delay}s…")
                time.sleep(delay)
    else:
        # All retries exhausted
        if progress_callback:
            progress_callback(f"  ✗ {tdate}: {last_exc}")
        return None

    # ── Extract CSV from ZIP ────────────────────────────────────────────────
    # BUG-FIX: Use case-insensitive match. NSE archives have varied casing
    # ('Pd300326.csv' vs 'pd300326.csv') across years. Match by lowercased tag.
    #
    # BUG-FIX (v4): NSE switched to 4-digit years INSIDE the ZIP for recent
    # dates (e.g. pd31122025.csv) while the ZIP URL itself still uses a 2-digit
    # year (PR311225.zip).  We try the 4-digit pattern first, then fall back to
    # the 2-digit pattern so older archives continue to work.
    _day, _month, _year_full = tdate.split("-")
    pd_pattern_4y = f"pd{_day}{_month}{_year_full}".lower()   # e.g. pd31122025
    pd_pattern_2y = f"pd{pd_tag}".lower()                     # e.g. pd311225
    try:
        with zipfile.ZipFile(zip_path) as zf:
            namelist = zf.namelist()
            namelist_lower = [f.lower() for f in namelist]
            pd_file = next(
                (
                    namelist[i]
                    for i, fl in enumerate(namelist_lower)
                    if pd_pattern_4y in fl or pd_pattern_2y in fl
                ),
                None,
            )
            if pd_file is None:
                log.warning(
                    "Pattern '%s' (or '%s') not found in ZIP for %s. ZIP contents: %s",
                    pd_pattern_4y, pd_pattern_2y, tdate, namelist,
                )
                if progress_callback:
                    progress_callback(f"  ⚠️ Pattern not in ZIP — skipping {tdate}")
                return None
            dest = os.path.join(temp_dir, os.path.basename(pd_file))
            with open(dest, "wb") as out:
                out.write(zf.read(pd_file))
            if progress_callback:
                progress_callback(f"  ✓ {tdate} → {os.path.basename(dest)}")
        return True
    except zipfile.BadZipFile:
        log.warning("Bad ZIP for %s", tdate)
        if progress_callback:
            progress_callback(f"  ⚠️ Bad ZIP — skipping {tdate}")
        return None
    except Exception as exc:
        log.error("Extraction error for %s: %s", tdate, exc)
        return None
    finally:
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass

# ═════════════════════════════════════════════════════════════════════════════
# FILE PROCESSING  (I-P3 — full Polars rewrite)
# ═════════════════════════════════════════════════════════════════════════════
def _parse_date_from_filename(filename: str) -> str:
    """
    Extract YYYY-MM-DD from a filename like Pd240325.csv.
    Validates that day ∈ [1,31] and month ∈ [1,12] before accepting
    the result (BUG-E1 / I-D1).

    Raises
    ------
    ValueError if the pattern is not found or the date components are
    out of range.
    """
    # BUG-FIX: Anchor the pattern to "Pd" or "pd" prefix so we don't
    # accidentally match other digit sequences in the filename.
    #
    # BUG-FIX (v4): NSE switched to 4-digit years in filenames for recent
    # dates (pd31122025.csv).  Match DDMMYYYY (8 digits) first, then fall
    # back to DDMMYY (6 digits) for older archives.
    base = os.path.basename(filename)
    m8 = re.search(r"[Pp][Dd](\d{2})(\d{2})(\d{4})", base)   # DDMMYYYY
    m6 = re.search(r"[Pp][Dd](\d{2})(\d{2})(\d{2})",  base)   # DDMMYY
    if m8:
        day, month, full_year = int(m8.group(1)), int(m8.group(2)), int(m8.group(3))
    elif m6:
        day, month, yr_2dig = int(m6.group(1)), int(m6.group(2)), int(m6.group(3))
        full_year = 2000 + yr_2dig
    else:
        raise ValueError(f"Cannot parse date from filename: {filename!r}")
    if not (1 <= day <= 31):
        raise ValueError(f"Implausible day {day} in filename: {filename!r}")
    if not (1 <= month <= 12):
        raise ValueError(f"Implausible month {month} in filename: {filename!r}")
    return f"{full_year}-{month:02d}-{day:02d}"

def process_file(file_path: str) -> pl.DataFrame:
    """
    Parse a single extracted Pd.csv into a clean Polars DataFrame.
    The NSE PD file has a special nested structure where category headings
    appear as rows with a null MKT cell.  This function reconstructs the
    CATEGORY label for every data row.

    Changes from v2
    ───────────────
    • Returns pl.DataFrame (was pd.DataFrame)
    • BUG-E3: validates len(category) == len(df_final) before assignment
    • BUG-E1: date parsed via _parse_date_from_filename (with range checks)
    """
    import pandas as pd  # pandas used only for this NSE-specific format parsing
    import numpy as np

    df_raw = pd.read_csv(file_path, dtype=str)
    df_raw = df_raw.replace(r"^\s*$", pd.NA, regex=True)

    # Drop irrelevant columns
    drop_cols = [c for c in ["IND_SEC", "CORP_IND"] if c in df_raw.columns]
    if drop_cols:
        df_raw = df_raw.drop(columns=drop_cols)

    df_raw = df_raw.dropna(subset=["SECURITY"]).reset_index(drop=True)

    # ── Build CATEGORY labels ─────────────────────────────────────────────────
    # Phase 1: count consecutive non-null MKT rows at the top = NIFTY INDEX rows
    n_index = 0
    for val in df_raw["MKT"]:
        if pd.notna(val):
            n_index += 1
        else:
            break

    category: List[str] = ["NIFTY INDEX"] * n_index

    # Phase 2: from index n_index onward, collect heading rows
    total = len(df_raw)
    heading_names: List[str] = []
    heading_idxs: List[int] = []

    for i in range(n_index, total):
        mkt = df_raw.at[i, "MKT"]
        sec = df_raw.at[i, "SECURITY"]
        if pd.isna(mkt) and pd.notna(sec):
            heading_names.append(str(sec))
            heading_idxs.append(i)

    # Phase 3: propagate category names between heading rows
    segments: List[str] = []
    for k in range(len(heading_idxs) - 1):
        gap = heading_idxs[k + 1] - heading_idxs[k] - 1
        segments.extend([heading_names[k]] * max(gap, 0))

    if heading_idxs:
        last_remaining = max(total - 1 - heading_idxs[-1], 0)
        segments.extend([heading_names[-1]] * last_remaining)

    category.extend(segments)

    # ── Drop heading rows (MKT is null) ─────────────────────────────────────
    df_final = df_raw.dropna(subset=["MKT"]).reset_index(drop=True)

    # BUG-E3: hard check before assignment
    if len(category) != len(df_final):
        raise ValueError(
            f"CATEGORY length mismatch in {os.path.basename(file_path)!r}: "
            f"expected {len(df_final)}, got {len(category)}. "
            f"NSE file format may have changed."
        )

    # SYMBOL fallback to SECURITY
    if "SYMBOL" in df_final.columns:
        mask = df_final["SYMBOL"].isna()
        df_final.loc[mask, "SYMBOL"] = df_final.loc[mask, "SECURITY"]
    else:
        df_final["SYMBOL"] = df_final["SECURITY"]

    df_final["CATEGORY"] = category
    df_final["DATE"] = _parse_date_from_filename(file_path)

    drop2 = [c for c in ["MKT", "SERIES"] if c in df_final.columns]
    if drop2:
        df_final = df_final.drop(columns=drop2)

    # ── Convert to Polars (I-P3) ──────────────────────────────────────────────
    return pl.from_pandas(df_final.reset_index(drop=True))

# ═════════════════════════════════════════════════════════════════════════════
# MAIN DOWNLOAD ORCHESTRATOR
# ═════════════════════════════════════════════════════════════════════════════
def download_year_data(
    year: int,
    force_redownload: bool = False,
    incremental: bool = False,
    max_workers: int = 4,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[bool, str]:
    """
    Download, extract, and consolidate all trading-day bhavcopy files for year.
    Parameters
    ----------
    year : Calendar year to download.
    force_redownload : Overwrite any existing master CSV.
    incremental : Only download dates newer than the last date already
                  in the master CSV and *append* (F7 / I-F7).
                  Ignored if force_redownload is True.
    max_workers : Thread-pool size for parallel downloads (I-P4).
                  Recommended: 4 (NSE tolerates moderate concurrency).
    progress_callback : Optional callable(str) for status messages
                        (used by Streamlit sidebar).

    Returns
    -------
    (success: bool, message: str)
    """
    out_csv = eod_csv_path(year)
    temp_dir = _year_temp_dir(year)

    try:
        # ── Early exit ────────────────────────────────────────────────────────
        if os.path.exists(out_csv) and not force_redownload and not incremental:
            return (
                True,
                f"Data for {year} already exists. "
                f"Use Force Re-download to overwrite, or enable Incremental mode.",
            )

        # ── Load calendar ─────────────────────────────────────────────────────
        if progress_callback:
            progress_callback(f"Loading NSE trading calendar for {year}…")
        all_days: List[str] = _load_trading_days(year)

        # BUG-E13 FIX: Filter out future dates BEFORE download attempts
        today = datetime.now().date()
        all_days = [
            d for d in all_days 
            if datetime.strptime(d, "%d-%m-%Y").date() <= today
        ]

        # ── Incremental: skip already-downloaded dates ────────────────────────
        if incremental and not force_redownload and os.path.exists(out_csv):
            try:
                existing_dates = set(
                    pl.read_csv(out_csv, columns=[Col.DATE])[Col.DATE].to_list()
                )
                pending_days = [
                    d for d in all_days
                    if _tdate_to_iso(d) not in existing_dates
                ]
                if progress_callback:
                    progress_callback(
                        f"Incremental mode: {len(pending_days)} new day(s) to download "
                        f"({len(existing_dates)} already on disk)."
                    )
            except Exception as exc:
                log.warning(
                    "Incremental pre-check failed (%s) — falling back to full download", exc
                )
                pending_days = all_days
        else:
            pending_days = all_days

        if not pending_days:
            return True, f"No new trading days to download for {year}."

        if progress_callback:
            progress_callback(
                f"Downloading {len(pending_days)} day(s) for {year} "
                f"with {max_workers} parallel worker(s)…"
            )

        # ── Prime NSE session before bulk download ────────────────────────────
        _prime_session(force=True)

        # ── Parallel download loop (I-P4) ──────────────────────────────────────
        success_count = 0
        failed_dates: List[str] = []
        _count_lock = threading.Lock()

        def _worker(tdate: str, idx: int) -> bool:
            nonlocal success_count
            ok = _download_one(tdate, temp_dir, progress_callback)
            with _count_lock:
                if ok:
                    success_count += 1
                else:
                    failed_dates.append(tdate)
                if progress_callback:
                    pct = idx / len(pending_days) * 100
                    progress_callback(
                        f"Progress: {idx}/{len(pending_days)} ({pct:.1f}%)"
                    )
            return bool(ok)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futs = {
                pool.submit(_worker, d, i + 1): d
                for i, d in enumerate(pending_days)
            }
            for fut in as_completed(futs):
                try:
                    fut.result()
                except Exception as exc:
                    log.error("Worker exception: %s", exc)

        if success_count == 0:
            return (
                False,
                "No data files downloaded. "
                "NSE may be blocking requests or all dates already exist.",
            )

        # ── Consolidate extracted files into master CSV ───────────────────────
        pd_files = sorted(
            f for f in os.listdir(temp_dir) if f.upper().startswith("PD")
        )
        if not pd_files:
            return False, "No extracted files found after download."

        if progress_callback:
            progress_callback(f"Parsing and consolidating {len(pd_files)} file(s)…")

        frames: List[pl.DataFrame] = []
        for fname in pd_files:
            fp = os.path.join(temp_dir, fname)
            try:
                frames.append(process_file(fp))
            except Exception as exc:
                log.warning("Skipping %s: %s", fname, exc)
                if progress_callback:
                    progress_callback(f"  ⚠ Skipping {fname}: {exc}")

        if not frames:
            return False, "All extracted files failed to parse."

        new_df = pl.concat(frames, how="diagonal")  # diagonal tolerates minor schema diffs

        # ── Atomic write / append (BUG-E9 / I-R3) ────────────────────────────
        tmp_csv = out_csv + ".tmp"
        if progress_callback:
            progress_callback("Writing master CSV…")

        if incremental and not force_redownload and os.path.exists(out_csv):
            existing_df = pl.read_csv(out_csv)
            combined = pl.concat([existing_df, new_df], how="diagonal")
            # De-duplicate in case of overlap
            combined = combined.unique(
                subset=[Col.DATE, Col.SYMBOL, Col.CATEGORY],
                keep="last",
            )
            combined.write_csv(tmp_csv)
        else:
            new_df.write_csv(tmp_csv)

        os.replace(tmp_csv, out_csv)  # atomic on POSIX; near-atomic on Windows (BUG-E9)

        # ── Clean up per-year temp files ──────────────────────────────────────
        for fname in pd_files:
            try:
                os.remove(os.path.join(temp_dir, fname))
            except Exception as exc:
                log.warning("Could not remove temp file %s: %s", fname, exc)

        if failed_dates:
            log.info(
                "Skipped %d date(s): %s",
                len(failed_dates),
                ", ".join(failed_dates[:20]),
            )

        msg = (
            f"✓ EoD data for {year} saved "
            f"({success_count}/{len(pending_days)} days downloaded "
            + (f", {len(failed_dates)} skipped" if failed_dates else " ")
            + ")"
        )
        log.info(msg)
        return True, msg

    except Exception as exc:
        log.error("download_year_data failed for %d: %s", year, exc)
        return False, f"Error: {exc}"

def _tdate_to_iso(tdate: str) -> str:
    """Convert DD-MM-YYYY → YYYY-MM-DD (used for incremental comparison)."""
    p = tdate.split("-")
    return f"{p[2]}-{p[1]}-{p[0]}"

# ═════════════════════════════════════════════════════════════════════════════
# DATA MANAGEMENT
# ═════════════════════════════════════════════════════════════════════════════
def get_available_years() -> List[int]:
    """Scan DATA_DIR and return sorted list of years with EOD CSVs."""
    years: List[int] = []
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            m = re.match(r"EOD_DATA_FOR_ANALYSIS_(\d{4}).csv$", f)
            if m:
                years.append(int(m.group(1)))
    return sorted(years)

def get_data_status(year: int) -> Dict[str, object]:
    """
    Return a status dict for year with counts and file metadata.
    Useful for displaying a summary card in the sidebar.
    Returns
    -------
    {
        "has_eod": bool,
        "has_pivots": bool,
        "eod_rows": int | None,
        "eod_size_kb": float | None,
        "pivot_rows": int | None,
        "latest_date": str | None,
        "earliest_date": str | None,
    }
    """
    status: Dict[str, object] = {
        "has_eod": False,
        "has_pivots": False,
        "eod_rows": None,
        "eod_size_kb": None,
        "pivot_rows": None,
        "latest_date": None,
        "earliest_date": None,
    }
    eod = eod_csv_path(year)
    if os.path.exists(eod):
        status["has_eod"] = True
        status["eod_size_kb"] = round(os.path.getsize(eod) / 1024, 1)
        try:
            df = pl.read_csv(eod, columns=[Col.DATE])
            status["eod_rows"] = len(df)
            dates = df[Col.DATE].drop_nulls().sort()
            status["earliest_date"] = dates[0] if len(dates) else None
            status["latest_date"] = dates[-1] if len(dates) else None
        except Exception:
            pass

    piv = pivot_csv_path(year)
    if os.path.exists(piv):
        status["has_pivots"] = True
        try:
            status["pivot_rows"] = pl.read_csv(piv, columns=[Col.DATE]).height
        except Exception:
            pass

    return status

def delete_year_data(year: int) -> Tuple[bool, str]:
    """
    Delete all files associated with year, including any lingering
    partial PD files in the per-year temp directory (BUG-E11 fix).
    """
    try:
        targets = [eod_csv_path(year), pivot_csv_path(year), cue_date_path(year)]
        deleted: List[str] = []
        for f in targets:
            if os.path.exists(f):
                os.remove(f)
                deleted.append(os.path.basename(f))

        # BUG-E11: clean up partial temp files
        temp_dir = _year_temp_dir(year)
        for f in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, f))
                deleted.append(f)
            except Exception:
                pass

        log.info("Deleted %d file(s) for year %d.", len(deleted), year)
        return (
            True,
            f"Deleted {len(deleted)} file(s) for year {year}: {', '.join(deleted) or 'none found'}",
        )
    except Exception as exc:
        log.error("delete_year_data failed for %d: %s", year, exc)
        return False, f"Error deleting data: {exc}"

# ═════════════════════════════════════════════════════════════════════════════
# AUTO-UPDATE  (OFF by default — BUG-E8 holiday-aware)
# ═════════════════════════════════════════════════════════════════════════════
#: Auto-update is OFF by default.  The Streamlit app should read this constant
#: to initialise the toggle widget rather than hard-coding True.
AUTO_UPDATE_DEFAULT: bool = False

def check_auto_update_needed() -> Optional[int]:
    """
    Return the year that needs updating if yesterday's trading data is absent,
    otherwise return None.
    Fixes applied
    ─────────────
    BUG-E5  Reads full DATE column (not just first N rows)
    BUG-E8  Consults CUE_DATE CSV so NSE holidays are not treated as gaps
    """
    try:
        yesterday = datetime.now() - timedelta(days=1)

        # Skip weekends immediately
        if yesterday.weekday() >= 5:
            return None

        year = yesterday.year
        date_iso = yesterday.strftime("%Y-%m-%d")
        date_dmy = yesterday.strftime("%d-%m-%Y")

        # BUG-E8: check if yesterday was an actual NSE trading day
        cal_path = cue_date_path(year)
        if os.path.exists(cal_path):
            trading_days = pl.read_csv(cal_path)["details"].to_list()
            if date_dmy not in trading_days:
                log.info(
                    "check_auto_update_needed: %s is an NSE holiday — no update needed.",
                    date_dmy,
                )
                return None

        out_csv = eod_csv_path(year)
        if not os.path.exists(out_csv):
            return year

        # BUG-E5: read full DATE column
        dates = pl.read_csv(out_csv, columns=[Col.DATE])[Col.DATE].to_list()
        if date_iso not in dates:
            return year

        return None

    except Exception as exc:
        log.warning("check_auto_update_needed error: %s", exc)
        return None

def run_auto_update(
    progress_callback: Optional[Callable[[str], None]] = None
) -> Tuple[bool, str]:
    """
    Download missing data for yesterday's year if needed.
    Uses incremental mode so only new dates are fetched (F7).
    Note: auto-update is OFF by default (AUTO_UPDATE_DEFAULT = False).
    The caller is responsible for checking the user's preference before
    calling this function.
    """
    year = check_auto_update_needed()
    if year:
        if progress_callback:
            progress_callback(f"Auto-update: fetching missing data for {year}…")
        return download_year_data(
            year,
            force_redownload=False,
            incremental=True,
            progress_callback=progress_callback,
        )
    return True, "Auto-update: all recent data is up to date."

# ═════════════════════════════════════════════════════════════════════════════
# PIVOT POINT COMPUTATION  (Polars — BUG-E6, I-D2 fixes)
# ═════════════════════════════════════════════════════════════════════════════
def compute_pivot_points(
    year: int,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[bool, str]:
    """
    Compute Classic, Fibonacci, Woodie, and Camarilla pivot points for year
    and write them to pivots_output.csv.
    Fixes applied
    ─────────────
    BUG-E6  Camarilla anchor is P_CAM = previous-day Close (not P_CLASSIC)
    BUG-E7  Column names always uppercase (normalised on load)
    I-D2    Output date format is YYYY-MM-DD (consistent with EOD CSV)
    I-R3    Atomic write via .tmp → os.replace
    """
    try:
        in_csv = eod_csv_path(year)
        out_csv = pivot_csv_path(year)

        if not os.path.exists(in_csv):
            return False, f"EoD data for {year} not found — download it first."

        if progress_callback:
            progress_callback(f"Computing pivot points for {year}…")

        df = pl.read_csv(in_csv, try_parse_dates=True)

        # ── Normalise column names to uppercase (BUG-E7) ──────────────────────
        df = df.rename({c: c.strip().upper() for c in df.columns})

        # ── Clean price / volume columns ──────────────────────────────────────
        for col in Col.PRICE_COLS:
            if col in df.columns:
                df = df.with_columns(
                    pl.col(col)
                    .cast(pl.String)
                    .str.replace_all(",", "")
                    .str.strip_chars()
                    .cast(pl.Float64, strict=False)
                    .alias(col)
                )

        # ── Ensure DATE is a proper date type ────────────────────────────────
        if df[Col.DATE].dtype in (pl.String, pl.Utf8):
            df = df.with_columns(
                pl.col(Col.DATE)
                .str.to_date(format="%Y-%m-%d", strict=False)
                .alias(Col.DATE)
            )

        df = df.sort([Col.SYMBOL, Col.CATEGORY, Col.DATE])

        # ── Previous-day H, L, C via shift-over ──────────────────────────────
        df = df.with_columns([
            pl.col(Col.HIGH).shift(1).over([Col.SYMBOL, Col.CATEGORY]).alias("H"),
            pl.col(Col.LOW).shift(1).over([Col.SYMBOL, Col.CATEGORY]).alias("L"),
            pl.col(Col.CLOSE).shift(1).over([Col.SYMBOL, Col.CATEGORY]).alias("C"),
        ])
        df = df.drop_nulls(["H", "L", "C"])

        df = df.with_columns([
            ((pl.col("H") + pl.col("L") + pl.col("C")) / 3).alias(Col.P_CLASSIC),
            (pl.col("H") - pl.col("L")).alias("RANGE"),
        ])

        # ── Classic pivots ────────────────────────────────────────────────────
        df = df.with_columns([
            (2 * pl.col(Col.P_CLASSIC) - pl.col("L")).alias(Col.CL_R1),
            (2 * pl.col(Col.P_CLASSIC) - pl.col("H")).alias(Col.CL_S1),
            (pl.col(Col.P_CLASSIC) + pl.col("RANGE")).alias(Col.CL_R2),
            (pl.col(Col.P_CLASSIC) - pl.col("RANGE")).alias(Col.CL_S2),
            (pl.col("H") + 2 * (pl.col(Col.P_CLASSIC) - pl.col("L"))).alias(Col.CL_R3),
            (pl.col("L") - 2 * (pl.col("H") - pl.col(Col.P_CLASSIC))).alias(Col.CL_S3),
        ])

        # ── Fibonacci pivots ──────────────────────────────────────────────────
        df = df.with_columns([
            (pl.col(Col.P_CLASSIC) + 0.382 * pl.col("RANGE")).alias(Col.FIB_R1),
            (pl.col(Col.P_CLASSIC) - 0.382 * pl.col("RANGE")).alias(Col.FIB_S1),
            (pl.col(Col.P_CLASSIC) + 0.618 * pl.col("RANGE")).alias(Col.FIB_R2),
            (pl.col(Col.P_CLASSIC) - 0.618 * pl.col("RANGE")).alias(Col.FIB_S2),
            (pl.col(Col.P_CLASSIC) + 1.000 * pl.col("RANGE")).alias(Col.FIB_R3),
            (pl.col(Col.P_CLASSIC) - 1.000 * pl.col("RANGE")).alias(Col.FIB_S3),
        ])

        # ── Woodie pivots ─────────────────────────────────────────────────────
        df = df.with_columns(
            ((pl.col("H") + pl.col("L") + 2 * pl.col("C")) / 4).alias(Col.P_WOODIE)
        )
        df = df.with_columns([
            (2 * pl.col(Col.P_WOODIE) - pl.col("L")).alias(Col.WD_R1),
            (2 * pl.col(Col.P_WOODIE) - pl.col("H")).alias(Col.WD_S1),
            (pl.col(Col.P_WOODIE) + pl.col("RANGE")).alias(Col.WD_R2),
            (pl.col(Col.P_WOODIE) - pl.col("RANGE")).alias(Col.WD_S2),
        ])

        # ── Camarilla pivots (BUG-E6: P_CAM = prev close C) ─────────────────
        df = df.with_columns(
            pl.col("C").alias(Col.P_CAM)  # anchor is previous-day close, not a pivot avg
        )
        df = df.with_columns([
            (pl.col("C") + pl.col("RANGE") * 1.1 / 12).alias(Col.CAM_R1),
            (pl.col("C") - pl.col("RANGE") * 1.1 / 12).alias(Col.CAM_S1),
            (pl.col("C") + pl.col("RANGE") * 1.1 / 6).alias(Col.CAM_R2),
            (pl.col("C") - pl.col("RANGE") * 1.1 / 6).alias(Col.CAM_S2),
            (pl.col("C") + pl.col("RANGE") * 1.1 / 4).alias(Col.CAM_R3),
            (pl.col("C") - pl.col("RANGE") * 1.1 / 4).alias(Col.CAM_S3),
            (pl.col("C") + pl.col("RANGE") * 1.1 / 2).alias(Col.CAM_R4),
            (pl.col("C") - pl.col("RANGE") * 1.1 / 2).alias(Col.CAM_S4),
        ])

        # ── Format DATE as YYYY-MM-DD (I-D2 — consistent with EOD CSV) ────────
        df = df.with_columns(
            pl.col(Col.DATE).dt.strftime("%Y-%m-%d").alias(Col.DATE)
        )

        # ── Select final columns (keep only those that exist) ─────────────────
        present = [c for c in Col.PIVOT_FINAL_COLS if c in df.columns]

        # ── Atomic write (I-R3 / BUG-E9) ─────────────────────────────────────
        tmp_csv = out_csv + ".tmp"
        df.select(present).write_csv(tmp_csv)
        os.replace(tmp_csv, out_csv)

        log.info("Pivot points saved for %d (%d rows).", year, df.height)
        return True, f"✓ Pivot points saved for {year} ({df.height:,} rows)"

    except Exception as exc:
        log.error("compute_pivot_points failed for %d: %s", year, exc)
        return False, f"Error computing pivots: {exc}"

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR DOWNLOAD HELPERS  (F6 — return bytes for st.download_button)
# ═════════════════════════════════════════════════════════════════════════════
def get_eod_csv_bytes(year: int) -> Optional[bytes]:
    """
    Return raw bytes of the EOD CSV for year, or None if not found.
    Usage in Streamlit sidebar
    --------------------------
    data = get_eod_csv_bytes(year)
    if data:
        st.download_button(
            label=f"⬇ Download EOD {year}",
            data=data,
            file_name=f"EOD_DATA_{year}.csv",
            mime="text/csv",
        )
    """
    path = eod_csv_path(year)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()

def get_pivot_csv_bytes(year: int) -> Optional[bytes]:
    """
    Return raw bytes of the pivot CSV for year, or None if not found.
    Usage in Streamlit sidebar
    --------------------------
    data = get_pivot_csv_bytes(year)
    if data:
        st.download_button(
            label=f"⬇ Download Pivots {year}",
            data=data,
            file_name=f"Pivots_{year}.csv",
            mime="text/csv",
        )
    """
    path = pivot_csv_path(year)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()

def get_filtered_eod_bytes(
    year: int,
    symbols: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Optional[bytes]:
    """
    Return filtered EOD data as CSV bytes for download.
    All filter parameters are optional.  Pass None to skip that filter.

    Parameters
    ----------
    year : Data year.
    symbols : List of SYMBOL values to include.
    categories : List of CATEGORY values to include.
    date_from : Inclusive lower bound as "YYYY-MM-DD".
    date_to : Inclusive upper bound as "YYYY-MM-DD".

    Returns
    -------
    CSV bytes, or None if the file does not exist.

    Usage in Streamlit
    ------------------
    data = get_filtered_eod_bytes(year, symbols=["RELIANCE", "TCS"],
                                  date_from="2025-01-01")
    if data:
        st.download_button("⬇ Download filtered EOD", data=data,
                           file_name="filtered_eod.csv", mime="text/csv")
    """
    path = eod_csv_path(year)
    if not os.path.exists(path):
        return None

    df = pl.read_csv(path)
    df = df.rename({c: c.strip().upper() for c in df.columns})

    # Parse DATE for range filtering
    if Col.DATE in df.columns and (date_from or date_to):
        if df[Col.DATE].dtype in (pl.String, pl.Utf8):
            df = df.with_columns(
                pl.col(Col.DATE)
                .str.to_date(format="%Y-%m-%d", strict=False)
                .alias(Col.DATE)
            )
        if date_from:
            df = df.filter(
                pl.col(Col.DATE) >= pl.lit(date_from).str.to_date(format="%Y-%m-%d")
            )
        if date_to:
            df = df.filter(
                pl.col(Col.DATE) <= pl.lit(date_to).str.to_date(format="%Y-%m-%d")
            )

    if symbols and Col.SYMBOL in df.columns:
        df = df.filter(pl.col(Col.SYMBOL).is_in(symbols))

    if categories and Col.CATEGORY in df.columns:
        df = df.filter(pl.col(Col.CATEGORY).is_in(categories))

    buf = io.BytesIO()
    df.write_csv(buf)
    return buf.getvalue()

def get_filtered_pivot_bytes(
    year: int,
    symbols: Optional[List[str]] = None,
    date: Optional[str] = None,
) -> Optional[bytes]:
    """
    Return pivot data filtered by symbol list and/or a specific date as bytes.
    Parameters
    ----------
    year : Data year.
    symbols : List of SYMBOL values to include.
    date : Exact date as "YYYY-MM-DD".

    Usage in Streamlit
    ------------------
    data = get_filtered_pivot_bytes(year, symbols=selected_symbols, date="2025-03-28")
    if data:
        st.download_button("⬇ Download Pivots", data=data,
                           file_name="pivots_filtered.csv", mime="text/csv")
    """
    path = pivot_csv_path(year)
    if not os.path.exists(path):
        return None

    df = pl.read_csv(path)
    df = df.rename({c: c.strip().upper() for c in df.columns})

    if symbols and Col.SYMBOL in df.columns:
        df = df.filter(pl.col(Col.SYMBOL).is_in(symbols))

    if date and Col.DATE in df.columns:
        df = df.filter(pl.col(Col.DATE) == date)

    buf = io.BytesIO()
    df.write_csv(buf)
    return buf.getvalue()
