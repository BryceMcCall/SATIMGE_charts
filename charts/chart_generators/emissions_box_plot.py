# Emissions box plot

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


def generate_fig_boxplot_emissions(df: pd.DataFrame, output_dir: str) -> None:
    print("generating box plot for core scenarios")

    ### DATA
    ###############
    emissions_2024_level = 438.9 #the code below works on the full data set to get the average of the national level emissions for 2024 which produces 438.9 as a result.  
    # (
    #     df[df["Year"] == 2024]
    #     .groupby("Scenario")["CO2eq"]
    #     .sum()
    #     .mean()
    #     * 0.001  # convert to Mt
    # )

    cols = ["Scenario","ScenarioKey","Year","CO2eq"]
    dfx = df[df["Year"].isin([2035])][cols].copy() 

    data = (
            dfx.groupby(["Scenario","ScenarioKey","Year"])["CO2eq"]
            .sum()
            .reset_index()
            )

    data["CO2eq"] = data["CO2eq"]*0.001 #convert to Mt

    ## CHART
    ################

    import plotly.express as px
    import plotly.graph_objects as go

    # Create the box plot
    fig = px.box(
        data_frame=data,
        x="ScenarioKey",
        y="CO2eq",
        color="ScenarioKey",
        points="all",  # optional: show all points overlaid; use "outliers" or False if you prefer cleaner boxes
        title=""
    )

    # Add a horizontal line at y = 450
    fig.add_hline(
        y=emissions_2024_level,
        line_dash="dash",
        line_color="black",
        annotation_text=f"Emissions level in 2024 ≈ {emissions_2024_level:.1f}",
        annotation_position="top left"
    )

    # Clean up layout
    fig.update_layout(
        template="plotly_white",
        xaxis_title="",
        yaxis_title="Mt CO₂eq",
        yaxis=dict(range=[200, 450]),  # limit y-axis to 450
        #legend_title="Scenario Key",
        height=600,
        width=1000
    )


    ### SAVE stuff

    print("saving box plot of scenarios emissions")
    save_figures(fig, output_dir, name="fig_boxplot_emissions")
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

    out = project_root / "outputs/charts_and_data/fig_boxplot_emissions"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_boxplot_emissions(df, str(out))
