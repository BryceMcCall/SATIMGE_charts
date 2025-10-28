# charts/chart_generators/fig4_4_1_scatter_elec_vs_total.py
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
# Curtailed = orange (same hue we use for WEM), Not curtailed = blue.
COLOR_MAP = {
    "Curtailed":     "#FF7F0E",
    "Not curtailed": "#1F77B4",
}
def color_for(label: str, i: int) -> str:
    return COLOR_MAP.get(label, FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)])

# ───────────────── Layout knobs ─────────────────
LEGEND_POSITION   = "right"  # "right" | "bottom"
AXIS_TITLE_SIZE   = 22
AXIS_TICK_SIZE    = 20
LEGEND_FONT_SIZE  = AXIS_TITLE_SIZE
MARKER_SIZE       = 11
MARKER_OPACITY    = 0.9
MARKER_LINE_WIDTH = 0.5

# ───────────────── Helpers ─────────────────
def _apply_legend(fig):
    if LEGEND_POSITION == "bottom":
        fig.update_layout(
            margin=dict(l=120, r=40, t=10, b=110),
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.22,
                xanchor="center", x=0.5, title="", font=dict(size=LEGEND_FONT_SIZE),
            ),
            title=None,
        )
    else:  # right
        fig.update_layout(
            margin=dict(l=120, r=110, t=10, b=80),
            legend=dict(
                orientation="v", yanchor="top", y=1,
                xanchor="left", x=1.02, title="", font=dict(size=LEGEND_FONT_SIZE),
            ),
            title=None,
        )

# ───────────────── Generator ─────────────────
def generate_fig4_4_1_scatter_elec_vs_total(df: pd.DataFrame, output_dir: str) -> None:
    """
    Scatter: Electricity sector emissions vs national GHG emissions (2035).
    Expects columns:
      - 'NDC scenarios sasol curtailed'  (category: Curtailed / Not curtailed)
      - 'Scenario'                       (scenario code)
      - 'Year'                           (=2035 for all rows)
      - 'Electricity sector emissions - Mt CO2-eq'  (x)
      - 'MtCO2-eq'                       (y, national)
    """
    df = df.copy()

    # Normalize column names (be tolerant of minor variations)
    rename_map = {}
    for c in df.columns:
        lc = c.lower().strip()
        if lc.startswith("ndc scenarios") or lc.startswith("ndc scen"):
            rename_map[c] = "CurtailStatus"
        elif lc in {"scenario"}:
            rename_map[c] = "Scenario"
        elif lc == "year":
            rename_map[c] = "Year"
        elif "electricity sector emissions" in lc:
            rename_map[c] = "ElecEmis"
        elif lc in {"mtco2-eq", "mtco2eq", "mtco2e"}:
            rename_map[c] = "NatEmis"
    if rename_map:
        df = df.rename(columns=rename_map)

    # Keep 2035 and clean types
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["ElecEmis"] = pd.to_numeric(df["ElecEmis"], errors="coerce")
    df["NatEmis"] = pd.to_numeric(df["NatEmis"], errors="coerce")
    df = df.dropna(subset=["CurtailStatus", "Scenario", "Year", "ElecEmis", "NatEmis"])
    df = df[df["Year"] == 2035].copy()

    # Standardize curtailed flag values
    df["CurtailStatus"] = df["CurtailStatus"].map(
        {"Curtailed": "Curtailed", "Not curtailed": "Not curtailed"}
    ).fillna(df["CurtailStatus"])

    # Plot
    order = ["Not curtailed", "Curtailed"]  # shows orange on top if legend right
    color_map = {k: color_for(k, i) for i, k in enumerate(order)}

    fig = px.scatter(
        df,
        x="ElecEmis", y="NatEmis",
        color="CurtailStatus",
        color_discrete_map=color_map,
        category_orders={"CurtailStatus": order},
        hover_data={"Scenario": True, "ElecEmis": ":.2f", "NatEmis": ":.2f"},
        labels={
            "ElecEmis": "Electricity sector emissions in 2035 (MtCO₂-eq)",
            "NatEmis": "National GHG emissions in 2035 (MtCO₂-eq)",
            "CurtailStatus": "Secunda Status",
        },
        title=None,
    )

    # Style: markers, grids, minor ticks
    fig.update_traces(
        marker=dict(size=MARKER_SIZE, opacity=MARKER_OPACITY,
                    line=dict(width=MARKER_LINE_WIDTH, color="white")),
        selector=dict(mode="markers"),
    )
    fig = apply_common_layout(fig)
    _apply_legend(fig)

    fig.update_legends(title_text="Secunda Production", font=dict(size=20))

    fig.update_xaxes(
        ticks="outside", showgrid=True,
        minor=dict(ticks="outside", dtick=5, showgrid=True),  # minor grid every 5 Mt on x
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
        rangemode="tozero",
    )
    fig.update_yaxes(
        ticks="outside", showgrid=True,
        minor=dict(ticks="outside", dtick=10, showgrid=True),  # minor grid every 10 Mt on y
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
        rangemode="tozero",
    )

# Squeeze the inner plotting area without changing exported pixel size
    fig.update_layout(margin=dict(l=140, r=400, t=10, b=90))  # r was 110; bump to ~200



    # Save
    out = Path(output_dir)
    if not DEV_MODE:
        save_figures(fig, str(out), name="fig4_4_1_scatter_elec_vs_total")
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "fig4_4_1_scatter_elec_vs_total_data.csv", index=False)

        gal = PROJECT_ROOT / "outputs" / "gallery"
        gal.mkdir(parents=True, exist_ok=True)
        png = out / "fig4_4_1_scatter_elec_vs_total_report.png"
        if png.exists():
            shutil.copy2(png, gal / png.name)

# ───────────────────── CLI ─────────────────────
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "4.4.1_scatter_elec_emissions_vs_total.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_4_1_scatter_elec_vs_total"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig4_4_1_scatter_elec_vs_total(df0, str(out_dir))