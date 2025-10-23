# Emissions pane chart by category for all scenarios

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


def generate_fig_pane_chart_emissions_category(df: pd.DataFrame, output_dir: str) -> None:
    print("generating pane chart of emissions by category for all scenarios")

    ## GET DATA READY
    ################################

    cols = ["Scenario","ScenarioKey","EconomicGrowth","IPCC_Category_L1","IPCC_Category_L3","IPCC_Category_L4","CO2eq"]
    dfx = df[df["Year"] == 2035][cols].copy() #only 2035
    dfx = dfx[~dfx["Scenario"].str.contains("CPP4EKH|CPP4EK|CPP4GE", regex=True)] # DROP these Variants.

    #MAPPING

    import pandas as pd
    import numpy as np

    #copied from tableau mapping, modified for python
    conditions = [
        dfx["IPCC_Category_L4"] == "1A1a Electricity and Heat Production",
        dfx["IPCC_Category_L4"] == "1A1b Petroleum refining",
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
        "1A1a - Electricity",
        "1A1b, 1A1c, 1B3 - <br>Liquid fuels supply",
        "1A1b, 1A1c, 1B3 - <br>Liquid fuels supply",
        "1A1b, 1A1c, 1B3 - <br>Liquid fuels supply",
        "1B1, 1B2 - <br>Other fugitive",
        "1B1, 1B2 - <br>Other fugitive",
        "1A2 - Industry",
        "1A3 - Transport",
        "1A4 - Other energy",
        "2 - IPPU",
        "3 - Agriculture <br>(non-energy)",
        "4 - Land",
        "5 - Waste"
    ]

    dfx["CategoryGroup"] = np.select(conditions, choices, default="Other")

    #reduce to just emissions sum
    data = (
            dfx.groupby(["CategoryGroup","Scenario","ScenarioKey","EconomicGrowth"])["CO2eq"]
            .sum()
            .reset_index()
            )

    data["CO2eq"] = data["CO2eq"]*0.001 #convert to Mt

    ## MAKE CHART
    #######################

    import plotly.express as px

    dfx = data.copy()

    #DROP STUFF
    dfx = dfx[dfx["CategoryGroup"] != "Other"]
    dfx = dfx[~dfx["Scenario"].str.contains("CPP4EKH|CPP4EK|CPP4GE", regex=True)] # DROP these Variants.

    # --- map scenario to x axis positions ---
    pos_map = {
        "WEM": -0.1,
        "CPP-IRP": 0,
        "CPP-IRPLight": 0.1,
        "CPP-SAREM": 0.2,
        "CPPS": 0.3,
        "CPPS Variant": 0.4,
        "High Carbon": 0.5,
        "Low Carbon": 0.6
    }
    dfx["xpos"] = dfx["ScenarioKey"].map(pos_map)

    # --- define fixed colors for ScenarioKey ---
    scenario_colors = {
        "WEM": "#0081dd",
        "CPP-IRP": "#ff7f0e",
        "CPP-IRPLight": "#2ca02c",
        "CPP-SAREM": "#d62728",
        "CPPS": "#9467bd",
        "CPPS Variant": "#87858a",
        "High Carbon": "#8c564b",
        "Low Carbon": "#17becf"
    }

    # --- create scatter plot ---
    fig = px.scatter(
        dfx,
        x="xpos",
        y="CO2eq",
        color="ScenarioKey",         # ✅ color by ScenarioKey
        symbol="EconomicGrowth",     # ✅ shape by EconomicGrowth
        facet_col="CategoryGroup",
        facet_col_spacing=0.009,
        color_discrete_map=scenario_colors,
        labels={
            "CO2eq": "CO₂eq Emissions (Mt)",
            "EconomicGrowth": "Economic Growth Rate",
            "ScenarioKey": "Scenario"
        },
    )

    # --- axis setup ---
    fig.update_xaxes(
        tickmode="array",
        tickvals=[-0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        ticktext=["WEM", "CPP-IRP", "CPP-IRPLight", "CPP-SAREM", "CPPS","CPPS Variant", "High Carbon", "Low Carbon"],
        range=[-0.15, 0.65],
        showgrid=False,
        matches=None,
        tickangle=-90  
    )
    fig.update_yaxes(matches="y")

    # --- layout ---
    fig.update_layout(
        legend_title_text="Legend",
        showlegend=True,
        height=500
    )

    fig.update_xaxes(title_text="")
    fig.update_traces(marker=dict(size=6, opacity=0.85))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    ## SAVE STUFF

    print("saving pane_chart_emissions_category")
    save_figures(fig, output_dir, name="fig_pane_chart_emissions_category")
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
        #selected_scenarios = ["NDC_BASE-LG", "NDC_BASE-RG", "NDC_BASE-HG"]
        #year_select = list(range(2024, 2036))
        #df = df[(df["Scenario"].isin(selected_scenarios)) & (df["Year"].isin(year_select))]

    out = project_root / "outputs/charts_and_data/fig_pane_chart_emissions_category"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_pane_chart_emissions_category(df, str(out))
