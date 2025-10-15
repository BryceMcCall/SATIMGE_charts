# demand chart including losses


import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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


def generate_fig_elc_demand_bar(df: pd.DataFrame, output_dir: str) -> None:
    print("generating elec demand bar chart including losses")

    
    ########## data prep for demand
    # get demand for sectors

    scen = "NDC_BASE-RG" # get this scenario
    year_range = range(2024, 2036)

    dem_df = df[(df["Scenario"] == scen)& #get this scenario
                df["Year"].isin(year_range)& # for these years
                (df["Indicator"] == "FlowIn") & # only get flow in
                df["Commodity"].str.match(r".+ELC$") &      # ends with ELC, with at least 1 char before
                ~df["Commodity"].isin(["ELC", "ELCC","INDELC"]) &      # exclude exact matches for ELC and ELCC, and INDELC. INDELC goes to Dx for industries and would be double counting
                ~df["Process"].isin(["XUCTLELC"]) # exclude this specifically, the CTL elec is captured already
    ]
    # exports 
    pexelc = df[(df["Scenario"] == scen)& #get this scenario
                df["Year"].isin(year_range)& # for these years
                (df["Indicator"] == "FlowIn") & # only get flow in
                df["Process"].isin(["PEXELC"]) # Get exports
    ]

    #add exports to this and then aggregate to sector level
    dem_agg = dem_df.groupby(["Year","Sector"], as_index=False)["SATIMGE"].sum()

    dem_agg['TWh'] = dem_agg['SATIMGE']/3.6 # convert to TWh
    dem_agg = dem_agg.drop(columns=['SATIMGE']) #dont need

    
    cols = ["Year","Subsector","Scenario","SATIMGE","Indicator","Commodity"]
    indics = ["FlowIn","FlowOut"]

    ###########
    # calaculate losses for storage and Tx and Dx

    #Storage losses
    techs = ["EBattery","EPumpStorage"]

    losses_df = df[(df["Scenario"] == scen)&
                df["Year"].isin(year_range)&
                df["Indicator"].isin(indics) &
                df["Commodity"].str.contains("ELC", regex=True) &      # has ELC in it
                df["Subsector"].isin(techs) # 
    ][cols]

    losses_df = losses_df.groupby(["Year","Subsector","Indicator"], as_index=False)["SATIMGE"].sum()
    d = losses_df.copy()

    # aggregate first
    agg = d.groupby(["Year", "Indicator"], as_index=False)["SATIMGE"].sum()

    # pivot keeping Subsector in the index
    wide = agg.pivot(index=["Year", ], columns="Indicator", values="SATIMGE").fillna(0.0)
    wide["TWh"] = (wide["FlowIn"] - wide["FlowOut"])/3.6

    store_losses_df =  wide.reset_index()[["Year","TWh"]]
    store_losses_df["Subsector"] = "Storage Losses"

    ############
    # calaculate losses for Tx and Dx and summarise

    techs = ["ETrans","EDist"]
    losses_df = df[(df["Scenario"] == scen)&
                df["Year"].isin(year_range)&
                df["Indicator"].isin(indics) &
                df["Commodity"].str.contains("ELC", regex=True) &      # has ELC in it
                df["Subsector"].isin(techs) # exclude this specifically, the CTL elec is captured already
    ][cols]

    losses_df = losses_df.groupby(["Year","Subsector","Indicator"], as_index=False)["SATIMGE"].sum()

    d = losses_df.copy()

    # aggregate first (safe if you had duplicates)
    agg = d.groupby(["Year", "Subsector", "Indicator"], as_index=False)["SATIMGE"].sum()

    # pivot keeping Subsector in the index
    wide = agg.pivot(index=["Year", "Subsector"], columns="Indicator", values="SATIMGE").fillna(0.0)
    wide["TWh"] = (wide["FlowIn"] - wide["FlowOut"])/3.6

    txdx_losses_df = wide.reset_index()[["Year","Subsector","TWh"]]

    #Group both df's for losses
    losses_df = pd.concat([store_losses_df, txdx_losses_df], axis=0, ignore_index=True)

    #rename
    losses_df["Subsector"] = losses_df["Subsector"].replace({
        "EDist": "Distribution Losses",
        "ETrans": "Transmission Losses",
        "EBattery": "Battery Storage Losses",
        "EPumpStorage": "Pumped Hydro Storage Losses"
    })

    losses_df = losses_df.rename(columns={'Subsector': 'Sector'})

    #group sectors and losses together

    total_dem_df = pd.concat([dem_agg, losses_df], axis=0, ignore_index=True)

    ##### END of data prep

    #### MAKE CHART
    
    # Define sector order and colors in one list of tuples
    sector_style = [
        ("Industry", "#2ca02c"),
        ("Residential", "#1f77b4"),
        ("Commerce", "#ff7f0e"),
        ("Transport", "#9467bd"),
        ("Refineries", "#bcbd22"),
        ("Agriculture", "#d62728"),
        ("Others", "#17becf"),    
        ("Storage Losses", "#8c564b"),
        ("Transmission Losses", "#e377c2"),
        ("Distribution Losses", "#7f7f7f"),
    ]

    # Extract order and color map from the list
    sector_order = [s[0] for s in sector_style]
    sector_colors = {s[0]: s[1] for s in sector_style}

    fig = px.bar(
        total_dem_df,
        x="Year",
        y="TWh",
        color="Sector",
        barmode="stack",
        title="",
        category_orders={"Sector": sector_order},
        color_discrete_map=sector_colors
    )
    fig.update_layout(
        yaxis_title="TWh",
        xaxis_title="",
        legend_title="Sector",
        bargap=0.15,
        xaxis=dict(
            tickmode="linear"  # Show all years (integers) on the x-axis
        )
    )



    print("saving elec demand bar chart including losses")
    save_figures(fig, output_dir, name="fig_elc_demand_bar")

    if not dev_mode:
        total_dem_df.to_csv(Path(output_dir) / "fig_data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig_fig_elc_demand_bar"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_elc_demand_bar(df, str(out))


