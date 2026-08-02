import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from groups import REGIONS, build_groups, G7, G20, INSTABILITY

# Colorblind-safe categorical palette, fixed order (validated via dataviz skill's
# palette validator — do not reorder or cycle).
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
           "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
OTHER_COLOR = "#898781"   # muted gray — reserved for the folded "Other" bucket
SURFACE = "#fcfcfb"       # chart surface, used as the gap color between stack segments

TOP_N_ONLY = 7  # cap on individually-colored countries in a "<group> only" stacked view

# Groups with a "vs / only" breakdown (see sidebar) instead of a flat member list
VS_GROUPS = {
    "G7": ("G7", G7),
    "G20": ("G20", G20),
    "Political instability": ("Instability", INSTABILITY),
}


@st.cache_data
def load_data():
    df = pd.read_csv("population_quarterly.csv")
    # BULK format includes a "Total" aggregate row — drop it to avoid double-counting
    df = df[df["citizenship"] != "Total"]
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

# Long dropdowns (groups, countries) were getting clipped before the last option —
# cap the popover height and let it scroll internally instead.
st.markdown(
    """
    <style>
    ul[data-testid="stSelectboxVirtualDropdown"] { max-height: 50vh !important; }
    div[data-baseweb="popover"] { max-height: 60vh !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

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

# ── Filter geography ───────────────────────────────────────────────────────────
df = pop.copy()
if selected_municipalities is not None:
    df = df[df["municipality"].isin(selected_municipalities)]

# Exclude Danish citizens unless the user explicitly asked for the Danish/Non-Danish comparison
if mode != "Danish / Non-Danish":
    df = df[df["citizenship"] != "Denmark"]


def drill_down_series(citizenship_set, label_prefix, top_n=TOP_N_ONLY):
    """Break a bucket of countries into its top-N individually, folding the
    long tail into a single "Other" segment — used by every "<category> only"
    view so any category (EU, a continent, G7's non-members, ...) can be
    drilled into, not just the top-level groups."""
    totals = (
        df[df["citizenship"].isin(citizenship_set)]
        .groupby("citizenship")["population"].sum()
        .sort_values(ascending=False)
    )
    top = list(totals.index[:top_n])
    rest = list(totals.index[top_n:])
    out = {}
    for c in top:
        out[c] = (
            df[df["citizenship"] == c].groupby("period")["population"].sum()
            .reindex(all_periods, fill_value=0)
        )
    if rest:
        out[f"Other {label_prefix} ({len(rest)})"] = (
            df[df["citizenship"].isin(rest)].groupby("period")["population"].sum()
            .reindex(all_periods, fill_value=0)
        )
    return out


# ── Build this mode's clean subgroup partition: label → set[citizenship] ──────
# (None for "Individual country", which bypasses subgroups/drill-down entirely.)
if mode == "All foreign citizenships":
    subgroups = {"All foreign": set(all_citizenships) - {"Denmark"}}
elif mode == "Individual country":
    subgroups = None
elif mode in VS_GROUPS:
    short, group_set = VS_GROUPS[mode]
    group_set = group_set & set(all_citizenships)
    non_set = set(foreign_citizenships) - group_set
    subgroups = {short: group_set, f"Non-{short}": non_set}
else:
    subgroups = {k: v for k, v in GROUPS[mode].items() if v}

# ── Secondary "view" selector: the subgroups together, or drill into any one
#     of them by individual country (every category is drillable, not just
#     the handful with a hardcoded vs/only structure) ─────────────────────────
view = None
labels_ordered = []
if subgroups is not None:
    labels_ordered = list(subgroups.keys())
    if len(labels_ordered) == 1:
        overview_label = "Total"
        view_options = [overview_label, "Top countries"]
    elif len(labels_ordered) == 2:
        overview_label = f"{labels_ordered[0]} vs {labels_ordered[1]}"
        view_options = [overview_label] + [f"{l} only" for l in labels_ordered]
    else:
        overview_label = "All categories"
        view_options = [overview_label] + [f"{l} only" for l in labels_ordered]
    view = st.sidebar.selectbox(f"{mode} view", view_options)

# ── Build series ───────────────────────────────────────────────────────────────
# Either a dict of label → set[citizenship] (aggregated below), or, for a
# drill-down view, a dict of label → pd.Series resolved directly by
# drill_down_series (it folds a long tail of countries into "Other", so it
# bypasses the generic set-based path).
series = None
series_data_override = None

if mode == "Individual country":
    country = st.sidebar.selectbox("Country", foreign_citizenships)
    series = {country: {country}}
    citizenship_label = country
elif view == overview_label:
    series = subgroups
    citizenship_label = mode if mode == "All foreign citizenships" else f"{mode} — {view}"
else:
    target_label = labels_ordered[0] if len(labels_ordered) == 1 else view[:-len(" only")]
    series_data_override = drill_down_series(subgroups[target_label], target_label)
    citizenship_label = f"{mode} — {view}"

# ── Aggregate each series over periods ────────────────────────────────────────
if series_data_override is not None:
    series_data = series_data_override
else:
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

# ── Isolate via table selection (selection persists across reruns) ────────────
# Keyed on the geography + citizenship choice so a stale row-index selection
# from a previous series list (e.g. G7 only → G20 only) never silently carries
# over and isolates the wrong countries — changing mode/view starts fresh.
TABLE_KEY = f"pop_explorer_series_select__{geo_label}__{mode}__{view}"
labels_all = list(series_data.keys())
prior_state = st.session_state.get(TABLE_KEY, {})
prior_sel = prior_state.get("selection", {}).get("rows", [])
prior_sel = [i for i in prior_sel if i < len(labels_all)]

chart_data = (
    {labels_all[i]: series_data[labels_all[i]] for i in prior_sel}
    if prior_sel else series_data
)

n = len(chart_data)
if n > 8:
    st.warning(f"{n} series selected — chart may be crowded. Consider a narrower group or isolate a subset in the table below.")

# ── Chart (stacked bar, click a legend entry to isolate/hide it) ───────────────
x_labels = []
for p in all_periods:
    q = p[-1]
    x_labels.append(f"{p[:4]}<br>K1" if q == "1" else f"K{q}")

fig = go.Figure()

for i, (label, data) in enumerate(chart_data.items()):
    color = OTHER_COLOR if label.startswith("Other ") else PALETTE[i % len(PALETTE)]
    fig.add_trace(go.Bar(
        x=all_periods,
        y=data.values,
        name=label,
        marker=dict(color=color, line=dict(color=SURFACE, width=1)),
        hovertemplate=f"<b>{label}</b>: " + "%{y:,.0f}<extra></extra>",
    ))

fig.update_layout(
    barmode="stack",
    template="plotly_white",
    height=600,
    title=f"Population — {geo_label} · {citizenship_label}",
    xaxis=dict(
        tickmode="array",
        tickvals=all_periods,
        ticktext=x_labels,
        title="Quarter",
    ),
    yaxis=dict(title="Population", tickformat=",.0f", rangemode="tozero"),
    hovermode="x unified",
    showlegend=n > 1,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    bargap=0.25,
    margin=dict(t=90),
)

st.plotly_chart(fig, use_container_width=True)

# ── Data & selection table ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Data")
st.caption("Select rows to isolate those series in the chart above. Clear the selection to show all again.")

summary_df = pd.DataFrame({
    "Series": labels_all,
    "Latest quarter": [int(series_data[l].iloc[-1]) for l in labels_all],
    "Total across periods": [int(series_data[l].sum()) for l in labels_all],
})

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="multi-row",
    key=TABLE_KEY,
)
