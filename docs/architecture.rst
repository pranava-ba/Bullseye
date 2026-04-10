.. _architecture:

Architecture
============

The dashboard is split into two Python files with a clean separation of
concerns:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - File
     - Responsibility
   * - ``EoD_module.py``
     - Download engine, file processing, pivot computation, path helpers,
       session management, trading calendar, export helpers.
   * - ``app_v2.py``
     - Streamlit UI — sidebar controls, chart rendering, KPI cards, filter
       bar, pivot matrix, export buttons.

``app_v2.py`` imports from ``EoD_module`` only through its public API; it
never accesses internal helpers directly.

----

Data Flow
---------

.. code-block:: text

   NSE Archives (HTTPS)
           │
           ▼
     _prime_session()          ← Acquire session cookie
           │
           ▼
     ThreadPoolExecutor        ← 4 parallel workers (configurable)
           │   ├── _download_one(date_1) ──────────────────────────────┐
           │   ├── _download_one(date_2)                               │
           │   └── _download_one(date_N)                               │
           │                                                            │
           ▼                                                            │
     _tdate_to_pdtag()         ← Build URL tag (DDMMYY)               │
           │                                                            │
           ▼                                                            │
     HTTP GET with retry/backoff                                        │
           │                                                            │
           ▼                                                            │
     zipfile.ZipFile           ← Match 4-digit OR 2-digit year pattern │
           │                                                            │
           ▼                                                            │
     Per-year temp dir  ←───────────────────────────────────────────────┘
           │
           ▼
     process_file()            ← pandas parse → CATEGORY reconstruction
           │                      → Polars DataFrame
           ▼
     pl.concat (diagonal)      ← Tolerates minor schema differences between years
           │
           ▼
     Atomic CSV write          ← .tmp → os.replace
           │
           ▼
     EOD_DATA_FOR_ANALYSIS_<year>.csv
           │
           ▼
     compute_pivot_points()    ← Polars vectorised: shift-over for prev OHLC,
           │                      then Classic / Fibonacci / Woodie / Camarilla
           ▼
     pivots_output<year>.csv
           │
           ▼
     app_v2.py (Streamlit)     ← Charts, KPIs, pivot matrix, filters, export

----

Module: EoD_module.py
----------------------

Key responsibilities and their implementations:

Session management
~~~~~~~~~~~~~~~~~~

``_prime_session(force=False)``
  Performs a ``GET`` to the NSE homepage to obtain a valid session cookie.
  Protected by a threading lock.  Re-primes automatically every
  ``_PRIME_INTERVAL = 300`` seconds, or immediately on a ``force=True`` call
  (triggered by a ``403`` response).

Trading calendar
~~~~~~~~~~~~~~~~

``get_nse_trading_days(year)``
  Fetches the NSE calendar from ``pandas-market-calendars`` and returns
  trading days as ``DD-MM-YYYY`` strings.

``_load_trading_days(year)``
  Loads the calendar from ``CUE_DATE_<year>.csv`` if present, otherwise
  fetches and caches it.

Download pipeline
~~~~~~~~~~~~~~~~~

``_download_one(tdate, temp_dir, progress_callback)``
  Downloads and extracts a single bhavcopy date.  Handles future-date
  filtering, retry with exponential backoff, ``403`` re-prime, ``404`` skip,
  case-insensitive ZIP member matching, and 4-digit/2-digit year filename
  variants.

``download_year_data(year, ...)``
  The main orchestrator.  Loads the calendar, filters future dates, optionally
  reads existing dates for incremental mode, dispatches parallel downloads via
  ``ThreadPoolExecutor``, calls ``process_file()`` on each extracted CSV,
  concatenates results, and writes atomically.

File processing
~~~~~~~~~~~~~~~

``process_file(file_path)``
  Parses a single ``Pd.csv`` file.  NSE PD files use a nested format where
  category headings appear inline as rows with a null ``MKT`` column.  The
  function:

  1. Reads the raw CSV with ``pandas`` (needed for the NSE format quirks).
  2. Identifies heading rows and propagates ``CATEGORY`` labels forward.
  3. Drops heading rows (``MKT`` is null).
  4. Validates ``len(CATEGORY) == len(df_final)`` before assignment.
  5. Parses the date from the filename via ``_parse_date_from_filename()``.
  6. Returns a ``polars.DataFrame``.

``_parse_date_from_filename(filename)``
  Extracts ``YYYY-MM-DD`` from a filename using two regex patterns
  (``DDMMYYYY`` and ``DDMMYY``).  Validates day ∈ [1, 31] and month ∈ [1, 12]
  before returning.

Pivot computation
~~~~~~~~~~~~~~~~~

``compute_pivot_points(year)``
  Reads the EOD CSV, normalises column names, casts price columns to
  ``Float64``, sorts by ``(SYMBOL, CATEGORY, DATE)``, and uses Polars
  ``shift(1).over([SYMBOL, CATEGORY])`` to derive previous-day H, L, C without
  a Python loop.  Then computes all four pivot families in vectorised
  ``with_columns`` calls and writes atomically.

Column-name schema
~~~~~~~~~~~~~~~~~~

``Col`` (dataclass)
  Every column name used across both CSVs is defined as a class-level string
  constant.  Both ``EoD_module.py`` and ``app_v2.py`` import from ``Col``
  rather than using hardcoded strings.  This eliminates silent column-lookup
  failures caused by trailing-space mismatches in NSE headers.

----

Module: app_v2.py
-----------------

Theme and fonts
~~~~~~~~~~~~~~~

The UI uses a custom light/pastel CSS theme injected via ``st.markdown``.
Typography is set to **Sora** (headings and UI text) and **JetBrains Mono**
(numbers and data values), loaded from Google Fonts.

Colour palette (key values):

- Page background: ``#f4f5f9``
- Sidebar background: ``#eef0f8``
- Primary accent (indigo): ``#3949ab``
- Text: ``#1e2035``
- Muted text: ``#5e6180``
- Grid lines: ``#c5cae9``

Plotly layout
~~~~~~~~~~~~~

All charts share a common ``PLOTLY_LAYOUT`` dict applied via
``fig.update_layout(**PLOTLY_LAYOUT)``.  This ensures consistent background
colour, font, and grid styling across OHLCV and pivot charts.  The layout
object is defined once at module level and never mutated at runtime.

Pivot matrix rendering
~~~~~~~~~~~~~~~~~~~~~~

The consolidated pivot matrix is rendered as a raw HTML ``<table>`` injected
via ``st.markdown(..., unsafe_allow_html=True)``.  This approach gives full
control over the colour-coded row and header styles that Streamlit's
``st.dataframe`` cannot express.

----

File Layout on Disk
-------------------

.. code-block:: text

   data/
   ├── EOD_DATA_FOR_ANALYSIS_2023.csv   ← OHLCV master for 2023
   ├── EOD_DATA_FOR_ANALYSIS_2024.csv
   ├── pivots_output2023.csv            ← Pivot output for 2023
   ├── pivots_output2024.csv
   ├── CUE_DATE_2023.csv                ← NSE trading-day calendar for 2023
   ├── CUE_DATE_2024.csv
   └── nse_eod_data_files/
       ├── 2023/                        ← Per-year temp dir (cleaned after download)
       └── 2024/

Windows (frozen executable):

.. code-block:: text

   %APPDATA%\BullseyeFintech\NSE_Dashboard\
   ├── data\                            ← Same layout as above
   └── bullseye.log                     ← Rotating log file
