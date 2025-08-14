# a dual figure with two charts for power sector cumulative new capacity and total capacity

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
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




def generate_cumulative_and_total_capacity(df: pd.DataFrame, output_dir: str) -> go.Figure:
    pwr_excl_list = ["ETrans", "EDist", "Demand", "AutoGen-Chemcial"]
    scenario_list = [
        "NDC_BASE-RG",
        "NDC_BASE-MES-RG",
        "NDC_BASE-LEAF-RG",
        "NDC_BASE-IRPLight-RG",
        "NDC_BASE-IRPFull-RG",
        "NDC_BASE-HEAF-RG",
        "NDC_BASE-SAREM-RG"
    ]

    color_map = {
        "ECoal": "#505457",
        "ENuclear": "#ca1d90",
        "EImports": "#9467bd",
        "EHydro": "#8c564b",
        "EGas": "#ee2c4c",
        "EOil": "#e66177",
        "EBiomass": "#03ff2d",
        "EWind": "#3f1ae6",
        "Solar PV": "#e6e21a",
        "EPV": "#e6e21a",
        "ECSP": "#fc5c34",
        "Other": "#e377c2"
    }

    df_power = df[
        (df['Scenario'].isin(scenario_list)) &
        (df["Year"].between(2025, 2040)) &
        (df["Sector"] == "Power") &
        (~df["Subsector"].isin(pwr_excl_list))
    ].copy()

    # Chart 1: cumulative new capacity
    newcap = df_power[df_power["Indicator"] == "NewCapacity"].copy()
    newcap = newcap[newcap["Year"].isin([2025, 2030, 2035, 2040])]

    newcap["Cumulative"] = (
        newcap.groupby(["Scenario", "Subsector"])["SATIMGE"]
        .cumsum()
    )

    target_years = [2030, 2035, 2040]
    cum_display = newcap[newcap["Year"].isin(target_years)]

    # Chart 1: Cumulative New Capacity
    cum_display["Year_Scenario"] = cum_display["Year"].astype(str) + "_" + cum_display["Scenario"]
    fig1 = px.bar(
        cum_display,
        x="Year_Scenario",         # <-- composite x axis
        y="Cumulative",
        color="Subsector",         # <-- color by Subsector
        category_orders={"Subsector": list(color_map.keys())}
    )


    # Chart 2: total capacity
    totalcap = df_power[
        (df_power["Indicator"] == "Capacity") &
        (df_power["Year"].isin([2025, 2030, 2035, 2040]))
    ].copy()

    # Chart 2: Total Capacity
    fig2 = px.bar(
    totalcap,
    x="Year",
    y="SATIMGE",
    color="Scenario",  # <-- group by scenario
    category_orders={"Scenario": scenario_list}
    )
    
    
    # Combine into one figure
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Cumulative New Capacity (from 2025)", "Total Capacity"),
        shared_yaxes=False
    )

    for trace in fig1.data:
        trace.showlegend = True
        fig.add_trace(trace, row=1, col=1)

    for trace in fig2.data:
        trace.showlegend = False
        fig.add_trace(trace, row=1, col=2)

    fig.update_layout(
        barmode="group",  # <-- group bars by scenario
        width=1000,
        height=500,
        legend_title_text="Scenario",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(tickmode="linear", dtick=5, tickangle=45),
        xaxis2=dict(tickmode="linear", dtick=5, tickangle=45)
    )



    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
        #fig.show() this crashes the script.

    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="ElecTWh_sentOut_consumed")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        newcap.to_csv(Path(output_dir) / "data1.csv", index=False)
        totalcap.to_csv(Path(output_dir) / "data2.csv", index=False)

# Example usage:
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/generate_cumulative_and_total_capacity"
    out.mkdir(parents=True, exist_ok=True)
    generate_cumulative_and_total_capacity(df, str(out))
