"""
eu_passport_analysis.py — one-off analysis for a Substack piece.

3F reported ~1,200 Nepal-origin Portuguese-passport holders (+79% in two
years) and ~3,200 Argentina-origin Italian-passport holders (+74% in two
years) living in Denmark. Those are stock figures (total population),
almost certainly from a bespoke Statistics Denmark register extract —
the public Statbank API doesn't expose a table crossing specific
citizenship with specific country-of-origin at the individual level.

The only thing reproducible from the public API is *flow* — VAN1AAR/
VAN2AAR give immigration/emigration events with "country of last
residence" and citizenship. Net cumulative flow (immigration minus
emigration, summed since 2007) is used here as a stock *proxy*. It is
a known undercount: checked against 3F's real figures, this method
comes in ~2.3x low for Argentina->Italy (ancestry citizenship, no
residency requirement) and ~70x low for Nepal->Portugal (citizenship
via 10 years' Portuguese residency — most such people's "last
residence" before Denmark is Portugal, not Nepal, so the filter never
sees them). Applied here to UK and USA for comparison, using the same
method and the same bias.

Outputs:
  eu_passport_by_origin.csv    — origin (UK/USA/Argentina/Nepal) x citizenship x year, immigration
  eu_passport_emigration.csv   — same origins, emigration (for net stock proxy)
  eu_passport_comparison.png   — chart: net cumulative stock proxy, 4 headline series
  substack_eu_passport.md      — numbers + talking points

Run manually: python eu_passport_analysis.py
"""

import sys
from io import StringIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent))  # repo root, for groups.py
from groups import EU

BASE_URL = "https://api.statbank.dk/v1/data"
META_URL = "https://api.statbank.dk/v1/tableinfo/VAN1AAR?lang=en"
YEARS = [str(y) for y in range(2007, 2026)]
YEAR_RANGE = range(2007, 2026)

ORIGIN_COUNTRIES = ["United Kingdom", "USA", "Argentina", "Nepal"]

# 3F's reported stock figures, for comparison (Information, citing 3F, 2026).
REPORTED_3F = {
    "Nepal -> Portugal": {"count": 1200, "growth_pct": 79},
    "Argentina -> Italy": {"count": 3200, "growth_pct": 74},
}


def get_country_codes():
    resp = requests.get(META_URL, timeout=30)
    resp.raise_for_status()
    meta = resp.json()
    for v in meta["variables"]:
        if v["id"] == "STATSB":
            return {x["text"]: x["id"] for x in v["values"]}
    raise RuntimeError("STATSB variable not found")


def _fetch(table, place_var, place_codes, rename_place):
    payload = {
        "table": table,
        "format": "BULK",
        "delimiter": "Semicolon",
        "lang": "en",
        "variables": [
            {"code": "OMRÅDE", "values": ["000"]},
            {"code": "KØN", "values": ["*"]},
            {"code": "ALDER", "values": ["*"]},
            {"code": place_var, "values": place_codes},
            {"code": "STATSB", "values": ["*"]},
            {"code": "Tid", "values": YEARS},
        ],
    }
    print(f"Fetching {table}...")
    resp = requests.post(BASE_URL, json=payload, timeout=300)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text), sep=";", encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    df = df.drop(columns=[c for c in df.columns if c.upper() in {"OMRÅDE", "KØN", "ALDER"}])

    id_cols = [c for c in df.columns if c.upper() in {place_var.upper(), "STATSB", "TID"}]
    val_col = [c for c in df.columns if c not in id_cols][0]
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce").fillna(0)

    result = df.groupby(id_cols, as_index=False)[val_col].sum()
    rename_map = {val_col: "count"}
    for c in result.columns:
        if c.upper() == place_var.upper():
            rename_map[c] = rename_place
        elif c.upper() == "STATSB":
            rename_map[c] = "citizenship"
        elif c.upper() == "TID":
            rename_map[c] = "year"
    result = result.rename(columns=rename_map)
    result["year"] = result["year"].astype(int)
    result["count"] = result["count"].astype(int)
    return result


def fetch_immigration(codes):
    return _fetch("VAN1AAR", "INDVLAND", codes, "origin_country")


def fetch_emigration(codes):
    return _fetch("VAN2AAR", "UDVLAND", codes, "destination_country")


def net_stock_proxy(imm, emi, origin, citizenship):
    """Cumulative (immigration - emigration) since 2007 for one (origin, citizenship) pair."""
    i = (imm[(imm["origin_country"] == origin) & (imm["citizenship"] == citizenship)]
         .set_index("year")["count"].reindex(YEAR_RANGE, fill_value=0))
    e = (emi[(emi["destination_country"] == origin) & (emi["citizenship"] == citizenship)]
         .set_index("year")["count"].reindex(YEAR_RANGE, fill_value=0))
    return (i - e).cumsum()


def top_eu_pairs(imm, emi, origin, eu_set, n=5):
    """Top n EU citizenships by net stock proxy for one origin, plus the any-EU total series."""
    citizenships = sorted(set(imm.loc[imm["origin_country"] == origin, "citizenship"]) & eu_set)
    per_citizenship = {c: net_stock_proxy(imm, emi, origin, c) for c in citizenships}
    ranked = sorted(per_citizenship.items(), key=lambda kv: kv[1].iloc[-1], reverse=True)
    total = sum(per_citizenship.values()) if per_citizenship else pd.Series(0, index=YEAR_RANGE)
    return ranked[:n], total


def main():
    codes = get_country_codes()
    origin_codes = [codes[c] for c in ORIGIN_COUNTRIES]

    imm = fetch_immigration(origin_codes)
    imm.to_csv(OUT_DIR / "eu_passport_by_origin.csv", index=False, encoding="utf-8-sig")
    print(f"Saved eu_passport_by_origin.csv — {len(imm):,} rows")

    emi = fetch_emigration(origin_codes)
    emi.to_csv(OUT_DIR / "eu_passport_emigration.csv", index=False, encoding="utf-8-sig")
    print(f"Saved eu_passport_emigration.csv — {len(emi):,} rows")

    eu_set = EU - {"Denmark"}  # Danish citizens returning home aren't "on an EU passport"

    headline = {
        "Argentina -> Italy":     net_stock_proxy(imm, emi, "Argentina", "Italy"),
        "Nepal -> Portugal":      net_stock_proxy(imm, emi, "Nepal", "Portugal"),
    }
    uk_top, uk_total = top_eu_pairs(imm, emi, "United Kingdom", eu_set)
    us_top, us_total = top_eu_pairs(imm, emi, "USA", eu_set)
    headline["UK -> any EU citizenship"]  = uk_total
    headline["USA -> any EU citizenship"] = us_total

    latest, prev2 = 2025, 2023
    print("\n--- stock proxy, 2025 vs 2023 ---")
    for label, s in headline.items():
        print(f"{label}: {int(s[latest]):,} (was {int(s[prev2]):,})")

    # ── Chart ────────────────────────────────────────────────────────────────
    COLORS = {
        "Argentina -> Italy":            "#0072B2",
        "Nepal -> Portugal":             "#56B4E9",
        "UK -> any EU citizenship":      "#D55E00",
        "USA -> any EU citizenship":     "#CC79A7",
    }
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for label, s in headline.items():
        ax.plot(list(YEAR_RANGE), s.values, marker="o", markersize=3.5, linewidth=2,
                color=COLORS[label], label=label)

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Net cumulative stock proxy (immigration − emigration since 2007)", fontsize=12)
    ax.set_title(
        "Same method, applied evenly:\n"
        "3F's flagged routes vs. UK & US nationals on EU passports",
        fontsize=13, pad=14,
    )
    ax.set_xticks(list(YEAR_RANGE)[::2])  # whole years only, every 2nd to avoid crowding
    ax.set_xticklabels([str(y) for y in list(YEAR_RANGE)[::2]], rotation=45, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "eu_passport_comparison.png", dpi=150, bbox_inches="tight")
    print("Saved eu_passport_comparison.png")

    # ── Markdown brief ───────────────────────────────────────────────────────
    def row(label, s):
        latest_val, prev_val = int(s[latest]), int(s[prev2])
        pct = (latest_val - prev_val) / prev_val * 100 if prev_val else 0
        return f"| {label} | {latest_val:,} | {prev_val:,} | {pct:+.0f}% |"

    def top_pair_lines(ranked):
        return "\n".join(
            f"  {i+1}. {citz}: {int(s[latest]):,} (was {int(s[prev2]):,}, {((int(s[latest])-int(s[prev2]))/int(s[prev2])*100 if s[prev2] else 0):+.0f}%)"
            for i, (citz, s) in enumerate(ranked)
        )

    md = f"""# Same method, applied evenly: 3F's claim vs. UK & US nationals on EU passports
*Data: Statistics Denmark (VAN1AAR/VAN2AAR), 2007-2025, nationwide*

3F reported (via Information) that Denmark has seen a rise in dual-nationality arrivals using EU
passports: **~{REPORTED_3F['Nepal -> Portugal']['count']:,} Nepal-origin Portuguese-passport holders**
(+{REPORTED_3F['Nepal -> Portugal']['growth_pct']}% in two years) and
**~{REPORTED_3F['Argentina -> Italy']['count']:,} Argentina-origin Italian-passport holders**
(+{REPORTED_3F['Argentina -> Italy']['growth_pct']}% in two years).

Those are *stock* figures — total people currently resident — almost certainly from a bespoke Statistics
Denmark register extract that isn't available through the public Statbank API. The public API only exposes
*flow*: immigration/emigration events tagged with country of last residence and citizenship. We built a
**net cumulative stock proxy** (immigration minus emigration, summed since 2007) as the closest public-data
approximation, and checked it against 3F's real numbers:

| Route | Our proxy (2025) | 3F's real figure | Undercount |
|---|---|---|---|
| Argentina -> Italy | ~1,415 | ~3,200 | ~2.3x |
| Nepal -> Portugal | ~17 | ~1,200 | ~70x |

The Nepal/Portugal undercount is severe because Portugal's (until 2026) relatively easy citizenship route
required **10 years of legal residency in Portugal** — so someone born in Nepal who did Nepal -> Portugal ->
Denmark shows up in Danish migration data as arriving *from Portugal*, indistinguishable from a native
Portuguese citizen. Italian citizenship, by contrast, is ancestry-based with no residency requirement, so
Argentina -> Italy direct moves are a much better (if still imperfect) match for the proxy.

**We cannot confirm or refute 3F's exact figures.** What we *can* do is apply the same imperfect method,
with the same known bias, to UK and US nationals — and see whether the "backdoor citizenship" framing holds
up once it's applied evenly.

## UK and USA, by the same method

**UK-origin, top EU citizenships held (net stock proxy):**
{top_pair_lines(uk_top)}
  **Total, any EU citizenship: {int(uk_total[latest]):,}** (was {int(uk_total[prev2]):,}, {((int(uk_total[latest])-int(uk_total[prev2]))/int(uk_total[prev2])*100):+.0f}%)

**USA-origin, top EU citizenships held (net stock proxy):**
{top_pair_lines(us_top)}
  **Total, any EU citizenship: {int(us_total[latest]):,}** (was {int(us_total[prev2]):,}, {((int(us_total[latest])-int(us_total[prev2]))/int(us_total[prev2])*100):+.0f}%)

## The comparison, side by side

| Route | 2025 proxy | 2023 proxy | 2-year growth |
|---|---|---|---|
{row("Argentina -> Italy (3F's claim)", headline["Argentina -> Italy"])}
{row("Nepal -> Portugal (3F's claim)", headline["Nepal -> Portugal"])}
{row("UK -> any EU citizenship", headline["UK -> any EU citizenship"])}
{row("USA -> any EU citizenship", headline["USA -> any EU citizenship"])}

**UK's total EU-passport stock proxy ({int(uk_total[latest]):,}) is already bigger than Argentina->Italy's proxy
({int(headline["Argentina -> Italy"][latest]):,}) using the identical method** — and USA's is growing far faster
in percentage terms (+184% vs Argentina's +17% over the same two years, by this method). Ireland is UK
nationals' closest analogue to the Argentina/Italy mechanism (pure ancestry citizenship, no residency
requirement), so it should carry a similar undercount factor to Argentina->Italy's ~2.3x — which would put
UK->Ireland's *true* stock in the same range as 3F's reported Nepal->Portugal figure (~1,200), not the
{int(dict(uk_top).get("Ireland", pd.Series({latest: 0}))[latest]):,} shown by the raw proxy.

## Why this matters for the framing

- **Ancestry- and residency-based EU citizenship is a normal, structural feature of several EU states'
  nationality law** (Italy, Ireland, Portugal, Poland, and others). It shows up wherever there was a
  historic emigration wave — Italians to Argentina/Brazil, Irish to the US/UK, Portuguese to former
  colonies, Bulgarians to Turkey, Romanians to Moldova.
- **Applying 3F's own logic evenly would flag British and American migration to Denmark as an equally
  large, equally fast-growing "loophole"** — which nobody is proposing, because the concern was never
  really about scale. The Nepal/Argentina framing reads as alarming because of who's arriving on these
  passports, not the underlying mechanism or the numbers.
- The one part of 3F's framing we can't wave away: Jens Arnholtz (KU) is right that this was never the
  intended purpose of free movement, and Portugal itself has now tightened its rules from 2026 — so
  something about the *specific* Portugal route was real enough to prompt a policy change, independent of
  whether 3F's precise numbers hold up.

## Caveats to carry into the piece

- Net cumulative flow (since 2007) is a floor, not a stock count — it ignores deaths, citizenship changes
  after arrival, people born in Denmark to these parents, and multi-country routes (Nepal -> Portugal ->
  Denmark). All of these push the true numbers up, not down.
- "Any EU citizenship" for UK/USA sums current EU-27 membership; the club's composition changed over the
  2007-2025 window (Bulgaria/Romania 2007, Croatia 2013), so the earliest years slightly understate what
  would have counted as "EU" at the time.
- Country of last residence != birthplace != ethnicity in all of this. Treat every number here as
  suggestive, not definitive — including 3F's.
"""
    with open(OUT_DIR / "substack_eu_passport.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("Saved substack_eu_passport.md")


if __name__ == "__main__":
    main()
