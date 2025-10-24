# Transport stacked bar emissions chart of transport measures on wem

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


def generate_fig_wem_transport_measures(df: pd.DataFrame, output_dir: str) -> None:
    print("generating stacked bar chart of emissions from transport sector for WEM and transport measures ")

        
    ## DATA
    ################

    cols = ["Scenario","Subsector","Year","CO2eq"]
    scenarios_list = ["NDC_BASE-RG", "NDC_BASE-PassM-RG", "NDC_BASE-FreiM-RG"]

    dfx = df[(df["Scenario"].isin(scenarios_list))&
            (df['Sector'] == "Transport")&
            (df["Year"].isin(range(2024,2036)))][cols].copy() 

    #RENAME

    scenario_map = {
        "NDC_BASE-RG": "WEM",
        "NDC_BASE-PassM-RG": "WEM + Passenger Modal Shift",
        "NDC_BASE-FreiM-RG": "WEM + Freight Modal Shift"
    }

    sector_map = {
        'Aviation-Domestic': "Domestic Aviation",
        'Aviation-International': "Intl. Aviation",
        'FreightPip': "Other Freight",
        'FreightRail': "Freight - Rail",
        'FreightRoad': "Freight - Road",
        'PassPriv': "Private Transport",
        'PassPub': "Public Transport",
        'TraOther': "Other"
    }
    # --- Apply mapping to your dataframe ---
    # This replaces any matching Scenario names with their friendly labels
    dfx["Scenario"] = dfx["Scenario"].replace(scenario_map)
    dfx["Subsector"] = dfx["Subsector"].replace(sector_map)

    import pandas as pd
    import numpy as np

    data = (
            dfx.groupby(["Subsector","Scenario","Year"])["CO2eq"]
            .sum()
            .reset_index()
            )

    data["CO2eq"] = data["CO2eq"]*0.001 #convert to Mt

    #save the data

    ## CHART
    ################

    import plotly.express as px

    fig = px.bar(
        data_frame=data,
        x="Scenario",          # group side-by-side by Scenario
        y="CO2eq",             # bar height
        color="Subsector",     # stacked by Subsector
        facet_col="Year",      # one facet per Year
        barmode="stack",       # stacked within each Scenario
        title=""
    )

    # Clean up facet titles
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    # Layout tweaks
    fig.update_layout(
        height=500,
        width=1200,
        legend_title="Subsector",
        xaxis_title="Scenario",
        yaxis_title="Mt CO₂eq",
        margin=dict(t=40, l=60, r=20, b=60),
        
        #template="plotly_white"
    )
    fig.update_xaxes(tickangle=-90)  # rotate x-axis labels by 45 degrees
    fig.update_xaxes(title_text="")


    print("saving generate_fig_line_emissions_ALL")
    save_figures(fig, output_dir, name="fig_wem_transport_measures")
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
        print("error importin")

    out = project_root / "outputs/charts_and_data/fig_wem_transport_measures"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_wem_transport_measures(df, str(out))
