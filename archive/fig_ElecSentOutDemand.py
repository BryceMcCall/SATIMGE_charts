# double chart for electricity sent out and consumed

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout, color_for, color_sequence
from charts.common.save import save_figures
import plotly.express as px
from plotly.subplots import make_subplots
import yaml


project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False



def generate_ElecTWh_chart(df: pd.DataFrame,  output_dir: str) -> go.Figure:
    # Example colour mapping for subsectors
    
    color_map = {
        "ECoal": "#505457", #the bottom
        "ENuclear": "#ca1d90",
        "EImports": "#9467bd",
        "EHydro": "#8c564b",
        "EGas": "#ee2c4c",
        "EOil":"#e66177",
        "EBiomass": "#03ff2d",
        "EWind": "#3f1ae6",
        "Solar PV": "#e6e21a",
        "EPV": "#e6e21a",
        "ECSP":  "#fc5c34",
        "Other": "#e377c2"
    }


    #exclude this stuff:

    pwr_exclude = ["ETrans","EDist","EBattery","EPumpStorage","Demand","AutoGen-Chemcials"]

    # Filter data for relevant years & sector
    filtered_pwr = df[
        (df["Scenario"] == "NDC_BASE-RG") &
        (df["Sector"] == "Power") &
        (df["Year"].between(2024, 2035))&
        (~df["Subsector"].isin(pwr_exclude))
    ].copy()

    # =========================== Chart 1: Sent out
    df_pwr_out = (
    filtered_pwr[(filtered_pwr["Indicator"] == "FlowOut")&
                 (filtered_pwr["Commodity"] == "ELCC")]
    .groupby(["Year", "Subsector"], as_index=False)["SATIMGE"]
    .sum()
    )

    #convert to TWh
    df_pwr_out["SATIMGE"] = df_pwr_out["SATIMGE"] * (1/3.6)  # Convert to TWh
    fig1 = px.area(
        df_pwr_out,
        x="Year",
        y="SATIMGE",
        color="Subsector",
        color_discrete_map=color_map,
        category_orders={"Subsector": list(color_map.keys())}
    )

    # ======================== Chart 2: TWh Consumed
    color_map_sectors = {
        "Industry": "#a79eaf", #the bottom
        "Residential": "#ca1d90",
        "Commerce": "#9467bd",
        "Transport": "#51d467",
        "Supply": "#5077f8"
    }

    elc_use_incl = ["Agriculture","Commerce","Industry","Residential","Transport","Supply"]

    df_TWh_consumed = df[
        (df["Scenario"] == "NDC_BASE-RG") &
        (df["Sector"] != "Power") &
        (df["Year"].between(2024, 2035))&
        (df["Indicator"] == "FlowIn") &
        (df["Short Description"] == "Electricity") &
        (df["Sector"].isin(elc_use_incl))
    ].copy()  # <-- Add .copy() here

    df_TWh_consumed["SATIMGE"] = df_TWh_consumed["SATIMGE"] * (1/3.6)  # Convert to TWh


    df_TWh_consumed = df_TWh_consumed.groupby(["Year", "Sector"], as_index=False)["SATIMGE"].sum()



    fig2 = px.bar(
        df_TWh_consumed,
        x="Year",
        y="SATIMGE",
        color="Sector",
        color_discrete_map=color_map_sectors,
        category_orders={"Sector": list(color_map_sectors.keys())}
    )

    # Create subplot figure
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Sent out", "Electricity use"),
        shared_yaxes=True
    )

    # Add traces (keep same legend group for both charts)
    for trace in fig1.data:
        trace.showlegend = True  # Legend only from first chart
        fig.add_trace(trace, row=1, col=1)

    for trace in fig2.data:
        trace.showlegend = True  
        fig.add_trace(trace, row=1, col=2)

    fig = apply_common_layout(fig)

    # Layout tweaks
    fig.update_layout(
        barmode="stack",
        width=1000,
        height=500,
        legend_title_text="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5
        ),

        xaxis=dict(
        tickmode="linear",
        dtick=1,
        tickangle=45
        ),
        xaxis2=dict(
            tickmode="linear",
            dtick=1,
            tickangle=45
        )
    )

    

    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
        #fig.show() this crashes the script.

    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="ElecTWh_sentOut_consumed")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        df_pwr_out.to_csv(Path(output_dir) / "data.csv", index=False)
        df_TWh_consumed.to_csv(Path(output_dir) / "data2.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/ElecTWhsentuse_chart"
    out.mkdir(parents=True, exist_ok=True)
    generate_ElecTWh_chart(df, str(out))
