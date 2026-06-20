import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from groups import REGIONS, build_groups

# Colorblind-friendly palette (Wong)
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7",
           "#56B4E9", "#E69F00", "#F0E442", "#999999"]


@st.cache_data
def load_data():
    df = pd.read_csv("population_quarterly.csv")
    return df.sort_values(["year", "quarter"]).reset_index(drop=True)


try:
    pop = load_data()
except FileNotFoundError:
    st.title("Population Explorer")
    st.info(
        "**Data not yet available.** Trigger a run via "
        "**Actions → Quarterly data refresh → Run workflow**, then redeploy."
    )
    st.stop()

all_municipalities  = sorted(pop["municipality"].unique())
all_citizenships    = sorted(pop["citizenship"].unique())
foreign_citizenships = [c for c in all_citizenships if c != "Denmark"]
all_periods        = pop.sort_values(["year", "quarter"])["period"].unique().tolist()
GROUPS             = build_groups(all_citizenships)
data_munis         = set(all_municipalities)

REGIONS_CLEAN = {
    region: [m for m in munis if m in data_munis]
    for region, munis in REGIONS.items()
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("Geographic scope")
geo_level = st.sidebar.radio("Level", ["All Denmark", "Region", "Municipality"], horizontal=True)

selected_municipalities = None
geo_label = "All Denmark"

if geo_level == "Region":
    region = st.sidebar.selectbox("Region", list(REGIONS_CLEAN.keys()))
    selected_municipalities = REGIONS_CLEAN[region]
    geo_label = region
elif geo_level == "Municipality":
    muni = st.sidebar.selectbox("Municipality", all_municipalities)
    selected_municipalities = [muni]
    geo_label = muni

st.sidebar.markdown("---")
st.sidebar.header("Citizenship")

mode = st.sidebar.selectbox(
    "Show",
    ["All foreign citizenships", "Individual country"] + list(GROUPS.keys()),
)

# Build series: dict of {label → set of citizenships}
if mode == "All foreign citizenships":
    series = {"All foreign": set(all_citizenships) - {"Denmark"}}
    citizenship_label = "All foreign citizenships"
elif mode == "Individual country":
    country = st.sidebar.selectbox("Country", foreign_citizenships)
    series = {country: {country}}
    citizenship_label = country
else:
    # Group selected — show all subgroups side by side, no extra dropdown
    series = {k: v for k, v in GROUPS[mode].items() if v}
    citizenship_label = mode

# ── Filter geography ───────────────────────────────────────────────────────────
df = pop.copy()
if selected_municipalities is not None:
    df = df[df["municipality"].isin(selected_municipalities)]

# Exclude Danish citizens unless the user explicitly asked for the Danish/Non-Danish comparison
if mode != "Danish / Non-Danish":
    df = df[df["citizenship"] != "Denmark"]

# ── Aggregate each series over periods ────────────────────────────────────────
series_data = {}
for label, citizenships in series.items():
    filtered = df[df["citizenship"].isin(citizenships)]
    series_data[label] = (
        filtered.groupby("period")["population"].sum()
        .reindex(all_periods, fill_value=0)
    )

# Drop series that are all zero
series_data = {k: v for k, v in series_data.items() if v.sum() > 0}

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Population Explorer")
st.markdown(f"**Location:** {geo_label} &nbsp;|&nbsp; **Citizenship:** {citizenship_label}")
st.caption("Total population at the start of each quarter, 2020 onwards (FOLK1B).")

if not series_data:
    st.warning("No data for this combination.")
    st.stop()

# ── Chart ──────────────────────────────────────────────────────────────────────
n = len(series_data)
if n > 8:
    st.warning(f"{n} series selected — chart may be crowded. Consider a narrower group.")

bar_width = min(0.8 / n, 0.25)
x = np.arange(len(all_periods))

fig, ax = plt.subplots(figsize=(max(13, len(all_periods) * 0.45), 6))

for i, (label, data) in enumerate(series_data.items()):
    offset = (i - (n - 1) / 2) * bar_width
    ax.bar(x + offset, data.values, bar_width,
           label=label, color=PALETTE[i % len(PALETTE)], alpha=0.88, zorder=3)

# ── X-axis labels: "2020\nK1", "K2", "K3", "K4", "2021\nK1", ... ─────────────
x_labels = []
for p in all_periods:
    q = p[-1]
    x_labels.append(f"{p[:4]}\nK1" if q == "1" else f"K{q}")

ax.set_xticks(x)
ax.set_xticklabels(x_labels, fontsize=8.5)
ax.set_xlabel("Quarter", fontsize=11)
ax.set_ylabel("Population", fontsize=11)
ax.set_title(
    f"Population — {geo_label}  ·  {citizenship_label}",
    fontsize=13, pad=14,
)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

if n > 1:
    ax.legend(fontsize=9, loc="upper left")

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)
