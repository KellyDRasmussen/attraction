"""
quarterly_report.py — analyse latest migration data and post findings to Slack.
Called by .github/workflows/quarterly-refresh.yml after the data fetch steps.
"""

import os
from datetime import datetime

import pandas as pd
import requests

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
STATBANK_META = "https://api.statbank.dk/v1/tableinfo/FOLK1D?lang=en"


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data():
    imm = pd.read_csv("immigration.csv")
    emi = pd.read_csv("emigration.csv")
    wa  = pd.read_csv("working_age_by_status.csv")
    return imm, emi, wa


def get_municipality_names():
    """Return dict of municipality code → name from Statbank metadata."""
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

    # Top 5 inflows and outflows (latest year, excluding Danish citizens)
    by_nat = (
        net[(net["year"] == latest) & (net["citizenship"] != "Denmark")]
        .groupby("citizenship")["net"].sum()
        .sort_values(ascending=False)
    )
    top5_in  = by_nat.head(5)
    top5_out = by_nat[by_nat < 0].tail(5).sort_values()

    # Biggest year-on-year movers (absolute change in net migration)
    curr = net[net["year"] == latest].groupby("citizenship")["net"].sum()
    prev_nat = net[net["year"] == prev].groupby("citizenship")["net"].sum()
    change = (curr - prev_nat).dropna()
    top_movers = change.reindex(change.abs().sort_values(ascending=False).index).head(5)

    return latest, latest_total, prev_total, delta, pct, top5_in, top5_out, top_movers


def working_age_analysis(wa, muni_names):
    foreign = wa[wa["citizenship_status"] == "Foreign citizen"]
    danish  = wa[wa["citizenship_status"] == "Danish citizen"]

    latest = int(wa["year"].max())
    prev   = latest - 1

    f_by_year = foreign.groupby("year")["working_age_population"].sum()
    d_by_year = danish.groupby("year")["working_age_population"].sum()

    f_latest = int(f_by_year.get(latest, 0))
    f_prev   = int(f_by_year.get(prev, 0))
    f_delta  = f_latest - f_prev
    f_pct    = (f_delta / f_prev * 100) if f_prev else 0

    total_latest  = f_latest + int(d_by_year.get(latest, 0))
    foreign_share = (f_latest / total_latest * 100) if total_latest else 0

    # Which municipality shifted most in foreign working-age share?
    def share_by_muni(year):
        f = foreign[foreign["year"] == year].groupby("municipality")["working_age_population"].sum()
        d = danish[danish["year"] == year].groupby("municipality")["working_age_population"].sum()
        total = (f + d).replace(0, pd.NA)
        return (f / total * 100).dropna()

    curr_share  = share_by_muni(latest)
    prev_share  = share_by_muni(prev)
    share_delta = (curr_share - prev_share).dropna().sort_values(ascending=False)

    if len(share_delta):
        top_code  = share_delta.index[0]
        top_name  = muni_names.get(str(top_code), str(top_code))
        top_delta = float(share_delta.iloc[0])
        top_curr  = float(curr_share.get(top_code, 0))
    else:
        top_name, top_delta, top_curr = "N/A", 0.0, 0.0

    return latest, f_latest, f_delta, f_pct, foreign_share, top_name, top_delta, top_curr


# ── Formatting ────────────────────────────────────────────────────────────────

def arrow(n):
    return "▲" if n > 0 else "▼"


def signed(n):
    return f"+{n:,}" if n > 0 else f"{n:,}"


def build_message(net_data, wa_data):
    (latest_year, latest_total, prev_total, delta, pct,
     top5_in, top5_out, top_movers) = net_data

    (wa_year, f_latest, f_delta, f_pct, foreign_share,
     top_muni, top_muni_delta, top_muni_curr) = wa_data

    now = datetime.now()
    quarter = f"Q{(now.month - 1) // 3 + 1} {now.year}"

    top5_lines = "\n".join(
        f"  {i+1}. {name}: {signed(int(val))}"
        for i, (name, val) in enumerate(top5_in.items())
    )

    mover_lines = "\n".join(
        f"  • {name}: {signed(int(val))} vs {latest_year - 1}"
        for name, val in top_movers.items()
    )

    outflow_lines = (
        "\n".join(
            f"  • {name}: {signed(int(val))}"
            for name, val in top5_out.items()
        )
        if len(top5_out) else "  None"
    )

    return f"""📊 *Quarterly migration update — {quarter}*

*Net migration {latest_year}:* {latest_total:,} people  {arrow(delta)} {abs(delta):,} ({abs(pct):.1f}%) vs {latest_year - 1}

*Top 5 nationalities by net inflow:*
{top5_lines}

*Net outflows:*
{outflow_lines}

*Biggest year-on-year shifts in net migration:*
{mover_lines}

*Working-age foreign residents (15–64), {wa_year}:* {f_latest:,}  {arrow(f_delta)} {abs(f_delta):,} ({abs(f_pct):.1f}%)
Foreign share of working-age population: {foreign_share:.1f}%

*Municipal flag:* {top_muni} had the biggest jump in foreign working-age share — {top_muni_delta:+.1f} percentage points, now {top_muni_curr:.1f}%"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("Loading CSVs...")
    imm, emi, wa = load_data()

    print("Fetching municipality names from Statbank...")
    muni_names = get_municipality_names()

    print("Analysing net migration...")
    net_data = net_migration_analysis(imm, emi)

    print("Analysing working-age population...")
    wa_data = working_age_analysis(wa, muni_names)

    message = build_message(net_data, wa_data)
    print("\n── Message preview ──────────────────────────\n")
    print(message)
    print("\n─────────────────────────────────────────────\n")

    resp = requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=30)
    resp.raise_for_status()
    print("Sent to Slack.")


if __name__ == "__main__":
    main()
