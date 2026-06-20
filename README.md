# Data in Denmark — Migration & Population Explorer

An interactive three-page Streamlit app for exploring immigration, emigration, and population patterns across Denmark.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://attraction.streamlit.app)

## Pages

**✈️ Migration Explorer** (home)
- Yearly immigration, emigration, and net migration as a mirrored bar chart (2020–present)
- Filter by geographic scope: all of Denmark, a specific region, or an individual kommune
- Filter by citizenship: individual country or grouped by EU membership, continent, G7/G20, Global North/South, and more
- Summary table with colour-coded values

**📊 Demographic Change**
- Working-age population (15–64) split between Danish and foreign citizens, quarterly from 2008 to present
- Trend line showing foreign share over time — seasonal dips reveal temporary worker patterns
- Stacked bar chart by year (K1 snapshots for comparability)
- Municipality rankings table with foreign share, year-on-year change, and seasonality index

**🔍 Population Explorer**
- Migration Explorer-style bar chart but for population stock, at quarterly resolution (2020–present)
- Filter by the same citizenship groups and geographic scope as the Migration Explorer
- Green/red dots on each bar show whether the quarter is up or down vs the same quarter last year — useful for spotting seasonal construction workers and students
- Summary table per quarter

## Data sources

All data from [Statistics Denmark (Danmarks Statistik)](https://www.statistikbanken.dk/) via their open API:

| Dataset | Contents | Granularity |
|---------|----------|-------------|
| VAN1AAR | Immigration by kommune, citizenship, sex, age | Annual |
| VAN2AAR | Emigration by kommune, citizenship, sex, age | Annual |
| FOLK1B  | Total population by municipality, citizenship | K1 annual + all quarters 2020+ |
| FOLK1D  | Working-age (15–64) population, Danish vs foreign, by municipality | All quarters |

Pre-fetched CSV files are included in this repo and refreshed automatically (see below).

## Quarterly automation

A GitHub Actions workflow runs on the **15th of February, May, August, and November** at 06:00 UTC — timed to give Statistics Denmark ~6 weeks after each reference date to publish new figures. It:

1. Pulls the latest data from all four Statbank datasets
2. Commits updated CSVs back to this repo, triggering a Streamlit Cloud redeploy
3. Runs a quarterly analysis and sends a summary DM via Slack covering:
   - Net migration total vs the same period last year
   - Top 5 nationalities by net inflow and any net outflows
   - Biggest year-on-year shifts by nationality
   - Working-age foreign population total and % change vs same quarter last year
   - Which municipality saw the biggest shift in foreign working-age share

To trigger a manual run: **Actions → Quarterly data refresh → Run workflow**.

To refresh data locally:

```bash
python fetch_migration.py   # VAN1AAR + VAN2AAR
python fetch_population.py  # FOLK1B (annual + quarterly) + FOLK1D (quarterly)
```

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```
app.py                          # Navigation router (st.navigation)
pages/
  0_Migration_Explorer.py       # Annual immigration & emigration explorer
  1_Demographic_Change.py       # Quarterly working-age Danish/foreign split
  2_Population_Explorer.py      # Quarterly population by nationality
groups.py                       # Region and citizenship group definitions
fetch_migration.py              # Fetches VAN1AAR + VAN2AAR from Statbank
fetch_population.py             # Fetches FOLK1B + FOLK1D from Statbank
quarterly_report.py             # Quarterly analysis and Slack notification
immigration.csv                 # Immigration data (VAN1AAR)
emigration.csv                  # Emigration data (VAN2AAR)
population_by_nationality.csv   # Population by municipality and citizenship, K1 (FOLK1B)
population_quarterly.csv        # Population by municipality and citizenship, all quarters 2020+ (FOLK1B)
working_age_by_status.csv       # Working-age population, Danish vs foreign, all quarters (FOLK1D)
requirements.txt                # Python dependencies
.github/workflows/
  quarterly-refresh.yml         # Scheduled data refresh and Slack notification
```

## Deploying to Streamlit Cloud

1. Fork or push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set the main file path to `app.py`
4. Deploy — no extra configuration needed

For the quarterly Slack notification, add a `SLACK_WEBHOOK` secret to the repo under **Settings → Secrets and variables → Actions**.
