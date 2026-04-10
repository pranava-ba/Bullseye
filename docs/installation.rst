.. _installation:

Installation
============

Prerequisites
-------------

- **Python 3.10** or higher
- ``pip`` (bundled with Python)
- Internet access for the initial data download
  (the dashboard works fully offline once data is on disk)

.. tip::

   On Windows you can skip the Python setup entirely and use the pre-built
   ``.exe`` — see :ref:`windows-exe` below.

From Source
-----------

1. Clone the repository
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/your-org/bullseye-nse-eod.git
   cd bullseye-nse-eod

2. Install dependencies
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install streamlit polars pandas plotly requests pandas-market-calendars

Or, if a ``requirements.txt`` is provided:

.. code-block:: bash

   pip install -r requirements.txt

The exact library versions the dashboard was developed and tested against:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Library
     - Minimum version
   * - ``streamlit``
     - 1.30
   * - ``polars``
     - 0.20
   * - ``pandas``
     - 2.0
   * - ``plotly``
     - 5.0
   * - ``requests``
     - 2.28
   * - ``pandas-market-calendars``
     - 4.3
   * - ``numpy``
     - 1.24

3. Run the dashboard
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   streamlit run app_v2.py

The dashboard opens in your browser at ``http://localhost:8501``.

----

.. _windows-exe:

Windows Executable
------------------

A pre-built ``.exe`` is available for Windows users who prefer not to manage
a Python environment.  It was packaged with **PyInstaller** and wrapped with
**Inno Setup**.

- Double-click the installer and follow the wizard.
- On first launch the dashboard creates a data folder at
  ``%APPDATA%\BullseyeFintech\NSE_Dashboard\data\``
- Log files are written to
  ``%APPDATA%\BullseyeFintech\NSE_Dashboard\bullseye.log``

.. note::

   The executable embeds Python and all dependencies.  No separate Python
   installation is required.

----

Directory Layout (Source)
--------------------------

After cloning, the project root looks like this:

.. code-block:: text

   bullseye-nse-eod/
   ├── app_v2.py              ← Streamlit UI
   ├── EoD_module.py          ← Core download + pivot engine
   ├── requirements.txt
   └── data/                  ← Created automatically on first run
       ├── EOD_DATA_FOR_ANALYSIS_<year>.csv
       ├── pivots_output<year>.csv
       ├── CUE_DATE_<year>.csv
       └── nse_eod_data_files/<year>/
