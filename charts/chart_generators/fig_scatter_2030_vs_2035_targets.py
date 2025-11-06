# charts/chart_generators/fig_scatter_2030_vs_2035_targets.py
from __future__ import annotations
import sys
from pathlib import Path
import shutil, yaml
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# ───────────────── Consistent colours (match family palette) ─────────────────
SCENARIO_COLORS = {
    "WEM":        "#1E1BD3",
    "CPP-IRP":    "#d46820",
    "CPP-IRPLight":"#e58e5a",
    "CPP-SAREM":  "#1cdaf3",
    "CPPS":       "#ff6e1a",
}
def color_for(label: str, i: int) -> str:
    return SCENARIO_COLORS.get(label, FALLBACK_CYCLE[i % len(FALLBACK_CYCLE)])

# ───────────────── Layout knobs ─────────────────
LEGEND_POSITION   = "right"  # "right" | "bottom"
AXIS_TITLE_SIZE   = 22
AXIS_TICK_SIZE    = 18
LEGEND_FONT_SIZE  = 18
MARKER_SIZE       = 10
MARKER_OPACITY    = 0.95
MARKER_LINE_WIDTH = 0.6

# ───────────────── Helpers ─────────────────
def _apply_legend(fig: go.Figure) -> None:
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
            margin=dict(l=120, r=220, t=10, b=80),
            legend=dict(
                orientation="v", yanchor="top", y=1,
                xanchor="left", x=1.02, title="", font=dict(size=LEGEND_FONT_SIZE),
            ),
            title=None,
        )

# ───────────────── Generator ─────────────────
def generate_fig_scatter_2030_vs_2035_targets(df: pd.DataFrame, output_dir: str) -> None:
    """
    Scatter: CO₂eq in 2030 (x) vs CO₂eq in 2035 (y).
    Expected columns:
      - Scenario (str)
      - ScenarioKey (e.g., WEM, CPP-IRP, CPP-IRPLight, CPP-SAREM, CPPS)
      - EconomicGrowth (Reference / High / Low)
      - Year_2030 (2030)
      - CO2eq_2030 (float)
      - Year_2035 (2035)
      - CO2eq_2035 (float)
    """
    df = df.copy()

    # Normalize column names defensively
    rename_map = {}
    for c in df.columns:
        lc = c.lower().strip()
        if lc == "scenariokey":
            rename_map[c] = "ScenarioKey"
        elif lc == "economicgrowth":
            rename_map[c] = "EconomicGrowth"
        elif lc in {"co2eq_2030", "co₂eq_2030"}:
            rename_map[c] = "CO2eq_2030"
        elif lc in {"co2eq_2035", "co₂eq_2035"}:
            rename_map[c] = "CO2eq_2035"
        elif lc == "year_2030":
            rename_map[c] = "Year_2030"
        elif lc == "year_2035":
            rename_map[c] = "Year_2035"
    if rename_map:
        df = df.rename(columns=rename_map)

    # Types & clean
    for col in ["CO2eq_2030", "CO2eq_2035"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["ScenarioKey", "EconomicGrowth", "CO2eq_2030", "CO2eq_2035"]).copy()

    # Orders & mappings
    scenario_order = ["WEM", "CPP-IRP", "CPP-IRPLight", "CPP-SAREM", "CPPS"]
    growth_order = ["Reference", "High", "Low"]
    color_map = {k: color_for(k, i) for i, k in enumerate(scenario_order)}
    symbol_map = {"Reference": "circle", "High": "diamond", "Low": "square"}

    # Plot
    fig = px.scatter(
        df,
        x="CO2eq_2030", y="CO2eq_2035",
        color="ScenarioKey",
        symbol="EconomicGrowth",
        color_discrete_map=color_map,
        symbol_map=symbol_map,
        category_orders={"ScenarioKey": scenario_order, "EconomicGrowth": growth_order},
        hover_data={
            "Scenario": True,
            "ScenarioKey": True,
            "EconomicGrowth": True,
            "CO2eq_2030": ":.1f",
            "CO2eq_2035": ":.1f",
        },
        labels={
            "CO2eq_2030": "CO₂eq Emissions in 2030 (Mt)",
            "CO2eq_2035": "CO₂eq Emissions in 2035 (Mt)",
            "ScenarioKey": "Scenario",
            "EconomicGrowth": "Growth rate",
        },
        title=None,
    )

    # Style markers
    fig.update_traces(
        marker=dict(size=MARKER_SIZE, opacity=MARKER_OPACITY,
                    line=dict(width=MARKER_LINE_WIDTH, color="white")),
        selector=dict(mode="markers"),
    )

    # Apply shared layout, legend, axes
    fig = apply_common_layout(fig)
    _apply_legend(fig)
    fig.update_layout(legend_title_text="Scenario, Economic Growth")

    fig.update_xaxes(
        ticks="outside", showgrid=True,
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
        dtick=20,
        range=[280, 440],  # like the example image
        minor=dict(dtick=5, ticks="outside", showgrid=True),
    )
    fig.update_yaxes(
        ticks="outside", showgrid=True,
        dtick=20,
        title_font=dict(size=AXIS_TITLE_SIZE),
        tickfont=dict(size=AXIS_TICK_SIZE),
        range=[200, 400],  # like the example image
        minor=dict(dtick=5, ticks="outside", showgrid=True),
    )

        # ── NDC 2030 guide lines (black) + on-chart labels
    ndc_guides = [(350, "2030 NDC Lower"), (420, "2030 NDC Upper")]
    for xline, label in ndc_guides:
        fig.add_vline(
            x=xline,
            line_width=2,
            line_color="black",
            line_dash="solid",
            layer="above"
        )
        fig.add_annotation(
            x=xline, y=0.8, xref="x", yref="paper",
            text=label,
            showarrow=False,
            yanchor="bottom",
            textangle=-90,
            font=dict(size=14, color="black"),
            bgcolor="rgba(255,255,255,0.7)",  # optional for readability
            bordercolor="black", borderwidth=0  # optional
        )


    # Save
    out = Path(output_dir)
    if not DEV_MODE:
        save_figures(fig, str(out), name="fig_scatter_2030_vs_2035_targets")
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "fig_scatter_2030_vs_2035_targets_data.csv", index=False)

        gal = PROJECT_ROOT / "outputs" / "gallery"
        gal.mkdir(parents=True, exist_ok=True)
        png = out / "fig_scatter_2030_vs_2035_targets_report.png"
        if png.exists():
            shutil.copy2(png, gal / png.name)

# ───────────────────── CLI ─────────────────────
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "data_2030v2035NDCtargets.csv"
    if not default_csv.exists():
        # also try raw/ for your upload flow
        alt = PROJECT_ROOT / "data" / "raw" / "data_2030v2035NDCtargets.csv"
        default_csv = alt if alt.exists() else default_csv
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv)
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig_scatter_2030_vs_2035_targets"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig_scatter_2030_vs_2035_targets(df0, str(out_dir))
