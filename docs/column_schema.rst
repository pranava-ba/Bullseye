.. _column_schema:

Column Schema
=============

All column names are defined as constants in the ``Col`` class inside
``EoD_module.py``.  This page documents every column in both output CSV files.

.. tip::

   Always reference ``Col.SYMBOL``, ``Col.CLOSE``, etc. in your code rather
   than the raw string ``"SYMBOL"`` or ``"CLOSE_PRICE"``.  This guards against
   silent failures if a name ever changes.

----

EOD_DATA_FOR_ANALYSIS_<year>.csv
----------------------------------

This is the master OHLCV file produced by ``download_year_data()``.

.. list-table::
   :widths: 25 15 60
   :header-rows: 1

   * - Column (``Col.*``)
     - Raw string
     - Description
   * - ``DATE``
     - ``DATE``
     - Trading date, format ``YYYY-MM-DD``.
   * - ``CATEGORY``
     - ``CATEGORY``
     - NSE equity category reconstructed by the parser.  Common values:
       ``EQ``, ``BE``, ``BZ``, ``SM``, ``NIFTY INDEX``, etc.
   * - ``SECURITY``
     - ``SECURITY``
     - Full security name as published by NSE.
   * - ``SYMBOL``
     - ``SYMBOL``
     - NSE ticker symbol.  Falls back to ``SECURITY`` when absent.
   * - ``OPEN``
     - ``OPEN_PRICE``
     - Opening price for the session (₹).
   * - ``HIGH``
     - ``HIGH_PRICE``
     - Intraday high (₹).
   * - ``LOW``
     - ``LOW_PRICE``
     - Intraday low (₹).
   * - ``CLOSE``
     - ``CLOSE_PRICE``
     - Closing price (₹).
   * - ``PREV_CLOSE``
     - ``PREV_CL_PR``
     - Previous session closing price as reported by NSE (₹).
   * - ``NET_TRDVAL``
     - ``NET_TRDVAL``
     - Net traded value (₹).
   * - ``NET_TRDQTY``
     - ``NET_TRDQTY``
     - Net traded quantity (number of shares).
   * - ``HI_52``
     - ``HI_52_WK``
     - 52-week high (₹), as published in the bhavcopy.
   * - ``LO_52``
     - ``LO_52_WK``
     - 52-week low (₹), as published in the bhavcopy.

----

pivots_output<year>.csv
------------------------

Produced by ``compute_pivot_points()``.  Each row corresponds to one
``(DATE, SYMBOL, CATEGORY)`` combination and contains pivot levels applicable
to trading *on* that date (calculated from the previous session's OHLC).

.. list-table::
   :widths: 25 15 60
   :header-rows: 1

   * - Column (``Col.*``)
     - Raw string
     - Description
   * - ``DATE``
     - ``DATE``
     - The session date for which these levels apply (``YYYY-MM-DD``).
   * - ``CATEGORY``
     - ``CATEGORY``
     - NSE equity category.
   * - ``SYMBOL``
     - ``SYMBOL``
     - NSE ticker symbol.
   * - ``P_CLASSIC``
     - ``P_CLASSIC``
     - Classic pivot point = (H + L + C) / 3 using previous-day values.
   * - ``CL_R1`` … ``CL_R3``
     - ``CL_R1`` – ``CL_R3``
     - Classic resistance levels 1–3.
   * - ``CL_S1`` … ``CL_S3``
     - ``CL_S1`` – ``CL_S3``
     - Classic support levels 1–3.
   * - ``FIB_R1`` … ``FIB_R3``
     - ``FIB_R1`` – ``FIB_R3``
     - Fibonacci resistance levels (0.382 / 0.618 / 1.000 × Range above PP).
   * - ``FIB_S1`` … ``FIB_S3``
     - ``FIB_S1`` – ``FIB_S3``
     - Fibonacci support levels (0.382 / 0.618 / 1.000 × Range below PP).
   * - ``P_WOODIE``
     - ``P_WOODIE``
     - Woodie pivot = (H + L + 2C) / 4 using previous-day values.
   * - ``WD_R1``, ``WD_R2``
     - ``WD_R1``, ``WD_R2``
     - Woodie resistance levels 1–2.
   * - ``WD_S1``, ``WD_S2``
     - ``WD_S1``, ``WD_S2``
     - Woodie support levels 1–2.
   * - ``P_CAM``
     - ``P_CAM``
     - Camarilla anchor = previous-day close (not a pivot average).
   * - ``CAM_R1`` … ``CAM_R4``
     - ``CAM_R1`` – ``CAM_R4``
     - Camarilla resistance levels 1–4.
   * - ``CAM_S1`` … ``CAM_S4``
     - ``CAM_S1`` – ``CAM_S4``
     - Camarilla support levels 1–4.

CUE_DATE_<year>.csv
--------------------

Single-column file produced by ``save_trading_days_to_csv()``.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Column
     - Description
   * - ``details``
     - NSE trading day as ``DD-MM-YYYY``.  One row per trading day.
