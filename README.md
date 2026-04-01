<div align="center">

<br/>

```
██████╗ ██╗   ██╗██╗     ██╗     ███████╗███████╗██╗   ██╗███████╗
██╔══██╗██║   ██║██║     ██║     ██╔════╝██╔════╝╚██╗ ██╔╝██╔════╝
██████╔╝██║   ██║██║     ██║     ███████╗█████╗   ╚████╔╝ █████╗  
██╔══██╗██║   ██║██║     ██║     ╚════██║██╔══╝    ╚██╔╝  ██╔══╝  
██████╔╝╚██████╔╝███████╗███████╗███████║███████╗   ██║   ███████╗
╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝╚══════╝   ╚═╝   ╚══════╝
```

### NSE End-of-Day Dashboard

**Bullseye Fintech © 2024–2026**

---

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Polars](https://img.shields.io/badge/Polars-DataFrame-CD792C?style=flat-square)](https://pola.rs)
[![NSE](https://img.shields.io/badge/Data-NSE%20India-0055A5?style=flat-square)](https://nseindia.com)
[![License](https://img.shields.io/badge/License-Proprietary-8B949E?style=flat-square)](LICENSE)

*Download · Analyse · Pivot — all your NSE equity data, locally.*

</div>

---

## What is this?

The **Bullseye NSE EOD Dashboard** is a desktop-grade Streamlit application that downloads, processes, and visualises National Stock Exchange of India (NSE) end-of-day bhavcopy data. It runs entirely on your machine — no cloud accounts, no subscriptions, no data leaving your system.

You can pull any year of NSE equity data back to 2000, browse OHLCV price history with interactive charts, and instantly compute **four pivot-point methodologies** (Classic, Fibonacci, Woodie, Camarilla) for every symbol in the dataset.

---

## Screenshots

> *Dark-terminal aesthetic · IBM Plex typography · GitHub-dark colour palette*

| OHLCV Chart View | Pivot Point Matrix |
|---|---|
| Candlestick / OHLC / Line charts with MA and Bollinger Band overlays | Consolidated R/S table across all four pivot methods side-by-side |

---

## Feature Highlights

### 📥 Data Acquisition
- Downloads NSE bhavcopy (PR) ZIP archives directly from `archives.nseindia.com`
- **Parallel downloads** via `ThreadPoolExecutor` — 4 workers by default
- **Session cookie priming** before bulk requests, with automatic re-prime on HTTP 403
- **Exponential backoff** retry logic (3 attempts, 2 / 4 / 8 s delays)
- Gracefully skips 404s (holidays, non-trading dates) and future dates
- Handles both legacy 2-digit year filenames (`pd300326.csv`) and modern 4-digit year filenames (`pd31122025.csv`) introduced by NSE in recent archives

### 🔄 Download Modes
| Mode | Description |
|---|---|
| **Single Year** | Download one calendar year in full |
| **Multiple Years** | Select any combination of years |
| **Date Range** | Pick a from/to date — all spanning years are downloaded automatically |
| **All Downloaded** | Re-process every year already on disk |

All modes support:
- `Force re-download` — overwrite existing data
- `Incremental` — append only new trading dates, skipping what's already saved

### 📊 OHLCV Analysis
- **Chart types** — Candlestick, OHLC Bar, Line (Close)
- **Overlays** — Volume (colour-coded green/red), 20-Day MA, 50-Day MA, Bollinger Bands (±2σ)
- **KPI cards** — Open, High, Low, Close, Prev Close, Volume with delta and percentage change
- **52-Week range bar** — visual gradient bar with live marker showing current position
- Multi-symbol selection with per-symbol detail view
- Quick date presets: Last 30 days, Last 90 days, Last 6 months, YTD, Full year

### 🎯 Pivot Points
Four methodologies computed daily for every symbol:

| Method | Pivot Formula | Levels |
|---|---|---|
| **Classic** | (H + L + C) / 3 | R1–R3, S1–S3 |
| **Fibonacci** | Classic PP ± 0.382 / 0.618 / 1.000 × Range | R1–R3, S1–S3 |
| **Woodie** | (H + L + 2C) / 4 | R1–R2, S1–S2 |
| **Camarilla** | Prev Close ± Range × 1.1 / (12, 6, 4, 2) | R1–R4, S1–S4 |

> **Note on Camarilla:** The anchor is the **previous day's close** (`P_CAM`), not the classic pivot average — this is the mathematically correct formulation, correcting a common implementation error.

- Consolidated multi-symbol, multi-method pivot matrix in a single colour-coded table
- **Editable pivot values** — override any computed level inline before charting
- Price chart overlay — all pivot levels drawn as horizontal lines across the date range
- Filterable by session date, symbol, and method

### 💾 Export
- Download EOD CSV or Pivot CSV for any loaded year directly from the sidebar
- Filtered exports via `get_filtered_eod_bytes()` and `get_filtered_pivot_bytes()` (programmatic API)

### 🔁 Auto-Update
- Optional toggle (off by default) — fetches previous trading day's data on launch
- **Holiday-aware**: consults the NSE trading calendar (`CUE_DATE_<year>.csv`) before deciding whether an update is needed — won't trigger on NSE holidays
- Uses incremental mode so only genuinely missing dates are fetched

---

## Architecture

```
bullseye-nse-eod/
│
├── app_v2.py            ← Streamlit UI — all pages, charts, filters, sidebar
├── EoD_module.py        ← Core engine — download, process, pivot, helpers
│
├── data/                ← Created automatically on first run
│   ├── EOD_DATA_FOR_ANALYSIS_<year>.csv    ← Consolidated OHLCV per year
│   ├── pivots_output<year>.csv             ← Computed pivot points per year
│   ├── CUE_DATE_<year>.csv                 ← NSE trading calendar cache
│   └── nse_eod_data_files/<year>/          ← Per-year temp extraction folder
│
└── bullseye.log         ← Rotating log file (APPDATA on Windows, local otherwise)
```

### Data Flow

```
NSE Archives (HTTPS)
        │
        ▼
  _prime_session()          ← Acquire session cookie
        │
        ▼
  ThreadPoolExecutor        ← Parallel bhavcopy ZIP downloads
        │
        ▼
  _download_one()           ← Retry / backoff / 403 recovery / 404 skip
        │
        ▼
  zipfile extract           ← 4-digit & 2-digit year filename patterns
        │
        ▼
  process_file()            ← pandas parse → Polars DataFrame
        │
        ▼
  pl.concat + deduplicate   ← Atomic CSV write (.tmp → os.replace)
        │
        ▼
  EOD_DATA_FOR_ANALYSIS_<year>.csv
        │
        ▼
  compute_pivot_points()    ← Polars vectorised pivot computation
        │
        ▼
  pivots_output<year>.csv
        │
        ▼
  app_v2.py (Streamlit)     ← Charts, KPIs, pivot matrix, filters
```

---

## Tech Stack

| Component | Library | Purpose |
|---|---|---|
| UI framework | [Streamlit](https://streamlit.io) | Web dashboard |
| Data engine | [Polars](https://pola.rs) | Fast DataFrame processing (vectorised pivots, CSV I/O) |
| Data parsing | [pandas](https://pandas.pydata.org) | NSE bhavcopy format parsing (complex category-row structure) |
| Charts | [Plotly](https://plotly.com/python/) | Interactive OHLCV and pivot charts |
| HTTP | [requests](https://requests.readthedocs.io) | Bhavcopy archive downloads with session management |
| Calendar | [pandas-market-calendars](https://github.com/rsheftel/pandas_market_calendars) | NSE holiday-aware trading day lookup |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` | Parallel date downloads |

---

## Installation

### Prerequisites
- Python 3.10 or higher
- pip

### 1. Clone the repository

```bash
git clone https://github.com/your-org/bullseye-nse-eod.git
cd bullseye-nse-eod
```

### 2. Install dependencies

```bash
pip install streamlit polars pandas plotly requests pandas-market-calendars
```

Or with a requirements file (if provided):

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app_v2.py
```

The dashboard will open in your browser at `http://localhost:8501`.

> **Windows users:** If you downloaded the pre-built `.exe`, simply double-click it. Data is stored in `%APPDATA%\BullseyeFintech\NSE_Dashboard\data\`.

---

## Quick Start

1. Open the **sidebar** (≡ top-left)
2. Under **Download from NSE**, select `Single Year` and choose a year
3. Click **🚀 Start Download** — progress is shown in real time
4. Once complete, click the year badge under **Available years** to load it
5. Use the **Filters** bar to pick a category, symbol, and date range
6. Switch between the **OHLCV Summary** and **Pivot Points** tabs

---

## Data Notes

### Source
All data is fetched from NSE's public bhavcopy archive:
```
https://archives.nseindia.com/archives/equities/bhavcopy/pr/PR<DDMMYY>.zip
```
Each ZIP contains a daily equity delivery file (`Pd<DDMMYY>.csv`) with OHLCV data for every listed security.

### File Encoding
NSE bhavcopy files use **latin-1 / cp1252** encoding, not UTF-8. The application handles this automatically — any `UnicodeDecodeError` silently falls back to `latin-1`.

### Categories
NSE PD files use a nested structure where category headings (e.g. `NIFTY 50`, `EQ`, `BE`) appear inline as separator rows. The parser reconstructs a `CATEGORY` column for every data row from this structure.

### Column Schema
All column names are defined as constants in the `Col` class inside `EoD_module.py` — a single source of truth used by both the engine and the UI, eliminating hardcoded string mismatches.

---

## Configuration

| Constant | Default | Description |
|---|---|---|
| `AUTO_UPDATE_DEFAULT` | `False` | Whether auto-update runs on launch |
| `_MAX_RETRIES` | `3` | Download retry attempts per date |
| `_RETRY_DELAYS` | `(2, 4, 8)` | Backoff delays in seconds |
| `_PRIME_INTERVAL` | `300` | Session re-prime interval in seconds |
| `max_workers` | `4` | Parallel download thread count |

---

## Known Limitations

- **NSE rate limiting** — very high `max_workers` values (> 6) may trigger 403 responses. The default of 4 is conservative and reliable.
- **Current year data** — only trading dates up to today are downloaded. Future dates in the current year are automatically skipped.
- **Network dependency** — the app requires internet access for downloads. Once data is on disk, all analysis features work fully offline.
- **NSE archive availability** — historical data prior to ~2000 may be incomplete or unavailable on NSE's servers.

---

## Changelog

### v2 (current)
- Full Polars pipeline replacing pandas in all processing and pivot computation
- Parallel downloads with `ThreadPoolExecutor`
- NSE session cookie priming and exponential backoff retry
- Holiday-aware auto-update using `pandas_market_calendars`
- Atomic CSV writes (`.tmp` → `os.replace`)
- Per-year temp directories eliminating cross-year file contamination
- 4-digit year filename support for modern NSE archives
- Incremental download mode (append-only)
- Corrected Camarilla pivot anchor (`P_CAM` = previous-day close)
- `Col` dataclass as shared column-name schema
- Date filter calendar now navigable to any year from 2000 onward
- UTF-8 / latin-1 encoding fallback for NSE CSV files

---

## License

Proprietary — Bullseye Fintech © 2024–2026. All rights reserved.  
See [LICENSE](LICENSE) for full terms.

---

<div align="center">

*Built with 📈 for serious NSE traders and quant researchers.*

**Bullseye Fintech** · Chennai, India

</div>
