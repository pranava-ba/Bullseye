.. _quickstart:

Quick Start
===========

This page gets you from a fresh install to your first chart in under five
minutes.

Step 1 — Open the sidebar
--------------------------

Click the **≡** icon at the top-left of the page (or press ``S``) to expand
the sidebar.

Step 2 — Download a year of data
---------------------------------

1. Under **Download from NSE**, select ``Single Year`` from the mode picker.
2. Choose the year you want (e.g. ``2024``).
3. Leave *Force re-download* unchecked and *Incremental* unchecked for a
   fresh download.
4. Click **🚀 Start Download**.

Progress messages appear in real time.  A full year typically takes
30–90 seconds depending on your connection speed and NSE's response times.

.. tip::

   The download uses four parallel workers by default.  If you see 403 errors,
   the session is automatically re-primed and the download retries.  You
   normally do not need to intervene.

Step 3 — Load the data
-----------------------

Once the download completes, the year badge appears under **Available years**
in the sidebar.  Click it to load the data into the dashboard.

Step 4 — Apply filters
-----------------------

The **Filters** bar at the top of the main area lets you narrow the view:

- **Category** — e.g. ``EQ``, ``BE``, ``NIFTY 50``
- **Symbol** — type-ahead search across all symbols in that category
- **Date range** — use the quick presets (Last 30 days, YTD, Full year …)
  or pick custom dates from the calendar

Step 5 — Explore charts and pivots
------------------------------------

Use the two tabs in the main area:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - **OHLCV Summary**
     - Interactive price chart with optional MA / Bollinger Band overlays,
       KPI cards, and a 52-week range bar.
   * - **Pivot Points**
     - Consolidated resistance/support table across all four pivot methods,
       with an optional price overlay chart.

----

What's Next?
------------

- :ref:`downloading_data` — download modes, incremental updates, auto-update
- :ref:`ohlcv_analysis` — chart types, overlays, KPI cards
- :ref:`pivot_points` — pivot methods explained, the matrix table, chart overlay
- :ref:`export` — downloading EOD and pivot CSVs
