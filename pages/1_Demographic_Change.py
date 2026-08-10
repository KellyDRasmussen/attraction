import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from groups import REGIONS

DANISH  = "Danish citizen"
FOREIGN = "Foreign citizen"

COL_DANISH  = "#0072B2"
COL_FOREIGN = "#D55E00"


@st.cache_data
def load_data():
    wa = pd.read_csv("working_age_by_status.csv")
    # sort by period so charts read left→right chronologically
    wa = wa.sort_values(["year", "quarter"]).reset_index(drop=True)
    return wa


wa = load_data()
all_municipalities = sorted(wa["municipality"].unique())
data_munis         = set(all_municipalities)
all_periods        = wa.sort_values(["year", "quarter"])["period"].unique().tolist()
all_years          = sorted(wa["year"].unique())

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

# ── Filter & aggregate ─────────────────────────────────────────────────────────
wa_f = wa if selected_municipalities is None else wa[wa["municipality"].isin(selected_municipalities)]

def by_period(status):
    return (
        wa_f[wa_f["citizenship_status"] == status]
        .groupby("period")["working_age_population"].sum()
        .reindex(all_periods, fill_value=0)
    )

danish_p  = by_period(DANISH)
foreign_p = by_period(FOREIGN)
total_p   = danish_p + foreign_p
share_p   = (foreign_p / total_p.replace(0, np.nan) * 100).fillna(0)

latest_period = all_periods[-1]
latest_year   = int(latest_period[:4])
latest_q      = int(latest_period[-1])
# same quarter last year
prev_period   = f"{latest_year - 1}K{latest_q}"
prev_share    = float(share_p.get(prev_period, share_p.iloc[-5] if len(share_p) > 4 else 0))

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Demographic Change")
st.markdown(
    f"**Working-age population (15–64) · {geo_label}** — "
    f"quarterly snapshots (K1–K4), Statistics Denmark (FOLK1D)"
)

# ── Metrics ────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
f_latest = int(foreign_p[latest_period])
f_prev   = int(foreign_p.get(prev_period, 0))
s_latest = float(share_p[latest_period])

c1.metric("Foreign working-age", f"{f_latest:,}",
          f"{f_latest - f_prev:+,} vs {prev_period}")
c2.metric("Foreign share", f"{s_latest:.1f}%",
          f"{s_latest - prev_share:+.1f} pp vs {prev_period}")
c3.metric("Latest period", latest_period)

st.markdown("---")

# ── Chart: Foreign share over all quarters ────────────────────────────────────
fig1, ax1 = plt.subplots(figsize=(13, 4))
x = np.arange(len(all_periods))

ax1.plot(x, share_p.values, color=COL_FOREIGN, linewidth=1.8, zorder=3)
ax1.fill_between(x, share_p.values, alpha=0.12, color=COL_FOREIGN)

# Label every K1 with the year; shade K2–K4 bands lightly to show quarters
for i, p in enumerate(all_periods):
    if p.endswith("K1"):
        ax1.axvline(i, color="grey", linewidth=0.4, linestyle="--", zorder=1)

# X-axis: show year labels at K1 ticks
k1_positions = [i for i, p in enumerate(all_periods) if p.endswith("K1")]
k1_labels    = [p[:4] for p in all_periods if p.endswith("K1")]
ax1.set_xticks(k1_positions)
ax1.set_xticklabels(k1_labels, fontsize=9)

ax1.set_xlabel("Year (dashed lines = Q1)", fontsize=10)
ax1.set_ylabel("Foreign share (%)", fontsize=10)
ax1.set_title(
    f"Foreign share of working-age population (15–64) — {geo_label}\n"
    "Seasonal dips = temporary workers / students leaving",
    fontsize=11, pad=10
)
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:.1f}%"))
ax1.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
plt.tight_layout()
st.pyplot(fig1)
plt.close(fig1)

# ── Chart: Stacked bar by year (K1 snapshot for comparability) ────────────────
danish_k1  = wa_f[(wa_f["citizenship_status"] == DANISH)  & (wa_f["quarter"] == 1)].groupby("year")["working_age_population"].sum().reindex(all_years, fill_value=0)
foreign_k1 = wa_f[(wa_f["citizenship_status"] == FOREIGN) & (wa_f["quarter"] == 1)].groupby("year")["working_age_population"].sum().reindex(all_years, fill_value=0)

fig2, ax2 = plt.subplots(figsize=(11, 4))
xb = np.arange(len(all_years))
ax2.bar(xb, danish_k1.values,  0.6, color=COL_DANISH,  alpha=0.85, label="Danish citizen",  zorder=3)
ax2.bar(xb, foreign_k1.values, 0.6, color=COL_FOREIGN, alpha=0.85, label="Foreign citizen",
        bottom=danish_k1.values, zorder=3)
ax2.set_xticks(xb)
ax2.set_xticklabels([str(y) for y in all_years], fontsize=9)
ax2.set_xlabel("Year (K1)", fontsize=10)
ax2.set_ylabel("People", fontsize=10)
ax2.set_title(f"Working-age population by citizenship — {geo_label} (K1 each year)", fontsize=11, pad=10)
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax2.legend(fontsize=10)
ax2.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
plt.tight_layout()
st.pyplot(fig2)
plt.close(fig2)

# ── Municipality table ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader(f"All municipalities — {latest_period}")
st.caption(
    "**4Q range** = peak minus trough foreign share across the last 4 quarters. "
    "High values can mean real seasonal swings (temporary workers or students) "
    "or just fast sustained growth — check the underlying trend before assuming either."
)

def muni_share_for(period):
    sub = wa[wa["period"] == period]
    f = sub[sub["citizenship_status"] == FOREIGN].set_index("municipality")["working_age_population"]
    d = sub[sub["citizenship_status"] == DANISH].set_index("municipality")["working_age_population"]
    total = (f + d).replace(0, np.nan)
    return (f / total * 100).dropna()

s_now  = muni_share_for(latest_period)
s_prev = muni_share_for(prev_period)

# Seasonality: max–min foreign share over the last 4 quarters
last4 = all_periods[-4:]
shares_last4 = pd.DataFrame({p: muni_share_for(p) for p in last4})
seasonality  = (shares_last4.max(axis=1) - shares_last4.min(axis=1)).reindex(s_now.index)

s_now = s_now.sort_values(ascending=False)

table = pd.DataFrame({
    "Municipality":       s_now.index,
    "Foreign share":      s_now.values,
    f"vs {prev_period}":  (s_now - s_prev.reindex(s_now.index)).values,
    "4Q range (pp)":      seasonality.reindex(s_now.index).values,
    "Foreign (15–64)":    wa[
        (wa["period"] == latest_period) & (wa["citizenship_status"] == FOREIGN)
    ].set_index("municipality")["working_age_population"].reindex(s_now.index).values,
})

st.dataframe(
    table.style
        .format({
            "Foreign share":    "{:.1f}%",
            f"vs {prev_period}": "{:+.1f} pp",
            "4Q range (pp)":    "{:.1f}",
            "Foreign (15–64)":  "{:,.0f}",
        })
        .map(
            lambda v: f"color: {'#009E73' if v > 0 else '#CC3311'}; font-weight:bold",
            subset=[f"vs {prev_period}"],
        )
        .background_gradient(subset=["4Q range (pp)"], cmap="OrRd", vmin=0),
    use_container_width=True,
    height=450,
    hide_index=True,
)
