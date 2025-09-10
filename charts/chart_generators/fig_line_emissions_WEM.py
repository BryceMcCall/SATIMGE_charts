# Emissions line chart for WEM for the three growth scenarios
# 
# 

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


def generate_fig_line_emissions_WEM(df: pd.DataFrame, output_dir: str) -> None:
    print("generating line emissions chart for three WEM scenarios")

    selected_scenarios = ["NDC_BASE-LG", "NDC_BASE-RG", "NDC_BASE-HG"]
    #select_growth_scenarios =["Reference", "Low", "High"]
    year_select = range(2024,2036,1)

    # Define custom color mapping
    growth_colours = {
        "Low": "#8ac41f",  # fixed hex color
        "Reference": "#1E1BD3",  
        "High": "#d46820",  
    }


    dfx = df[(df["Scenario"].isin(selected_scenarios))&
            (df["Year"].isin(year_select))]

    data = (
        dfx.groupby(["EconomicGrowth", "Year"])["CO2eq"]
        .sum()
        .reset_index()
        )

    data['CO2eq'] = data['CO2eq']*0.001 #convert to Mt

    # Define the desired legend order
    legend_order = ["Low","Reference","High"]

    fig = go.Figure()
    for scenario in legend_order:
        subset = data[data["EconomicGrowth"] == scenario]
        fig.add_trace(go.Scatter(
            x=subset["Year"],
            y=subset["CO2eq"],
            mode="lines",
            name = scenario,
            line=dict(width=2, color= growth_colours.get(scenario)),
            showlegend=True
        ))

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
            title = "Economic Growth",
            orientation="h",
            yanchor="top",
            #xanchor="left",
            #x = 0.4,
            #y = -0.15  #move it to underneath
        )
    )

    print("saving WEM line emissions chart for three growth scenarios")
    save_figures(fig, output_dir, name="fig_line_emissions_WEM")

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

    out = project_root / "outputs/charts_and_data/generate_fig_line_emissions_WEM"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_line_emissions_WEM(df, str(out))
