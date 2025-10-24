# EMissions by scenario in panes


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


def generate_fig_pane_chart_emissions_by_scenario(df: pd.DataFrame, output_dir: str) -> None:
    print("generating a pane chart of emissions by scenario ")
    
    
    ## GET DATA
    #####################
    import pandas as pd
    import numpy as np
    import plotly.express as px

    cols = ["Scenario","ScenarioKey","EconomicGrowth","CarbonBudget","CO2eq"]
    dfx = df[df["Year"] == 2035][cols].copy()
    dfx = dfx[~dfx["Scenario"].str.contains("CPP4EKH|CPP4EK|CPP4GE", regex=True)] # DROP these Variants.

    # sum co2 emissions first
    #reduce to just emissions sum
    data = (
            dfx.groupby(["Scenario","ScenarioKey","EconomicGrowth","CarbonBudget"])["CO2eq"]
            .sum()
            .reset_index()
            )

    data["CO2eq"] = data["CO2eq"]*0.001 #convert to Mt

    #change the name
    data.loc[data["CarbonBudget"] != "NoBudget", "CarbonBudget"] = "Additional mitigation"
    data.loc[data["CarbonBudget"] == "NoBudget", "CarbonBudget"] = "Unconstrained"

    # --- Map Budget to numeric positions ---
    dfx = data.copy()
    pos_map = {"Unconstrained": -0.5, "Additional mitigation": 0.5}
    dfx["xpos"] = dfx["CarbonBudget"].map(pos_map)

    #MAKE CHART
    ###############

    # --- Create scatter plot ---
    fig = px.scatter(
        dfx,
        x="xpos",
        y="CO2eq",
        color="EconomicGrowth",
        facet_col="ScenarioKey",
        #facet_col_wrap=3,
        facet_col_spacing=0.009, #space between the panes/facets
        #title="CO₂eq Emissions by Budget and Economic Growth across Scenario Groups",
        labels={
            "CO2eq": "CO₂eq Emissions (Mt)",
            "EconomicGrowth": "Economic Growth Rate"
        },
    )

    # --- Make axes shared and fixed ---
    fig.update_xaxes(
        tickmode="array",
        tickvals=[-0.5, 0.5],
        ticktext=["Unconstrained", "Additional<br>mitigation"],
        range=[-1, 1],
        showgrid=False,
        matches=None  # allows independent but correct ticks
    )

    fig.update_yaxes(matches="y")  # ✅ make all facets share same y-scale

    # --- Layout tweaks ---
    fig.update_layout(
        legend_title_text="Economic Growth",
        showlegend=True,
        height=400,
        width = 3000
        
    )
    fig.update_xaxes(title_text="")
    fig.update_traces(marker=dict(size=10, opacity=0.85))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    
    ## SAVE STUFF
    ########################

    print("saving pane_chart_emissions_by_scenario")
    save_figures(fig, output_dir, name="fig_pane_chart_emissions_by_scenario")
    
    if not dev_mode:
        save_data_path = Path(output_dir) / "data.csv"
        print(f"Saving data set to {save_data_path}")
        data.to_csv(save_data_path, index=False)


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
        

    out = project_root / "outputs/charts_and_data/fig_pane_chart_emissions_by_scenario"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_pane_chart_emissions_by_scenario(df, str(out))
