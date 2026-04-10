.. _ohlcv_analysis:

OHLCV Analysis
==============

The **OHLCV Summary** tab is the primary price exploration view.  It combines
an interactive Plotly chart, a set of KPI cards, and a 52-week range bar.

----

Loading Data
------------

Before the OHLCV tab is usable, at least one year of data must be downloaded
and loaded.  Click a year badge in the sidebar to load that year's
``EOD_DATA_FOR_ANALYSIS_<year>.csv`` into memory.

----

Filters
-------

The filter bar at the top of the page controls which rows are visible across
both tabs:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Filter
     - Notes
   * - **Category**
     - NSE equity categories (``EQ``, ``BE``, ``NIFTY 50``, etc.).  Only
       categories present in the loaded year are shown.
   * - **Symbol**
     - Type-ahead multiselect.  Filtered to the selected category.
   * - **Date range**
     - Calendar pickers navigable back to 2000.  Quick presets are available
       (see below).

Quick date presets
~~~~~~~~~~~~~~~~~~

- Last 30 days
- Last 90 days
- Last 6 months
- Year-to-date (YTD)
- Full year

----

Chart Types
-----------

Three chart types are available from the chart-type selector:

Candlestick
~~~~~~~~~~~

The default view.  Each bar represents one trading day:

- **Green candle** — close ≥ open (up day)
- **Red candle** — close < open (down day)
- Wicks extend to the daily high and low.

OHLC Bar
~~~~~~~~

A traditional OHLC bar chart.  Colour coding follows the same up/down
convention as the candlestick view.

Line (Close)
~~~~~~~~~~~~

A simple line connecting daily closing prices.  Useful for multi-symbol
comparison where candlestick density is visually overwhelming.

----

Overlays
--------

Overlays are optional and toggled individually via checkboxes below the chart:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Overlay
     - Calculation
   * - **Volume**
     - Bar chart on a secondary y-axis.  Bars are coloured green (up day)
       or red (down day) to match the price candles.
   * - **20-Day MA**
     - Simple moving average of ``CLOSE_PRICE`` over 20 trading days.
   * - **50-Day MA**
     - Simple moving average of ``CLOSE_PRICE`` over 50 trading days.
   * - **Bollinger Bands**
     - 20-day SMA ± 2 standard deviations.  The band is filled with a
       semi-transparent pastel shading.

----

KPI Cards
---------

Below the chart a row of metric cards shows the most recent trading day's
data for the selected symbol:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Card
     - Notes
   * - **Open**
     - ``OPEN_PRICE`` for the latest date in the filtered range.
   * - **High**
     - ``HIGH_PRICE`` for the latest date.
   * - **Low**
     - ``LOW_PRICE`` for the latest date.
   * - **Close**
     - ``CLOSE_PRICE`` for the latest date, with a delta and percentage
       change relative to *Prev Close*.
   * - **Prev Close**
     - ``PREV_CL_PR`` as reported by NSE.
   * - **Volume**
     - ``NET_TRDQTY`` (net traded quantity).  Formatted with thousand
       separators.

----

52-Week Range Bar
-----------------

A gradient bar beneath the KPI row shows where the latest close sits within
the 52-week high/low range.  The live marker moves between:

- **Left end** — 52-week low (``LO_52_WK``)
- **Right end** — 52-week high (``HI_52_WK``)

Values are sourced directly from the NSE bhavcopy ``HI_52_WK`` and
``LO_52_WK`` columns, which NSE publishes in the PD file.

----

Multi-Symbol Comparison
-----------------------

Selecting more than one symbol in the Symbol filter enables comparison mode.
All selected symbols are plotted on the same chart.  For candlestick and OHLC
charts each symbol gets its own distinct colour.  KPI cards are shown per
symbol in a scrollable row.
