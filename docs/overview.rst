.. _overview:

Overview
========

Bullseye Fintech NSE EOD Dashboard (``app_v2.py``) is a Windows desktop
application built on Streamlit.  It downloads open-source end-of-day (EOD)
equity bhavcopy data published by the National Stock Exchange of India, stores
it as CSV files locally, and provides an interactive UI for viewing OHLCV price
history with technical chart overlays and pivot point levels across four methods.

----

Why This Software Exists
------------------------

NSE publishes daily bhavcopy ZIP files on its website, but accessing them
reliably is non-trivial.  The server requires session cookies, blocks
unauthenticated requests, returns malformed responses on some dates, and uses
an inconsistent file-naming format.  On top of that, the raw files have a
nested structure where category headings are mixed in with actual data rows,
making them difficult to parse directly.

This application hides all of that complexity behind a clean, reliable API
so the dashboard never needs to handle low-level download concerns.

----

Technology Stack
----------------

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
     - Plotly — Candlestick, OHLC Bar, Line, MA, Bollinger Bands, pivot overlays
   * - **Data Source**
     - NSE India public bhavcopy archives — https://archives.nseindia.com
   * - **Local Storage**
     - CSV files (not Parquet): ``EOD_DATA_FOR_ANALYSIS_{year}.csv``,
       ``pivots_output{year}.csv``
   * - **HTTP Client**
     - ``requests.Session`` with NSE homepage cookie priming and exponential
       backoff
   * - **Trading Calendar**
     - ``pandas_market_calendars`` (NSE calendar) — holiday-aware
   * - **Packaging**
     - PyInstaller (frozen bundle) + Inno Setup (Windows installer)
   * - **Target OS**
     - Windows 10 / 11 (64-bit)

----

Feature Summary
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Feature Area
     - Description
   * - **Download Modes**
     - Single Year, Multiple Years, Date Range, and All Downloaded
       (re-process existing).  Supports incremental (append only) and
       force-redownload modes.
   * - **Local Storage**
     - Persistent local CSV storage of parsed OHLCV data keyed by year.
   * - **OHLCV Summary Tab**
     - KPI cards, 52-week range bar, interactive Candlestick / OHLC / Line
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
     - Single Windows installer (Sora + JetBrains Mono theme).

----

Scope
-----

What the system **will** do
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
- Expose all of this through a clean function-level API, including in-memory
  CSV bytes for direct download buttons.

What the system **will not** do
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Provide real-time or intraday price data — the smallest unit is one full
  trading day.
- Support exchanges other than NSE.
- Store data in a database — all persistence is flat CSV files.
- Perform any trading, order placement, or brokerage integration.
- Send alerts or notifications.
- Compute technical indicators beyond the four supported pivot methods.
- Validate whether downloaded data is financially accurate — it trusts NSE's
  published figures.
- Operate if NSE changes its archive URL structure or file format, as no
  fallback source is implemented.

----

Roles
-----

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Actor
     - Description & Capabilities
   * - **Admin — Developer**
     - Deploys and maintains the application.  Interacts directly with both
       ``app_v2.py`` and ``EoD_module.py``, manages the data directory, and
       handles updates.
   * - **End User (Trader / Analyst)**
     - Sole human user.  No login required.  Installs the app, selects download
       options, reads OHLCV charts and pivot outputs.  Cannot modify the app.
   * - **NSE Archives Server**
     - External HTTPS endpoint.  Read-only source of bhavcopy ZIPs at
       ``archives.nseindia.com/archives/equities/bhavcopy/pr/``.  Requires
       session-cookie priming via GET to ``nseindia.com``.
   * - **NSE Homepage**
     - ``GET https://www.nseindia.com`` — visited to acquire valid session
       cookies before bulk downloads.
   * - **Local File System**
     - Stores CSVs and temp files.  Frozen mode:
       ``%APPDATA%\\BullseyeFintech\\NSE_Dashboard\\data\\``.
       Dev mode: ``./data/`` alongside the script.

----

Assumptions & Constraints
--------------------------

**Assumptions**

- The end user has internet access when initiating downloads.
- NSE continues to publish bhavcopy ZIPs at the ``archives.nseindia.com`` URL.
- NSE's session-cookie requirement is satisfied by GET-ing the homepage before
  bulk requests.
- The internal ZIP filename convention (4-digit vs 2-digit year) may vary; both
  patterns are matched.
- The target machine runs 64-bit Windows 10 or 11; no Python pre-installation
  is required.

**Constraints**

- Single-user desktop application — no concurrency, authentication, or
  multi-tenant access.
- Data volume is limited by available disk space in ``%APPDATA%``; no automatic
  pruning.
- Streamlit runs locally on a fixed localhost port; the frozen launcher must
  prevent self-respawn via ``multiprocessing.freeze_support`` guard.
- NSE rate-limiting constrains maximum parallel workers to 4 by default.
- Auto-update is OFF by default (``AUTO_UPDATE_DEFAULT = False``) to avoid
  unintended network access.
- Polars is used for all bulk data operations; Pandas is used only for parsing
  the NSE PD CSV file format due to its special heading-row structure.
