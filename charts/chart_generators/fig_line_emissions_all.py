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
    

    import plotly.graph_objects as go

    # Define your color mapping
    scenario_colors = {
        'CPP-IRP': "#d46820",  
        'CPP-IRPLight': "#e58e5a",
        'CPP-SAREM': "#1cdaf3",
        'CPPS': "#ff6e1a",
        'CPPS Variant': "#b3ada9",
        'High Carbon': "#ff0000",
        'Low Carbon': "#008000",
        'WEM': "#1E1BD3"
    }

    cols = ["Scenario","ScenarioKey","Year","CO2eq"]

    dfx = df[(df["Year"].isin(year_select))][cols]
    dfx['CO2eq'] = dfx['CO2eq']*0.001 #convert to Mt

    dfx = (
            dfx.groupby(["Scenario","ScenarioKey","Year"])["CO2eq"]
            .sum()
            .reset_index()
            )


    # Sort for clean plotting
    dfx = dfx.sort_values(["Scenario", "Year"])

    # Create the figure
    fig = go.Figure()


    for scenario in dfx["Scenario"].unique():
        subset = dfx[dfx["Scenario"] == scenario]
        fig.add_trace(go.Scatter(
            x=subset["Year"],
            y=subset["CO2eq"],
            mode="lines",
            line=dict(width=1.5, color="#919090"),  
            showlegend=False
        ))

    # --- Add colored mean dots for each ScenarioKey at 2035 ---
    # (mean across all included scenarios with that key)
    mean2035 = (
        dfx[dfx["Year"] == 2035]
        .groupby("ScenarioKey", as_index=False)["CO2eq"]
        .mean()
    )

    for _, row in mean2035.iterrows():
        scen_key = row["ScenarioKey"]
        color = scenario_colors.get(scen_key, "grey")
        fig.add_trace(go.Scatter(
            x=[2035],
            y=[row["CO2eq"]],
            mode="markers",
            name=scen_key,
            marker=dict(size=10, color=color, symbol = "diamond"),
            showlegend=True
        ))

    # --- Layout ---
    

    #fig.update_layout(legend=dict(itemsizing='constant')) # make the size of the colour band in the legend larger so it's easier to see
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="Mt CO₂eq",
        legend_title="Mean value in 2035",
        #template="plotly_white",
        xaxis=dict(dtick=1)
    )


    print("saving generate_fig_line_emissions_ALL")
    save_figures(fig, output_dir, name="fig_line_emissions_all")
    data = dfx.copy()

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
        
        year_select = list(range(2024, 2036))
        table = pq.read_table(
            parquet_path        
        )
        df = table.to_pandas()
        
    except ImportError:
        # Fallback to pandas, but still only load columns
        df = pd.read_parquet(parquet_path, columns=columns_needed)
        selected_scenarios = ["NDC_BASE-LG", "NDC_BASE-RG", "NDC_BASE-HG"]
        year_select = list(range(2024, 2036))
        df = df[(df["Scenario"].isin(selected_scenarios)) & (df["Year"].isin(year_select))]

    out = project_root / "outputs/charts_and_data/generate_fig_line_emissions_ALL"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_line_emissions_ALL(df, str(out))
