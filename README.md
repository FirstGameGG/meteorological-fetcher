# Thailand Meteorological Analyzer

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.56.0-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-3.0.2-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-6.6.0-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/python/)
[![Meteostat](https://img.shields.io/badge/Meteostat-2.1.4-0055A4)](https://dev.meteostat.net/python/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Interactive Streamlit app for Thailand weather analysis using Meteostat station data and NOAA ONI index.

## Highlights

- Region-based station selection (map color matching)
- Parallel station fetch with retry and nearest-station fallback
- Automated cleaning, interpolation, and monthly aggregation
- ONI merge + El Niño/La Niña intensity classification
- Interactive charts and CSV/Excel export

## Project Structure

```text
.
├── app.py               # Streamlit entrypoint and app flow
├── weather_fetcher.py   # Station loading + Meteostat/ONI fetching
├── data_processing.py   # Cleaning, aggregation, ONI labels, exports
├── ui_components.py     # Reusable UI blocks
├── stations.json        # Thailand station metadata
└── assets/              # UI assets
```

## Quick Start

```bash
# 1) Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Launch app
streamlit run app.py
```

## Data Pipeline

```mermaid
flowchart LR
    A[User input: regions + date range] --> B[Load stations.json]
    B --> C[Filter stations by region]
    C --> D[Parallel Meteostat fetch]
    D --> E[Normalize and clean raw data]
    E --> F[Interpolate missing weather values]
    F --> G[Daily and monthly aggregation]
    G --> H[Merge NOAA ONI index]
    H --> I[Classify ONI intensity]
    I --> J[Render charts + export CSV/Excel]
```

## Aggregation Output (Monthly)

| Field | Meaning |
|---|---|
| `temp_mean` | Mean monthly temperature |
| `tmax_max` | Monthly maximum of daily max temperature |
| `tmin_min` | Monthly minimum of daily min temperature |
| `rhum_mean` | Mean monthly relative humidity |
| `wspd_mean` | Mean monthly wind speed |
| `pres_mean` | Mean monthly pressure |
| `prcp_sum` | Total monthly precipitation |
| `rainy_days` | Count of days with `prcp > 0.5` |
| `ONI_Index` | NOAA ONI value for that month |
| `ONI_Category` | Neutral / Weak / Moderate / Strong / Very Strong |

## Notes

- `stations.json` must exist at repository root.
- External services (Meteostat and NOAA) are required for full functionality.

## Troubleshooting

```bash
# If dependencies break, recreate environment cleanly
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Missing stations file: add a valid `stations.json` at project root.
- Frequent timeouts/fetch failures: reduce date range and retry.

## License

MIT
