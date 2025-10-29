# GVA versus emisssion scatter plot for economic impact

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


def generate_fig_gva_v_emis(df: pd.DataFrame, output_dir: str) -> None:
    print("generating gva v emissions for all scenarios")

            
    import plotly.express as px

    fig = px.scatter(
        gva_emis,
        x="SATIMGE",
        y="CO2eq",
        color="ScenarioKey",
        symbol="EconomicGrowth",
        hover_data=gva_emis.columns,   # shows extra info on hover (optional)
    )

    fig.update_layout(
        title="",
        xaxis_title="GVA bn ZAR",
        yaxis_title="Mt CO₂eq",
        legend_title="Scenario Details"
    )



    print("saving generate_fig_line_emissions_ALL")
    save_figures(fig, output_dir, name="fig_gva_v_emis")
    data = gva_emis.copy()

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

    out = project_root / "outputs/charts_and_data/fig_gva_v_emis"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_gva_v_emis(df, str(out))
