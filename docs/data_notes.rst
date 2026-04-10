.. _data_notes:

Data Notes
==========

Source
------

All data comes from NSE's public bhavcopy archive:

.. code-block:: text

   https://archives.nseindia.com/archives/equities/bhavcopy/pr/PR<DDMMYY>.zip

Each ZIP contains one equity delivery file (``Pd<DDMMYY>.csv``) with OHLCV
data for every security listed on NSE for that trading session.

Historical coverage begins around the year 2000.  Data prior to that may be
incomplete or unavailable on NSE's servers.

----

File Encoding
-------------

NSE bhavcopy files use **latin-1 / cp1252** encoding, not UTF-8.  The parser
handles this automatically; any ``UnicodeDecodeError`` silently falls back to
``latin-1``.

----

PD File Structure
-----------------

NSE PD files use a nested format that is not a standard flat CSV:

.. code-block:: text

   SECURITY,MKT,...          ← header row
   NIFTY 50,,,...            ← index heading (MKT = null)
   SYMBOL_A,NSE,...          ← data rows (MKT = "NSE")
   SYMBOL_B,NSE,...
   EQ,,,...                  ← category heading (MKT = null)
   SYMBOL_C,NSE,...          ← data rows for "EQ" category
   ...

The ``process_file()`` function reconstructs the ``CATEGORY`` column by
identifying heading rows (``MKT`` is null) and propagating their label forward
to all following data rows until the next heading.

----

Categories
----------

Common values for the ``CATEGORY`` column:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Value
     - Description
   * - ``NIFTY INDEX``
     - Nifty index constituents (top of each PD file)
   * - ``EQ``
     - Normal equity series
   * - ``BE``
     - Trade-for-trade (book entry) segment
   * - ``BZ``
     - Trade-for-trade odd lot
   * - ``SM``
     - SME equity series
   * - ``ST``
     - Stock Throughput series

----

Column Headers
--------------

NSE bhavcopy headers sometimes include trailing spaces (e.g. ``"SYMBOL "``).
The parser strips and uppercases all column names before any further
processing.  ``Col.*`` constants are defined without trailing spaces —
the normalisation step in ``process_file()`` and ``compute_pivot_points()``
ensures these always match.

----

Date Format
-----------

Both output CSVs use **YYYY-MM-DD** throughout.  The NSE calendar CSV
(``CUE_DATE_<year>.csv``) uses **DD-MM-YYYY**, which is the format returned
by ``pandas-market-calendars`` and expected by the URL-construction logic.

----

NSE Rate Limiting
-----------------

NSE's archive server tolerates moderate download concurrency but will return
``403 Forbidden`` if too many requests arrive too quickly.  The default of
four parallel workers is conservative and reliable.  The session is
automatically re-primed on any ``403``.

If you experience persistent ``403`` responses even with four workers, try
reducing ``max_workers`` to ``2`` or increasing ``_PRIME_INTERVAL`` to ``120``
seconds.
