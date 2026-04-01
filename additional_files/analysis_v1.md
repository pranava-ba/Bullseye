# Bullseye Fintech — NSE EOD Dashboard
## Comprehensive Technical Analysis: Algorithm, Issues & Improvements

> **Files analysed:** `EoD_module.py` · `app_v2.py`  
> **Date:** March 2026  
> **Version:** v2 (post-bugfix series 1–12)

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [EoD_module.py — Step-by-Step Algorithm](#2-eod_modulepy--step-by-step-algorithm)
   - 2.1 Initialisation & Logging
   - 2.2 Path Resolution
   - 2.3 HTTP Session
   - 2.4 Trading Calendar
   - 2.5 Single-Date Download (`process_date`)
   - 2.6 File Processing (`process_file`)
   - 2.7 Download Orchestrator (`download_year_data`)
   - 2.8 Data Management Helpers
   - 2.9 Auto-Update Check
   - 2.10 Pivot Point Computation
3. [app_v2.py — Step-by-Step Algorithm](#3-app_v2py--step-by-step-algorithm)
   - 3.1 Page Config & CSS Injection
   - 3.2 Constants & Colour Palette
   - 3.3 Cached Data Loaders
   - 3.4 Sidebar — Settings, Data Management, Downloader
   - 3.5 Auto-Update Hook
   - 3.6 Global Filters
   - 3.7 Tab 1 — OHLCV Summary
   - 3.8 Tab 2 — Pivot Points
4. [Known / Potential Bugs & Issues](#4-known--potential-bugs--issues)
   - 4.1 EoD_module.py Issues
   - 4.2 app_v2.py Issues
   - 4.3 Cross-Module Issues
5. [Improvements](#5-improvements)
   - 5.1 Reliability & Robustness
   - 5.2 Performance
   - 5.3 Data Correctness
   - 5.4 Code Quality & Maintainability
6. [Proposed New Features](#6-proposed-new-features)
7. [Data Flow Diagram (Text)](#7-data-flow-diagram-text)

---

## 1. High-Level Architecture

```
┌───────────────────────────────────────────────────────┐
│                   app_v2.py                           │
│  Streamlit frontend — UI, filtering, charting         │
│  Imports: download_year_data, compute_pivot_points,   │
│           get_available_years, delete_year_data,      │
│           run_auto_update, DATA_DIR                   │
└──────────────────┬────────────────────────────────────┘
                   │  function calls
┌──────────────────▼────────────────────────────────────┐
│                 EoD_module.py                         │
│  Backend — download, parse, compute, persist          │
└──────────────────┬────────────────────────────────────┘
                   │  reads/writes
┌──────────────────▼────────────────────────────────────┐
│  File System (DATA_DIR)                               │
│  ├── CUE_DATE_<year>.csv          (trading calendar)  │
│  ├── EOD_DATA_FOR_ANALYSIS_<year>.csv  (raw EoD)      │
│  ├── pivots_output<year>.csv      (computed pivots)   │
│  └── nse_eod_data_files/          (temp extracted PD) │
└───────────────────────────────────────────────────────┘
                   │  HTTP GET
┌──────────────────▼────────────────────────────────────┐
│  NSE Archives (archives.nseindia.com)                 │
│  PR<DDMMYY>.zip → Pd<DDMMYY>.csv                     │
└───────────────────────────────────────────────────────┘
```

The application is a two-layer system. `EoD_module.py` is a pure-Python backend that handles all I/O (network, filesystem, parsing, computation). `app_v2.py` is a Streamlit frontend that calls backend functions and renders results. There is no database — all state lives in flat CSV files on disk.

---

## 2. EoD_module.py — Step-by-Step Algorithm

### 2.1 Initialisation & Logging

1. Standard library and third-party packages are imported at module level (`os`, `re`, `sys`, `zipfile`, `warnings`, `time`, `logging`, `numpy`, `pandas`, `polars`, `requests`, `datetime`, `pandas_market_calendars`).
2. `_get_log_path()` is called at import time to determine a writable log path:
   - If the app is running as a **frozen PyInstaller EXE on Windows** → `%APPDATA%\BullseyeFintech\NSE_Dashboard\bullseye.log`
   - Otherwise (development mode) → same directory as the module file.
3. `logging.basicConfig` sets up two handlers: a `FileHandler` (UTF-8) and a `StreamHandler` to stdout. All subsequent log calls use the module-level `log` logger.
4. Pandas future-downcasting warnings and generic `FutureWarning` are suppressed.

### 2.2 Path Resolution

1. `get_data_dir()` is called at module import time (not on first use) so `DATA_DIR` is always available as a module constant.
2. Path logic branches on two conditions: `sys.frozen` (PyInstaller) and `os.name == 'nt'` (Windows):
   - **Frozen + Windows** → `%APPDATA%\BullseyeFintech\NSE_Dashboard\data`
   - **Frozen + non-Windows** → `<executable_dir>/data`
   - **Development** → `<module_dir>/data`
3. `NSE_EOD_DIR = DATA_DIR/nse_eod_data_files` is created immediately for temp files.

### 2.3 HTTP Session

1. A module-level `requests.Session` is created once and reused for all downloads.
2. Headers mimic a Chrome browser on Windows 10 to avoid NSE's bot-detection:
   - `User-Agent`, `Accept`, `Accept-Language`, `Referer`
3. The session is shared across all `process_date` calls in a single run.

### 2.4 Trading Calendar

**`get_nse_trading_days(year)`**

1. Uses `pandas_market_calendars.get_calendar("NSE")` to retrieve the NSE exchange calendar object.
2. Calls `.valid_days(start_date, end_date)` for the full year to get all valid trading days as pandas Timestamps.
3. Converts each to `DD-MM-YYYY` string format (the format expected by NSE archive URLs).
4. Returns the list.

**`save_trading_days_to_csv(trading_days, year)`**

1. Wraps the list in a single-column DataFrame with header `details`.
2. Writes to `DATA_DIR/CUE_DATE_<year>.csv`.

### 2.5 Single-Date Download — `process_date(Tdate, target_year, progress_callback)`

This is the innermost loop function, called once per trading day.

**Step 1 — Build the URL**

The NSE bhavcopy archive URL has the format:
```
https://archives.nseindia.com/archives/equities/bhavcopy/pr/PR<DDMMYY>.zip
```
The two-digit year (`YY`) is extracted from the last two characters of the `YYYY` portion of the `DD-MM-YYYY` date string. Example: `24-03-2025` → `Tdate_1_pd = "240325"` → URL contains `PR240325.zip`.

**Step 2 — Download ZIP**

1. A process-specific temp file `pd_<PID>.zip` is used to avoid collisions in concurrent runs.
2. `SESSION.get(url, timeout=30)` fetches the ZIP.
3. If HTTP 403 is returned (NSE blocking), the function returns `None` immediately (not a fatal error).
4. Any other non-2xx status raises via `raise_for_status()`.
5. On success, raw bytes are written to the temp zip path.

**Step 3 — Extract the CSV from the ZIP**

1. The ZIP is opened with `zipfile.ZipFile`.
2. The member file is located by searching `zf.namelist()` for a name containing `Pd<DDMMYY>` (capitalised `Pd`, not `PD`).
3. If not found (malformed archive), `None` is returned.
4. The member is read as raw bytes and written to `NSE_EOD_DIR/<filename>`.

**Step 4 — Cleanup (finally block)**

Regardless of success or failure, the temp `pd_<PID>.zip` is deleted.

**Returns:** `True` on success, `None` on any failure.

### 2.6 File Processing — `process_file(file_path)`

Parses a single extracted `Pd<DDMMYY>.csv` into a clean DataFrame for appending to the master CSV.

**Step 1 — Load & Clean**

1. `pd.read_csv(file_path)` loads the raw NSE file.
2. Whitespace-only cells are replaced with `NaN` (regex `^\s+$`).
3. Columns `IND_SEC` and `CORP_IND` are dropped if present.
4. Rows where `SECURITY` is `NaN` are dropped (these are blank separator rows in NSE format).

**Step 2 — Build CATEGORY Labels**

The NSE PD file has a nested structure where category headings appear as special rows (rows where `MKT` is null but `SECURITY` holds a category name, e.g. `"A"`, `"SME EMERGE"`). The code reconstructs which category each security row belongs to:

1. Count consecutive non-null `MKT` rows from the top → these are **NIFTY INDEX** rows.
2. From index `count1` onwards, identify rows where `MKT` is null and `SECURITY` is non-null → these are **category heading rows**, collected into `list_category`.
3. Identify the row indices of each heading → `list_index`.
4. For each consecutive pair of heading indices `(i, j)`, assign the category name to all data rows between them.
5. Assign the last category name to all remaining rows after the last heading.
6. Combine: `["NIFTY INDEX"] * count1 + heading_assignments`.

**Step 3 — Build Final DataFrame**

1. Rows where `MKT` is null are dropped (these are the heading rows themselves, not security data rows).
2. The index is reset.
3. `SYMBOL` column is filled: if `SYMBOL` is null for a row, use `SECURITY` as the symbol (this handles some NSE format edge cases).
4. The reconstructed `CATEGORY` list is assigned as a new column.

**Step 4 — Parse Date from Filename**

1. A regex `(\d{2})(\d{2})(\d{2})` extracts `DD`, `MM`, `YY` from the filename (e.g. `Pd240325.csv` → `24`, `03`, `25`).
2. Full year is computed as `2000 + YY`. This hardcodes the assumption that all data is post-2000.
3. The date is stored as `YYYY-MM-DD` string in a new `DATE` column.

**Step 5 — Final Cleanup**

Columns `MKT` and `SERIES` are dropped. The clean DataFrame is returned.

### 2.7 Download Orchestrator — `download_year_data(year, force_redownload, progress_callback)`

**Step 1 — Trading Calendar**

If `CUE_DATE_<year>.csv` does not exist, `get_nse_trading_days(year)` is called and saved. Otherwise the existing file is used.

**Step 2 — Early Exit**

If `EOD_DATA_FOR_ANALYSIS_<year>.csv` already exists and `force_redownload=False`, the function returns immediately with a success message.

**Step 3 — Download Loop**

Iterates over every date in `CUE_DATE_<year>.csv`. For each date, calls `process_date()`. Tracks how many dates were successfully downloaded (`success_count`).

**Step 4 — Consolidation to Master CSV**

1. Lists all files in `NSE_EOD_DIR` whose names start with `PD` (case-insensitive).
2. Sorts them (chronological by filename).
3. Opens `EOD_DATA_FOR_ANALYSIS_<year>.csv` for writing in text mode.
4. For each extracted file:
   - Calls `process_file()` to get a clean DataFrame.
   - Writes to the master CSV with `header=True` only for the first file, then `header=False` for subsequent files. This produces a single-header CSV.
   - On per-file exceptions, logs a warning and continues.

**Step 5 — Temp File Cleanup**

All extracted `PD*.csv` files in `NSE_EOD_DIR` are deleted (single cleanup loop — previously this was done inside `process_file`, which caused issues).

### 2.8 Data Management Helpers

**`get_available_years()`**

Scans `DATA_DIR` for files matching `EOD_DATA_FOR_ANALYSIS_(\d{4}).csv` and returns a sorted list of years.

**`delete_year_data(year)`**

Attempts to delete three files: the EOD CSV, the pivots CSV, and the CUE_DATE CSV for the given year. Returns a tuple `(success, message)`.

### 2.9 Auto-Update Check — `check_auto_update_needed()` / `run_auto_update()`

1. Computes `yesterday = today - 1 day`.
2. If yesterday is a weekend (`weekday >= 5`), returns `None` (no update needed).
3. Checks if `EOD_DATA_FOR_ANALYSIS_<year>.csv` exists; if not, returns `year`.
4. Reads only the `DATE` column from the full CSV and checks if yesterday's date (`YYYY-MM-DD`) is present.
5. If missing, returns `year` to signal that data for that year needs re-downloading.
6. `run_auto_update()` calls `check_auto_update_needed()` and if a year is returned, calls `download_year_data(year, force_redownload=False)`.

### 2.10 Pivot Point Computation — `compute_pivot_points(year)`

Computes four standard methods of pivot points and writes them to `pivots_output<year>.csv`.

**Step 1 — Load & Clean with Polars**

1. Reads the EOD CSV with `pl.read_csv(..., try_parse_dates=True)`.
2. For each of the seven price/volume columns (`HIGH_PRICE`, `LOW_PRICE`, `CLOSE_PRICE`, `OPEN_PRICE`, `PREV_CL_PR`, `NET_TRDVAL`, `NET_TRDQTY`):
   - Casts to `String`, strips commas and whitespace, casts to `Float64` (non-strict, so invalid values become `null`).

**Step 2 — Sort & Shift for Previous Day**

1. Sorts the DataFrame by `["SYMBOL", "CATEGORY", "DATE"]`.
2. Uses `pl.col().shift(1).over(["SYMBOL", "CATEGORY"])` to get the previous trading day's High (`H`), Low (`L`), Close (`C`) for each symbol-category group.
3. Drops rows where any of H, L, C is null (i.e. the first row for each symbol, which has no prior day).

**Step 3 — Classic Pivot Points**

```
PP  = (H + L + C) / 3
R1  = 2*PP − L
S1  = 2*PP − H
R2  = PP + (H − L)
S2  = PP − (H − L)
R3  = H + 2*(PP − L)
S3  = L − 2*(H − PP)
```

**Step 4 — Fibonacci Pivot Points**

Uses the Classic PP as the pivot base:
```
R1 = PP + 0.382 * Range
S1 = PP − 0.382 * Range
R2 = PP + 0.618 * Range
S2 = PP − 0.618 * Range
R3 = PP + 1.000 * Range
S3 = PP − 1.000 * Range
```

**Step 5 — Woodie Pivot Points**

Uses a different pivot formula that weights today's close more:
```
PP_W = (H + L + 2*C) / 4
R1   = 2*PP_W − L
S1   = 2*PP_W − H
R2   = PP_W + Range
S2   = PP_W − Range
```

**Step 6 — Camarilla Pivot Points**

Based on yesterday's close rather than a pivot average:
```
R1 = C + Range * 1.1/12
S1 = C − Range * 1.1/12
R2 = C + Range * 1.1/6
S2 = C − Range * 1.1/6
R3 = C + Range * 1.1/4
S3 = C − Range * 1.1/4
R4 = C + Range * 1.1/2
S4 = C − Range * 1.1/2
```

**Step 7 — Finalise & Write**

1. The `DATE` column (currently a Polars Date type due to `try_parse_dates`) is formatted back to `DD-MM-YYYY` string with `dt.strftime`.
2. A curated set of columns is selected and written to `pivots_output<year>.csv`.

---

## 3. app_v2.py — Step-by-Step Algorithm

### 3.1 Page Config & CSS Injection

1. `st.set_page_config` sets the browser tab title, icon, wide layout, and a collapsed sidebar default.
2. A large `st.markdown` block injects raw CSS via `unsafe_allow_html=True`. This defines:
   - Google Fonts (`IBM Plex Mono`, `IBM Plex Sans`) loaded via CDN.
   - Dark theme colours (GitHub-like: `#0d1117` background, `#e6edf3` text).
   - Custom component classes: `.kpi-card`, `.wk52-wrap`, `.pivot-row`, `.pivot-table-wrap`, `.method-badge`, etc.
   - Streamlit internal selectors overridden (`.stTabs`, `[data-testid="stSidebar"]`).
3. A `PLOTLY_LAYOUT` dict is defined as a shared base layout for all Plotly figures.
4. `METHOD_COLORS` defines colour palettes for each pivot method (PP colour, resistance colours array, support colours array).

### 3.2 Constants & Colour Palette

Column name constants are defined (e.g. `C_OPEN = "OPEN_PRICE"`) to allow a single point of change if column names ever shift.

`METHOD_COLS` maps each pivot method name to a tuple of `(pp_column_name, [resistance_col_names], [support_col_names])`. These names are **uppercase** (e.g. `"P_CLASSIC"`, `"CL_R1"`).

`DEFAULT_LEVELS` defines the default set of R/S indices shown per method.

### 3.3 Cached Data Loaders

**`load_data(path)`** — `@st.cache_data`

1. Reads the EOD CSV with `pd.read_csv`.
2. Strips and uppercases all column names (defensive normalisation).
3. Parses `DATE` column by trying three formats in order: `%Y-%m-%d`, `%d-%m-%Y`, `%d/%m/%Y`.
4. For each numeric column in the standard list, strips commas and whitespace, then coerces to numeric (errors → NaN).
5. Sorts by `["SYMBOL", "CATEGORY", "DATE"]`.

**`load_pivots(path)`** — `@st.cache_data`

1. Reads the pivots CSV, uppercases column names.
2. Parses `DATE` with the same three-format try loop.

### 3.4 Sidebar — Settings, Data Management, Downloader

The entire sidebar is built inside a `with st.sidebar:` block executed at module level (i.e. on every Streamlit re-run):

**Settings section**
- An `st.toggle` for "Auto-update on launch" writes to `st.session_state.auto_update_enabled`.

**Data Management section**
- `get_available_years()` is called to list available data years.
- Each year is displayed as a button. Clicking sets `st.session_state.selected_year = yr` and calls `st.rerun()`.

**Download Data section**
- A radio for download mode: Single Year / Multiple Years / All Available.
- A checkbox for force re-download.
- On "Start Download" button click:
  1. Iterates over `selected_years`.
  2. For each year, calls `download_year_data()` in a `st.status` widget.
  3. If download succeeds, immediately calls `compute_pivot_points()`.
  4. After all years, sets `auto_update_done = True` and calls `st.rerun()`.

**Delete Data section**
- A selectbox + delete button. On confirmation, calls `delete_year_data()` and reruns.

**Footer**
- Displays `DATA_DIR` path in small monospaced font.

### 3.5 Auto-Update Hook

`check_and_run_auto_update()` is called at module level (after the sidebar) on every Streamlit run. It checks:
- `auto_update_enabled == True`
- `auto_update_done == False`

If both conditions are met, runs `run_auto_update()` with `st.write` as the progress callback, displayed inside a `st.status` widget in the sidebar.

### 3.6 Global Filters

Four filter widgets are placed in a 4-column row:
- **Category** multiselect (defaults to first category)
- **Symbol** multiselect (pool filtered by selected categories; defaults to first symbol)
- **Date From** date_input (min date in dataset)
- **Date To** date_input (max date in dataset)

`df_filtered` is computed by applying all four filters to `df_raw`. If the result is empty, a warning is shown and `st.stop()` is called.

### 3.7 Tab 1 — OHLCV Summary

1. If multiple symbols are selected, a secondary selectbox allows choosing which single symbol to show detail for (`detail_symbol`).
2. `df_sym` is filtered from `df_filtered` for the detail symbol. `latest = df_sym.iloc[-1]` gets the most recent row.

**KPI Cards (toggleable):**
- Six KPI cards: Open, High, Low, Close (with delta vs prev close), Prev Close, Volume.
- Each card rendered as raw HTML using the `.kpi-card` CSS class.
- Delta is green/red/neutral based on sign.

**52-Week Range Bar (toggleable):**
- Reads `HI_52_WK` and `LO_52_WK` from the latest row.
- Computes `pct = (current − low52) / (high52 − low52) * 100`.
- Renders a CSS gradient bar with a circle marker at `pct%` position, entirely via `st.markdown` HTML.

**OHLCV Chart:**
- `chart_opts` selectbox: Candlestick / Line (Close) / OHLC Bar.
- `overlay_opts` multiselect: Volume, 20-Day MA, 50-Day MA, Bollinger Bands.
- Subplots are 2-row (price + volume) if Volume is selected, otherwise 1-row.
- MA and Bollinger Bands use pandas rolling on the already-filtered `df_sym` series.
- Volume bars are coloured green/red based on `close >= prev_close`.
- If fewer data points exist than required for an overlay (e.g. < 20 rows for MA20), a warning info box is shown.

**Raw Data Table (toggleable):**
- Displays selected columns sorted newest-first.

### 3.8 Tab 2 — Pivot Points

**Comparison Settings:**

Four column controls:
1. `pivot_methods` multiselect (Classic / Fibonacci / Woodie / Camarilla)
2. `comp_categories` multiselect (from pivot CSV)
3. `comp_symbols` multiselect (filtered by selected categories)
4. `sel_piv_date` selectbox (available dates for selected symbols, newest selected by default)

**Configurable Pivot Levels expander:**

For each selected method, the user can choose which R and S level indices to display (e.g. only R1 and S1 for Classic). Stored in `st.session_state.pivot_level_selections`.

**Custom Pivot Value Overrides expander:**

For each method and each level (PP, R1…Rn, S1…Sn), a text input allows manual override of the computed value. The auto-computed value is shown as placeholder hint text. Overrides are stored in `custom_overrides` dict.

**Pivot Table:**

For each symbol in `comp_symbols`:
1. Filters `df_piv_all` for that symbol and the selected date.
2. Builds a CSS grid table with columns = pivot methods, rows = levels (R_max down to PP down to S_max).
3. Values from `custom_overrides` take precedence over computed values.
4. Each row class (`pivot-res`, `pivot-pp`, `pivot-sup`) applies the colour coding from CSS.

**Overlapping Price + Pivot Chart:**

1. Plots a price line for each symbol in `comp_symbols` (using `df_raw`, filtered by date range).
2. For each symbol × method combination, draws horizontal lines (as two-point Scatter traces) for PP, selected R levels, and selected S levels, using the **latest** pivot values from `df_piv_all` (not the selected date).
3. Legend grouping collapses all levels for a symbol+method under one toggle.
4. Custom overrides are respected.

**Full Pivot Data Table (toggleable):**

Displays the full filtered pivot DataFrame for selected symbols, filtered to selected columns per method.

---

## 4. Known / Potential Bugs & Issues

### 4.1 EoD_module.py Issues

---

#### BUG-E1 — Two-Digit Year Ambiguity (Partial Fix Only)

**Severity: High**

`process_file` computes the full year as `2000 + yr_2dig`. This is hard-coded. If NSE ever restores access to pre-2000 archives (they do exist), or if the date format in the filename changes, this silently produces wrong dates.

More practically: the filename parsing regex `(\d{2})(\d{2})(\d{2})` will also match any other six consecutive digits in the filename (e.g. if NSE changes their naming convention). There is no validation that the extracted day/month are in a valid calendar range.

---

#### BUG-E2 — `process_date` Uses Only Last Two Characters of Year String

**Severity: Medium**

```python
year_str   = Tdate[6:]          # e.g. "2025"
Tdate_1_pd = T_d + T_month + year_str[-2:]  # → "240325"
```

If `Tdate` were ever in a different format or longer than expected, `year_str[-2:]` could silently produce wrong output. The slicing is fragile and relies on exact string length with no validation.

---

#### BUG-E3 — CATEGORY Assignment Logic Can Silently Produce Wrong Results

**Severity: High**

The category assignment in `process_file` is a pure index-arithmetic reconstruction. If NSE ever changes the file format (e.g. adds a new separator row type, or renames the heading structure), the `list_category`, `list_index`, `heading` logic will produce wrong or mis-aligned categories without raising any error. There is no assertion that `len(category) == len(df_final)` before assignment.

In fact, if `df_dropped.shape[0] - 1 - list_index[-1]` is ever negative (edge case), the `list3` assignment would silently produce an empty list and the final `category` list would be shorter than `df_final`, causing a length mismatch on `df_final["CATEGORY"] = category`.

---

#### BUG-E4 — No Session Cookie Refresh

**Severity: Medium**

NSE often requires a valid session cookie to serve bhavcopy files. The current code creates one `requests.Session` at module import and never refreshes it. If a long download (e.g. full year = 250 days) causes the session/cookie to expire mid-run, the subsequent requests will return 403 silently, and those dates will be skipped without any retry.

---

#### BUG-E5 — No Retry Logic

**Severity: Medium**

`process_date` returns `None` on any failure (403, timeout, bad ZIP, extraction error) and moves on. There is no retry with backoff for transient network errors. A momentary connectivity blip will cause an entire trading day to be skipped silently.

---

#### BUG-E6 — `compute_pivot_points` Uses `P_CLASSIC` for Fibonacci and Camarilla PP Column Name

**Severity: Medium — Column Name Mismatch**

In `EoD_module.py`, the pivot point for Camarilla is not actually a separate computation — Camarilla levels are derived from `C` (previous close), not from any pivot average. However, looking at `METHOD_COLS` in `app_v2.py`:

```python
"Camarilla": ("P_CLASSIC", ...)
```

This means the frontend looks for `P_CLASSIC` as the PP column for Camarilla display. But conceptually, Camarilla does not have a traditional PP. The current approach repurposes `P_CLASSIC` for Camarilla's pivot display, which is technically incorrect but functionally works because `P_CLASSIC` is in the output CSV. This is a semantic bug that will mislead users who interpret the Camarilla "PP" row as the Camarilla pivot.

---

#### BUG-E7 — Column Name Case Mismatch Between Module and Frontend (Active Risk)

**Severity: High**

The pivot CSV is written with column names exactly as Polars produces them (e.g. `P_classic`, `P_woodie` — lowercase suffix). The `load_pivots()` function in `app_v2.py` uppercases all column names with `df.columns = [c.strip().upper() for c in df.columns]`. This means the frontend looks for `P_CLASSIC` (uppercased), which correctly maps to what was written as `P_classic`.

**However**, `METHOD_COLS` in `app_v2.py` is hardcoded with uppercase names (`"P_CLASSIC"`, `"CL_R1"`, etc.). If anyone adds a column in `compute_pivot_points` with an uppercase name in Polars (e.g. `pl.col("P_CLASSIC").alias("P_CLASSIC")`) while the load step already uppercases, there is no double-uppercase issue, but this is fragile and the correctness depends entirely on the `.upper()` normalisation in `load_pivots`. If that normalisation is ever removed or skipped, every column lookup in the pivot tab will produce NaN.

---

#### BUG-E8 — `check_auto_update_needed` Does Not Account for NSE Holidays

**Severity: Medium**

The function skips weekends but does not consult the trading calendar. If yesterday was an NSE holiday (not a weekend), the function will return `year`, triggering a download attempt that will succeed for 0 new files (since there's no bhavcopy for a holiday). This wastes time and may confuse users who see an "update triggered" message on a holiday.

---

#### BUG-E9 — Master CSV Written With `open(..., "w")` — No Atomic Write

**Severity: Medium**

`download_year_data` opens the master CSV for writing immediately before the consolidation loop. If the process is interrupted mid-loop (crash, user kills the app), the resulting CSV will be truncated and corrupt. There is no temp-file-then-rename strategy to ensure atomicity.

---

#### BUG-E10 — All PD Files From `NSE_EOD_DIR` Are Consolidated, Regardless of Year

**Severity: Medium**

```python
files = sorted([f for f in os.listdir(NSE_EOD_DIR) if f.upper().startswith("PD")])
```

If two download operations are running concurrently (e.g. user rapidly clicks "Start Download" twice with different years), the `NSE_EOD_DIR` folder is shared and both runs will see each other's extracted files. The consolidation step would merge data from two different years into one year's master CSV.

---

#### BUG-E11 — `delete_year_data` Does Not Delete Partial PD Files

**Severity: Low**

`delete_year_data` deletes the three known CSVs. But if a download was interrupted and left partial PD files in `NSE_EOD_DIR`, those are not cleaned up. Over time these can accumulate and cause incorrect consolidation on the next download attempt.

---

#### BUG-E12 — `get_nse_trading_days` Is Not Error-Handled

**Severity: Low**

If `pandas_market_calendars` cannot fetch the NSE calendar (e.g. the library's internal data is missing or the package is outdated), the exception propagates unhandled from `download_year_data` and surfaces as a generic error message. A more specific error message would be helpful.

---

### 4.2 app_v2.py Issues

---

#### BUG-A1 — Pivot Levels Chart Uses Latest Pivot Values, Not the Selected Date's Values

**Severity: High**

In the overlapping pivot chart (Tab 2):

```python
latest_piv = df_piv_sym.iloc[-1]
```

This always uses the **last available** pivot row for the symbol, regardless of `sel_piv_date`. This means the horizontal pivot lines on the chart always reflect the most recent computed pivots, not the date the user selected in the table above. The pivot table and chart show different things for any date other than the latest.

---

#### BUG-A2 — `st.cache_data` Cache Is Never Invalidated After Download

**Severity: High**

`load_data` and `load_pivots` are decorated with `@st.cache_data`. After a new year is downloaded, `st.rerun()` is called. However, the cache key is the file path, which does not change. If the same path had been loaded before (e.g. a year was re-downloaded with `force_redownload=True`), Streamlit will serve the stale cached DataFrame. Users will see old data until the cache is manually cleared or the app is restarted.

---

#### BUG-A3 — "All Available" Download Mode Attempts to Download from Year 2000 to Present

**Severity: Medium**

```python
year_options = list(range(2000, current_year + 1))
# ...
else:  # "All Available"
    selected_years = year_options
```

Selecting "All Available" will attempt to download 25+ years of data, one year at a time. This would run for many hours and is almost certainly not what the user intends. The name "All Available" implies "all years I already have data for", not "all years since 2000". The available years (from `get_available_years()`) are not used here.

---

#### BUG-A4 — `date_from` / `date_to` Filter on Pivot Tab Uses Global Date Filter

**Severity: Low — Design Issue**

The pivot table date filter (`sel_piv_date`) and the chart date range both use `date_from` / `date_to` from the global filter row at the top. This creates confusion: the global date filter is supposed to filter OHLCV data in Tab 1, but it silently also controls what's visible in the pivot chart in Tab 2. If a user sets a narrow date range in Tab 1 to zoom into a specific period, Tab 2's chart will also be cropped.

---

#### BUG-A5 — `_pivot_row_html` Uses `r.get(col_key)` Which Falls Back to `NaN` (Not the Override)

**Severity: Medium**

In the pivot table rendering loop:

```python
def _get(col_key):
    raw = r.get(col_key, np.nan)
    ov_val = ov.get(col_key)
    return ov_val if ov_val is not None else raw
```

`r` here is a pandas Series (a row from `iloc[0]`). `r.get(col_key, np.nan)` works for Series, but if `col_key` is not in the column list, it returns `np.nan`. The override logic is correct. However, the `_pivot_row_html` function itself calls `r.get(col_key)` directly in some paths without going through `_get`, meaning custom overrides may not be applied consistently.

---

#### BUG-A6 — `progress_callback` Defined Inside Sidebar Block Is Used Outside

**Severity: Low — Scoping Issue**

`progress_callback = st.write` is defined inside `with st.sidebar:`. This means when it is used during the download, `st.write` renders inside the sidebar context. This is intentional for the auto-update flow, but during manual downloads, the `st.status` widget handles progress differently and the callback may produce double rendering.

---

#### BUG-A7 — Volume Bar Colour Uses `PREV_CL_PR`, Falls Back to `shift(1)` of Close

**Severity: Low**

```python
df_sym[C_PREV].fillna(0) if C_PREV in df_sym.columns
else df_sym[C_CLOSE].shift(1).fillna(0)
```

If `PREV_CL_PR` is present but has `NaN` for some rows, `fillna(0)` will colour those bars green (since any close ≥ 0). A zero fill for price data is semantically wrong; it should fall back to `shift(1)` of close on a per-row basis.

---

#### BUG-A8 — No Error Handling if `comp_symbols` Is Empty in Pivot Tab

**Severity: Low**

`available_dates` is computed as:
```python
df_piv_all[df_piv_all["SYMBOL"].isin(comp_symbols)]["DATE"].dt.date.unique()
```
If `comp_symbols` is somehow empty (edge case if pivot data has no symbols), this returns an empty array and `sel_piv_date = None`. The downstream code for the chart then silently renders nothing without a clear user message.

---

#### BUG-A9 — `load_data` Date Parsing Tries Formats Sequentially Without Catching All Exceptions

**Severity: Low**

```python
for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
    try:
        df["DATE"] = pd.to_datetime(df["DATE"], format=fmt)
        break
    except (ValueError, TypeError):
        continue
```

If none of the three formats match, the loop exits silently and `DATE` remains as an object (string) column. No warning is raised. All downstream date comparisons (`df["DATE"].dt.date >= date_from`) will throw an `AttributeError` that is not caught.

---

#### BUG-A10 — Bollinger Band Fill Direction

**Severity: Very Low — Visual**

```python
fig.add_trace(go.Scatter(x=x, y=bb_dn, ..., fill="tonexty", ...))
```

`fill="tonexty"` fills between this trace and the *previous* trace. Since the upper band is added first, this correctly fills between upper and lower bands. However, if the user adds MA20 or MA50 (which are added before Bollinger Bands), the `tonexty` fill will extend to the MA line, not the BB upper band. The fill should use `fillbetween` with an explicit target trace ID.

---

### 4.3 Cross-Module Issues

---

#### BUG-X1 — Column Name Contract Is Implicit and Undocumented

The only thing keeping `EoD_module.py` and `app_v2.py` in sync on column names is the `.upper()` normalisation in `load_data`/`load_pivots` and the hardcoded constants in `METHOD_COLS`. There is no schema definition, no validation, no test. Any future change to a column name in one file will silently produce NaN in the other.

---

#### BUG-X2 — Pivot CSV Date Format Mismatch

`compute_pivot_points` writes dates as `DD-MM-YYYY`:
```python
pl.col("DATE").dt.strftime("%d-%m-%Y").alias("DATE")
```
`load_pivots` tries `%Y-%m-%d` first, then `%d-%m-%Y`. This works but only because the fallback catches it. If `load_pivots` ever changes format order, pivot date parsing silently fails (see BUG-A9).

---

## 5. Improvements

### 5.1 Reliability & Robustness

**I-R1 — Add Session Cookie Priming**

Before the download loop, make a GET request to `https://www.nseindia.com/` to prime the session cookie. NSE's CDN returns 403 without a valid `nsit` cookie. Re-prime every N requests (e.g. every 50 dates) or on first 403.

**I-R2 — Retry with Exponential Backoff**

Wrap the `SESSION.get` call in a retry loop (3 attempts, 2s/4s/8s backoff) for transient errors. Use `urllib3.util.retry.Retry` or a manual loop. Only skip on persistent 403.

**I-R3 — Atomic CSV Write**

Write the consolidated master CSV to a `.tmp` file first, then rename to the final path. This prevents a partial/corrupt CSV if the process is interrupted.

**I-R4 — Per-Year Temp Directory**

Use `NSE_EOD_DIR/<year>/` as the temp extraction folder instead of a shared `NSE_EOD_DIR`. This completely eliminates the cross-year file contamination risk (BUG-E10).

**I-R5 — Holiday-Aware Auto-Update**

In `check_auto_update_needed`, before declaring an update is needed, also check that yesterday was an actual NSE trading day by consulting the `CUE_DATE_<year>.csv` calendar file.

**I-R6 — Validate CATEGORY Length Before Assignment**

In `process_file`, assert `len(category) == len(df_final)` after building the category list. Raise a descriptive `ValueError` if they don't match, rather than allowing a silent broadcast or crash.

**I-R7 — Cache Invalidation on Download**

After a successful download, call `st.cache_data.clear()` before `st.rerun()` so that the newly downloaded file is actually loaded fresh.

---

### 5.2 Performance

**I-P1 — Lazy Loading for Large Years**

Currently the entire year's CSV (potentially millions of rows for 250 trading days × all NSE securities) is loaded into memory on every `selected_year` change. Consider reading only the requested symbol(s) using `pd.read_csv(..., chunksize=...)` or pre-indexing by symbol.

**I-P2 — Persist Pivot Dates as Python Dates in Cache**

`load_pivots` parses dates on every cache miss. Since pivots for a year don't change once computed, caching the parsed DataFrame is correct — but the cache key should include a hash of the file's modification time to detect re-downloads.

**I-P3 — Use Polars Throughout**

`process_file` uses pandas. Switching the entire processing pipeline to Polars (already used in `compute_pivot_points`) would give significant speed improvements for large files.

**I-P4 — Parallel Downloads**

Use `concurrent.futures.ThreadPoolExecutor` to download multiple dates in parallel (e.g. 4 workers). NSE's server generally tolerates moderate parallelism. This could reduce a full-year download from ~15 minutes to ~4 minutes.

---

### 5.3 Data Correctness

**I-D1 — Validate Date From Filename**

After extracting day, month, year from the filename, validate: `1 ≤ day ≤ 31`, `1 ≤ month ≤ 12`. If invalid, log a warning and skip the file rather than storing corrupt dates.

**I-D2 — Store DATE as True Date Type in EOD CSV**

Currently the EOD CSV stores dates as `YYYY-MM-DD` strings. Consider storing as ISO date strings consistently (already done) but ensure the pivot CSV also uses `YYYY-MM-DD` rather than `DD-MM-YYYY` to avoid the format mismatch.

**I-D3 — Camarilla PP Display**

Since Camarilla doesn't have a traditional pivot point, rename the displayed value in the pivot table to `Prev Close` or `C` rather than `PP` to avoid misleading users.

**I-D4 — Correct Bollinger Band Fill**

Fix the `tonexty` fill to properly target the upper band trace using `fill="tonexty"` with the correct trace ordering, or switch to using `fillbetween` with explicit trace references.

---

### 5.4 Code Quality & Maintainability

**I-C1 — Define a Column Name Schema**

Create a single `COLUMNS` dataclass or `TypedDict` in `EoD_module.py` that is imported by `app_v2.py`. Both files should reference `COLUMNS.HIGH_PRICE` etc. rather than hardcoded strings in two places.

**I-C2 — Type Annotations Throughout**

`process_file` returns `pd.DataFrame` but has no type annotations. `compute_pivot_points` takes `year: int` but progress_callback has no annotation. Add full type hints.

**I-C3 — Separate `app_v2.py` Into Modules**

At ~1,200 lines, `app_v2.py` is monolithic. Split into:
- `ui_sidebar.py` — sidebar controls
- `ui_tab_ohlcv.py` — Tab 1 rendering
- `ui_tab_pivots.py` — Tab 2 rendering
- `ui_components.py` — reusable HTML/Plotly builders

**I-C4 — Replace Raw HTML CSS Components With `st.metric` Where Possible**

KPI cards can largely be replaced with `st.metric` (which Streamlit renders well) reducing the raw HTML surface area and XSS risk from `unsafe_allow_html`.

**I-C5 — Add Unit Tests for Core Computations**

`process_file`, `compute_pivot_points`, and `check_auto_update_needed` are pure functions with deterministic behaviour. Add `pytest` tests with sample data to guard against regressions.

---

## 6. Proposed New Features

**F1 — RSI / MACD Technical Indicators**

Extend the OHLCV chart overlays to include RSI (14-period) and MACD (12/26/9). Both can be computed from the close price series already in memory using `pandas-ta` or pure pandas rolling windows.

**F2 — Symbol Search / Autocomplete**

Replace the multiselect symbol picker with a searchable text input using `st.selectbox` with a filterable list, making it faster to find specific symbols across thousands of entries.

**F3 — Watchlist / Favourites**

Allow users to save a named watchlist of symbols to `st.session_state` (persisted to a JSON file in `DATA_DIR`). The watchlist becomes a quick-select option in the symbol filter.

**F4 — Pivot Breach Alerts**

After loading the latest pivot data, scan all symbols and display a table of symbols where today's price is within a configurable percentage (e.g. 0.5%) of any pivot level. This gives a "levels to watch" view without manual scanning.

**F5 — Multi-Year Comparison**

Allow loading two years simultaneously to compare a symbol's price action across years (normalised to percentage change from year-start). Requires merging two `EOD_DATA_FOR_ANALYSIS_*.csv` files.

**F6 — Data Export**

Add a "Download filtered data as CSV/Excel" button using `st.download_button` on both the OHLCV and pivot tables. Currently data is view-only.

**F7 — Incremental/Append Download**

Modify `download_year_data` to support an incremental mode: read the last date in the existing master CSV and download only from that date onwards, then append to the existing file. This avoids re-downloading an entire year when only a few new dates are needed.

**F8 — Dark/Light Theme Toggle**

The CSS is hardcoded for a dark theme. Add a toggle that switches to a light variant by swapping CSS variables.

**F9 — Volume Profile / VWAP**

Add Volume Profile (price level vs cumulative volume) as a horizontal histogram overlay on the candlestick chart, and VWAP as a line overlay.

**F10 — Deployment-Ready Settings Page**

Add a dedicated Settings tab with configurable options: default date range, default symbols, NSE request delay (ms), log level. Persist to a `settings.json` in `DATA_DIR`.

---

## 7. Data Flow Diagram (Text)

```
USER CLICKS "Start Download" FOR YEAR Y
│
├─► get_nse_trading_days(Y)
│   └─► pandas_market_calendars → list of DD-MM-YYYY dates
│   └─► save to CUE_DATE_Y.csv
│
├─► for each Tdate in CUE_DATE_Y.csv:
│   └─► process_date(Tdate)
│       ├─► BUILD URL: archives.nseindia.com/.../PRDDMMYY.zip
│       ├─► SESSION.get(url) → bytes
│       ├─► write to NSE_EOD_DIR/pd_<PID>.zip
│       ├─► ZipFile.extract Pd<DDMMYY>.csv → NSE_EOD_DIR/
│       └─► delete pd_<PID>.zip
│
├─► Consolidate:
│   for each Pd*.csv in NSE_EOD_DIR/:
│   └─► process_file(filepath)
│       ├─► pd.read_csv → DataFrame
│       ├─► Clean whitespace/nulls
│       ├─► Reconstruct CATEGORY from NSE heading structure
│       ├─► Fill SYMBOL from SECURITY
│       ├─► Parse DATE from filename (DDMMYY → YYYY-MM-DD)
│       └─► return clean DataFrame
│   └─► append to EOD_DATA_FOR_ANALYSIS_Y.csv (single header)
│
├─► Delete all Pd*.csv from NSE_EOD_DIR/
│
└─► compute_pivot_points(Y)
    ├─► pl.read_csv EOD_DATA_FOR_ANALYSIS_Y.csv
    ├─► Strip commas, cast to Float64 for price cols
    ├─► Sort by [SYMBOL, CATEGORY, DATE]
    ├─► shift(1).over([SYMBOL, CATEGORY]) → prev H, L, C
    ├─► drop_nulls on H, L, C
    ├─► Compute: P_classic, RANGE
    ├─► Compute: Classic R1/R2/R3, S1/S2/S3
    ├─► Compute: Fibonacci R1/R2/R3, S1/S2/S3
    ├─► Compute: P_woodie, Woodie R1/R2, S1/S2
    ├─► Compute: Camarilla R1/R2/R3/R4, S1/S2/S3/S4
    ├─► Format DATE → DD-MM-YYYY
    └─► write pivots_outputY.csv

USER SELECTS YEAR → FILTERS → TAB 1
│
├─► load_data(EOD_DATA_FOR_ANALYSIS_Y.csv)  [cached]
│   ├─► pd.read_csv
│   ├─► .upper() column names
│   ├─► parse DATE (try 3 formats)
│   └─► coerce numeric columns
│
├─► Filter by category, symbol, date range → df_filtered
├─► Render KPI Cards (latest row HTML)
├─► Render 52-Week Range bar (HTML gradient)
└─► Render Plotly OHLCV chart + overlays

USER SELECTS TAB 2
│
├─► load_pivots(pivots_outputY.csv)  [cached]
├─► Select methods, categories, symbols, date
├─► Render pivot table (HTML grid per symbol)
│   ├─► Respect custom overrides
│   └─► Apply configurable R/S level selections
└─► Render Plotly price chart with pivot level lines
    └─► Pivot lines drawn at LATEST pivot values (BUG-A1)
```

---

*End of Document*

> **Bullseye Fintech © 2024–2026**  
> Document prepared for internal development review.
