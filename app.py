import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from groups import REGIONS, build_groups

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Denmark Migration Explorer", layout="wide")

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    imm = pd.read_csv("immigration.csv")
    emi = pd.read_csv("emigration.csv")
    return imm, emi

imm, emi = load_data()

all_kommuner   = sorted(imm["kommune"].unique())
all_citizenships = sorted(imm["citizenship"].unique())
GROUPS         = build_groups(all_citizenships)

YEARS = list(range(2020, 2026))

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("Geographic scope")

geo_level = st.sidebar.radio(
    "Level",
    ["All Denmark", "Region", "Kommune"],
    horizontal=True,
)

selected_kommuner = None   # None = all
geo_label = "All Denmark"

if geo_level == "Region":
    region = st.sidebar.selectbox("Region", list(REGIONS.keys()))
    selected_kommuner = REGIONS[region]
    geo_label = region
elif geo_level == "Kommune":
    kommune = st.sidebar.selectbox("Kommune", all_kommuner)
    selected_kommuner = [kommune]
    geo_label = kommune

st.sidebar.markdown("---")
st.sidebar.header("Citizenship filter")

citizenship_group = st.sidebar.selectbox(
    "Group by",
    ["All citizenships", "Individual country"] + list(GROUPS.keys()),
)

selected_citizenships = None   # None = all
citizenship_label = "All citizenships"

if citizenship_group == "Individual country":
    country = st.sidebar.selectbox("Country", all_citizenships)
    selected_citizenships = {country}
    citizenship_label = country
elif citizenship_group in GROUPS:
    subgroup_options = list(GROUPS[citizenship_group].keys())
    subgroup = st.sidebar.selectbox("Subgroup", subgroup_options)
    selected_citizenships = GROUPS[citizenship_group][subgroup]
    citizenship_label = f"{citizenship_group} — {subgroup}"

# ── Filter helper ──────────────────────────────────────────────────────────────
def filter_df(df):
    if selected_kommuner is not None:
        df = df[df["kommune"].isin(selected_kommuner)]
    if selected_citizenships is not None:
        df = df[df["citizenship"].isin(selected_citizenships)]
    return df

imm_f = filter_df(imm)
emi_f = filter_df(emi)

imm_yr = imm_f.groupby("year")["count"].sum().reindex(YEARS, fill_value=0)
emi_yr = emi_f.groupby("year")["count"].sum().reindex(YEARS, fill_value=0)
net_yr = imm_yr - emi_yr

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Denmark Migration Explorer")
st.markdown(f"**Location:** {geo_label} &nbsp;|&nbsp; **Citizenship:** {citizenship_label}")

# ── Chart ──────────────────────────────────────────────────────────────────────
COL_IMM = "#0072B2"
COL_EMI = "#D55E00"

x     = np.arange(len(YEARS))
width = 0.55

fig, ax = plt.subplots(figsize=(11, 6))

ax.bar(x,  imm_yr.values, width, color=COL_IMM, alpha=0.85, zorder=3)
ax.bar(x, -emi_yr.values, width, color=COL_EMI, alpha=0.85, zorder=3)

max_val = max(imm_yr.max(), emi_yr.max(), 1)
offset  = max_val * 0.03

for i, yr in enumerate(YEARS):
    net     = net_yr[yr]
    imm_val = imm_yr[yr]
    emi_val = emi_yr[yr]

    # Net migration tick line
    ax.plot(
        [x[i] - width / 2, x[i] + width / 2],
        [net, net],
        color="black", linewidth=2.5, zorder=5,
    )

    # Net value label
    va  = "bottom" if net >= 0 else "top"
    y_l = net + (offset if net >= 0 else -offset)
    ax.text(x[i], y_l, f"{net:+,.0f}",
            ha="center", va=va, fontsize=9, fontweight="bold", color="black")

    # Bar value labels (only when non-zero)
    if imm_val > 0:
        ax.text(x[i], imm_val + offset * 0.4, f"{imm_val:,.0f}",
                ha="center", va="bottom", fontsize=7.5,
                color=COL_IMM, fontweight="bold")
    if emi_val > 0:
        ax.text(x[i], -emi_val - offset * 0.4, f"{emi_val:,.0f}",
                ha="center", va="top", fontsize=7.5,
                color=COL_EMI, fontweight="bold")

ax.axhline(0, color="black", linewidth=0.8, zorder=4)
ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in YEARS], fontsize=11)
ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("People", fontsize=12)
ax.set_title(
    f"Immigration & Emigration 2020–2025\n{geo_label}  ·  {citizenship_label}",
    fontsize=13, pad=14,
)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{abs(v):,.0f}"))

imm_patch = mpatches.Patch(color=COL_IMM, alpha=0.85, label="Immigration")
emi_patch = mpatches.Patch(color=COL_EMI, alpha=0.85, label="Emigration")
net_line  = plt.Line2D([0], [0], color="black", linewidth=2.5, label="Net migration")
ax.legend(handles=[imm_patch, emi_patch, net_line], loc="upper left", fontsize=10)

ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ── Summary table ──────────────────────────────────────────────────────────────
st.markdown("---")
summary = pd.DataFrame({
    "Year":          YEARS,
    "Immigration":   imm_yr.values,
    "Emigration":    emi_yr.values,
    "Net Migration": net_yr.values,
}).set_index("Year")

st.dataframe(
    summary.style
        .format("{:,.0f}")
        .map(lambda v: "color: #0072B2; font-weight:bold", subset=["Immigration"])
        .map(lambda v: "color: #D55E00; font-weight:bold", subset=["Emigration"])
        .map(
            lambda v: f"color: {'#009E73' if v >= 0 else '#CC3311'}; font-weight:bold",
            subset=["Net Migration"],
        ),
    use_container_width=True,
)
