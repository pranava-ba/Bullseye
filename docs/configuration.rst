.. _configuration:

Configuration
=============

All tuneable constants live at the top of ``EoD_module.py``.  Edit them
directly in the source file; no external config file is required.

----

Download Behaviour
------------------

.. list-table::
   :widths: 30 15 55
   :header-rows: 1

   * - Constant
     - Default
     - Description
   * - ``_MAX_RETRIES``
     - ``3``
     - Maximum download attempts per date before the date is skipped.
   * - ``_RETRY_DELAYS``
     - ``(2, 4, 8)``
     - Seconds to wait between successive retry attempts (exponential
       backoff).
   * - ``_PRIME_INTERVAL``
     - ``300``
     - Seconds between automatic session re-primes during a long download.
       A prime also triggers immediately on any ``403`` response.
   * - ``max_workers`` *(parameter)*
     - ``4``
     - Number of parallel download threads.  Pass to ``download_year_data()``
       as a keyword argument.  Values above ``6`` risk sustained ``403``
       blocks from NSE.

Auto-Update
-----------

.. list-table::
   :widths: 30 15 55
   :header-rows: 1

   * - Constant
     - Default
     - Description
   * - ``AUTO_UPDATE_DEFAULT``
     - ``False``
     - Whether the auto-update toggle is on when the app first opens.
       Read by ``app_v2.py`` to initialise the sidebar widget; do not
       hard-code ``True`` in the UI.

Logging
-------

The log is written to ``bullseye.log``:

- **Development mode** — same directory as the Python files.
- **Windows .exe** — ``%APPDATA%\BullseyeFintech\NSE_Dashboard\bullseye.log``

Log level is ``INFO`` by default.  To enable debug output, change
``logging.INFO`` to ``logging.DEBUG`` in the ``logging.basicConfig`` call near
the top of ``EoD_module.py``.

HTTP Headers
------------

The ``_HEADERS`` dict in ``EoD_module.py`` controls the ``User-Agent`` and
other request headers sent to NSE.  The current defaults mimic a real Chrome
browser on Windows 10.  If NSE changes its bot-detection heuristics you may
need to update this string.

.. code-block:: python

   _HEADERS = {
       "User-Agent": (
           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
           "AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/124.0.0.0 Safari/537.36"
       ),
       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
       "Accept-Language": "en-US,en;q=0.5",
       "Referer": "https://www.nseindia.com/",
   }
