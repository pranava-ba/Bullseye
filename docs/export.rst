.. _export:

Exporting Data
==============

The dashboard provides both sidebar quick-export buttons and a programmatic
API for filtered downloads.

----

Sidebar Quick Export
--------------------

With a year loaded, the sidebar shows two download buttons:

- **⬇ Download EOD <year>** — the full ``EOD_DATA_FOR_ANALYSIS_<year>.csv``
  as a browser download.
- **⬇ Download Pivots <year>** — the full ``pivots_output<year>.csv``.

These are served in-memory by ``get_eod_csv_bytes()`` and
``get_pivot_csv_bytes()`` and passed directly to Streamlit's
``st.download_button``.

----

Programmatic / Filtered Export
-------------------------------

Two helpers in ``EoD_module.py`` allow filtered CSV exports from code:

``get_filtered_eod_bytes()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from EoD_module import get_filtered_eod_bytes

   data = get_filtered_eod_bytes(
       year=2025,
       symbols=["RELIANCE", "TCS", "INFY"],
       categories=["EQ"],
       date_from="2025-01-01",
       date_to="2025-03-31",
   )

   if data:
       with open("filtered_eod.csv", "wb") as f:
           f.write(data)

All parameters are optional.  Pass ``None`` to skip a particular filter.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Parameter
     - Description
   * - ``year``
     - Calendar year to load from disk.
   * - ``symbols``
     - List of ``SYMBOL`` values to include.  ``None`` = all symbols.
   * - ``categories``
     - List of ``CATEGORY`` values.  ``None`` = all categories.
   * - ``date_from``
     - Inclusive lower bound as ``"YYYY-MM-DD"``.  ``None`` = no lower bound.
   * - ``date_to``
     - Inclusive upper bound as ``"YYYY-MM-DD"``.  ``None`` = no upper bound.

Returns ``bytes`` (CSV), or ``None`` if the EOD file for that year does not
exist on disk.

``get_filtered_pivot_bytes()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from EoD_module import get_filtered_pivot_bytes

   data = get_filtered_pivot_bytes(
       year=2025,
       symbols=["RELIANCE"],
       date="2025-03-28",
   )

   if data:
       with open("pivots_filtered.csv", "wb") as f:
           f.write(data)

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Parameter
     - Description
   * - ``year``
     - Calendar year to load from disk.
   * - ``symbols``
     - List of ``SYMBOL`` values.  ``None`` = all symbols.
   * - ``date``
     - Exact date as ``"YYYY-MM-DD"``.  ``None`` = all dates.

Returns ``bytes`` (CSV), or ``None`` if the pivot file does not exist.

----

Column Schemas
--------------

See :ref:`column_schema` for a full description of every column in both the
EOD and pivot CSV files.
