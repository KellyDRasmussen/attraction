import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from groups import REGIONS

DANISH  = "Danish citizen"
FOREIGN = "Foreign citizen"

COL_DANISH  = "#0072B2"
COL_FOREIGN = "#D55E00"


@st.cache_data
def load_data():
    return pd.read_csv("working_age_by_status.csv")


wa = load_data()
all_years          = sorted(wa["year"].unique())
all_municipalities = sorted(wa["municipality"].unique())
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

# ── Filter ─────────────────────────────────────────────────────────────────────
wa_f = wa if selected_municipalities is None else wa[wa["municipality"].isin(selected_municipalities)]

danish_yr  = wa_f[wa_f["citizenship_status"] == DANISH].groupby("year")["working_age_population"].sum().reindex(all_years, fill_value=0)
foreign_yr = wa_f[wa_f["citizenship_status"] == FOREIGN].groupby("year")["working_age_population"].sum().reindex(all_years, fill_value=0)
total_yr   = danish_yr + foreign_yr
share_yr   = (foreign_yr / total_yr.replace(0, np.nan) * 100).fillna(0)

latest = all_years[-1]
prev   = all_years[-2]

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Demographic Change")
st.markdown(f"**Working-age population (15–64) · {geo_label}** — Q1 snapshots, Statistics Denmark (FOLK1D)")

# ── Metrics ────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric(
    "Foreign working-age residents",
    f"{int(foreign_yr[latest]):,}",
    f"{int(foreign_yr[latest]) - int(foreign_yr[prev]):+,} vs {prev}",
)
c2.metric(
    "Foreign share",
    f"{share_yr[latest]:.1f}%",
    f"{share_yr[latest] - share_yr[prev]:+.1f} pp vs {prev}",
)
c3.metric(
    "Total working-age (15–64)",
    f"{int(total_yr[latest]):,}",
)

st.markdown("---")

# ── Chart 1: Foreign share over time ──────────────────────────────────────────
fig1, ax1 = plt.subplots(figsize=(11, 4))
ax1.plot(all_years, share_yr.values, color=COL_FOREIGN, linewidth=2.5, marker="o", markersize=5, zorder=3)
ax1.fill_between(all_years, share_yr.values, alpha=0.12, color=COL_FOREIGN)
ax1.set_xlabel("Year (Q1)", fontsize=11)
ax1.set_ylabel("Foreign share of working-age pop. (%)", fontsize=11)
ax1.set_title(f"Foreign share of working-age population (15–64) — {geo_label}", fontsize=12, pad=12)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))
ax1.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
plt.tight_layout()
st.pyplot(fig1)
plt.close(fig1)

# ── Chart 2: Stacked bar — Danish vs Foreign ───────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(11, 5))
x = np.arange(len(all_years))
w = 0.6

ax2.bar(x, danish_yr.values,  w, color=COL_DANISH,  alpha=0.85, label="Danish citizen",  zorder=3)
ax2.bar(x, foreign_yr.values, w, color=COL_FOREIGN, alpha=0.85, label="Foreign citizen",
        bottom=danish_yr.values, zorder=3)

ax2.set_xticks(x)
ax2.set_xticklabels([str(y) for y in all_years], rotation=45, ha="right", fontsize=9)
ax2.set_xlabel("Year (Q1)", fontsize=11)
ax2.set_ylabel("People", fontsize=11)
ax2.set_title(f"Working-age population (15–64) by citizenship — {geo_label}", fontsize=12, pad=12)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax2.legend(fontsize=10)
ax2.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
plt.tight_layout()
st.pyplot(fig2)
plt.close(fig2)

# ── Municipality rankings table ────────────────────────────────────────────────
st.markdown("---")
st.subheader(f"All municipalities — foreign working-age share ({latest})")

def muni_shares(year):
    f = wa[(wa["year"] == year) & (wa["citizenship_status"] == FOREIGN)].set_index("municipality")["working_age_population"]
    d = wa[(wa["year"] == year) & (wa["citizenship_status"] == DANISH)].set_index("municipality")["working_age_population"]
    total = (f + d).replace(0, np.nan)
    return f, d, total, f / total * 100

f_now, d_now, t_now, s_now = muni_shares(latest)
_, _, _, s_prev = muni_shares(prev)

s_now = s_now.dropna().sort_values(ascending=False)

table = pd.DataFrame({
    "Municipality":          s_now.index,
    "Foreign share":         s_now.values,
    f"Change vs {prev}":    (s_now - s_prev.reindex(s_now.index)).values,
    "Foreign (15–64)":       f_now.reindex(s_now.index).values,
    "Total (15–64)":         t_now.reindex(s_now.index).values,
})

st.dataframe(
    table.style
        .format({
            "Foreign share":       "{:.1f}%",
            f"Change vs {prev}":   "{:+.1f} pp",
            "Foreign (15–64)":     "{:,.0f}",
            "Total (15–64)":       "{:,.0f}",
        })
        .map(
            lambda v: f"color: {'#009E73' if v > 0 else '#CC3311'}; font-weight:bold",
            subset=[f"Change vs {prev}"],
        ),
    use_container_width=True,
    height=420,
    hide_index=True,
)
