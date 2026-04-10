import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Load data
imm = pd.read_csv("immigration.csv")
emi = pd.read_csv("emigration.csv")

# Aggregate to total Denmark per year
imm_yr = imm.groupby("year")["count"].sum().reset_index(name="immigration")
emi_yr = emi.groupby("year")["count"].sum().reset_index(name="emigration")

df = imm_yr.merge(emi_yr, on="year")
df["net"] = df["immigration"] - df["emigration"]

print(df.to_string(index=False))

# Okabe-Ito colorblind-safe palette
COL_IMM = "#0072B2"   # blue
COL_EMI = "#D55E00"   # vermillion
COL_NET = "#009E73"   # green (for net label)

years = df["year"].astype(str).tolist()
x = np.arange(len(years))
width = 0.55

fig, ax = plt.subplots(figsize=(10, 6))

# Immigration bars: positive, above 0
ax.bar(x, df["immigration"], width, color=COL_IMM, alpha=0.85, zorder=3, label="Immigration")

# Emigration bars: negative, below 0
ax.bar(x, -df["emigration"], width, color=COL_EMI, alpha=0.85, zorder=3, label="Emigration")

# Net migration markers (dots + values)
for i, row in df.iterrows():
    net = row["net"]
    # Small horizontal line at net migration level
    ax.plot([x[i] - width / 2, x[i] + width / 2], [net, net],
            color="black", linewidth=2, zorder=5)
    ax.annotate(
        f"{net:+,.0f}",
        xy=(x[i], net),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color="black",
    )

# Zero line
ax.axhline(0, color="black", linewidth=0.8, zorder=4)

# Axis labels on immigration bars
for i, row in df.iterrows():
    ax.text(x[i], row["immigration"] + 1500, f"{row['immigration']:,.0f}",
            ha="center", va="bottom", fontsize=8, color=COL_IMM, fontweight="bold")
    ax.text(x[i], -row["emigration"] - 1500, f"{row['emigration']:,.0f}",
            ha="center", va="top", fontsize=8, color=COL_EMI, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(years, fontsize=11)
ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("People", fontsize=12)
ax.set_title("Denmark: Immigration & Emigration 2020–2025\n(net migration shown as black line + value)", fontsize=13, pad=14)

# Y axis: format with commas, show absolute values with +/- labels
def fmt(v, _):
    return f"{abs(v):,.0f}"
ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt))

# Legend
imm_patch = mpatches.Patch(color=COL_IMM, alpha=0.85, label="Immigration")
emi_patch = mpatches.Patch(color=COL_EMI, alpha=0.85, label="Emigration")
net_line = plt.Line2D([0], [0], color="black", linewidth=2, label="Net migration")
ax.legend(handles=[imm_patch, emi_patch, net_line], loc="upper left", fontsize=10)

ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("poc_net_migration.png", dpi=150, bbox_inches="tight")
print("\nSaved poc_net_migration.png")
plt.show()
