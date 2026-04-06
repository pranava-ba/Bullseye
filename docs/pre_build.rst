================================================================================
BULLSEYE FINTECH — NSE End-of-Day Dashboard
================================================================================

Software Requirements Specification
====================================

:Version: 2.0.6
:Date: April 2026
:Document: SRS

.. contents:: Table of Contents
   :depth: 2
   :backlinks: entry

----


1. Project Overview
===================

1.1 What is this Software?
--------------------------

Bullseye Fintech NSE EOD Dashboard (``app_v2.py``) is a Windows desktop
application built on Streamlit. It downloads open-source end-of-day (EOD)
equity bhavcopy data published by the National Stock Exchange of India, stores
it as CSV files locally, and provides an interactive UI for viewing OHLCV price
history with technical chart overlays and calculated pivot point levels across
four methods.

1.2 What is the use of this software?
--------------------------------------

NSE publishes daily bhavcopy ZIP files on its website, but accessing them
reliably is non-trivial — the server requires session cookies, blocks
unauthenticated requests, returns malformed responses on some dates, and uses
an inconsistent file naming format. On top of that, the raw files have a nested
structure where category headings are mixed in with actual data rows, making
them difficult to parse directly. This module exists to hide all of that
complexity behind a clean, reliable API so the dashboard never has to think
about it.

1.3 Technology Stack
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Component
     - Technology / Detail
   * - **Frontend / UI**
     - Streamlit (Python) — wide layout, custom light-pastel CSS theme
   * - **Fonts**
     - Sora (UI / headings), JetBrains Mono (numeric / data)
   * - **Data Processing**
     - Polars (consolidation, pivot computation, filtering); Pandas (NSE file
       parsing only)
   * - **Charting**
     - Plotly (Candlestick, OHLC Bar, Line, MA, Bollinger Bands, pivot overlays)
   * - **Data Source**
     - NSE India public bhav-copy archives — https://archives.nseindia.com
   * - **Local Storage**
     - CSV files (not Parquet): ``EOD_DATA_FOR_ANALYSIS_{year}.csv``,
       ``pivots_output{year}.csv``
   * - **HTTP Client**
     - ``requests.Session`` with NSE homepage cookie priming and exponential back-off
   * - **Trading Calendar**
     - ``pandas_market_calendars`` (NSE calendar) — holiday-aware
   * - **Packaging**
     - PyInstaller (frozen bundle) + Inno Setup (Windows installer)
   * - **Target OS**
     - Windows 10 / 11 (64-bit)


----


2. Scope and Functionality
==========================

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Feature Area
     - Description
   * - **Download Modes**
     - Single Year, Multiple Years, Date Range, and All Downloaded
       (re-process existing). Supports incremental (append only) and
       force-redownload modes.
   * - **Local Storage**
     - Persistent local CSV storage of parsed OHLCV data keyed by year.
   * - **OHLCV Summary Tab**
     - KPI cards, 52-week range bar, interactive candlestick / OHLC / line
       chart with Volume, MA 20, MA 50, Bollinger Band overlays, and raw
       data table.
   * - **Pivot Points Tab**
     - Classic, Fibonacci, Woodie, Camarilla pivot computation; editable
       Fibonacci multipliers and Camarilla k constant; pivot-overlay price
       chart.
   * - **Global Filter Bar**
     - Category, Symbol (multiselect), date-range pickers, and quick-range
       presets.
   * - **CSV Export**
     - Export buttons for EOD data and pivot points (per year).
   * - **Year Management**
     - Year delete functionality.
   * - **Auto-Update Toggle**
     - Off by default; fetches previous trading day's data on launch when
       enabled.
   * - **Distribution**
     - Light-themed UI (Sora + JetBrains Mono fonts) as a single Windows
       installer.

2.1 What the System Will Do
----------------------------

- Connect to NSE's public archive servers and download EOD bhavcopy data for
  any trading day between 2000 and the current year.
- Handle session management, retries, and parallel downloads automatically.
- Parse and clean the raw NSE file format, including reconstructing stock
  categories from the nested heading structure.
- Consolidate everything into a single master CSV per year.
- Compute four sets of pivot point levels (Classic, Fibonacci, Woodie,
  Camarilla) from the consolidated data and write them to a separate pivot CSV.
- Support incremental updates so only missing dates are fetched on subsequent
  runs.
- Expose all of this to the Streamlit dashboard through a clean function-level
  API, including in-memory CSV bytes for direct download buttons.

2.2 What the System Will Not Do
--------------------------------

- Provide real-time or intraday price data — the smallest unit of data is one
  full trading day.
- Support exchanges other than NSE.
- Store data in a database — all persistence is flat CSV files.
- Perform any trading, order placement, or brokerage integration of any kind.
- Send alerts or notifications.
- Compute any technical indicators beyond the four supported pivot point methods.
- Validate whether the downloaded data is financially accurate — it trusts
  NSE's published figures.
- Operate if NSE changes its archive URL structure or file format, as no
  fallback source is implemented.


----


3. Roles
========

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Actor
     - Description & Capabilities
   * - **Admin — Developer**
     - Deploys and maintains the application. Interacts directly with both
       ``app_v2.py`` and ``EoD_module.py``, manages the data directory, and
       handles updates.
   * - **End User (Trader / Analyst)**
     - Sole human user. No login required. Installs the app, selects download
       options, reads OHLCV charts and pivot outputs. Cannot change or modify
       the app in any manner.
   * - **NSE Archives Server**
     - External HTTPS endpoint. Read-only source of bhav-copy ZIPs at
       ``archives.nseindia.com/archives/equities/bhavcopy/pr/``. Requires
       session-cookie priming via GET ``nseindia.com``.
   * - **NSE Homepage**
     - ``GET https://www.nseindia.com`` — visited to acquire valid session
       cookies before bulk downloads.
   * - **Local File System**
     - Stores CSVs and temp files. Frozen mode:
       ``%APPDATA%\BullseyeFintech\NSE_Dashboard\data\``. Dev mode:
       ``./data/`` alongside the script.


----


4. Functional Requirements
==========================

4.1 Download Module (``EoD_module.py`` — ``download_year_data``)
-----------------------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **FR-DL-01**
     - The system shall download NSE bhav-copy ZIPs over HTTPS from
       ``https://archives.nseindia.com/archives/equities/bhavcopy/pr/PR{DDMMYY}.zip``.
   * - **FR-DL-02**
     - The system shall support four download modes: (a) Single Year,
       (b) Multiple Years, (c) Date Range, (d) All Downloaded — reprocess all
       years already on disk.
   * - **FR-DL-03**
     - The system shall prime the NSE HTTP session by GET-ing the NSE homepage
       before bulk downloads, and re-prime every 300 seconds during long
       operations.
   * - **FR-DL-04**
     - On HTTP 403, the system shall immediately re-prime the session and retry
       the request once before counting it as a failed attempt.
   * - **FR-DL-05**
     - The system shall implement exponential back-off retry: up to 3 attempts
       with delays of 2 s, 4 s, 8 s between attempts (configurable via
       ``_MAX_RETRIES`` / ``_RETRY_DELAYS``).
   * - **FR-DL-06**
     - The system shall skip HTTP 404 responses immediately without retrying
       (missing file = no data for that date).
   * - **FR-DL-07**
     - The system shall skip future dates before attempting any download to
       prevent 404 loops (BUG-E13).
   * - **FR-DL-08**
     - The system shall execute downloads in parallel using
       ``ThreadPoolExecutor`` with a default of 4 worker threads
       (``max_workers`` configurable).
   * - **FR-DL-09**
     - When extracting the CSV from a ZIP, the system shall match both 4-digit
       year filenames (``pd31122025.csv``) AND 2-digit year filenames
       (``pd311225.csv``) using case-insensitive matching.
   * - **FR-DL-10**
     - The system shall use per-year temporary directories
       (``data/nse_eod_data_files/{year}/``) for extraction, preventing
       cross-year file contamination (BUG-E10).
   * - **FR-DL-11**
     - The system shall write the final master CSV atomically: write to
       ``{path}.tmp`` then ``os.replace()`` to the target path (BUG-E9).
   * - **FR-DL-12**
     - In incremental mode, the system shall read existing DATE values from the
       master CSV and only download dates absent from that set, then append and
       deduplicate on ``(DATE, SYMBOL, CATEGORY)``.
   * - **FR-DL-13**
     - The system shall clean up per-year temp files after successful
       consolidation.
   * - **FR-DL-14**
     - The system shall accept an optional ``progress_callback(str)`` called
       per trading date, used by the Streamlit sidebar to update the progress
       bar in real time.

4.2 File Processing (``process_file`` / ``_parse_date_from_filename``)
----------------------------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **FR-FP-01**
     - The system shall parse the NSE PD CSV format, reconstructing the
       CATEGORY column from section heading rows (NIFTY INDEX, EQ, BE, BL,
       etc.).
   * - **FR-FP-02**
     - The system shall validate CATEGORY length against the number of data
       rows and raise a descriptive ``ValueError`` on mismatch (BUG-E3).
   * - **FR-FP-03**
     - The system shall extract the trading date from the filename supporting
       both DDMMYYYY (8-digit) and DDMMYY (6-digit) patterns, and validate
       that day ∈ [1, 31] and month ∈ [1, 12] (BUG-E1).
   * - **FR-FP-04**
     - The system shall fall back to SECURITY when the SYMBOL column is absent
       or null.
   * - **FR-FP-05**
     - The system shall output dates in YYYY-MM-DD format in all CSVs (I-D2).

4.3 Trading Calendar (``get_nse_trading_days`` / ``_load_trading_days``)
------------------------------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **FR-CAL-01**
     - The system shall use ``pandas_market_calendars`` (NSE calendar) to
       enumerate trading days per year, caching results to
       ``CUE_DATE_{year}.csv``.
   * - **FR-CAL-02**
     - The system shall raise a ``RuntimeError`` with a helpful message if the
       calendar cannot be fetched (BUG-E12).
   * - **FR-CAL-03**
     - Auto-update shall consult CUE_DATE CSV to distinguish trading days from
       NSE holidays; weekends are skipped early without a calendar lookup
       (BUG-E8).

4.4 Pivot Point Computation (``compute_pivot_points``)
------------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **FR-PP-01**
     - Pivot inputs shall be the previous session's High (H), Low (L), Close
       (C) via ``Polars shift(1).over([SYMBOL, CATEGORY])``.
   * - **FR-PP-02**
     - Classic: PP = (H + L + C) / 3; R1 = 2PP − L; S1 = 2PP − H; R2 = PP +
       Range; S2 = PP − Range; R3 = H + 2(PP − L); S3 = L − 2(H − PP).
   * - **FR-PP-03**
     - Fibonacci: PP = Classic PP; R/Sn = PP ± ratio_n × Range. Default
       ratios: 0.382 (R1/S1), 0.618 (R2/S2), 1.000 (R3/S3). Ratios are
       editable at runtime in the UI.
   * - **FR-PP-04**
     - Woodie: PP = (H + L + 2C) / 4; R1 = 2PP − L; S1 = 2PP − H; R2 = PP +
       Range; S2 = PP − Range. (2 R/S levels only.)
   * - **FR-PP-05**
     - Camarilla: anchor = previous-day Close (P_CAM = C, NOT a classic PP
       average — BUG-E6 fix). R/Sn = C ± Range × k / divisor_n. Default
       k = 1.1, divisors = 12, 6, 4, 2 for levels 1–4. k is editable at
       runtime.
   * - **FR-PP-06**
     - Pivot output shall be written atomically to ``pivots_output{year}.csv``
       with columns ordered as: DATE, CATEGORY, SYMBOL, then all pivot columns
       per ``Col.PIVOT_FINAL_COLS``.
   * - **FR-PP-07**
     - Pivot computation shall trigger automatically after each successful year
       download.

4.5 Sidebar — Download & Management Panel
-----------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **FR-SB-01**
     - The sidebar shall display the Bullseye Fintech branding header and an
       'NSE EOD Dashboard' subtitle.
   * - **FR-SB-02**
     - The sidebar shall display a list of available on-disk years as clickable
       buttons; clicking a year loads it into the main view.
   * - **FR-SB-03**
     - The sidebar shall provide an auto-update toggle checkbox (default: OFF
       per ``AUTO_UPDATE_DEFAULT = False``).
   * - **FR-SB-04**
     - The sidebar shall show Download buttons for EOD CSV and Pivot CSV for
       the currently loaded year.
   * - **FR-SB-05**
     - The sidebar shall contain a download mode selectbox: Single Year,
       Multiple Years, Date Range, All Downloaded.
   * - **FR-SB-06**
     - In Date Range mode, the sidebar shall validate that From ≤ To and warn
       when the current year is selected (no future dates).
   * - **FR-SB-07**
     - The sidebar shall show Force Re-download and Incremental checkboxes for
       download control.
   * - **FR-SB-08**
     - During download, the sidebar shall render an animated progress bar (%
       complete, year label, ok/fail counts) updated at ~4 fps from a
       background thread.
   * - **FR-SB-09**
     - After download, the sidebar shall persist a colour-coded log card (✅ ok
       / ❌ err / ⚠ warn entries) that survives Streamlit reruns until the user
       clears it.
   * - **FR-SB-10**
     - The sidebar shall contain a Delete Data section allowing the user to
       delete all files for a selected year (EOD CSV, Pivot CSV, CUE_DATE CSV,
       and temp PD files — BUG-E11).
   * - **FR-SB-11**
     - The sidebar footer shall display the DATA_DIR path in small monospaced
       text.

4.6 Global Filter Bar (Main Screen)
------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **FR-GF-01**
     - The main screen shall display a persistent global filter bar with five
       controls: Category (multiselect), Symbol (multiselect), From date, To
       date, and Quick range preset.
   * - **FR-GF-02**
     - Category filter shall default to the first available category and drive
       the symbol pool (symbols shown are filtered by selected categories).
   * - **FR-GF-03**
     - Symbol filter shall use ``_safe_default`` to avoid selecting symbols not
       in the filtered pool, preventing Streamlit multiselect errors on data
       reload.
   * - **FR-GF-04**
     - Quick range presets shall be: Custom, Last 30 days, Last 90 days, Last
       6 months, YTD, Full year. Selecting a preset overrides the From/To date
       pickers.
   * - **FR-GF-05**
     - If From > To the system shall swap the dates and show an error banner.
   * - **FR-GF-06**
     - Date pickers shall use DD/MM/YYYY format and accept dates from
       2000-01-01 to today.

4.7 Tab 1 — OHLCV Summary
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **FR-T1-01**
     - When multiple symbols are selected globally, Tab 1 shall show a 'Detail
       view' selectbox to choose which symbol drives the chart and KPI cards.
   * - **FR-T1-02**
     - KPI cards (toggleable) shall show Open, High, Low, Close (with change Δ
       and Δ%), Prev Close, and Volume for the latest session in the filtered
       date range.
   * - **FR-T1-03**
     - A 52-week range bar (toggleable) shall show a gradient bar, a circle
       marker at the current close position, and the 52-week High / Low labels
       below.
   * - **FR-T1-04**
     - The chart section shall offer three chart types: Candlestick, Line
       (Close), OHLC Bar.
   * - **FR-T1-05**
     - Candlestick and OHLC charts shall use green (#a5d6a7 fill / #2e7d32
       line) for up candles and red (#ef9a9a fill / #c62828 line) for down
       candles.
   * - **FR-T1-06**
     - The chart shall support four toggleable overlays: Volume (coloured bar
       subplot), 20-Day MA, 50-Day MA, and Bollinger Bands (20-period, ±2σ).
   * - **FR-T1-07**
     - Volume bars shall be coloured green when Close ≥ Prev Close, red
       otherwise.
   * - **FR-T1-08**
     - The system shall display a warning banner listing any overlays that
       cannot be shown due to insufficient data (e.g. MA-20 needs ≥ 20
       sessions).
   * - **FR-T1-09**
     - A 'Show raw data table' checkbox shall reveal a sortable Streamlit
       dataframe with columns: DATE, OPEN_PRICE, HIGH_PRICE, LOW_PRICE,
       CLOSE_PRICE, PREV_CL_PR, NET_TRDQTY, NET_TRDVAL.

4.8 Tab 2 — Pivot Points
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **FR-T2-01**
     - Tab 2 shall allow the user to select 1–4 pivot methods simultaneously
       from: Classic, Fibonacci, Woodie, Camarilla.
   * - **FR-T2-02**
     - Tab 2 shall allow the user to select the number of R/S levels to
       display: 1, 2, 3, or 4 (Woodie max = 2, Classic/Fibonacci max = 3,
       Camarilla max = 4).
   * - **FR-T2-03**
     - Tab 2 shall allow the user to select a session date from all available
       dates for the selected symbols.
   * - **FR-T2-04**
     - An 'Edit Pivot Values' toggle button shall reveal the parameter editor
       panel; closing it shall hide the panel without a page reload.
   * - **FR-T2-05**
     - In the editor, Fibonacci multipliers f1, f2, f3 shall be editable text
       inputs (default: 0.382, 0.618, 1.000). Changing any value shall
       immediately recompute all Fibonacci levels.
   * - **FR-T2-06**
     - In the editor, the Camarilla k constant shall be an editable text input
       (default: 1.1). Changing it shall immediately recompute all Camarilla
       levels.
   * - **FR-T2-07**
     - Classic and Woodie levels shall be displayed read-only in the editor
       (computed from stored pivot CSV values).
   * - **FR-T2-08**
     - The consolidated pivot matrix table shall show rows R3→R1, PP, S1→S3
       with methods as column groups and symbols as sub-columns, using
       colour-coded row backgrounds: red (#fff0f0) for resistance, amber
       (#fffde7) for PP, green (#f0faf0) for support.
   * - **FR-T2-09**
     - A 'Overlay pivot levels on price chart' checkbox shall render a Plotly
       line chart showing the closing price and all selected pivot levels as
       horizontal dashed/dotted lines, colour-coded by method.
   * - **FR-T2-10**
     - A 'Show full pivot data table' checkbox shall reveal a sortable
       dataframe of all pivot rows for the selected symbols and date range.
   * - **FR-T2-11**
     - Fibonacci and Camarilla levels shown in the chart and matrix shall use
       the live-recomputed values from the text-input parameters, not the
       stored CSV values.
   * - **FR-T2-12**
     - Tab 2 shall use a JavaScript keyboard handler to block BaseWeb's global
       arrow-key interception on text inputs and number inputs, preventing
       unintended selectbox navigation.


----


5. Non-Functional Requirements
===============================

5.1 Performance
---------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **NFR-P-01**
     - The OHLCV data table shall load for a single year (≈ 250 days × ~2,000
       symbols) within 5 seconds on reference hardware.
   * - **NFR-P-02**
     - Pivot calculations for a full year via Polars shall complete within 10
       seconds.
   * - **NFR-P-03**
     - The download progress bar shall refresh at ~4 fps (``time.sleep(0.25)``
       in the animation loop) without blocking Streamlit's main thread.

5.2 Reliability
---------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **NFR-R-01**
     - Atomic CSV writes (tmp → ``os.replace``) shall ensure no corrupt master
       files are left on unexpected termination.
   * - **NFR-R-02**
     - The system shall not crash on bad ZIPs, malformed filenames, or CATEGORY
       length mismatches — each file is logged and skipped individually.
   * - **NFR-R-03**
     - A ``bullseye.log`` file shall be written to
       ``%APPDATA%\BullseyeFintech\NSE_Dashboard\`` (frozen) or script
       directory (dev mode) for post-hoc debugging.

5.3 Usability
-------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **NFR-U-01**
     - The UI shall implement a complete light/pastel CSS theme (background:
       #f4f5f9, accent: #3949ab) covering Streamlit BaseWeb internals including
       popovers, menus, calendar pickers, toggle switches, and notification
       banners so that no dark-mode artefacts leak through.
   * - **NFR-U-02**
     - Plotly charts shall use a white paper background (#ffffff), near-white
       plot area (#fafbff), and light-blue grid lines (#c5cae9) consistent with
       the app theme.
   * - **NFR-U-03**
     - All numeric data (KPI values, pivot levels) shall be formatted with
       JetBrains Mono font.

5.4 Distribution / Packaging
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **NFR-D-01**
     - The application shall be distributed as a Windows installer built with
       Inno Setup wrapping a PyInstaller-frozen bundle.
   * - **NFR-D-02**
     - The frozen launcher shall guard against self-spawning by using
       ``multiprocessing.freeze_support()`` and setting the start method to
       'spawn' with an ``if __name__ == '__main__'`` guard.
   * - **NFR-D-03**
     - All internal resource paths shall use ``sys._MEIPASS`` (PyInstaller
       bundle root) rather than ``__file__``-relative paths.
   * - **NFR-D-04**
     - Data and log files shall be stored in
       ``%APPDATA%\BullseyeFintech\NSE_Dashboard\`` so the install directory
       does not require write access.

5.5 Maintainability
-------------------

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Req ID
     - Requirement
   * - **NFR-M-01**
     - All column name literals shall be defined exclusively in the ``Col``
       dataclass (``EoD_module.py``) and imported by ``app_v2.py`` — no raw
       strings elsewhere.
   * - **NFR-M-02**
     - Pivot formula parameters (Fibonacci ratios, Camarilla k and divisors)
       shall be passed as arguments to recompute helpers, not hard-coded in
       computation functions.
   * - **NFR-M-03**
     - The ``AUTO_UPDATE_DEFAULT`` constant shall control the initial state of
       the auto-update toggle and shall remain ``False`` unless explicitly
       changed.


----


6. Data Requirements
====================

6.1 Input — NSE Bhav-copy CSV (inside ZIP)
-------------------------------------------

URL pattern::

  https://archives.nseindia.com/archives/equities/bhavcopy/pr/PR{DDMMYY}.zip

Filename inside ZIP: ``pd{DDMMYYYY}.csv`` (4-digit year, recent) or
``pd{DDMMYY}.csv`` (2-digit year, older).

.. list-table::
   :header-rows: 1
   :widths: 20 12 68

   * - NSE Field
     - Type
     - Notes
   * - **SECURITY**
     - String
     - Company / index name. Used as SYMBOL fallback if SYMBOL is absent.
   * - **SYMBOL**
     - String
     - NSE ticker.
   * - **MKT**
     - String
     - Null on category-heading rows; non-null on data rows.
   * - **OPEN_PRICE**
     - Float
     - Session open.
   * - **HIGH_PRICE**
     - Float
     - Session high. ``Col.HIGH``
   * - **LOW_PRICE**
     - Float
     - Session low. ``Col.LOW``
   * - **CLOSE_PRICE**
     - Float
     - Official closing price. ``Col.CLOSE``
   * - **PREV_CL_PR**
     - Float
     - Previous close. ``Col.PREV_CLOSE``
   * - **NET_TRDVAL**
     - Float
     - Total traded value. ``Col.NET_TRDVAL``
   * - **NET_TRDQTY**
     - Integer
     - Total traded quantity (volume). ``Col.NET_TRDQTY``
   * - **HI_52_WK**
     - Float
     - 52-week high. ``Col.HI_52``
   * - **LO_52_WK**
     - Float
     - 52-week low. ``Col.LO_52``

6.2 EOD Master CSV (``EOD_DATA_FOR_ANALYSIS_{year}.csv``)
----------------------------------------------------------

Columns written: all NSE fields above, plus DATE (YYYY-MM-DD) and CATEGORY
(derived from section headings). Dropped columns: MKT, SERIES, IND_SEC,
CORP_IND.

6.3 Pivot Output CSV (``pivots_output{year}.csv``)
---------------------------------------------------

Columns (in order per ``Col.PIVOT_FINAL_COLS``): DATE, CATEGORY, SYMBOL,
P_CLASSIC, CL_R1, CL_R2, CL_R3, CL_S1, CL_S2, CL_S3, FIB_R1, FIB_R2,
FIB_R3, FIB_S1, FIB_S2, FIB_S3, P_WOODIE, WD_R1, WD_R2, WD_S1, WD_S2,
P_CAM, CAM_R1, CAM_R2, CAM_R3, CAM_R4, CAM_S1, CAM_S2, CAM_S3, CAM_S4.

.. note::

   P_CAM = previous-day Close (the true Camarilla anchor — NOT a pivot
   average). This is intentional per the BUG-E6 fix.

6.4 Trading Calendar CSV (``CUE_DATE_{year}.csv``)
---------------------------------------------------

Single column 'details' containing trading dates as DD-MM-YYYY strings. Used
by auto-update to distinguish NSE holidays from missing data.

6.5 Local Directory Layout
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Path
     - Description
   * - ``data/``
     - Master CSVs (EOD + pivots + calendar)
   * - ``data/nse_eod_data_files/{year}/``
     - Per-year temp extraction folder for PD CSVs
   * - ``data/EOD_DATA_FOR_ANALYSIS_{year}.csv``
     - Annual EOD master data file
   * - ``data/pivots_output{year}.csv``
     - Annual pivot point output file
   * - ``data/CUE_DATE_{year}.csv``
     - NSE trading calendar cache
   * - ``%APPDATA%\BullseyeFintech\NSE_Dashboard\bullseye.log``
     - Application log file (frozen mode only)


----


7. Use Cases
============

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Use Case
     - Title
   * - UC-01
     - Download Data for a Year
   * - UC-02
     - View OHLCV Summary (Tab 1)
   * - UC-03
     - View and Edit Pivot Points (Tab 2)

UC-01: Download Data for a Year
--------------------------------

1. User opens the sidebar and selects 'Single Year' mode, picks a year.
2. User toggles Incremental if desired. Clicks 'Start Download'.
3. System fetches trading calendar (or loads from CUE_DATE CSV).
4. System filters out future dates and already-downloaded dates (incremental
   mode).
5. System primes NSE session, then dispatches up to 4 parallel download
   workers.
6. Sidebar progress bar animates; status widgets log each date outcome.
7. System consolidates extracted PD CSVs into master EOD CSV (atomic write).
8. System runs ``compute_pivot_points`` and writes the pivot CSV.
9. ``st.cache_data.clear()`` is called; the app reruns and loads the new data.

UC-02: View OHLCV Summary (Tab 1)
-----------------------------------

1. User clicks 'OHLCV Summary' tab.
2. User sets Category and Symbol in the global filter bar; optionally picks a
   date range or quick preset.
3. KPI cards show the latest session's OHLCV values.
4. 52-week range bar shows where the close sits within the annual range.
5. User selects chart type (Candlestick, Line, OHLC) and overlays (Volume,
   MA 20/50, BB).
6. System renders the Plotly chart; insufficient-data warnings appear if needed.

UC-03: View and Edit Pivot Points (Tab 2)
------------------------------------------

1. User clicks 'Pivot Points' tab.
2. User selects pivot methods (e.g. Classic + Camarilla), number of R/S levels,
   and session date.
3. The pivot matrix table renders with colour-coded resistance / PP / support
   rows.
4. Optionally, user clicks 'Edit Pivot Values' to open the parameter editor.
5. User changes Fibonacci f2 from 0.618 to 0.5; the matrix and chart instantly
   update.
6. User toggles 'Overlay pivot levels on price chart' to view levels over the
   price history.


----


8. Mathematical Reference
=========================

**Inputs for all methods:** H = previous session High, L = previous session
Low, C = previous session Close, Range = H − L.

.. list-table::
   :header-rows: 1
   :widths: 16 28 56

   * - Method
     - Pivot (PP) Formula
     - Level Formulas
   * - **Classic**
     - (H + L + C) / 3
     - R1=2PP−L, R2=PP+Range, R3=H+2(PP−L) | S1=2PP−H, S2=PP−Range,
       S3=L−2(H−PP)
   * - **Fibonacci**
     - Same as Classic PP
     - Rn = PP + fn × Range, Sn = PP − fn × Range | Default fn: f1=0.382,
       f2=0.618, f3=1.000 (fn editable in UI)
   * - **Woodie**
     - (H + L + 2C) / 4
     - R1=2PP−L, R2=PP+Range | S1=2PP−H, S2=PP−Range (2 levels only)
   * - **Camarilla**
     - P_CAM = C (prev close; NOT a pivot avg — BUG-E6)
     - Rn = C + Range × k / dn | Sn = C − Range × k / dn | Default k=1.1,
       d1=12, d2=6, d3=4, d4=2 (k editable in UI; 4 levels R1–R4 / S1–S4)


----


9. Key Column Name Constants (``Col`` Dataclass)
=================================================

All column names are centralised in the ``Col`` class in ``EoD_module.py``.
``app_v2.py`` imports and uses only these constants.

.. list-table::
   :header-rows: 1
   :widths: 25 22 53

   * - Constant
     - CSV Column Name
     - Description
   * - ``Col.SYMBOL``
     - SYMBOL
     - NSE ticker
   * - ``Col.CATEGORY``
     - CATEGORY
     - Market segment (NIFTY INDEX, EQ, BE …)
   * - ``Col.DATE``
     - DATE
     - Trading date YYYY-MM-DD
   * - ``Col.OPEN``
     - OPEN_PRICE
     - Opening price
   * - ``Col.HIGH``
     - HIGH_PRICE
     - Session high
   * - ``Col.LOW``
     - LOW_PRICE
     - Session low
   * - ``Col.CLOSE``
     - CLOSE_PRICE
     - Official close
   * - ``Col.PREV_CLOSE``
     - PREV_CL_PR
     - Previous close
   * - ``Col.NET_TRDQTY``
     - NET_TRDQTY
     - Volume (total traded quantity)
   * - ``Col.NET_TRDVAL``
     - NET_TRDVAL
     - Total traded value
   * - ``Col.HI_52``
     - HI_52_WK
     - 52-week high
   * - ``Col.LO_52``
     - LO_52_WK
     - 52-week low
   * - ``Col.P_CLASSIC``
     - P_CLASSIC
     - Classic pivot point
   * - ``Col.P_WOODIE``
     - P_WOODIE
     - Woodie pivot point
   * - ``Col.P_CAM``
     - P_CAM
     - Camarilla anchor = previous Close


----


10. Assumptions & Constraints
==============================

10.1 Assumptions
----------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Assumption
     - Detail
   * - **Internet Access**
     - The end user has internet access when initiating downloads.
   * - **NSE URL Stability**
     - NSE continues to publish bhav-copy ZIPs at the archives.nseindia.com
       URL.
   * - **Cookie Priming**
     - NSE's session-cookie requirement is satisfied by GET-ing the homepage
       before bulk requests.
   * - **ZIP Filename Convention**
     - The internal ZIP filename convention (4-digit vs 2-digit year) may vary;
       both patterns must be matched.
   * - **Target Platform**
     - The target machine runs 64-bit Windows 10 or 11; no Python
       pre-installation is required.

10.2 Constraints
----------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Constraint
     - Detail
   * - **Single-User Desktop**
     - No concurrency, authentication, or multi-tenant access.
   * - **Disk Space**
     - Data volume is limited by available disk space in ``%APPDATA%``; no
       automatic pruning.
   * - **Localhost Port**
     - Streamlit runs locally on a fixed localhost port; the frozen launcher
       must prevent self-respawn (``multiprocessing.freeze_support`` guard).
   * - **NSE Rate-Limiting**
     - Constrains maximum parallel workers to 4 (``max_workers=4`` default).
   * - **Auto-Update Default**
     - Auto-update is OFF by default (``AUTO_UPDATE_DEFAULT = False``) to avoid
       unintended network access.
   * - **Data Processing Split**
     - Polars is used for all bulk data operations; Pandas is used only for
       parsing the NSE PD CSV file format due to its special heading-row
       structure.
