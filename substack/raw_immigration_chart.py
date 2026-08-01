"""
raw_immigration_chart.py — plain annual immigration flow (not the net
cumulative stock proxy), for the four EU-passport routes:
  Argentina -> Italy citizenship (specific, as named by 3F)
  Nepal -> Portugal citizenship (specific, as named by 3F)
  UK -> any EU citizenship (aggregate, excl. Denmark)
  USA -> any EU citizenship (aggregate, excl. Denmark)

Reuses eu_passport_by_origin.csv (already fetched by eu_passport_analysis.py)
rather than hitting Statbank again.

Outputs: eu_passport_raw_immigration.png

Run manually: python raw_immigration_chart.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR.parent))  # repo root, for groups.py
from groups import EU

YEAR_RANGE = range(2007, 2026)


def main():
    df = pd.read_csv(OUT_DIR / "eu_passport_by_origin.csv", encoding="utf-8-sig")
    eu_set = EU - {"Denmark"}  # Danish citizens returning home aren't "on an EU passport"

    def specific(origin, citizenship):
        sub = df[(df["origin_country"] == origin) & (df["citizenship"] == citizenship)]
        return sub.groupby("year")["count"].sum().reindex(YEAR_RANGE, fill_value=0)

    def any_eu(origin):
        sub = df[(df["origin_country"] == origin) & (df["citizenship"] != origin)]
        sub = sub[sub["citizenship"].isin(eu_set)]
        return sub.groupby("year")["count"].sum().reindex(YEAR_RANGE, fill_value=0)

    series = {
        "Argentina -> Italy":       specific("Argentina", "Italy"),
        "Nepal -> Portugal":        specific("Nepal", "Portugal"),
        "UK -> any EU citizenship": any_eu("United Kingdom"),
        "USA -> any EU citizenship": any_eu("USA"),
    }

    COLORS = {
        "Argentina -> Italy":        "#0072B2",
        "Nepal -> Portugal":         "#56B4E9",
        "UK -> any EU citizenship":  "#D55E00",
        "USA -> any EU citizenship": "#CC79A7",
    }

    fig, ax = plt.subplots(figsize=(11, 6.5))
    for label, s in series.items():
        ax.plot(list(YEAR_RANGE), s.values, marker="o", markersize=3.5, linewidth=2,
                color=COLORS[label], label=label)

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Immigrants to Denmark that year (nationwide)", fontsize=12)
    ax.set_title(
        "Annual immigration on an EU passport, 2007-2025\n"
        "3F's flagged routes vs. UK & US nationals",
        fontsize=13, pad=14,
    )
    ax.set_xticks(list(YEAR_RANGE)[::2])
    ax.set_xticklabels([str(y) for y in list(YEAR_RANGE)[::2]], rotation=45, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "eu_passport_raw_immigration.png", dpi=150, bbox_inches="tight")
    print("Saved eu_passport_raw_immigration.png")

    print("\n--- 2025 snapshot (raw annual immigration) ---")
    for label, s in series.items():
        print(f"{label}: {int(s[2025]):,}")


if __name__ == "__main__":
    main()
