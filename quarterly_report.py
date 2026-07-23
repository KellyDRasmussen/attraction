"""
quarterly_report.py — analyse latest migration data and post findings to Slack.
Called by .github/workflows/quarterly-refresh.yml after the data fetch steps.

Q1 message: full annual migration recap + quarterly working-age update.
Q2/Q3/Q4 message: quarterly working-age update only (migration data unchanged).
"""

import os
from datetime import datetime

import pandas as pd
import requests

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
STATBANK_META = "https://api.statbank.dk/v1/tableinfo/FOLK1D?lang=en"

# 3F's "backdoor citizenship" claim: dual nationality lets non-EU nationals
# in via EU passports — Argentinians on Italian citizenship, Nepalese on
# Portuguese citizenship. Checked against VAN1AAR (see fetch_migration.py).
DUAL_CITIZENSHIP_WATCH = [("Argentina", "Italy"), ("Nepal", "Portugal")]


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data():
    imm = pd.read_csv("immigration.csv")
    emi = pd.read_csv("emigration.csv")
    wa  = pd.read_csv("working_age_by_status.csv")
    try:
        dual = pd.read_csv("dual_citizenship_check.csv")
    except FileNotFoundError:
        dual = None
    try:
        pop = pd.read_csv("population_by_nationality.csv")
    except FileNotFoundError:
        pop = None
    return imm, emi, wa, dual, pop


def get_municipality_names():
    resp = requests.get(STATBANK_META, timeout=30)
    resp.raise_for_status()
    for var in resp.json()["variables"]:
        if var["id"] == "OMRÅDE":
            return {
                v["id"]: v["text"]
                for v in var["values"]
                if str(v["id"]).isdigit() and 101 <= int(v["id"]) <= 860
            }
    return {}


# ── Analysis ──────────────────────────────────────────────────────────────────

def net_migration_analysis(imm, emi):
    net = imm.merge(emi, on=["kommune", "citizenship", "year"], suffixes=("_in", "_out"))
    net["net"] = net["count_in"] - net["count_out"]

    latest = int(net["year"].max())
    prev   = latest - 1

    annual       = net.groupby("year")["net"].sum()
    latest_total = int(annual.get(latest, 0))
    prev_total   = int(annual.get(prev, 0))
    delta        = latest_total - prev_total
    pct          = (delta / abs(prev_total) * 100) if prev_total else 0

    by_nat = (
        net[(net["year"] == latest) & (net["citizenship"] != "Denmark")]
        .groupby("citizenship")["net"].sum()
        .sort_values(ascending=False)
    )
    top5_in  = by_nat.head(5)
    top5_out = by_nat[by_nat < 0].tail(5).sort_values()

    curr     = net[net["year"] == latest].groupby("citizenship")["net"].sum()
    prev_nat = net[net["year"] == prev].groupby("citizenship")["net"].sum()
    change   = (curr - prev_nat).dropna()
    top_movers = change.reindex(change.abs().sort_values(ascending=False).index).head(5)

    return latest, latest_total, prev_total, delta, pct, top5_in, top5_out, top_movers


def dual_citizenship_analysis(dual, pop):
    """
    For each watched (origin, citizenship) pair: direct-arrival flow (latest vs
    peak year) plus total stock of that citizenship in Denmark (latest vs 2
    years prior), so the Slack message doesn't overstate what flow data alone
    can show. Flow only captures people who moved straight from the origin
    country while already holding the EU citizenship — it misses anyone who
    naturalised via years of residency in a third EU country first, or after
    arriving in Denmark, or was born here to parents who hold it.
    """
    if dual is None:
        return None

    rows = []
    for origin, citizenship in DUAL_CITIZENSHIP_WATCH:
        series = (
            dual[(dual["origin_country"] == origin) & (dual["citizenship"] == citizenship)]
            .set_index("year")["count"]
        )
        if series.empty:
            continue
        latest_year  = int(series.index.max())
        latest_count = int(series.get(latest_year, 0))
        peak_year    = int(series.idxmax())
        peak_count   = int(series.max())

        stock_latest, stock_2yr_ago = None, None
        if pop is not None:
            stock = pop[pop["citizenship"] == citizenship].groupby("year")["population"].sum()
            if latest_year in stock.index:
                stock_latest = int(stock[latest_year])
                if (latest_year - 2) in stock.index:
                    stock_2yr_ago = int(stock[latest_year - 2])

        rows.append((origin, citizenship, latest_year, latest_count, peak_year, peak_count,
                     stock_latest, stock_2yr_ago))
    return rows


def working_age_analysis(wa, muni_names):
    foreign = wa[wa["citizenship_status"] == "Foreign citizen"]
    danish  = wa[wa["citizenship_status"] == "Danish citizen"]

    periods       = wa.sort_values(["year", "quarter"])["period"].unique()
    latest_period = periods[-1]
    latest_year   = int(latest_period[:4])
    latest_q      = int(latest_period[-1])
    prev_period   = f"{latest_year - 1}K{latest_q}"

    def totals_for(period):
        f = foreign[foreign["period"] == period]["working_age_population"].sum()
        d = danish[danish["period"] == period]["working_age_population"].sum()
        return int(f), int(d)

    f_latest, d_latest = totals_for(latest_period)
    f_prev, _          = totals_for(prev_period)
    f_delta            = f_latest - f_prev
    f_pct              = (f_delta / f_prev * 100) if f_prev else 0
    total_latest       = f_latest + d_latest
    foreign_share      = (f_latest / total_latest * 100) if total_latest else 0

    def share_by_muni(period):
        f = foreign[foreign["period"] == period].groupby("municipality")["working_age_population"].sum()
        d = danish[danish["period"] == period].groupby("municipality")["working_age_population"].sum()
        total = (f + d).replace(0, pd.NA)
        return (f / total * 100).dropna()

    curr_share  = share_by_muni(latest_period)
    prev_share  = share_by_muni(prev_period)
    share_delta = (curr_share - prev_share).dropna().sort_values(ascending=False)

    if len(share_delta):
        top_code  = share_delta.index[0]
        top_name  = muni_names.get(str(top_code), str(top_code))
        top_delta = float(share_delta.iloc[0])
        top_curr  = float(curr_share.get(top_code, 0))
    else:
        top_name, top_delta, top_curr = "N/A", 0.0, 0.0

    return latest_period, prev_period, f_latest, f_delta, f_pct, foreign_share, top_name, top_delta, top_curr


# ── Message building ──────────────────────────────────────────────────────────

def arrow(n):
    return "▲" if n > 0 else "▼"

def signed(n):
    return f"+{n:,}" if n > 0 else f"{n:,}"


def build_quarterly_section(wa_data):
    (wa_period, wa_prev_period, f_latest, f_delta, f_pct, foreign_share,
     top_muni, top_muni_delta, top_muni_curr) = wa_data

    return f"""*Working-age foreign residents (15–64), {wa_period}:* {f_latest:,}  {arrow(f_delta)} {abs(f_delta):,} ({abs(f_pct):.1f}%) vs {wa_prev_period}
Foreign share of working-age population: {foreign_share:.1f}%

*Municipal flag:* {top_muni} had the biggest shift in foreign working-age share — {top_muni_delta:+.1f} pp, now {top_muni_curr:.1f}%"""


def build_annual_section(net_data):
    (latest_year, latest_total, prev_total, delta, pct,
     top5_in, top5_out, top_movers) = net_data

    top5_lines = "\n".join(
        f"  {i+1}. {name}: {signed(int(val))}"
        for i, (name, val) in enumerate(top5_in.items())
    )
    outflow_lines = (
        "\n".join(f"  • {name}: {signed(int(val))}" for name, val in top5_out.items())
        if len(top5_out) else "  None"
    )
    mover_lines = "\n".join(
        f"  • {name}: {signed(int(val))} vs {latest_year - 1}"
        for name, val in top_movers.items()
    )

    return f"""*Net migration {latest_year}:* {latest_total:,} people  {arrow(delta)} {abs(delta):,} ({abs(pct):.1f}%) vs {latest_year - 1}

*Top 5 nationalities by net inflow:*
{top5_lines}

*Net outflows:*
{outflow_lines}

*Biggest year-on-year shifts:*
{mover_lines}"""


def build_dual_citizenship_section(rows):
    if not rows:
        return None

    lines = []
    for origin, citizenship, latest_year, latest_count, peak_year, peak_count, stock_latest, stock_2yr_ago in rows:
        if peak_count == 0:
            trend = "no activity"
        elif latest_year == peak_year:
            trend = "highest on record"
        else:
            pct = (peak_count - latest_count) / peak_count * 100
            trend = f"{'down' if latest_count < peak_count else 'up'} {abs(pct):.0f}% vs {peak_year} peak of {peak_count:,}"
        lines.append(f"  • {origin} → {citizenship} citizenship, direct-arrival flow: {latest_count:,} in {latest_year} ({trend})")

        if stock_latest is not None and stock_2yr_ago:
            stock_pct = (stock_latest - stock_2yr_ago) / stock_2yr_ago * 100
            lines.append(
                f"    (context: total {citizenship}-citizenship population in DK is {stock_latest:,}, "
                f"{arrow(stock_pct)} {abs(stock_pct):.0f}% over 2 years — flow data can't tell us how much "
                f"of that is {origin}-origin)"
            )

    return f"""*3F "backdoor citizenship" claim — what we can check:* 3F reports ~1,200 Nepal-origin Portuguese-passport holders and ~3,200 Argentina-origin Italian-passport holders in Denmark, both up ~75-80% in two years.
{chr(10).join(lines)}
Direct-arrival flow only counts people who moved straight from the origin country already holding the EU passport — it misses anyone who naturalised via years of residency in a third EU country, naturalised after arriving here, or was born in DK to parents who hold it. We can't confirm or refute 3F's stock figures with this data; flow declining doesn't mean the resident population isn't growing."""


def build_message(net_data, wa_data, dual_rows, quarter: int):
    now     = datetime.now()
    label   = f"Q{quarter} {now.year}"
    wa_section = build_quarterly_section(wa_data)

    if quarter == 1:
        annual_section = build_annual_section(net_data)
        dual_section   = build_dual_citizenship_section(dual_rows)
        sections = [annual_section]
        if dual_section:
            sections.append(dual_section)
        sections.append(wa_section)
        body = "\n\n──\n".join(sections)
        return f"""📊 *Q1 update — {label}*

{body}"""
    else:
        return f"""📊 *{label} population update*

{wa_section}

_Annual migration figures update in Q1._"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    now     = datetime.now()
    quarter = (now.month - 1) // 3 + 1

    print("Loading CSVs...")
    imm, emi, wa, dual, pop = load_data()

    print("Fetching municipality names from Statbank...")
    muni_names = get_municipality_names()

    print("Analysing working-age population...")
    wa_data = working_age_analysis(wa, muni_names)

    if quarter == 1:
        print("Q1 — including annual migration analysis...")
        net_data  = net_migration_analysis(imm, emi)
        dual_rows = dual_citizenship_analysis(dual, pop)
    else:
        print(f"Q{quarter} — quarterly update only (migration data unchanged)...")
        net_data  = None
        dual_rows = None

    message = build_message(net_data, wa_data, dual_rows, quarter)
    print("\n── Message preview ──────────────────────────\n")
    print(message)
    print("\n─────────────────────────────────────────────\n")

    resp = requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=30)
    resp.raise_for_status()
    print("Sent to Slack.")


if __name__ == "__main__":
    main()
