# charts/chart_generators/fig4_2_pane_emissions_by_scenario.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml

# ── safe import path
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


def generate_fig4_2_pane_emissions_by_scenario(df: pd.DataFrame, output_dir: str) -> None:
    """
    Pane chart: CO2eq (Mt) by CarbonBudget and EconomicGrowth, faceted by ScenarioKey (2035).
    - Two x-ticks per pane: Unconstrained vs Additional mitigation
    - Single horizontal row of facets
    - Shared y-axis fixed to 200–400 Mt
    """
    print("▶ Generating Fig 5.1.2 — pane emissions by scenario")
    print(f"dev_mode={dev_mode}  out={output_dir}")

    # ── columns & (optional) year filter if present
    cols = ["Scenario", "ScenarioKey", "EconomicGrowth", "CarbonBudget", "CO2eq"]
    dfx = df.copy()
    if "Year" in dfx.columns:
        dfx = dfx[dfx["Year"] == 2035]
    dfx = dfx[cols].copy()

    # ---- NO RESCALE (data already in Mt) ----
    dfx["CO2eq"] = pd.to_numeric(dfx["CO2eq"], errors="coerce")

    # Budget label harmonization (guide image)
    dfx["CarbonBudget"] = dfx["CarbonBudget"].replace({
        "No Budget": "Unconstrained",
        "Constrained": "Additional mitigation"
    })
    budget_order = ["Unconstrained", "Additional mitigation"]
    dfx = dfx[dfx["CarbonBudget"].isin(budget_order)]

    # Map budgets to numeric x-positions for even spacing + custom tick text
    pos_map = {"Unconstrained": -0.5, "Additional mitigation": 0.5}
    dfx["xpos"] = dfx["CarbonBudget"].map(pos_map)

    # Facet order
    scenario_order = [
        "WEM", "CPP-IRP", "CPP-IRPLight", "CPP-SAREM",
        "CPPS", "CPPS Variant", "High Carbon", "Low Carbon"
    ]
    present = [s for s in scenario_order if s in dfx["ScenarioKey"].unique()]
    dfx["ScenarioKey"] = pd.Categorical(dfx["ScenarioKey"], categories=present, ordered=True)

    # ── Plot
    fig = px.scatter(
        dfx,
        x="xpos",
        y="CO2eq",
        color="EconomicGrowth",
        facet_col="ScenarioKey",
        facet_col_wrap=len(present),          # single horizontal row
        facet_col_spacing=0.012,
        labels={"CO2eq": "CO₂eq Emissions (Mt)", "EconomicGrowth": "Economic Growth"},
    )
    # Style
    fig = apply_common_layout(fig)

    # x-axes: exactly two ticks at our custom positions, fixed range
    fig.update_xaxes(
        tickmode="array",
        tickvals=[-0.5, 0.5],
        ticktext=["Unconstrained","Additional mitigation"],  
        range=[-1, 1],
        showgrid=False,
        zeroline=False,
        title_text="",
        tickangle=-90
    )


    fig.update_yaxes(
        title_font=dict(size=20),
        range=[200, 400],
        matches="y",        
        tick0=200,
        dtick=20,
        minor=dict(
            ticks="outside",
            showgrid=True,
            dtick=5

        ),
)

    fig.update_traces(marker=dict(size=10, opacity=0.9))
    fig.update_layout(
        width=3000, height=420,
        margin=dict(l=100, r=60, t=40, b=90),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.02, xanchor="left",   # right side
            y=1.0,  yanchor="top",
            font=dict(size=18),
            title_text="Economic Growth",
        ),
)


    # Clean facet titles
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=16)))

    # ── Save
    if dev_mode:
        print("dev_mode=True — preview only (not saving)")
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    save_figures(fig, output_dir, name="fig4_2_pane_emissions_by_scenario")
    dfx.to_csv(Path(output_dir) / "fig4_2_pane_emissions_by_scenario_data.csv", index=False)


if __name__ == "__main__":
    # Use the usual dataset location you attached
    data_path = project_root / "data" / "processed" / "data_Scenario_Pane_2035.csv"
    df = pd.read_csv(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig4_2_pane_emissions_by_scenario"
    generate_fig4_2_pane_emissions_by_scenario(df, str(out))
