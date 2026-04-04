# Thailand Meteorological Analyzer

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.56.0-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-3.0.2-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-6.6.0-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/python/)
[![Meteostat](https://img.shields.io/badge/Meteostat-2.1.4-0055A4)](https://dev.meteostat.net/python/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Streamlit app for Thailand weather analysis using Meteostat station data and NOAA ONI index.

## What It Does

- Region-based station selection (color-matched with map)
- Parallel weather fetching with retry and nearest-station fallback
- Data cleaning and monthly aggregation
- ONI merge and event classification
- Interactive map/charts and CSV/Excel export

## Project Layout

- app.py: App entry point and page flow
- weather_fetcher.py: Station loading, Meteostat/ONI fetching, parallel fetch logic
- data_processing.py: Cleaning, monthly aggregation, ONI labeling, Excel export
- ui_components.py: Reusable Streamlit UI components
- stations.json: Station metadata source

## Data Processing Pipeline (Detailed)

1. Input validation
- Ensure at least one region is selected.
- Ensure `start_date <= end_date`.
- If end date is in the future, clamp it to today.

2. Station filtering
- Load station metadata from `stations.json`.
- Filter stations by selected regions.

3. Parallel weather fetch
- Fetch each station in parallel using `ThreadPoolExecutor`.
- For each station, try primary WMO fetch with retries and exponential backoff.
- If primary fetch fails or returns empty, resolve nearest station by lat/lon and retry.
- Capture fetch status per station (`success`, `timeout`, `empty`, `exception`) for diagnostics.

4. Raw frame normalization
- Concatenate all successful station dataframes.
- Drop unsupported/unused columns (`snow`, `wpgt`, `tsun`) when present.
- Reset index and normalize time column to `date`.
- Coerce `date` to datetime and drop invalid rows.

5. Missing-value handling and interpolation
- Convert weather columns to numeric: `temp`, `tmin`, `tmax`, `rhum`, `pres`, `wspd`, `prcp`.
- Fill missing precipitation (`prcp`) with `0`.
- For each station (`wmo_id`), interpolate the core weather columns linearly with a capped gap limit.

6. Aggregation logic
- Daily aggregation (across stations by date): mean for temperature, humidity, pressure, wind, and precipitation.
- Monthly aggregation (from daily):
   - `temp_mean`: monthly mean temperature
   - `tmax_max`: monthly max of daily max temperature
   - `tmin_min`: monthly min of daily min temperature
   - `rhum_mean`, `wspd_mean`, `pres_mean`: monthly means
   - `prcp_sum`: monthly precipitation sum
   - `rainy_days`: count of days where `prcp > 0.5`
- Backfill remaining gaps and cast period key to string (`year_month`).

7. ONI integration and labeling
- Fetch ONI table from NOAA and normalize to `year_month` + `ONI_Index`.
- Left-join ONI into monthly weather data.
- Classify ONI intensity into labels (Neutral / Weak / Moderate / Strong / Very Strong).

8. Output and delivery
- Render map, monthly chart, station logs, and summary table.
- Enable CSV and Excel export from the final monthly dataframe.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- `stations.json` is required at project root.
- App depends on external APIs (Meteostat and NOAA) availability.

## Troubleshooting

- `stations.json` missing: place a valid file at project root.
- Too many fetch failures/timeouts: narrow date range and retry.
- Broken local `streamlit` in venv: recreate venv and reinstall requirements.

## License

MIT
