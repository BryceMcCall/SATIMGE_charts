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


def generate_fig_emissions_category_growths(df: pd.DataFrame, output_dir: str) -> None:
    print("generating emissions by category for WEM and economic growth rate")

        
    cols = ["Scenario","ScenarioKey","EconomicGrowth","IPCC_Category_L1","IPCC_Category_L3","IPCC_Category_L4","CO2eq","Year"]
    scenarios_of_interest = ["NDC_BASE-RG", "NDC_BASE-LG", "NDC_BASE-HG"]
    dfx = df[(df["Scenario"].isin(scenarios_of_interest))&
            (df["Year"]==2035)][cols].copy()
    #MAPPING

    #copied from tableau mapping, modified for python
    import numpy as np

    conditions = [
        dfx["IPCC_Category_L4"] == "1A1a Electricity and Heat Production",
        dfx["IPCC_Category_L4"] == "1A1b Petroleum refining ",
        dfx["IPCC_Category_L4"] == "1A1c Manufacture of solid fuels and other energy industries",
        dfx["IPCC_Category_L4"] == "1B3 Other Emissions - Sasol",
        dfx["IPCC_Category_L3"] == "1B1 Solid Fuels",
        dfx["IPCC_Category_L3"] == "1B2 Oil and Natural Gas",
        dfx["IPCC_Category_L3"] == "1A2 Manufacturing Industries and Construction",
        dfx["IPCC_Category_L3"] == "1A3 Transport",
        dfx["IPCC_Category_L3"] == "1A4 Other Sectors",
        dfx["IPCC_Category_L1"] == "2 Industrial Processes and Product Use ",
        dfx["IPCC_Category_L1"] == "3 Agriculture",
        dfx["IPCC_Category_L1"] == "4 LULUCF",
        dfx["IPCC_Category_L1"] == "5 Waste"
    ]

    choices = [
        "Electricity",                        # 1A1a Electricity and Heat Production
        "Liquid fuels supply",                # 1A1b Petroleum refining
        "Liquid fuels supply",                # 1A1c Manufacture of solid fuels and other energy industries
        "Liquid fuels supply",                # 1B3 Other Emissions - Sasol
        "Other energy",                       # 1B1 Solid Fuels
        "Other energy",                       # 1B2 Oil and Natural Gas
        "Industry<br>(energy and IPPU)",  # 1A2 Manufacturing Industries and Construction
        "Transport",                          # 1A3 Transport
        "Other energy",                       # 1A4 Other Sectors
        "Industry<br>(energy and IPPU)",  # 2 Industrial Processes and Product Use
        "Agriculture<br>(non-energy)",           # 3 Agriculture
        "Land",                               # 4 LULUCF
        "Waste"                               # 5 Waste
    ]


    # Define the order you want on the x-axis
    x_order = [
        "Electricity",
        "Liquid fuels supply",
        "Industry<br>(energy and IPPU)",
        "Transport",
        "Other energy",
        "Agriculture<br>(non-energy)",
        "Land",
        "Waste"
    ]


    dfx["CategoryGroup"] = np.select(conditions, choices, default="Other")

    #reduce to just emissions sum
    data = (
            dfx.groupby(["CategoryGroup","Scenario","EconomicGrowth"])["CO2eq"]
            .sum()
            .reset_index()
            )

    data["CO2eq"] = data["CO2eq"]*0.001 #convert to Mt
    # Make your column categorical with the desired order
    data["CategoryGroup"] = pd.Categorical(data["CategoryGroup"], categories=x_order, ordered=True)


    #PLOT
    import plotly.express as px

    fig = px.scatter(
        data_frame=data,
        x="CategoryGroup",
        y="CO2eq",
        color="EconomicGrowth",
        symbol="EconomicGrowth",   # optional: adds different marker shapes
        title=""
    )

    #fig.update_xaxes(title_text="Category Group")
    fig.update_yaxes(title_text="Mt CO₂eq")

    fig.update_layout(
        height=500,
        width=1200,
        legend_title="Economic Growth",
        margin=dict(t=50, l=60, r=20, b=60)
        #template="plotly_white"  # cleaner background
    )
    fig.update_xaxes(title_text="", tickangle=0)
    

    print("saving generate_fig_emissions_category_growths")
    save_figures(fig, output_dir, name="fig_emissions_category_growths")
    data = dfx.copy()

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
        selected_scenarios = ["NDC_BASE-LG", "NDC_BASE-RG", "NDC_BASE-HG"]
        year_select = list(range(2024, 2036))
        df = df[(df["Scenario"].isin(selected_scenarios)) & (df["Year"].isin(year_select))]

    out = project_root / "outputs/charts_and_data/fig_emissions_category_growths"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_emissions_category_growths(df, str(out))
