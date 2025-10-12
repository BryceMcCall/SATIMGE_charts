# Emissions line chart for all PAMS measures scenarios on WEM

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


def generate_fig_line_emissions_pams(df: pd.DataFrame, output_dir: str) -> None:
    print("generating line emissions chart for PAMs on WEM")

    ### slice up dataset

    year_select = range(2024,2036,1)

    cols = ["Scenario","ScenarioKey","Year","CO2eq"]
    scen_keep = "WEM"

    dfx = df[(df["Year"].isin(year_select))]
    dfx['CO2eq'] = dfx['CO2eq']*0.001 #convert to Mt

    dfx = dfx[dfx['ScenarioKey']==scen_keep]
    dfx = dfx[dfx["EconomicGrowth"]=="Reference"]
    dfx = dfx[dfx["CarbonBudget"] == "NoBudget"]

    dfx = dfx[~dfx["Scenario"].str.contains("Oil", case=False, na=False)] # drop the oil sensitivities
    dfx = dfx[~dfx["Scenario"].str.contains("EAF", case=False, na=False)] # drop the EAF sensitivities

    #rename scenarios for these specifically:

    dfx["Scenario_clean"] = (
        dfx["Scenario"]
        .str.replace(r"^NDC_", "", regex=True)     # remove prefix NDC_
        .str.replace(r"-RG$", "", regex=True)      # remove suffix -RG
        .str.replace("BASE", "WEM", regex=False)   # replace BASE with WEM
    )


    #### END of data selection
    data = (
            dfx.groupby(["Scenario","Scenario_clean","Year"])["CO2eq"]
            .sum()
            .reset_index()
            )
    scenarios_list = data["Scenario_clean"].unique().tolist()

    import plotly.graph_objects as go

    highlight_scenario = "WEM"  # Set this to the Scenario_clean you want to color
    highlight_color = "#1A17DF"  # Your chosen color for the highlight

    fig = go.Figure()
    for scenario in scenarios_list:
        subset = data[data["Scenario_clean"] == scenario]
        if not subset.empty:
            color = highlight_color if scenario == highlight_scenario else None  # None lets Plotly pick default
            fig.add_trace(go.Scatter(
                x=subset["Year"],
                y=subset["CO2eq"],
                mode="lines",
                name=scenario,
                line=dict(width=3 if scenario == highlight_scenario else 1.8, color=color),
                showlegend=True
            ))

    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="Mt CO₂eq",
        legend_title="",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    fig = apply_common_layout(fig)

    print("saving generate_fig_line_emissions_ALL")
    save_figures(fig, output_dir, name="fig_line_emissions_pams")

    if not dev_mode:
        data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    parquet_path = project_root / "data/processed/processed_dataset.parquet"
    
    
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

    out = project_root / "outputs/charts_and_data/fig_line_emissions_pams"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_line_emissions_pams(df, str(out))
