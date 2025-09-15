# Emissions line chart for all scenarios in the NDC project, colour coded by scenario family

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout, color_for, color_sequence
from charts.common.save import save_figures

import yaml
project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False


def generate_fig_line_emissions_ALL(df: pd.DataFrame, output_dir: str) -> None:
    print("generating line emissions chart for all scenarios ")

    year_select = range(2024,2036,1)

    scenario_colors = {
        'CPP-IRP': "#d46820",  
        'CPP-IRPLight': "#e58e5a",
        'CPP-SAREM': "#1cdaf3",
        'CPPS': "#ff6e1a",
        'High Carbon': "#ff0000",
        'Low Carbon': "#008000",
        'WEM': "#1E1BD3"
    }

    cols = ["Scenario","ScenarioKey","Year","CO2eq"]

    dfx = df[(df["Year"].isin(year_select))][cols]
    dfx['CO2eq'] = dfx['CO2eq']*0.001 #convert to Mt

    data = (
            dfx.groupby(["Scenario","ScenarioKey","Year"])["CO2eq"]
            .sum()
            .reset_index()
            )



    fig = go.Figure()
    # Use the order from scenario_colors for consistent legend and color mapping
    for scenario in scenario_colors:
        subset = data[data["ScenarioKey"] == scenario]
        if not subset.empty:
            fig.add_trace(go.Scatter(
                x=subset["Year"],
                y=subset["CO2eq"],
                mode="lines",
                name=scenario,
                line=dict(width=1.5, color=scenario_colors[scenario]),
                showlegend=True
            ))

    fig.update_layout(
    title="CO₂ Emissions by Scenario",
    xaxis_title="Year",
    yaxis_title="Mt CO₂eq",
    legend_title="Scenario",
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.02
        )
    )

    

    fig = apply_common_layout(fig)

    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="Mt CO₂eq",
        xaxis=dict(
            range=[2024, 2035],
            tickmode="linear",
            dtick=1),

        legend=dict(
            title = "",
            orientation="h",
            yanchor="top",
            #xanchor="left",
            #x = 0.4,
            #y = -0.15  #move it to underneath
        )
    )

    print("saving generate_fig_line_emissions_ALL")
    save_figures(fig, output_dir, name="fig_line_emissions_ALL")

    if not dev_mode:
        data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    parquet_path = project_root / "data/processed/processed_dataset.parquet"
    # Only load necessary columns
    columns_needed = ["Scenario", "Year", "CO2eq"]
    # Read in chunks and filter as we go (if pyarrow is available)
    try:
        import pyarrow.parquet as pq
        selected_scenarios = ["NDC_BASE-LG", "NDC_BASE-RG", "NDC_BASE-HG"]
        year_select = list(range(2024, 2036))
        table = pq.read_table(
            parquet_path,
            columns=columns_needed,
        )
        df = table.to_pandas()
        df = df[(df["Scenario"].isin(selected_scenarios)) & (df["Year"].isin(year_select))]
    except ImportError:
        # Fallback to pandas, but still only load columns
        df = pd.read_parquet(parquet_path, columns=columns_needed)
        selected_scenarios = ["NDC_BASE-LG", "NDC_BASE-RG", "NDC_BASE-HG"]
        year_select = list(range(2024, 2036))
        df = df[(df["Scenario"].isin(selected_scenarios)) & (df["Year"].isin(year_select))]

    out = project_root / "outputs/charts_and_data/generate_fig_line_emissions_ALL"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_line_emissions_ALL(df, str(out))
