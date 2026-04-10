import requests
import pandas as pd
from io import StringIO

BASE_URL = "https://api.statbank.dk/v1/data"
META_URL = "https://api.statbank.dk/v1/tableinfo"
YEARS = ["2020", "2021", "2022", "2023", "2024", "2025"]


def get_kommune_codes():
    """Fetch all OMRÅDE codes from metadata and return only kommune codes (101-860)."""
    resp = requests.post(META_URL, json={"table": "VAN1AAR", "lang": "en"}, timeout=30)
    resp.raise_for_status()
    meta = resp.json()
    omrade_var = next(v for v in meta["variables"] if v["id"] == "OMRÅDE")
    kommune_codes = [
        v["id"] for v in omrade_var["values"]
        if v["id"].isdigit() and 100 <= int(v["id"]) <= 860
    ]
    print(f"Found {len(kommune_codes)} kommune codes")
    return kommune_codes


def fetch_table(table_id, destination_var, kommune_codes):
    """Fetch data from Statbank using specific kommune codes to keep payload manageable."""
    payload = {
        "table": table_id,
        "format": "BULK",
        "delimiter": "Semicolon",
        "lang": "en",
        "variables": [
            {"code": "OMRÅDE", "values": kommune_codes},
            {"code": "KØN", "values": ["*"]},
            {"code": "ALDER", "values": ["*"]},
            {"code": destination_var, "values": ["*"]},
            {"code": "STATSB", "values": ["*"]},
            {"code": "Tid", "values": YEARS},
        ],
    }
    print(f"Fetching {table_id} (this may take a while)...")
    resp = requests.post(BASE_URL, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.text


def process_df(raw_text, dest_col):
    """Parse bulk CSV, sum over sex/age, return kommune+citizenship+year+count."""
    df = pd.read_csv(StringIO(raw_text), sep=";", encoding="utf-8")

    # Normalize column names — strip whitespace and fix any oddities
    df.columns = [c.strip() for c in df.columns]
    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Shape: {df.shape}")

    # Drop destination country (INDVLAND / UDVLAND) and sex/age dimensions
    drop = [c for c in [dest_col, "KØN", "ALDER"] if c in df.columns]
    df = df.drop(columns=drop)

    # Identify id columns vs value column
    # Remaining should be: OMRÅDE, STATSB, TID, INDHOLD (value)
    id_candidates = {"OMRÅDE", "STATSB", "TID"}
    id_cols = [c for c in df.columns if c.upper() in id_candidates or c in id_candidates]
    val_cols = [c for c in df.columns if c not in id_cols]
    assert len(val_cols) == 1, f"Expected 1 value col, got: {val_cols}"
    val_col = val_cols[0]

    df[val_col] = pd.to_numeric(df[val_col], errors="coerce").fillna(0)
    result = df.groupby(id_cols, as_index=False)[val_col].sum()

    # Rename columns
    rename_map = {val_col: "count"}
    for c in result.columns:
        if c.upper() == "OMRÅDE":
            rename_map[c] = "kommune"
        elif c.upper() == "STATSB":
            rename_map[c] = "citizenship"
        elif c.upper() == "TID":
            rename_map[c] = "year"
    result = result.rename(columns=rename_map)

    # Cast year and count
    result["year"] = result["year"].astype(int)
    result["count"] = result["count"].astype(int)

    return result.sort_values(["year", "kommune", "citizenship"]).reset_index(drop=True)


def main():
    kommune_codes = get_kommune_codes()

    # Immigration (VAN1AAR)
    imm_raw = fetch_table("VAN1AAR", "INDVLAND", kommune_codes)
    imm = process_df(imm_raw, dest_col="INDVLAND")
    imm.to_csv("immigration.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved immigration.csv — {len(imm):,} rows, {imm['count'].sum():,} total immigrants")

    # Emigration (VAN2AAR)
    emi_raw = fetch_table("VAN2AAR", "UDVLAND", kommune_codes)
    emi = process_df(emi_raw, dest_col="UDVLAND")
    emi.to_csv("emigration.csv", index=False, encoding="utf-8-sig")
    print(f"Saved emigration.csv — {len(emi):,} rows, {emi['count'].sum():,} total emigrants")

    # Quick sanity check
    print(f"\nTop 5 immigration rows:\n{imm.head()}")
    print(f"\nYearly immigration totals:\n{imm.groupby('year')['count'].sum()}")
    print(f"\nYearly emigration totals:\n{emi.groupby('year')['count'].sum()}")


if __name__ == "__main__":
    main()
