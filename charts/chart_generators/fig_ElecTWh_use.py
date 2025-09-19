# a chart of electricity consumption by sectors including losses

chart_name = "fig_ElecTWh_use"

import sys
from pathlib import Path
import math

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout, color_for
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


def _add_footer_legend(fig: go.Figure, items, domain, *,
                       y=-0.26, per_row=6, swatch_w=0.015, swatch_h=0.02, gap=0.006,
                       font_size=14):
    """Draw a legend-like footer under a subplot (wrapping by per_row)."""
    x0, x1 = float(domain[0]), float(domain[1])
    width = x1 - x0
    cols = max(1, min(per_row, len(items)))
    cell_w = width / cols

    row = 0
    col = 0
    for name, color in items:
        rect_x0 = x0 + col * cell_w
        rect_x1 = rect_x0 + swatch_w
        rect_y0 = y - row * (swatch_h + 0.05)
        rect_y1 = rect_y0 + swatch_h

        fig.add_shape(
            type="rect",
            xref="paper", yref="paper",
            x0=rect_x0, x1=rect_x1, y0=rect_y0, y1=rect_y1,
            line=dict(width=1, color=color),
            fillcolor=color,
            layer="above"
        )

        fig.add_annotation(
            xref="paper", yref="paper",
            x=rect_x1 + gap, y=rect_y0 + swatch_h / 2.0,
            xanchor="left", yanchor="middle",
            text=name,
            showarrow=False,
            font=dict(size=font_size)
        )

        col += 1
        if col >= cols:
            col = 0
            row += 1


def generate_ElecTWh_use_chart(df: pd.DataFrame, output_dir: str) -> go.Figure:
    

    # get demand from all sectors - the consumed amount
    # add lossess as a demand for Tx, and Dx
    # add lossess from storage, and pumpedhydro
    import plotly.express as px

    ########## data prep for demand
    # get demand for sectors

    scen = "NDC_BASE-RG"
    year_range = range(2024, 2036)

    
    dem_df = df[(df["Scenario"] == scen)&
                df["Year"].isin(year_range)&
                (df["Indicator"] == "FlowIn") &
                df["Commodity"].str.match(r".+ELC$") &      # ends with ELC, with at least 1 char before
                ~df["Commodity"].isin(["ELC", "ELCC","INDELC"]) &      # exclude exact matches for ELC and ELCC, and INDELC. INDELC goes to Dx for industries and would be double counting
                ~df["Process"].isin(["XUCTLELC"]) # exclude this specifically, the CTL elec is captured already
    ]

    #aggregate to sector level
    dem_agg = dem_df.groupby(["Year","Sector"], as_index=False)["SATIMGE"].sum()

    dem_agg['TWh'] = dem_agg['SATIMGE']/3.6 # convert to TWh
    dem_agg = dem_agg.drop(columns=['SATIMGE']) #dont need

    #RENAME STUFF
    dem_agg["Sector"] = dem_agg["Sector"].replace({
        "Supply": "Others"
    })


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

    ##### make chart
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

    ##### end of chart making

    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name=chart_name)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        

    return fig


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/Charts_and_data"/ chart_name
    out.mkdir(parents=True, exist_ok=True)
    generate_ElecTWh_use_chart(df, str(out))
