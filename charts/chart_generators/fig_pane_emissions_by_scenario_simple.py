# charts/chart_generators/fig_pane_emissions_by_scenario.py
#simpler version
# charts/chart_generators/fig_pane_emissions_by_scenario_simple.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yaml

# ── safe import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures


# ── config
config_path = PROJECT_ROOT / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f) or {}
    DEV_MODE = bool(_CFG.get("dev_mode", False))
else:
    DEV_MODE = False


def generate_fig_emissions_by_scenario_growth(df: pd.DataFrame, output_dir: str) -> None:
    """
    Emissions by scenario, 3 growth rates (unconstrained only):
      - No facets
      - ScenarioKey on x-axis
      - 3 points per scenario (EconomicGrowth) with deterministic offsets
      - Collapse CPPS Variant -> CPPS
      - Remove 'Additional mitigation' by filtering CarbonBudget == Unconstrained
    """
    print("▶ Generating: emissions by scenario (3 growth rates, unconstrained only)")
    print(f"dev_mode={DEV_MODE}  out={output_dir}")

    dfx = df.copy()

    # If Year exists, keep 2035 snapshot
    if "Year" in dfx.columns:
        dfx = dfx[dfx["Year"] == 2035].copy()

    required = ["ScenarioKey", "EconomicGrowth", "CarbonBudget", "CO2eq"]
    missing = [c for c in required if c not in dfx.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    dfx["CO2eq"] = pd.to_numeric(dfx["CO2eq"], errors="coerce")

    # Collapse CPPS Variant → CPPS
    dfx["ScenarioKey"] = dfx["ScenarioKey"].replace({"CPPS Variant": "CPPS"})

    # Harmonise budget labels and keep only Unconstrained
    dfx["CarbonBudget"] = dfx["CarbonBudget"].replace({
        "No Budget": "Unconstrained",
        "Constrained": "Additional mitigation",
    })
    dfx = dfx[dfx["CarbonBudget"] == "Unconstrained"].copy()
    dfx = dfx.dropna(subset=["ScenarioKey", "EconomicGrowth", "CO2eq"])

    # Scenario order
    scenario_order = ["WEM", "CPP-IRP", "CPP-IRPLight", "CPP-SAREM", "CPPS", "High Carbon", "Low Carbon"]
    present_scen = [s for s in scenario_order if s in set(dfx["ScenarioKey"].astype(str))]
    if not present_scen:
        present_scen = sorted(dfx["ScenarioKey"].astype(str).unique().tolist())

    # Growth order (best effort)
    growth_order_pref = ["Low", "Medium", "High"]
    present_growth = [g for g in growth_order_pref if g in set(dfx["EconomicGrowth"].astype(str))]
    if not present_growth:
        # fallback to alphabetical but stable
        present_growth = sorted(dfx["EconomicGrowth"].astype(str).unique().tolist())

    # Deterministic offsets (so points don't overlap)
    # Example offsets: [-0.22, 0, 0.22] for three growth rates
    if len(present_growth) == 1:
        offsets = {present_growth[0]: 0.0}
    else:
        step = 0.22
        center = (len(present_growth) - 1) / 2.0
        offsets = {g: (i - center) * step for i, g in enumerate(present_growth)}

    # Base x positions for scenarios
    scen_to_x = {s: i for i, s in enumerate(present_scen)}
    dfx["x"] = dfx["ScenarioKey"].astype(str).map(scen_to_x)
    dfx["x_off"] = dfx["EconomicGrowth"].astype(str).map(offsets)
    dfx["x_plot"] = dfx["x"] + dfx["x_off"]

    # Colors for growth rates (Plotly default qualitative palette)
    palette = px.colors.qualitative.Plotly
    growth_to_color = {g: palette[i % len(palette)] for i, g in enumerate(present_growth)}

    fig = go.Figure()

    # One trace per growth rate (clean legend)
    for g in present_growth:
        sub = dfx[dfx["EconomicGrowth"].astype(str) == g].copy()
        fig.add_trace(
            go.Scatter(
                x=sub["x_plot"],
                y=sub["CO2eq"],
                mode="markers",
                name=str(g),
                marker=dict(size=12, opacity=0.95, color=growth_to_color[g]),
                hovertemplate="Scenario: %{customdata[0]}<br>Growth: %{customdata[1]}<br>CO₂eq: %{y:.1f} Mt<extra></extra>",
                customdata=sub[["ScenarioKey", "EconomicGrowth"]].to_numpy(),
            )
        )

    # Common layout styling
    apply_common_layout(fig, image_type="report")

    # X axis as categorical labels at integer positions
    fig.update_xaxes(
        title_text="",
        tickmode="array",
        tickvals=list(range(len(present_scen))),
        ticktext=present_scen,
        tickangle=-35,
        range=[-0.6, len(present_scen) - 0.4],
        showgrid=False,
        zeroline=False,
    )

    # Y axis
    fig.update_yaxes(
        title="CO₂eq Emissions (Mt)",
        range=[200, 450],
        tick0=200,
        dtick=25,
        minor=dict(
            ticks="outside",
            showgrid=True,
            dtick=5,
        ),
    )

    fig.update_layout(
        title_text="",
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.02, xanchor="left",
            y=1.0, yanchor="top",
            font=dict(size=16),
            title_text="Economic Growth",
        ),
        margin=dict(l=110, r=200, t=20, b=80),
        height=520,
    )

    if DEV_MODE:
        print("dev_mode=True — preview only (not saving)")
        return

    outp = Path(output_dir)
    outp.mkdir(parents=True, exist_ok=True)
    save_figures(fig, str(outp), name="fig_emissions_by_scenario_growth")
    dfx.to_csv(outp / "fig_emissions_by_scenario_growth_data.csv", index=False)

    print("✓ Saved fig_emissions_by_scenario_growth")


if __name__ == "__main__":
    data_path = PROJECT_ROOT / "data" / "processed" / "data_Scenario_Pane_2035.csv"
    df = pd.read_csv(data_path)

    out = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig_emissions_by_scenario_growth"
    generate_fig_emissions_by_scenario_growth(df, str(out))
