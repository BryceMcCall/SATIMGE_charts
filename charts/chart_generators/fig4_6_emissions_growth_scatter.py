# charts/chart_generators/fig4_6_emissions_growth_scatter.py
from __future__ import annotations
import sys
from pathlib import Path
import shutil, yaml
import pandas as pd
import plotly.express as px

# Allow shared imports when run directly
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, FALLBACK_CYCLE
from charts.common.save import save_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEV_MODE = False
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        DEV_MODE = yaml.safe_load(f).get("dev_mode", False)

# ── styling (kept consistent with other generators)
LEGEND_POSITION   = "right"
AXIS_TITLE_SIZE   = 20
AXIS_TICK_SIZE    = 18
LEGEND_FONT_SIZE  = 18
MARKER_SIZE       = 10
MARKER_LINE_WIDTH = 0

# Colours & symbols to match the image
GROWTH_ORDER  = ["High", "Low", "Reference"]
#GROWTH_COLORS = {"High": "#1F77B4", "Low": "#D62728", "Reference": "#2CA02C"}  # blue, red, green
GROWTH_SYMBOL = {"High": "circle", "Low": "diamond", "Reference": "square"}

def _apply_legend(fig):
    if LEGEND_POSITION == "right":
        fig.update_layout(
            margin=dict(l=100, r=320, t=30, b=120),
            legend=dict(
                orientation="v",
                x=1.02, xanchor="left",
                y=0.9,  yanchor="middle",   # ← center vertically so it’s not at the very top
                title="Economic Growth",
                font=dict(size=LEGEND_FONT_SIZE),
            ),
            title=None,
        )
    else:
        fig.update_layout(
            margin=dict(l=100, r=40, t=30, b=140),
            legend=dict(
                orientation="h",
                x=0.5, xanchor="center",
                y=-0.3, yanchor="top",
                title="Economic Growth",
                font=dict(size=LEGEND_FONT_SIZE),
            ),
            title=None,
        )

def generate_fig4_6_emissions_growth_scatter(
    df: pd.DataFrame, output_dir: str, xtick_labels: dict[str, str] | None = None
) -> None:
    """
    Scatter: category emissions (2035) by economic growth case.

    Expected columns (case/spacing tolerant):
      - 'NDC GHG emisssion cats short'  → Category (e.g., 'A.Electricity', ...)
      - 'NDC growth cats'               → High / Low / Reference
      - 'Scenario'                      → scenario label (hover only)
      - 'MtCO2-eq'                      → y value
    """
    df = df.copy()

    # tolerant renaming
    rename = {}
    for c in df.columns:
        lc = str(c).lower().strip()
        if lc.startswith("ndc ghg"):
            rename[c] = "Category"
        elif "growth" in lc:
            rename[c] = "Growth"
        elif lc in {"mtco2-eq", "co2eq", "mtco2eq"}:
            rename[c] = "MtCO2eq"
        elif lc == "scenario":
            rename[c] = "Scenario"
    if rename:
        df = df.rename(columns=rename)

    # ensure numeric
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce")
    df = df.dropna(subset=["Category", "Growth", "MtCO2eq"])

    # order x-axis alphabetically by the leading letter prefix (A., B., …)
    cats = sorted(df["Category"].unique(), key=str)
    df["Category"] = pd.Categorical(df["Category"], cats, ordered=True)


    # plot
    fig = px.scatter(
        df,
        x="Category",
        y="MtCO2eq",
        color="Growth",
        symbol="Growth",
        #color_discrete_map=GROWTH_COLORS,
        symbol_map=GROWTH_SYMBOL,
        category_orders={"Growth": GROWTH_ORDER, "Category": cats},
        hover_data={"Scenario": True, "MtCO2eq": ":.2f"},
        # 2) labels – change y-axis title
        labels={
            "Category": "",
            "MtCO2eq": "2035 CO₂-eq Emissions (Mt)",   
            "Growth": "Economic Growth",
        },

        title=None,
    )

    # markers & layout
    fig.update_traces(
        marker=dict(size=MARKER_SIZE, line=dict(width=MARKER_LINE_WIDTH, color="white")),
        selector=dict(mode="markers"),
    )
    fig = apply_common_layout(fig)
    _apply_legend(fig)

    # axes: 20-unit y ticks, include negative band for Land
    ymin = min(-25, int(df["MtCO2eq"].min() // 10 * 10) - 5)
    ymax = max(140, int(df["MtCO2eq"].max() // 10 * 10) + 10)
    fig.update_yaxes(
        range=[ymin, ymax],
        dtick=20,
        ticks="outside",
        showgrid=True,
        minor=dict(ticks="outside", dtick=5, showgrid=True),
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
        zeroline=False,
    )
# 3) axis styling – rotate x ticks and keep right margin for legend
    if xtick_labels:
            ticktext = [xtick_labels.get(c, c) for c in cats]
            fig.update_xaxes(
                tickmode="array",
                tickvals=cats,
                ticktext=ticktext,
                ticks="outside",
                showgrid=True,
                tickfont=dict(size=AXIS_TICK_SIZE),
                tickangle=-45,
            )
    else:
            fig.update_xaxes(
                ticks="outside",
                showgrid=True,
                tickfont=dict(size=AXIS_TICK_SIZE),
                tickangle=-90,
            )


    # save
    out = Path(output_dir)
    if not DEV_MODE:
        save_figures(fig, str(out), name="fig4_6_emissions_growth_scatter")
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "fig4_6_emissions_growth_scatter_data.csv", index=False)

        gal = PROJECT_ROOT / "outputs" / "gallery"
        gal.mkdir(parents=True, exist_ok=True)
        png = out / "fig4_6_emissions_growth_scatter_report.png"
        if png.exists():
            shutil.copy2(png, gal / png.name)

# ── CLI ──
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "4_6_emissions_econ_growth_rates_categories_scatter_2035.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv, encoding="utf-8-sig")
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_6_emissions_growth_scatter"
    out_dir.mkdir(parents=True, exist_ok=True)
    pretty = {
        "A.Electricity": "A. Electricity",
        "B.Liquid fuels supply": "B. Liquid fuels<br>supply",
        "C.Industry (combustion and process)": "C. Industry (combustion<br>& process)",
        "D.Transport": "D. Transport",
        "E.Other energy": "E. Other energy",
        "F.Agriculture (non-energy)": "F. Agriculture<br>(non-energy)",
        "G.Land": "G. Land",
        "H.Waste": "H. Waste",
    }
    generate_fig4_6_emissions_growth_scatter(df0, str(out_dir), xtick_labels=pretty)

