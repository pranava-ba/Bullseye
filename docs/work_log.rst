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
   * - Read The Docs
     - 1.5–2.0
     - Hosted the docs and created a new readme. 
   
**Total: 19.0–20.5 hours**

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
     - 01-04-2026
   * - Performance
     - Lag when applying slicers on large datasets
     - Implemented lazy loading + "Load Data" button
     - 01-04-2026
   * - Data Processing
     - Pandas slow + rate limits
     - Switched to Polars (< 2 min runtime) + added error logs
     - 01-04-2026
   * - Pivot
     - Values not displayed
     - Fixed column naming mismatch
     - 01-04-2026
   * - Pivot
     - Values not adjustable
     - Added slider + editable defaults
     - 02-04-2026
   * - Tables
     - Multiple fragmented tables with blanks
     - Merged into single comparison table + colour coding
     - 02-04-2026
   * - UI
     - Date picker only numeric
     - Added calendar-based date selection
     - 02-04-2026
   * - Storage
     - Large data accumulation
     - Added deletion/cleanup buttons
     - 02-04-2026
   * - Data Integrity
     - Missing/spotty data
     - Added manual override for specific years
     - 02-04-2026
   * - EXE
     - Recursive terminal opening
     - Fixed pathing issue
     - 02-04-2026
   * - Streamlit
     - App not running (main thread error)
     - Patched threading issue
     - 02-04-2026
   * - Hosting
     - Localhost not found
     - Fixed spec file module recognition
     - 02-04-2026
   * - Build
     - EXE crashes due to dependency conflicts
     - Resolved ``launcher.py`` issues
     - 03-04-2026
   * - Stability
     - Fragile to multiple clicks
     - Improved robustness using Claude suggestions
     - 03-04-2026
   * - UX
     - No progress visibility
     - Added progress bar + sticky logs
     - 03-04-2026
   * - UI Theme
     - Dark theme not preferred
     - Rebuilt full light theme
     - 03-04-2026
   * - UI Bug
     - Theme toggle caused errors
     - Replaced toggle with radio button
     - 03-04-2026
   * - UI Bug
     - Pivot edit overlap with keyboard
     - Fixed using inline CSS + sticky layout
     - 03-04-2026
   * - Deployment
     - Need updated deliverables
     - Rebuilt EXE + updated GitHub + releases
     - 03-04-2026
   * - Documentation
     - Needed structured tracking
     - Created MD work log
     - 03-04-2026
   * - Pivot Value Error
     - Blunder in editing pivot values
     - Only Fibonacci and Camarilla can be updated; Classic and Woodie
       are read-only
     - 03-04-2026
   * - UI Theme
     - Font size small, readability poor
     - Theme updated to have larger font
     - 03-04-2026
   * - Documentation
     - Lack of Documentation
     - Hosted read the docs
     - 10-04-2026
