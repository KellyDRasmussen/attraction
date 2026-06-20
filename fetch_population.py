"""
fetch_population.py — pull FOLK1B and FOLK1D from Statbank and write CSVs.

Outputs:
  population_by_nationality.csv  — total population per municipality × citizenship × year (K1 snapshots)
  working_age_by_status.csv      — working-age (15–64) per municipality × Danish/Foreign × all quarters
                                   columns: municipality, citizenship_status, year, quarter, period,
                                            working_age_population
  population_quarterly.csv       — total population per municipality × citizenship × all quarters (2020+)
                                   columns: municipality, citizenship, year, quarter, period, population

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


def get_all_periods() -> list[str]:
    # All quarters: 2008K1, 2008K2, 2008K3, 2008K4, 2009K1, ...
    return _get_variable_values("FOLK1D", "Tid")


def get_recent_periods(from_year: int = 2020) -> list[str]:
    # All quarters from from_year onwards (keeps FOLK1B quarterly data manageable)
    return [t for t in _get_variable_values("FOLK1B", "Tid") if int(t[:4]) >= from_year]


def _fetch_bulk(table: str, variables: list[dict]) -> pd.DataFrame:
    payload = {
        "table": table,
        "format": "BULK",
        "delimiter": "Semicolon",
        "lang": "en",
        "variables": variables,
    }
    resp = requests.post(f"{API_BASE}/data", json=payload, timeout=300)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text), sep=";", dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _val_col(df: pd.DataFrame, id_cols: set[str]) -> str:
    others = [c for c in df.columns if c not in id_cols]
    assert len(others) == 1, f"Expected 1 value column, got: {others}"
    return others[0]


def fetch_population_by_nationality(municipalities: list[str], q1_periods: list[str]) -> pd.DataFrame:
    """
    FOLK1B — total population by municipality, citizenship, year (K1 snapshots only).
    """
    df = _fetch_bulk("FOLK1B", [
        {"code": "OMRÅDE", "values": municipalities},
        {"code": "KØN",    "values": ["TOT"]},
        {"code": "ALDER",  "values": ["IALT"]},
        {"code": "STATSB", "values": ["*"]},
        {"code": "Tid",    "values": q1_periods},
    ])
    id_cols = {"OMRÅDE", "KØN", "ALDER", "STATSB", "TID"}
    val = _val_col(df, id_cols)
    df["year"] = df["TID"].str[:4].astype(int)
    df[val] = pd.to_numeric(df[val], errors="coerce").fillna(0).astype(int)
    return (
        df.groupby(["OMRÅDE", "STATSB", "year"])[val]
        .sum()
        .reset_index()
        .rename(columns={"OMRÅDE": "municipality", "STATSB": "citizenship", val: "population"})
    )


def fetch_working_age_by_status(municipalities: list[str], all_periods: list[str]) -> pd.DataFrame:
    """
    FOLK1D — working-age (15–64) population by municipality, citizenship status, all quarters.
    Includes year, quarter (1–4), and period (e.g. '2024K2') columns so seasonal
    patterns are visible.
    """
    working_age_codes = [str(age) for age in range(15, 65)]
    df = _fetch_bulk("FOLK1D", [
        {"code": "OMRÅDE", "values": municipalities},
        {"code": "KØN",    "values": ["TOT"]},
        {"code": "ALDER",  "values": working_age_codes},
        {"code": "STATSB", "values": ["DANSK", "UDLAND"]},
        {"code": "Tid",    "values": all_periods},
    ])
    id_cols = {"OMRÅDE", "KØN", "ALDER", "STATSB", "TID"}
    val = _val_col(df, id_cols)
    df["year"]    = df["TID"].str[:4].astype(int)
    df["quarter"] = df["TID"].str[-1].astype(int)   # "2024K3" → 3
    df["period"]  = df["TID"]                        # keep "2024K3"
    df[val] = pd.to_numeric(df[val], errors="coerce").fillna(0).astype(int)
    return (
        df.groupby(["OMRÅDE", "STATSB", "year", "quarter", "period"])[val]
        .sum()
        .reset_index()
        .rename(columns={
            "OMRÅDE": "municipality",
            "STATSB": "citizenship_status",
            val: "working_age_population",
        })
    )


def fetch_population_quarterly(municipalities: list[str], recent_periods: list[str]) -> pd.DataFrame:
    """
    FOLK1B — total population by municipality, citizenship, all quarters (2020+).
    Used by the Population Explorer page for quarterly nationality breakdowns.
    """
    df = _fetch_bulk("FOLK1B", [
        {"code": "OMRÅDE", "values": municipalities},
        {"code": "KØN",    "values": ["TOT"]},
        {"code": "ALDER",  "values": ["IALT"]},
        {"code": "STATSB", "values": ["*"]},
        {"code": "Tid",    "values": recent_periods},
    ])
    id_cols = {"OMRÅDE", "KØN", "ALDER", "STATSB", "TID"}
    val = _val_col(df, id_cols)
    df["year"]    = df["TID"].str[:4].astype(int)
    df["quarter"] = df["TID"].str[-1].astype(int)
    df["period"]  = df["TID"]
    df[val] = pd.to_numeric(df[val], errors="coerce").fillna(0).astype(int)
    return (
        df.groupby(["OMRÅDE", "STATSB", "year", "quarter", "period"])[val]
        .sum()
        .reset_index()
        .rename(columns={"OMRÅDE": "municipality", "STATSB": "citizenship", val: "population"})
    )


if __name__ == "__main__":
    print("Fetching municipality codes...")
    municipalities = get_municipality_codes()
    print(f"  {len(municipalities)} municipalities")

    print("Fetching K1 periods (for FOLK1B)...")
    q1_periods = get_q1_periods()
    print(f"  {len(q1_periods)} periods ({q1_periods[0]} → {q1_periods[-1]})")

    print("Fetching all quarters (for FOLK1D)...")
    all_periods = get_all_periods()
    print(f"  {len(all_periods)} periods ({all_periods[0]} → {all_periods[-1]})")

    print("Fetching FOLK1B (population by nationality, K1 only)...")
    pop = fetch_population_by_nationality(municipalities, q1_periods)
    pop.to_csv("population_by_nationality.csv", index=False)
    print(f"  → population_by_nationality.csv  ({len(pop):,} rows)")

    print("Fetching FOLK1D (working-age by citizenship status, all quarters)...")
    wa = fetch_working_age_by_status(municipalities, all_periods)
    wa.to_csv("working_age_by_status.csv", index=False)
    print(f"  → working_age_by_status.csv  ({len(wa):,} rows)")

    print("Fetching recent periods (for FOLK1B quarterly)...")
    recent_periods = get_recent_periods(from_year=2020)
    print(f"  {len(recent_periods)} periods ({recent_periods[0]} → {recent_periods[-1]})")

    print("Fetching FOLK1B (population by nationality, all quarters 2020+)...")
    pop_q = fetch_population_quarterly(municipalities, recent_periods)
    pop_q.to_csv("population_quarterly.csv", index=False)
    print(f"  → population_quarterly.csv  ({len(pop_q):,} rows)")
