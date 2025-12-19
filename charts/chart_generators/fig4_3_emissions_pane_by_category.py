from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ── config
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# ---------- knobs ----------
WIDTH_PER_FACET = 360
WIDTH_MULTIPLIER = 2.0
WIDTH = 12000    
HEIGHT = 450
LEGEND_FONT = 12
YTITLE_FONT = 16
Y_TICK_FONT = 11   # ← set your desired y-axis tick label size

FACET_TITLE_FONT = 12          # <— smaller facet titles
X_TICK_FONT = 8                # <— much smaller x-tick labels
MARKER_SIZE = 7

scenario_order = [
    "WEM", "CPP-IRP", "CPP-IRPLight", "CPP-SAREM",
    "CPPS", "High Carbon", "Low Carbon"
]
growth_order = ["Reference", "High", "Low"]
symbol_sequence = ["circle", "square", "triangle-up"]

def generate_fig4_2_emissions_pane_by_category(df: pd.DataFrame, output_dir: str) -> None:
    print("▶ Generating Fig 4.2 — Emissions pane by category (2035)")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cols = ["CategoryGroup", "Scenario", "ScenarioKey", "EconomicGrowth", "CO2eq"]
    dfx = df[cols].copy()
    dfx["CO2eq"] = pd.to_numeric(dfx["CO2eq"], errors="coerce")

    present_scen = [s for s in scenario_order if s in dfx["ScenarioKey"].unique()]
    dfx["ScenarioKey"] = pd.Categorical(dfx["ScenarioKey"], categories=present_scen, ordered=True)
    groups = list(dict.fromkeys(dfx["CategoryGroup"].tolist()))
    dfx["CategoryGroup"] = pd.Categorical(dfx["CategoryGroup"], categories=groups, ordered=True)
    dfx["EconomicGrowth"] = pd.Categorical(dfx["EconomicGrowth"], categories=growth_order, ordered=True)

    fig = px.scatter(
        dfx,
        x="ScenarioKey",
        y="CO2eq",
        color="ScenarioKey",
        symbol="EconomicGrowth",
        facet_col="CategoryGroup",
        facet_col_wrap=len(groups),
        facet_col_spacing=0.01,
        category_orders={
            "ScenarioKey": present_scen,
            "EconomicGrowth": growth_order,
            "CategoryGroup": groups,
        },
        labels={
            "ScenarioKey": "",
            "CO2eq": "CO₂eq Emissions (Mt)",
            "EconomicGrowth": "Economic Growth",
        },
        symbol_sequence=symbol_sequence,
    )

    # Apply house style first
    fig = apply_common_layout(fig)

    # Markers
    fig.update_traces(marker=dict(size=MARKER_SIZE, opacity=0.9), selector=dict(mode="markers"))

    # Axes
    fig.update_xaxes(tickangle=-90, showgrid=False, title_text="", tickfont=dict(size=X_TICK_FONT))
    fig.update_yaxes(
    matches="y",
    title_font=dict(size=YTITLE_FONT),
    tickfont=dict(size=Y_TICK_FONT)   # ← y-axis tick size
)


    # Facet titles smaller
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=FACET_TITLE_FONT)))

    # Very wide canvas + legend BELOW
    #width = max(1600, int(WIDTH_PER_FACET * len(groups) * WIDTH_MULTIPLIER))
    fig.update_layout(
        width=WIDTH,
        height=HEIGHT,
        margin=dict(l=80, r=40, t=50, b=170),
        legend=dict(
            title="Scenario,<br>Economic Growth",
            orientation="h",
            x=0.5,  xanchor="center",
            y=-0.22, yanchor="top",
            font=dict(size=LEGEND_FONT),
            itemsizing="trace",
        ),
        showlegend=True,
    )

    if dev_mode:
        print("dev_mode=True — preview only (not saving)")
        return

    save_figures(fig, output_dir, name="fig4_2_emissions_pane_by_category")
    dfx.to_csv(Path(output_dir) / "fig4_2_emissions_pane_by_category_data.csv", index=False)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "emissions_pane_by_category_scenarios.csv"
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_2_emissions_pane_by_category"
    generate_fig4_2_emissions_pane_by_category(df, str(out))
