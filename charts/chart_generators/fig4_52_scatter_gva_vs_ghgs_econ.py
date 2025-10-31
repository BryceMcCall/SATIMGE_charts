# charts/chart_generators/fig4_52_scatter_gva_vs_ghgs.py
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

# ───────────────── Consistent colours ─────────────────
# FamilyGroup palette to match the reference graphic (keep stable order).
FAMILY_ORDER = [
    "WEM", "CPP-IRP", "CPP-IRPLight", "CPP-SAREM",
    "CPPS", "CPPS Variant", "High Carbon", "Low Carbon",
]
FAMILY_COLORS = {
    "WEM":           "#329FEE",  # blue
    "CPP-IRP":       "#41D541",  # green
    "CPP-IRPLight":  "#FF7F0E",  # orange
    "CPP-SAREM":     "#D62728",  # red
    "CPPS":          "#9345DC",  # purple
    "CPPS Variant":  "#FBD83C",  # yellow-green
    "High Carbon":   "#E377C2",  # pink
    "Low Carbon":    "#7F7F7F",  # grey
}
def _family_color(label: str, i: int) -> str:
    return FAMILY_COLORS.get(label, FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)])

# GDP growth rate → symbols 
GROWTH_ORDER  = ["High", "Low", "Reference"]
GROWTH_SYMBOL = {"High": "circle-open", "Low": "square-open", "Reference": "x-open"}

# ───────────────── Layout knobs (same as 4_4_1) ─────────────────
LEGEND_POSITION   = "right"  # "right" | "bottom"
AXIS_TITLE_SIZE   = 20
AXIS_TICK_SIZE    = 20
LEGEND_FONT_SIZE  = 20
MARKER_SIZE       = 13
MARKER_OPACITY    = 0.95
MARKER_LINE_WIDTH = 3.0  # open markers look nicer with a slightly thicker edge

# ───────────────── Helpers ─────────────────
def _apply_legend(fig):
    if LEGEND_POSITION == "bottom":
        fig.update_layout(
            margin=dict(l=120, r=40, t=10, b=120),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=-0.25,
                xanchor="center", x=0.5,
                title="", font=dict(size=20),
            ),
            title=None,
        )
    else:  # right
        fig.update_layout(
            margin=dict(l=120, r=420, t=10, b=90),
            legend=dict(
                orientation="v",
                yanchor="top", y=1,
                xanchor="left", x=1.02,
                title="", font=dict(size=20),
            ),
            title=None,
        )
def _legend_growth_first(fig):
    fig.update_layout(legend_traceorder="grouped")
    for tr in fig.data:
        title = getattr(getattr(tr, "legendgrouptitle", None), "text", "")
        if title == "Scenario: GDP growth rate":
            tr.legendrank = 0
        elif title == "Scenario: FamilyGroup":
            tr.legendrank = 1
            
# ───────────────── Generator ─────────────────
def generate_fig4_52_scatter_gva_vs_ghgs(df: pd.DataFrame, output_dir: str) -> None:
    """
    Scatter: NDC GVA vs national GHG emissions (2035).

    Expected columns (case/spacing tolerant):
      - 'Scenario'         → scenario code (hover)
      - 'ScenarioKey'      → family group (color)
      - 'EconomicGrowth'   → High/Low/Reference (shape)
      - 'CO2eq'            → x-axis (MtCO2-eq)
      - 'SATIMGE'          → y-axis (NDC GVA)
    """
    df = df.copy()

    # Tolerant renaming
    rename = {}
    for c in df.columns:
        lc = c.lower().strip()
        if lc == "scenario":
            rename[c] = "Scenario"
        elif "scenariokey" in lc or lc == "familygroup":
            rename[c] = "Family"
        elif "economicgrowth" in lc or lc == "gdp_growth" or lc == "growth":
            rename[c] = "Growth"
        elif lc in {"co2eq", "mtco2-eq", "mtco2eq"}:
            rename[c] = "CO2eq"
        elif lc in {"satimge", "gva", "ndc gva"}:
            rename[c] = "GVA"
    if rename:
        df = df.rename(columns=rename)

    # Types & clean
    df["CO2eq"] = pd.to_numeric(df["CO2eq"], errors="coerce")
    df["GVA"]   = pd.to_numeric(df["GVA"], errors="coerce")
    df["Family"] = df["Family"].astype(str)
    df["Growth"] = df["Growth"].astype(str)
    df = df.dropna(subset=["Scenario", "Family", "Growth", "CO2eq", "GVA"])

    # Orders & maps
    fam_colors = {k: _family_color(k, i) for i, k in enumerate(FAMILY_ORDER)}
    fig = px.scatter(
        df,
        x="CO2eq",
        y="GVA",
        color="Family",
        symbol="Growth",
        color_discrete_map=fam_colors,
        category_orders={"Family": FAMILY_ORDER, "Growth": GROWTH_ORDER},
        symbol_map=GROWTH_SYMBOL,
        hover_data={"Scenario": True, "CO2eq": ":.1f", "GVA": ":.0f"},
        labels={
            "CO2eq": "CO₂-eq Emissions (Mt)",
            "GVA": "GVA (Billion 2022 ZAR)",
            "Family": "Scenario: FamilyGroup",
            "Growth": "Scenario: GDP growth rate",
        },
        title=None,
    )
    fig = apply_common_layout(fig)
    _apply_legend(fig)

    # Style (mirror 4_4_1)
    fig.update_traces(
        marker=dict(
            size=MARKER_SIZE,
            opacity=MARKER_OPACITY,
            line=dict(width=MARKER_LINE_WIDTH, color="rgba(0,0,0,0.6)"),
        ),
        selector=dict(mode="markers"),
    )
    _legend_growth_first(fig)
    # Axes
    fig.update_xaxes(
        range=[200, 400],
        ticks="outside", showgrid=True,
        minor=dict(ticks="outside", dtick=10, showgrid=True),
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
        #rangemode="tozero",
    )
    fig.update_yaxes(
        dtick=200,
        range=[4400, 6300],
        ticks="outside", showgrid=True,
        minor=dict(ticks="outside", dtick=50, showgrid=True),
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
        rangemode="tozero",
    )

    # Save artifacts (PNG + SVG + data + gallery copy)
    out = Path(output_dir)
    if not DEV_MODE:
        save_figures(fig, str(out), name="fig4_52_scatter_gva_vs_ghgs")
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "fig4_52_scatter_gva_vs_ghgs_data.csv", index=False)

        gal = PROJECT_ROOT / "outputs" / "gallery"
        gal.mkdir(parents=True, exist_ok=True)
        png = out / "fig4_52_scatter_gva_vs_ghgs_report.png"
        if png.exists():
            shutil.copy2(png, gal / png.name)

# ───────────────────── CLI ─────────────────────
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "GVA_v_Emissions_scenarios.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_52_scatter_gva_vs_ghgs"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig4_52_scatter_gva_vs_ghgs(df0, str(out_dir))
