"""
fetch_population.py — pull FOLK1B and FOLK1D from Statbank and write CSVs.

Outputs:
  population_by_nationality.csv  — total population per municipality × citizenship × year (Q1 snapshots)
  working_age_by_status.csv      — working-age (15–64) per municipality × Danish/Foreign × year (Q1 snapshots)

Run manually:  python fetch_population.py
Run in CI:     called by .github/workflows/quarterly-refresh.yml
"""

import re
from io import StringIO

import pandas as pd
import requests

API_BASE = "https://api.statbank.dk/v1"


def _get_variable_values(table: str, variable_id: str) -> list[str]:
    resp = requests.get(f"{API_BASE}/tableinfo/{table}?lang=en", timeout=30)
    resp.raise_for_status()
    for var in resp.json()["variables"]:
        if var["id"] == variable_id:
            return [v["id"] for v in var["values"]]
    raise ValueError(f"Variable {variable_id} not found in {table}")


def get_municipality_codes() -> list[str]:
    codes = _get_variable_values("FOLK1B", "OMRÅDE")
    return [c for c in codes if re.match(r"^\d{3}$", c) and 101 <= int(c) <= 860]


def get_q1_periods() -> list[str]:
    # Statbank uses Danish notation: 2024K1 = Q1 2024
    return [t for t in _get_variable_values("FOLK1B", "Tid") if t.endswith("K1")]


def _fetch_csv(table: str, variables: list[dict]) -> pd.DataFrame:
    payload = {
        "table": table,
        "format": "CSV",
        "valuePresentation": "Code",
        "delimiter": "Semicolon",
        "lang": "en",
        "variables": variables,
    }
    resp = requests.post(f"{API_BASE}/data", json=payload, timeout=180)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text), sep=";", dtype=str)
    df.columns = [c.upper() for c in df.columns]
    return df


def fetch_population_by_nationality(municipalities: list[str], q1_periods: list[str]) -> pd.DataFrame:
    """
    FOLK1B — total population by municipality, citizenship, year.
    One row per municipality × citizenship × year; sex and age collapsed to totals.
    """
    df = _fetch_csv("FOLK1B", [
        {"code": "OMRÅDE", "values": municipalities},
        {"code": "KØN",    "values": ["TOT"]},
        {"code": "ALDER",  "values": ["IALT"]},
        {"code": "STATSB", "values": ["*"]},
        {"code": "Tid",    "values": q1_periods},
    ])
    df["year"] = df["TID"].str[:4].astype(int)
    df["INDHOLD"] = pd.to_numeric(df["INDHOLD"], errors="coerce").fillna(0).astype(int)
    return (
        df.groupby(["OMRÅDE", "STATSB", "year"])["INDHOLD"]
        .sum()
        .reset_index()
        .rename(columns={"OMRÅDE": "municipality", "STATSB": "citizenship", "INDHOLD": "population"})
    )


def fetch_working_age_by_status(municipalities: list[str], q1_periods: list[str]) -> pd.DataFrame:
    """
    FOLK1D — working-age (15–64) population by municipality, citizenship status (Danish/Foreign), year.
    Ages summed across 15–64; both sexes combined.
    """
    working_age_codes = [str(age) for age in range(15, 65)]
    df = _fetch_csv("FOLK1D", [
        {"code": "OMRÅDE", "values": municipalities},
        {"code": "KØN",    "values": ["TOT"]},
        {"code": "ALDER",  "values": working_age_codes},
        {"code": "STATSB", "values": ["DANSK", "UDLAND"]},
        {"code": "Tid",    "values": q1_periods},
    ])
    df["year"] = df["TID"].str[:4].astype(int)
    df["INDHOLD"] = pd.to_numeric(df["INDHOLD"], errors="coerce").fillna(0).astype(int)
    return (
        df.groupby(["OMRÅDE", "STATSB", "year"])["INDHOLD"]
        .sum()
        .reset_index()
        .rename(columns={
            "OMRÅDE": "municipality",
            "STATSB": "citizenship_status",
            "INDHOLD": "working_age_population",
        })
    )


if __name__ == "__main__":
    print("Fetching municipality codes...")
    municipalities = get_municipality_codes()
    print(f"  {len(municipalities)} municipalities")

    print("Fetching Q1 time periods...")
    q1_periods = get_q1_periods()
    print(f"  {len(q1_periods)} Q1 periods ({q1_periods[0]} → {q1_periods[-1]})")

    print("Fetching FOLK1B (population by nationality)...")
    pop = fetch_population_by_nationality(municipalities, q1_periods)
    pop.to_csv("population_by_nationality.csv", index=False)
    print(f"  → population_by_nationality.csv  ({len(pop):,} rows)")

    print("Fetching FOLK1D (working-age by citizenship status)...")
    wa = fetch_working_age_by_status(municipalities, q1_periods)
    wa.to_csv("working_age_by_status.csv", index=False)
    print(f"  → working_age_by_status.csv  ({len(wa):,} rows)")
