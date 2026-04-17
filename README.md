# Denmark Migration Explorer

An interactive Streamlit app for exploring immigration and emigration patterns across Denmark from 2020 to 2025.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://attraction.streamlit.app)

## What it does

- Visualises yearly immigration, emigration, and net migration as a mirrored bar chart
- Filter by **geographic scope**: all of Denmark, a specific region, or an individual kommune
- Filter by **citizenship**: all countries, a single country, or grouped by EU membership, continent, G7/G20, Global North/South, and more
- Summary table with colour-coded values for quick reading

## Data source

Data comes from [Statistics Denmark (Danmarks Statistik)](https://www.statistikbanken.dk/) via their open API:

- **VAN1AAR** — immigration by kommune, citizenship, sex, age, and year
- **VAN2AAR** — emigration by kommune, citizenship, sex, age, and year

The pre-fetched CSV files (`immigration.csv`, `emigration.csv`) are included in this repo. To refresh the data, run:

```bash
python fetch_migration.py
```

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploying to Streamlit Cloud

1. Fork or push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set the main file path to `app.py`
4. Deploy — no extra configuration needed

## Project structure

```
app.py               # Streamlit app
groups.py            # Region and citizenship group definitions
fetch_migration.py   # Script to re-fetch data from Statistics Denmark API
immigration.csv      # Pre-fetched immigration data (2020–2025)
emigration.csv       # Pre-fetched emigration data (2020–2025)
requirements.txt     # Python dependencies
```
