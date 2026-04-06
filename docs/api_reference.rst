.. _api_reference:

API Reference — EoD_module
===========================

This page documents the public API of ``EoD_module.py``.  All symbols listed
here are safe to import into other scripts or a custom Streamlit page.

----

Constants
---------

.. py:data:: DATA_DIR

   ``str`` — Absolute path to the writable data directory.

   - **Development mode** — ``<project_root>/data/``
   - **Frozen (Windows .exe)** — ``%APPDATA%\BullseyeFintech\NSE_Dashboard\data\``

   Created automatically on module import.

.. py:data:: AUTO_UPDATE_DEFAULT

   ``bool`` — ``False``.  Read this constant when initialising the
   auto-update toggle in the UI rather than hard-coding ``True`` or ``False``.

----

Col — Column-Name Schema
-------------------------

.. py:class:: Col

   Single source of truth for every column name used across the EOD and pivot
   CSV files.  Import ``Col`` in place of hardcoded strings to avoid
   silent mismatches caused by column-name drift.

   **EOD fields**

   .. py:attribute:: SECURITY = "SECURITY"
   .. py:attribute:: SYMBOL = "SYMBOL"
   .. py:attribute:: CATEGORY = "CATEGORY"
   .. py:attribute:: DATE = "DATE"
   .. py:attribute:: OPEN = "OPEN_PRICE"
   .. py:attribute:: HIGH = "HIGH_PRICE"
   .. py:attribute:: LOW = "LOW_PRICE"
   .. py:attribute:: CLOSE = "CLOSE_PRICE"
   .. py:attribute:: PREV_CLOSE = "PREV_CL_PR"
   .. py:attribute:: NET_TRDVAL = "NET_TRDVAL"
   .. py:attribute:: NET_TRDQTY = "NET_TRDQTY"
   .. py:attribute:: HI_52 = "HI_52_WK"
   .. py:attribute:: LO_52 = "LO_52_WK"

   **Classic pivot columns**

   ``P_CLASSIC``, ``CL_R1``, ``CL_R2``, ``CL_R3``, ``CL_S1``, ``CL_S2``,
   ``CL_S3``

   **Fibonacci pivot columns**

   ``FIB_R1``, ``FIB_R2``, ``FIB_R3``, ``FIB_S1``, ``FIB_S2``, ``FIB_S3``

   **Woodie pivot columns**

   ``P_WOODIE``, ``WD_R1``, ``WD_R2``, ``WD_S1``, ``WD_S2``

   **Camarilla pivot columns**

   ``P_CAM``, ``CAM_R1``, ``CAM_R2``, ``CAM_R3``, ``CAM_R4``,
   ``CAM_S1``, ``CAM_S2``, ``CAM_S3``, ``CAM_S4``

   **Convenience tuples**

   .. py:attribute:: PRICE_COLS

      Tuple of price and volume column names used for numeric casting in the
      pivot computation step.

   .. py:attribute:: PIVOT_FINAL_COLS

      Ordered tuple of all columns written to ``pivots_output<year>.csv``.

----

Path Helpers
------------

.. py:function:: eod_csv_path(year: int) -> str

   Return the absolute path to ``EOD_DATA_FOR_ANALYSIS_<year>.csv``.

.. py:function:: pivot_csv_path(year: int) -> str

   Return the absolute path to ``pivots_output<year>.csv``.

----

Trading Calendar
----------------

.. py:function:: get_nse_trading_days(year: int) -> list[str]

   Return all NSE trading days for *year* as ``DD-MM-YYYY`` strings, fetched
   from ``pandas-market-calendars``.

   :raises RuntimeError: if the calendar cannot be fetched (e.g. library
       out of date, network error).

.. py:function:: save_trading_days_to_csv(trading_days: list[str], year: int) -> str

   Persist *trading_days* to ``CUE_DATE_<year>.csv``.  Returns the path
   written.

----

Download Functions
------------------

.. py:function:: download_year_data(year, force_redownload=False, incremental=False, max_workers=4, progress_callback=None) -> tuple[bool, str]

   Download, extract, and consolidate all NSE bhavcopy files for *year*.

   :param int year: Calendar year to download.
   :param bool force_redownload: Overwrite an existing master CSV.
   :param bool incremental: Append only dates newer than the last date in the
       existing CSV.  Ignored when *force_redownload* is ``True``.
   :param int max_workers: Number of parallel download threads.
       Default ``4`` is conservative and reliable; do not exceed ``6``.
   :param progress_callback: Optional ``Callable[[str], None]`` for progress
       messages (used by the Streamlit sidebar).
   :returns: ``(success, message)`` tuple.

   **Examples**

   Full download:

   .. code-block:: python

      from EoD_module import download_year_data

      ok, msg = download_year_data(2024)
      print(msg)

   Incremental update:

   .. code-block:: python

      ok, msg = download_year_data(2025, incremental=True)

   With a progress callback:

   .. code-block:: python

      def on_progress(text: str) -> None:
          print(text)

      ok, msg = download_year_data(2024, progress_callback=on_progress)

----

Pivot Computation
-----------------

.. py:function:: compute_pivot_points(year: int, progress_callback=None) -> tuple[bool, str]

   Compute Classic, Fibonacci, Woodie, and Camarilla pivot points for *year*
   and write them to ``pivots_output<year>.csv``.

   Requires ``EOD_DATA_FOR_ANALYSIS_<year>.csv`` to exist.

   :param int year: Calendar year to compute pivots for.
   :param progress_callback: Optional ``Callable[[str], None]``.
   :returns: ``(success, message)`` tuple.

   .. code-block:: python

      from EoD_module import compute_pivot_points

      ok, msg = compute_pivot_points(2024)
      print(msg)  # ✓ Pivot points saved for 2024 (246,000 rows)

----

Data Management
---------------

.. py:function:: get_available_years() -> list[int]

   Scan ``DATA_DIR`` and return a sorted list of years that have an
   ``EOD_DATA_FOR_ANALYSIS_<year>.csv`` on disk.

.. py:function:: get_data_status(year: int) -> dict

   Return a status dictionary for *year*:

   .. code-block:: python

      {
          "has_eod": bool,
          "has_pivots": bool,
          "eod_rows": int | None,
          "eod_size_kb": float | None,
          "pivot_rows": int | None,
          "latest_date": str | None,
          "earliest_date": str | None,
      }

.. py:function:: delete_year_data(year: int) -> tuple[bool, str]

   Delete all files for *year*: EOD CSV, pivot CSV, calendar CSV, and any
   partial files remaining in the per-year temp directory.

   :returns: ``(success, message)`` tuple.

----

Auto-Update
-----------

.. py:function:: check_auto_update_needed() -> int | None

   Return the year that needs updating if yesterday's trading data is absent,
   otherwise ``None``.  Consults ``CUE_DATE_<year>.csv`` so NSE holidays are
   not treated as missing data.

.. py:function:: run_auto_update(progress_callback=None) -> tuple[bool, str]

   Call ``download_year_data()`` in incremental mode for the year returned by
   ``check_auto_update_needed()``.  The caller is responsible for checking the
   user's auto-update preference before calling this function.

----

Export Helpers
--------------

.. py:function:: get_eod_csv_bytes(year: int) -> bytes | None

   Return the raw bytes of ``EOD_DATA_FOR_ANALYSIS_<year>.csv``, or ``None``
   if the file does not exist.  For use with ``st.download_button``.

.. py:function:: get_pivot_csv_bytes(year: int) -> bytes | None

   Return the raw bytes of ``pivots_output<year>.csv``, or ``None`` if the
   file does not exist.

.. py:function:: get_filtered_eod_bytes(year, symbols=None, categories=None, date_from=None, date_to=None) -> bytes | None

   Return filtered EOD data as CSV bytes.  All filter parameters are optional.

   :param int year: Data year.
   :param list[str] | None symbols: Symbol filter.
   :param list[str] | None categories: Category filter.
   :param str | None date_from: Inclusive lower bound as ``"YYYY-MM-DD"``.
   :param str | None date_to: Inclusive upper bound as ``"YYYY-MM-DD"``.
   :returns: CSV bytes, or ``None``.

.. py:function:: get_filtered_pivot_bytes(year, symbols=None, date=None) -> bytes | None

   Return filtered pivot data as CSV bytes.

   :param int year: Data year.
   :param list[str] | None symbols: Symbol filter.
   :param str | None date: Exact date as ``"YYYY-MM-DD"``.
   :returns: CSV bytes, or ``None``.
