.. _downloading_data:

Downloading Data
================

All NSE data is fetched from the public bhavcopy archive:

.. code-block:: text

   https://archives.nseindia.com/archives/equities/bhavcopy/pr/PR<DDMMYY>.zip

Each ZIP contains a daily equity delivery file (``Pd<DDMMYY>.csv`` or
``pd<DDMMYYYY>.csv`` for newer archives) with OHLCV data for every listed
security.

----

Download Modes
--------------

The sidebar **Download from NSE** section exposes four modes:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Mode
     - Description
   * - **Single Year**
     - Download one full calendar year.  All NSE trading days for that year
       are fetched, skipping weekends, holidays, and future dates automatically.
   * - **Multiple Years**
     - Select any combination of years from a multiselect.  Each year is
       processed in sequence.
   * - **Date Range**
     - Pick a *from* and *to* date.  All calendar years that span the range
       are downloaded automatically.
   * - **All Downloaded**
     - Re-process (or re-download) every year that already has an EOD CSV
       on disk.  Useful after a bulk upgrade or format fix.

All modes support two additional flags:

- **Force re-download** — overwrite the existing master CSV even if it
  already exists.
- **Incremental** — append only trading dates newer than the last date
  already in the CSV.  Does nothing if *Force re-download* is also enabled.

----

How Downloads Work
------------------

Session priming
~~~~~~~~~~~~~~~

Before any bulk download begins, the engine performs a *session prime*: a
``GET`` request to ``https://www.nseindia.com/`` to acquire a valid session
cookie.  NSE's archive server requires this cookie and returns ``403 Forbidden``
for requests made without it.

The session is re-primed automatically every five minutes during long downloads
(``_PRIME_INTERVAL = 300`` seconds).  If a ``403`` is received mid-download,
the session is force-re-primed immediately and the request is retried.

Parallel downloads
~~~~~~~~~~~~~~~~~~

Trading days within a year are downloaded concurrently via a
``ThreadPoolExecutor`` with **four workers** by default.  Each worker calls
``_download_one()`` for a single date.

Retry and backoff
~~~~~~~~~~~~~~~~~

For each date, up to three attempts are made with exponential backoff:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Attempt
     - Wait before next attempt
   * - 1
     - 2 seconds
   * - 2
     - 4 seconds
   * - 3
     - 8 seconds (final)

If all three attempts fail the date is recorded as skipped and reported in
the progress log.  The overall download still succeeds if at least one date
was downloaded.

404 handling
~~~~~~~~~~~~

A ``404`` response means no bhavcopy was published for that date — a holiday,
a weekend that slipped through, or a gap in the NSE archive.  These are
silently skipped; they are not counted as failures.

Future date filtering
~~~~~~~~~~~~~~~~~~~~~

All dates beyond today are filtered out before any download attempts begin
(``BUG-E13``).  This prevents spurious 404 loops when downloading the current
year.

Filename pattern matching
~~~~~~~~~~~~~~~~~~~~~~~~~

NSE changed the filename convention inside ZIP archives in recent years:

- **Older archives** — ``pd300326.csv`` (DDMMYY — two-digit year)
- **Newer archives** — ``pd31122025.csv`` (DDMMYYYY — four-digit year)

The engine tries the four-digit pattern first and falls back to the two-digit
pattern, so all historical and current archives are handled correctly.

Consolidation and atomic writes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After all files for a year are downloaded and extracted to a per-year temp
directory, they are parsed with ``process_file()`` and concatenated into a
single Polars DataFrame.  The master CSV is written atomically:

1. The new data is written to ``EOD_DATA_FOR_ANALYSIS_<year>.csv.tmp``.
2. ``os.replace()`` renames the temp file to the final path.

This prevents a partial or corrupt CSV if the process is interrupted.

Incremental mode appends new rows to the existing CSV and de-duplicates on
``(DATE, SYMBOL, CATEGORY)`` before writing.

----

Auto-Update
-----------

The sidebar exposes an **Auto-update** toggle (off by default,
``AUTO_UPDATE_DEFAULT = False``).  When enabled, the dashboard checks on
launch whether yesterday's trading data is present.

The check is holiday-aware: it consults ``CUE_DATE_<year>.csv`` (the cached
NSE trading calendar) before deciding whether an update is needed.  If
yesterday was an NSE holiday the check returns immediately with no action.

When an update is needed, ``run_auto_update()`` calls ``download_year_data()``
in incremental mode, fetching only the missing date(s).

----

Trading Calendar
----------------

NSE trading days are fetched from ``pandas-market-calendars`` using the
``"NSE"`` calendar identifier.  The resulting list is cached to
``CUE_DATE_<year>.csv`` so subsequent launches do not require a network call
for the calendar.

.. code-block:: python

   from pandas_market_calendars import get_calendar

   cal = get_calendar("NSE")
   schedule = cal.valid_days(start_date="2025-01-01", end_date="2025-12-31")

If the calendar library cannot be reached a ``RuntimeError`` is raised with a
descriptive message advising you to update ``pandas-market-calendars``.
