.. _work_log:

Project Work Log
================

This page records the total effort and iterative improvements made during
development of Bullseye Fintech NSE EOD Dashboard v2.

----

Task Breakdown
--------------

.. list-table::
   :header-rows: 1
   :widths: 50 15 35

   * - Task
     - Time (hrs)
     - Tools Used
   * - Download and test ``EoD_Module``
     - 2.0
     - Python
   * - Fix the Pivot CSV
     - 1.5
     - Claude
   * - Create Streamlit Interface
     - 3.0
     - Claude
   * - Get support files (spec, requirements, iss)
     - 2.5
     - Inno Installer, PyInstaller
   * - Push files to Git & create repository
     - 1.0
     - GitHub Actions, Cursor IDE
   * - Create light theme (CSS & HTML)
     - 0.5
     - Claude
   * - Re-compile & update EXE + GitHub
     - 1.0
     - GitHub, Inno Installer
   * - Miscellaneous fixes & debugging
     - 5.5–6.0
     - Initially Qwen and Claude; later fully Claude

**Total: 17.0–17.5 hours**

----

Iterative Progress Log
----------------------

.. list-table::
   :header-rows: 1
   :widths: 18 34 34 14

   * - Category
     - Issue
     - Fix / Improvement
     - Date
   * - EoD Module
     - Failed due to hardcoded filename mismatch (case issue)
     - Used regex for dynamic file handling
     -
   * - Performance
     - Lag when applying slicers on large datasets
     - Implemented lazy loading + "Load Data" button
     -
   * - Data Processing
     - Pandas slow + rate limits
     - Switched to Polars (< 2 min runtime) + added error logs
     -
   * - Pivot
     - Values not displayed
     - Fixed column naming mismatch
     -
   * - Pivot
     - Values not adjustable
     - Added slider + editable defaults
     -
   * - Tables
     - Multiple fragmented tables with blanks
     - Merged into single comparison table + colour coding
     -
   * - UI
     - Date picker only numeric
     - Added calendar-based date selection
     -
   * - Storage
     - Large data accumulation
     - Added deletion/cleanup buttons
     -
   * - Data Integrity
     - Missing/spotty data
     - Added manual override for specific years
     -
   * - EXE
     - Recursive terminal opening
     - Fixed pathing issue
     -
   * - Streamlit
     - App not running (main thread error)
     - Patched threading issue
     -
   * - Hosting
     - Localhost not found
     - Fixed spec file module recognition
     -
   * - Build
     - EXE crashes due to dependency conflicts
     - Resolved ``launcher.py`` issues
     -
   * - Stability
     - Fragile to multiple clicks
     - Improved robustness using Claude suggestions
     -
   * - UX
     - No progress visibility
     - Added progress bar + sticky logs
     -
   * - UI Theme
     - Dark theme not preferred
     - Rebuilt full light theme
     -
   * - UI Bug
     - Theme toggle caused errors
     - Replaced toggle with radio button
     -
   * - UI Bug
     - Pivot edit overlap with keyboard
     - Fixed using inline CSS + sticky layout
     -
   * - Deployment
     - Need updated deliverables
     - Rebuilt EXE + updated GitHub + releases
     -
   * - Documentation
     - Needed structured tracking
     - Created MD work log
     -
   * - Pivot Value Error
     - Blunder in editing pivot values
     - Only Fibonacci and Camarilla can be updated; Classic and Woodie
       are read-only
     - 03-04-2026
   * - UI Theme
     - Font size small, readability poor
     - Theme updated to have larger font
     - 03-04-2026
