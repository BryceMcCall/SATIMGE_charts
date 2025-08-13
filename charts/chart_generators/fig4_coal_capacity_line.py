
# coal power sector capacity 

import difflib
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


def generate_fig_coal_capacity(df: pd.DataFrame, output_dir: str) -> None:
    print("Generating coal power capacity line chart")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Filter to target data
    subset = df[
        (df["Scenario"] == "NDC_BASE-RG") &
        (df["Sector"] == "Power") &
        (df["Subsector"] == "ECoal") &
        (df["Indicator"] == "Capacity") &
        (df["Year"].between(2024, 2035))
    ].copy()
    
    

    if subset.empty:
        print("⚠️ No data found for the specified filters.")
        return

    # Aggregate capacity per year (in case of duplicates)
    data = subset.groupby("Year")["SATIMGE"].sum().reset_index()

    # Build the line chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[str(year) for year in data["Year"]],  # Ensure x values are strings
            y=data["SATIMGE"],
            mode="lines+markers",
            name="Coal Capacity",
            line=dict(width=3, color= "#505457"),
            marker=dict(size=6)
            )
        )

    fig = apply_common_layout(fig)
    
    fig.update_layout(  
    title="",
    xaxis=dict(
        title="",
        type="category",
        tickmode="array",
        tickvals=[str(year) for year in range(2024, 2036)],  # Use string years
        ticktext=[str(year) for year in range(2024, 2036)]
        #showgrid=False,
        #range=["2024", "2035"]  # Set range as strings to match x values
    ),
    yaxis=dict(
        title="Capacity (GW)",
        rangemode="tozero"
    ),
    legend=dict(title=""),
    )
    

    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
        # fig.show()  # Uncomment for local interactive testing
    else:
        print("💾 Saving figure and data")
        save_figures(fig, output_dir, name="fig_coal_capacity_line")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig_coal_capacity_line"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig_coal_capacity(df, str(out))
