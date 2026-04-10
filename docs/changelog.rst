.. _changelog:

Changelog
=========

v2 (current)
------------

This release is a ground-up rewrite of the download engine and a complete
rework of the Streamlit UI.

Engine changes
~~~~~~~~~~~~~~

- **Full Polars pipeline** — ``process_file()``, consolidation, pivot
  computation, and all CSV helpers now use Polars instead of pandas.
  pandas is retained only for NSE's PD-file format parsing, which requires
  its row-drop and category-propagation logic.

- **Parallel downloads** — ``ThreadPoolExecutor`` with four workers replaces
  the sequential download loop.  Typical year-download time drops by 3–4×.

- **Session priming** — a ``GET`` to the NSE homepage is performed before
  bulk downloads and automatically refreshed every five minutes.

- **Exponential backoff retry** — three attempts with 2 / 4 / 8 second waits,
  replacing single-attempt downloads that silently failed.

- **Atomic CSV writes** — all master CSV updates go through a ``.tmp`` file
  renamed by ``os.replace()``, preventing corruption on crash or interrupt.

- **Per-year temp directories** — each year's extracted PD files land in
  ``data/nse_eod_data_files/<year>/``, eliminating cross-year file
  contamination.

- **Incremental download mode** — appends only missing dates to an existing
  CSV and de-duplicates on ``(DATE, SYMBOL, CATEGORY)``.

- **Holiday-aware auto-update** — consults ``CUE_DATE_<year>.csv`` before
  deciding whether an update is needed.  NSE holidays no longer trigger a
  spurious download attempt.

- **4-digit year filename support** — NSE switched from ``pd300326.csv``
  (DDMMYY) to ``pd31122025.csv`` (DDMMYYYY) in recent archives.  The engine
  tries the 4-digit pattern first and falls back to 2-digit for older data.

- **Future date filtering** — dates beyond today are excluded from the
  download queue before any HTTP requests are made.

- **Col dataclass** — all column name strings are centralised in the ``Col``
  class.  Both ``EoD_module.py`` and ``app_v2.py`` reference ``Col.*``
  constants rather than raw strings.

- **Corrected Camarilla pivot anchor** — ``P_CAM`` is now the previous-day
  close, not the Classic PP average.  This is the mathematically correct
  formulation.

- **YYYY-MM-DD date format** — consistent date string format across both
  output CSVs, replacing a mixed DDMMYY/YYYY-MM-DD format in v1.

Bug fixes (cross-referenced to Deep Analysis document)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Bug ID
     - Fix
   * - BUG-E1
     - Filename date parser now validates day ∈ [1, 31] and month ∈ [1, 12]
       before accepting the result.
   * - BUG-E2
     - URL year-slice fragility guarded by full ``datetime`` parsing instead
       of raw string slicing.
   * - BUG-E3
     - ``CATEGORY`` length validated against ``len(df_final)`` before
       assignment; raises a descriptive ``ValueError`` on mismatch.
   * - BUG-E4
     - Session cookie primed before bulk download; re-primed on ``403``.
   * - BUG-E5
     - Retry with exponential backoff (3 attempts, 2 / 4 / 8 s delays).
   * - BUG-E6
     - Camarilla anchor renamed ``P_CAM`` = previous-day close, not
       ``P_CLASSIC``.
   * - BUG-E7
     - Column names normalised to uppercase on every CSV load, eliminating
       trailing-space mismatches from NSE headers.
   * - BUG-E8
     - Auto-update consults the NSE trading calendar before acting; no longer
       triggers on NSE holidays.
   * - BUG-E9
     - Atomic CSV write via ``tmp → os.replace()``.
   * - BUG-E10
     - Per-year temp directories prevent cross-year file contamination.
   * - BUG-E11
     - ``delete_year_data()`` also removes partial PD files from the per-year
       temp directory.
   * - BUG-E12
     - ``get_nse_trading_days()`` raises a ``RuntimeError`` with a helpful
       message when the calendar cannot be fetched.
   * - BUG-E13
     - Future dates filtered from the download queue before any HTTP requests
       are made.

UI changes
~~~~~~~~~~

- Light/pastel CSS theme with Sora and JetBrains Mono typography.
- Four-method consolidated pivot matrix rendered as colour-coded HTML table.
- Editable pivot values inline before chart overlay.
- Pivot chart groups levels by method with distinct colour families.
- Date filter calendar navigable back to year 2000.
- Auto-update toggle replaced by radio button (sidebar).
- ``st.download_button`` for EOD and pivot CSVs in the sidebar.
- 52-week range bar with live marker.

----

v1
---

Initial release.  Sequential downloads, single-threaded, pandas-only pipeline,
no session priming, no retry logic.  Camarilla anchor incorrectly used the
Classic PP average.
