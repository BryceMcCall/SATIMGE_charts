# charts/chart_generators/fig5_base_reference_emissions.py

import sys
from pathlib import Path

# ────────────────────────────────────────────────────────
# Bootstrap so you can run this file directly:
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
# ────────────────────────────────────────────────────────

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
from charts.common.save import save_figures

def generate_fig5_base_reference_emissions(df: pd.DataFrame, output_dir: str) -> None:
    """
    Fig 5: Total Emissions for BASE Scenarios (Reference Economic Growth)
    - df: processed DataFrame with columns ScenarioFamily, EconomicGrowth, Scenario, Year, CO2eq
    - output_dir: folder to save images and data.csv
    """
    print("generating figure 5")

    # Step 1: Filter the data
    filtered = df[
        (df["ScenarioFamily"] == "BASE") &
        (df["EconomicGrowth"] == "Reference")
    ].copy()

    # Step 2: Aggregate emissions by Scenario and Year
    data = (
        filtered
        .groupby(["Scenario", "Year"])["CO2eq"]
        .sum()
        .reset_index()
    )

    # Step 3: Build the line chart
    fig = go.Figure()
    for scenario in data["Scenario"].unique():
        subset = data[data["Scenario"] == scenario]
        fig.add_trace(go.Scatter(
            x=subset["Year"],
            y=subset["CO2eq"],
            mode="lines",
            name=scenario,
            line=dict(width=2)
        ))

    # Step 4: Apply common styling
    fig = apply_common_layout(fig)

    # Step 5: Chart-specific layout
    fig.update_layout(
        title="Fig 5: Total Emissions for BASE Scenarios (Reference Economic Growth)",
        xaxis_title="Year",
        yaxis_title="CO₂eq (kt)"
    )

    # Step 6: Save images & data
    print("saving figure 5")
    save_figures(
        fig,
        output_dir,
        name="fig5_base_reference_emissions"
    )

    # Export the data used to plot
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    data.to_csv(Path(output_dir) / "data.csv", index=False)


# ────────────────────────────────────────────────────────
# Allows direct execution for testing:
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig5_base_reference_emissions"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_base_reference_emissions(df, str(out))
# ────────────────────────────────────────────────────────
