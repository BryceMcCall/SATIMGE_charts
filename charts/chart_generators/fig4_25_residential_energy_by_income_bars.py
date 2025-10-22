# charts/chart_generators/fig4_25_residential_energy_by_income_bars.py
# -*- coding: utf-8 -*-
"""
Fig 4.25 — Household energy consumption by income group (PJ and % shares)
Aligned panels, clean labels, normal save + gallery copy.
"""

from __future__ import annotations
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ── Project paths ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "4_25_residential_energy_consump_by_income_cat_bar.csv"
OUTPUT_STEM = "fig4_25_residential_energy_by_income_bars"

# ── Try the project's saver; provide a safe fallback ─────────────────────────
try:
    from charts.common.save import save_matplotlib_fig  # type: ignore

    def save_with_gallery(fig):
        save_matplotlib_fig(fig, OUTPUT_STEM, subdir=None, gallery=True,
                            formats=("png", "svg", "pdf"), dpi=300)
except Exception:
    def save_with_gallery(fig):
        charts_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / OUTPUT_STEM
        gallery_dir = PROJECT_ROOT / "outputs" / "gallery" / OUTPUT_STEM
        charts_dir.mkdir(parents=True, exist_ok=True)
        gallery_dir.mkdir(parents=True, exist_ok=True)
        png = charts_dir / f"{OUTPUT_STEM}.png"
        svg = charts_dir / f"{OUTPUT_STEM}.svg"
        pdf = charts_dir / f"{OUTPUT_STEM}.pdf"
        fig.savefig(png, dpi=300, bbox_inches="tight")
        fig.savefig(svg, bbox_inches="tight")
        fig.savefig(pdf, bbox_inches="tight")
        shutil.copy2(png, gallery_dir / png.name)
        print(f"Saved to:\n  {charts_dir}\n  {gallery_dir}")

# ── Styling knobs (easy to tweak later) ──────────────────────────────────────
LEGEND_FONTSIZE = 14
AXIS_LABEL_FONTSIZE = 18
TICK_FONTSIZE = 12
BAR_LABEL_FONTSIZE = 11
XTICK_ROTATION = -45
BAR_EDGE_WIDTH = 0
ABS_YLABEL = "PJ consumed"
SHARE_YLABEL = "Share of household category"
ORDER_YEARS = [2024, 2030, 2035]
ORDER_INCOME = ["HighIncome", "MiddleIncome", "LowIncome"]
ORDER_FUELS = ["Coal", "Kerosene", "LPG", "Gas", "Electricity", "Biowood"]

# Colour convention (Electricity must remain exact)
FUEL_COLORS = {
    "Coal":        "#4D4D4D",
    "Kerosene":    "#C49A00",
    "LPG":         "#F1C40F",
    "Gas":         "#D3543A",
    "Electricity": "#6F63B6",
    "Biowood":     "#2E8B57",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _coerce_percent(x):
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float)):
        return (x / 100.0) if x > 1 else float(x)
    s = str(x).strip().replace("%", "").replace(",", "")
    try:
        v = float(s)
        return (v / 100.0) if v > 1 else v
    except ValueError:
        return np.nan

def _prep(df_raw: pd.DataFrame):
    df = df_raw.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df[df["Year"].isin(ORDER_YEARS)]
    df["share"] = df["% of Total SATIMGE"].apply(_coerce_percent)
    df.rename(columns={"SATIMGE": "PJ", "Commodity Short Description": "Fuel"}, inplace=True)
    df["Subsector"] = pd.Categorical(df["Subsector"], ORDER_INCOME, ordered=True)
    df["Fuel"] = pd.Categorical(df["Fuel"], ORDER_FUELS, ordered=True)
    # totals for y-limit on the top panel
    totals = (
        df.pivot_table(index=["Subsector", "Year"], columns="Fuel",
                       values="PJ", aggfunc="sum", fill_value=0, observed=False)
          .sum(axis=1)
    )
    abs_ymax = float(totals.max()) * 1.10  # 10% headroom
    return df, abs_ymax

def _x_positions():
    """
    Shared x positions: strictly 9 slots (3 years × 3 income groups), NO gaps.
    """
    positions = []
    labels = []
    centers = []
    idx = 0
    yrs_per_grp = len(ORDER_YEARS)
    for inc in ORDER_INCOME:
        start = idx
        for y in ORDER_YEARS:
            positions.append(idx)
            labels.append(str(y))
            idx += 1
        centers.append(start + (yrs_per_grp - 1) / 2.0)
    return np.array(positions), labels, np.array(centers)

def _plot_stacked(ax, df, value_col, ylabel, ylim=None, label_threshold=None):
    x_all, year_labels, centers = _x_positions()
    width = 0.8

    # initialise bottoms
    bottoms = np.zeros_like(x_all, dtype=float)

    for fuel in ORDER_FUELS:
        seg = (
            df[df["Fuel"] == fuel]
            .pivot_table(index=["Subsector", "Year"], values=value_col,
                         aggfunc="sum", observed=False)
        )

        vals = []
        for inc in ORDER_INCOME:
            for y in ORDER_YEARS:
                try:
                    vals.append(float(seg.loc[(inc, y)][value_col]))
                except Exception:
                    vals.append(0.0)
        vals = np.array(vals, dtype=float)  # length must be 9
        ax.bar(x_all, vals, width,
               bottom=bottoms,
               color=FUEL_COLORS.get(fuel, "#777777"),
               edgecolor="none" if BAR_EDGE_WIDTH == 0 else "white",
               linewidth=BAR_EDGE_WIDTH,
               label=fuel)

        bottoms += vals

        # Optional internal labels for share panel
        if value_col == "share" and label_threshold is not None:
            mids = bottoms - vals / 2.0
            for xi, v, mid in zip(x_all, vals, mids):
                if v >= label_threshold:
                    ax.text(xi, mid, f"{v*100:.0f}%", ha="center", va="center",
                            fontsize=BAR_LABEL_FONTSIZE, color="black")

    ax.set_xticks(x_all)
    ax.set_xticklabels(year_labels, rotation=XTICK_ROTATION, ha="right", fontsize=TICK_FONTSIZE)
    ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
    ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(axis="y", linestyle="-", alpha=0.15)

    # Income headings above groups
    y_top = ax.get_ylim()[1]
    for inc, cx in zip(ORDER_INCOME, centers):
        ax.text(cx, y_top * 1.01, inc, ha="center", va="bottom", fontsize=TICK_FONTSIZE)

def main():
    df_raw = pd.read_csv(DATA_PATH, encoding="utf-8")
    df, abs_ymax = _prep(df_raw)

    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1, figsize=(16, 9), constrained_layout=True, sharex=True
    )

    # Top: absolute PJ
    _plot_stacked(ax_top, df, value_col="PJ", ylabel=ABS_YLABEL, ylim=(0, abs_ymax))

    # Bottom: shares
    _plot_stacked(ax_bot, df, value_col="share", ylabel=SHARE_YLABEL,
                  ylim=(0, 1.0001), label_threshold=0.04)
    ax_bot.set_yticks(np.linspace(0, 1, 6))
    ax_bot.set_yticklabels([f"{int(t*100)}%" for t in np.linspace(0, 1, 6)],
                           fontsize=TICK_FONTSIZE)

    # Tidy spines
    for ax in (ax_top, ax_bot):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # Legend (right side)
    handles, labels = ax_top.get_legend_handles_labels()
    ax_top.legend(handles, labels, loc="center left", bbox_to_anchor=(1.02, 0.5),
                  frameon=False, fontsize=LEGEND_FONTSIZE, title=None)

    save_with_gallery(fig)
    plt.close(fig)

if __name__ == "__main__":
    main()
