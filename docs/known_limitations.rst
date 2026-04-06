.. _known_limitations:

Known Limitations
=================

NSE Rate Limiting
-----------------

Very high ``max_workers`` values (above 6) may trigger sustained ``403``
responses from NSE's archive server.  The default of 4 is conservative and
reliable.  If you need faster downloads on a very fast connection, try 5 and
monitor the progress log for 403s.

Current Year Data
-----------------

Only trading dates up to and including today are downloaded.  Future dates in
the current calendar year are automatically skipped before any HTTP requests
are made.  This means a download of the current year will be incomplete until
the year ends — use incremental mode or auto-update to keep it current.

Historical Data Availability
-----------------------------

NSE's public bhavcopy archive is generally complete from around 2000 onward.
Data for years prior to 2000 may be missing, partial, or in a different format
that the parser does not handle.

Network Dependency for Downloads
---------------------------------

The application requires internet access to download data.  All analysis
features — charts, pivot computation, export — work fully offline once data is
on disk.  The auto-update feature is the only feature that requires a
connection at runtime (and it is off by default).

Polars / Pandas Version Sensitivity
-------------------------------------

The data pipeline targets Polars ≥ 0.20 and Pandas ≥ 2.0.  Older versions
may cause ``AttributeError`` or schema inference errors.  If you see
unexpected errors after a library upgrade, check the ``requirements.txt``
pinned versions.

Windows Signal Handler (PyInstaller)
--------------------------------------

The pre-built Windows ``.exe`` uses a custom PyInstaller runtime hook to
suppress a threading-related signal-handler crash that Streamlit triggers in
frozen mode.  If you build your own ``.exe``, ensure this hook is included
in your ``spec`` file.

Pivot CSV Requires Re-Computation After EOD Re-Download
-------------------------------------------------------

The pivot CSV is not automatically regenerated when EOD data is re-downloaded.
If you use *Force re-download*, click **Compute Pivot Points** afterward to
ensure the pivot file reflects the updated EOD data.
