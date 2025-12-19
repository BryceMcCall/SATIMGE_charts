# figure of power sector emissions and subsectors in power sector

#uses fuzzy matching to map subsectors to colors


import difflib
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
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

def generate_fig3(df: pd.DataFrame, output_dir: str) -> None:
    print("Generating stacked bar chart for Power sector")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    df["CO2eq"] = df["CO2eq"] * 0.001  # Convert to Mt

    # Subsector exclusions
    pwr_excl_subsectors = ['Demand', 'EPumpStorage', 'ETrans', 'EconInputs', 'EDist']

    # Filter data
    subset = df[
        (df["Scenario"] == "NDC_BASE-RG") &
        (df["Sector"] == "Power") &
        (~df["Subsector"].isin(pwr_excl_subsectors)) &
        (df["Year"].between(2024, 2035))
    ].copy()

    # Color mapping
    subsector_colors = {
        "Coal": "#505457", #the bottom
        "Nuclear": "#ca1d90",
        "Imports": "#9467bd",
        "Hydro": "#8c564b",
        "Gas": "#ee2c4c",
        "Oil":"#e66177",
        "Biomass": "#03ff2d",
        "Wind": "#3f1ae6",
        "Solar PV": "#e6e21a",
        "CSP":  "#fc5c34",
        "Other": "#e377c2"
    }

    # Map subsectors to color keys using best fuzzy match
    def match_to_color(subsector):
        match = difflib.get_close_matches(subsector, subsector_colors.keys(), n=1, cutoff=0.3)
        return match[0] if match else "Other"

    subset["ColorCategory"] = subset["Subsector"].apply(match_to_color)

    # Aggregate emissions
    subset_grouped = (
        subset
        .groupby(["Year", "ColorCategory"])["CO2eq"]
        .sum()
        .reset_index()
    )

    pivot = subset_grouped.pivot(index="Year", columns="ColorCategory", values="CO2eq").fillna(0)

    # Ensure color and stacking order
    final_order = [k for k in subsector_colors.keys() if k in pivot.columns]
    remaining = [col for col in pivot.columns if col not in final_order]
    ordered_columns = final_order + remaining

    # Drop columns with all zeros
    ordered_columns = [col for col in ordered_columns if pivot[col].sum() > 0]


    pivot = pivot[ordered_columns]

    # Build figure
    fig = go.Figure()
    for subsector in ordered_columns:
        fig.add_trace(go.Bar(
            name=subsector,
            x=pivot.index,
            y=pivot[subsector],
            marker_color=subsector_colors.get(subsector, "#aaaaaa")  # default grey if missing
        ))

    fig = apply_common_layout(fig)

    fig.update_layout(
        barmode="stack",
        title="",        
        xaxis=dict(
            showgrid=False,
            title="",
            type="category",
            tickmode="array",
            tickvals=list(range(2024, 2036)),  # <-- Explicitly set all years
            ticktext=[str(year) for year in range(2024, 2036)]  # <-- Show all years as labels
        ),
        yaxis=dict(
            title="Mt CO₂eq",
            rangemode="tozero"
        ),
        legend=dict(
            title=""
        )
    )

    #

    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
        # fig.show()  # Uncomment if viewing interactively
    else:
        print("💾 Saving figure and data")
        save_figures(fig, output_dir, name="fig_power_sector_stack")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        pivot.to_csv(Path(output_dir) / "data.csv")

if __name__ == "__main__":
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig_power_sector_stack"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig3(df, str(out))
