# Denmark Migration Explorer

An interactive Streamlit app for exploring immigration and emigration patterns across Denmark from 2020 onwards.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://attraction.streamlit.app)

## What it does

- Visualises yearly immigration, emigration, and net migration as a mirrored bar chart
- Filter by **geographic scope**: all of Denmark, a specific region, or an individual kommune
- Filter by **citizenship**: all countries, a single country, or grouped by EU membership, continent, G7/G20, Global North/South, and more
- Summary table with colour-coded values for quick reading

## Data sources

Data comes from [Statistics Denmark (Danmarks Statistik)](https://www.statistikbanken.dk/) via their open API:

| Dataset | Contents |
|---------|----------|
| VAN1AAR | Immigration by kommune, citizenship, sex, age, year |
| VAN2AAR | Emigration by kommune, citizenship, sex, age, year |
| FOLK1B  | Population by municipality, citizenship, year (Q1 snapshots) |
| FOLK1D  | Working-age (15–64) population by municipality, Danish/Foreign, year (Q1 snapshots) |

Pre-fetched CSV files are included in this repo and refreshed automatically each quarter (see below).

## Quarterly automation

A GitHub Actions workflow runs on the **1st of January, April, July, and October** at 06:00 UTC. It:

1. Pulls the latest data from all four Statbank datasets
2. Commits updated CSVs back to this repo (which triggers a Streamlit Cloud redeploy)
3. Runs a quarterly analysis and sends a summary to Slack covering:
   - Net migration total vs the same period last year
   - Top 5 nationalities by net inflow and any net outflows
   - Biggest year-on-year shifts by nationality
   - Working-age foreign population total and % change
   - Which municipality saw the biggest shift in foreign working-age share

To trigger a manual run: **Actions → Quarterly data refresh → Run workflow**.

To refresh data locally:

```bash
python fetch_migration.py   # VAN1AAR + VAN2AAR
python fetch_population.py  # FOLK1B + FOLK1D
```

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```
app.py                        # Streamlit app
groups.py                     # Region and citizenship group definitions
fetch_migration.py            # Fetches VAN1AAR + VAN2AAR from Statbank
fetch_population.py           # Fetches FOLK1B + FOLK1D from Statbank
quarterly_report.py           # Quarterly analysis and Slack notification
immigration.csv               # Immigration data (VAN1AAR)
emigration.csv                # Emigration data (VAN2AAR)
population_by_nationality.csv # Population by municipality and citizenship (FOLK1B)
working_age_by_status.csv     # Working-age population, Danish vs foreign (FOLK1D)
requirements.txt              # Python dependencies
.github/workflows/
  quarterly-refresh.yml       # Scheduled data refresh and Slack notification
```

## Deploying to Streamlit Cloud

1. Fork or push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set the main file path to `app.py`
4. Deploy — no extra configuration needed

For the quarterly Slack notification, add a `SLACK_WEBHOOK` secret to the repo under **Settings → Secrets and variables → Actions**.
