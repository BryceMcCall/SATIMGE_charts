# charts/chart_generators/fig4_53_scatter_gva_vs_ghgs_diff.py
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

# ───── layout knobs (kept consistent) ─────
LEGEND_POSITION   = "right"
AXIS_TITLE_SIZE   = 20
AXIS_TICK_SIZE    = 20
LEGEND_FONT_SIZE  = 20
MARKER_SIZE       = 14
MARKER_OPACITY    = 0.95
MARKER_LINE_WIDTH = 1.5

# Fixed scenario order (as provided) → stable legend order
SCENARIO_ORDER = [
    "NDC_BASE-RG",
    "NDC_CPP1-RG",
    "NDC_CPP2-RG",
    "NDC_CPP3-RG",
    "NDC_CPP4-RG",
    "NDC_CPP4S-RG",
    "NDC_HCARB-RG",
    "NDC_LCARB-RG",
]

def _apply_legend(fig):
    if LEGEND_POSITION == "bottom":
        fig.update_layout(
            margin=dict(l=120, r=40, t=10, b=120),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                        xanchor="center", x=0.5, title="", font=dict(size=LEGEND_FONT_SIZE)),
            title=None,
        )
    else:
        fig.update_layout(
            margin=dict(l=120, r=320, t=10, b=90),
            legend=dict(orientation="v", yanchor="top", y=1,
                        xanchor="left", x=1.02, title="", font=dict(size=LEGEND_FONT_SIZE)),
            title=None,
        )

def generate_fig4_53_scatter_gva_vs_ghgs_diff(df: pd.DataFrame, output_dir: str) -> None:
    """
    Scatter: NDC GVA (x) vs national GHG emissions (y) for selected scenarios.
    Data labels show the % difference in NDC GVA vs NDC_BASE-RG.

    Expected columns (case/spacing tolerant):
      - 'Scenario'
      - '% Difference in NDC GVA from the 'NDC_BASE-RG' along Scenario'  (string like '-0.40%')
      - 'MtCO2-eq'
      - 'NDC GVA'
    """
    df = df.copy()

        # ── tolerant renaming
    rename = {}
    for c in df.columns:
        lc = c.lower().strip()
        if lc == "scenario":
            rename[c] = "Scenario"
        elif lc in {"mtco2-eq", "co2eq", "mtco2eq"}:
            rename[c] = "MtCO2eq"
        elif "ndc gva" in lc or lc == "gva" or lc == "satimge":
            rename[c] = "GVA"
        elif lc.startswith("% difference"):
            rename[c] = "PctDiff"
    if rename:
        df = df.rename(columns=rename)

    # ── if any duplicate column names resulted from the renaming, keep the last
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep="last")]

    # ── ensure Series (not 2D frames) before numeric coercion
    if isinstance(df.get("GVA"), pd.DataFrame):
        df["GVA"] = df["GVA"].iloc[:, 0]
    if isinstance(df.get("MtCO2eq"), pd.DataFrame):
        df["MtCO2eq"] = df["MtCO2eq"].iloc[:, 0]

    # ── types & clean
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce")
    df["GVA"]     = pd.to_numeric(df["GVA"], errors="coerce")
    df["Scenario"] = df["Scenario"].astype(str)
    df["PctDiff"]  = df["PctDiff"].astype(str)  # keep percents as text labels
    df = df.dropna(subset=["Scenario", "MtCO2eq", "GVA", "PctDiff"])


    # colours: just use the shared fallback cycle stably
    color_map = {s: FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)] for i, s in enumerate(SCENARIO_ORDER)}

    fig = px.scatter(
        df,
        x="GVA",
        y="MtCO2eq",
        color="Scenario",
        color_discrete_map=color_map,
        category_orders={"Scenario": SCENARIO_ORDER},
        hover_data={"Scenario": True, "GVA": ":.0f", "MtCO2eq": ":.0f", "PctDiff": True},
        text="PctDiff",  # ← percentage labels on points
        labels={
            "GVA": "GVA (Billion ZAR)",
            "MtCO2eq": "CO2-eq Emissions (Mt)",
            "Scenario": "Scenario",
        },
        title=None,
    )

    # common style + legend
    fig = apply_common_layout(fig)
    _apply_legend(fig)

    # markers + text styling
    fig.update_traces(
        marker=dict(size=MARKER_SIZE, opacity=MARKER_OPACITY,
                    line=dict(width=MARKER_LINE_WIDTH, color="white")),
        selector=dict(mode="markers"),
        textfont=dict(size=14),
        textposition="top center",
    )

    # axes ranges to match the mock
    fig.update_xaxes(
        range=[5200, 5800],
        ticks="outside", showgrid=True,
        minor=dict(ticks="outside", dtick=50, showgrid=True),
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
    )
    # pad a little around the y data
    ymin = max(0, (df["MtCO2eq"].min() // 10) * 10 - 10)  # ~280 in your example
    ymax = ((df["MtCO2eq"].max() // 10) + 2) * 10         # ~390
    fig.update_yaxes(
        range=[ymin, ymax],
        ticks="outside", showgrid=True,
        minor=dict(ticks="outside", dtick=5, showgrid=True),
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
    )

    # save
    out = Path(output_dir)
    if not DEV_MODE:
        save_figures(fig, str(out), name="fig4_53_scatter_gva_vs_ghgs_diff")
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "fig4_53_scatter_gva_vs_ghgs_diff_data.csv", index=False)
        gal = PROJECT_ROOT / "outputs" / "gallery"
        gal.mkdir(parents=True, exist_ok=True)
        png = out / "fig4_53_scatter_gva_vs_ghgs_diff_report.png"
        if png.exists():
            shutil.copy2(png, gal / png.name)

# ───── CLI ─────
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "GVA_difference_scenarios.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_53_scatter_gva_vs_ghgs_diff"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig4_53_scatter_gva_vs_ghgs_diff(df0, str(out_dir))
