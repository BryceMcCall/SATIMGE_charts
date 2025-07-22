# charts/chart_generators/fig1_total_emissions.py

import sys
from pathlib import Path

# —————————————————————————————————————
# When run as a script, add project root to sys.path so
# `import charts.common…` works, then fall through to imports.
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
# —————————————————————————————————————

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
from charts.common.save import save_figures


def generate_fig1_total_emissions(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generates Figure 1: Total CO₂ Emissions by Scenario.

    - df: processed DataFrame including a CO2eq column
    - output_dir: folder (path-string) to save images & data.csv
    """
    print("generating figure 1")

    # 1) Aggregate
    data = (
        df
        .groupby(["ScenarioFamily", "Scenario", "Year"])["CO2eq"]
        .sum()
        .reset_index()
    )

    # 2) Plot
    fig = go.Figure()
    for scenario in data["Scenario"].unique():
        subset = data[data["Scenario"] == scenario]
        fig.add_trace(go.Scatter(
            x=subset["Year"],
            y=subset["CO2eq"],
            mode="lines",
            line=dict(width=1, color="lightgray"),
            showlegend=False
        ))

    # 3) Apply common styling
    fig = apply_common_layout(fig)

    # 4) Chart-specific layout
    fig.update_layout(
        title="",
        xaxis_title="Year",
        yaxis_title="CO₂eq (kt)"
    )

    # 5) Save figure
    print("saving figure 1")
    save_figures(fig, output_dir, name="fig1_total_emissions")

    # 6) Write out the data
    (Path(output_dir) / "data.csv").write_text("")  # ensure folder exists
    data.to_csv(Path(output_dir) / "data.csv", index=False)


# —————————————————————————————————————
# If you run this file directly:
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig1_total_emissions"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig1_total_emissions(df, str(out))
# —————————————————————————————————————
