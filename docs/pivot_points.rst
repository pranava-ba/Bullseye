.. _pivot_points:

Pivot Points
============

The **Pivot Points** tab computes and displays support and resistance levels
for every symbol and trading day using four well-known methodologies.

Pivots are computed by ``compute_pivot_points()`` in ``EoD_module.py`` and
stored in ``pivots_output<year>.csv``.  The computation uses **previous-day**
OHLC values — each row in the pivot CSV gives the levels applicable to
*trading on that date*, calculated from the prior session.

----

Methodology Reference
---------------------

All four methods use the previous session's High (H), Low (L), and Close (C).
Range = H − L.

Classic
~~~~~~~

The original floor-trader pivot.

.. math::

   PP &= \frac{H + L + C}{3} \\
   R1 &= 2 \times PP - L \\
   R2 &= PP + \text{Range} \\
   R3 &= H + 2 \times (PP - L) \\
   S1 &= 2 \times PP - H \\
   S2 &= PP - \text{Range} \\
   S3 &= L - 2 \times (H - PP)

Fibonacci
~~~~~~~~~

Uses the Classic PP as the anchor but scales the levels by Fibonacci ratios
(0.382, 0.618, 1.000).

.. math::

   FIB\_R1 &= PP + 0.382 \times \text{Range} \\
   FIB\_R2 &= PP + 0.618 \times \text{Range} \\
   FIB\_R3 &= PP + 1.000 \times \text{Range} \\
   FIB\_S1 &= PP - 0.382 \times \text{Range} \\
   FIB\_S2 &= PP - 0.618 \times \text{Range} \\
   FIB\_S3 &= PP - 1.000 \times \text{Range}

Woodie
~~~~~~

Gives extra weight to the close; the pivot formula differs from Classic.

.. math::

   PP\_W &= \frac{H + L + 2C}{4} \\
   WD\_R1 &= 2 \times PP\_W - L \\
   WD\_R2 &= PP\_W + \text{Range} \\
   WD\_S1 &= 2 \times PP\_W - H \\
   WD\_S2 &= PP\_W - \text{Range}

Camarilla
~~~~~~~~~

Camarilla levels are tightly clustered around the *previous day's closing
price* — **not** a pivot average.  This is the mathematically correct
formulation; many implementations incorrectly use the Classic PP as the anchor.

.. math::

   P\_CAM &= C \quad (\text{previous-day close — the true Camarilla anchor}) \\
   CAM\_R1 &= C + \text{Range} \times \frac{1.1}{12} \\
   CAM\_R2 &= C + \text{Range} \times \frac{1.1}{6} \\
   CAM\_R3 &= C + \text{Range} \times \frac{1.1}{4} \\
   CAM\_R4 &= C + \text{Range} \times \frac{1.1}{2} \\
   CAM\_S1 &= C - \text{Range} \times \frac{1.1}{12} \\
   CAM\_S2 &= C - \text{Range} \times \frac{1.1}{6} \\
   CAM\_S3 &= C - \text{Range} \times \frac{1.1}{4} \\
   CAM\_S4 &= C - \text{Range} \times \frac{1.1}{2}

.. important::

   The Camarilla anchor ``P_CAM`` equals the **previous-day close**, not the
   arithmetic mean of H, L, and C.  This was corrected in v2 (``BUG-E6``).
   If you computed pivots with an earlier build, re-run
   **Compute Pivot Points** to regenerate the correct values.

----

The Pivot Matrix Table
-----------------------

The consolidated matrix shows all four methods side by side for the selected
symbols and date.

**Reading the table:**

- Each **column group** is one pivot method (colour-coded header).
- Each **sub-column** within a group is one symbol.
- Rows are sorted from highest resistance (R3/R4) down through the pivot
  point (PP) to the deepest support (S3/S4).
- Resistance rows are tinted red; support rows are tinted green; the PP row
  is neutral.
- ``—`` means the level is not defined for that method (e.g. Woodie only has
  R1/R2 and S1/S2).

**Controls above the table:**

- **Session date** — select which trading day's pivots to display.  Defaults
  to the most recent date in the loaded year.
- **Symbols** — multiselect; adds columns to the matrix.
- **Methods** — choose which of the four methods to include.
- **Number of levels** — cap R/S levels at 1, 2, 3, or 4 (Camarilla).

----

Editable Pivot Values
---------------------

Any cell in the matrix can be overridden inline before the chart is drawn.
This allows you to adjust a level if you have additional context (e.g. a
significant gap-fill level) and immediately see the updated horizontal line
on the chart.

To reset, reload the page or click **Recompute**.

----

Price Chart with Pivot Levels
------------------------------

The **Overlay pivot levels on price chart** checkbox (checked by default)
draws all selected pivot levels as horizontal lines across the date range:

- Dashed lines — pivot points (PP)
- Dotted lines — resistance levels (Rn) in progressively lighter shades
- Dotted lines — support levels (Sn) in progressively lighter shades

Each method has a distinct colour family (Classic: indigo, Fibonacci: teal,
Woodie: amber, Camarilla: rose) so lines from different methods remain
visually distinct even when all four are shown simultaneously.

----

Full Data Table
---------------

At the bottom of the tab the **Show full pivot data table** checkbox expands
a raw ``st.dataframe`` widget showing the underlying pivot rows for the
selected symbols and date range.  This is useful for verifying computed values
or preparing a manual export.

----

Computing / Recomputing Pivot Points
--------------------------------------

Pivots are computed separately from the download step.  After downloading EOD
data for a year, click **Compute Pivot Points** in the sidebar to generate
``pivots_output<year>.csv``.

This step must be re-run if:

- You re-downloaded EOD data with *Force re-download*.
- You updated from v1 (which used an incorrect Camarilla anchor).
- The pivot CSV is missing or corrupt.

The computation is fast — a full year of all NSE equity symbols typically
takes under five seconds on modern hardware, courtesy of the Polars vectorised
pipeline.
