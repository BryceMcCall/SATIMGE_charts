# charts/chart_generators/fig5_base_reference_emissions.py

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


def generate_fig5_base_reference_emissions(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 5")

    filtered = df[
        (df["ScenarioFamily"] == "BASE") &
        (df["EconomicGrowth"] == "Reference")
    ].copy()

    data = (
        filtered
        .groupby(["Scenario", "Year"])["CO2eq"]
        .sum()
        .reset_index()
    )

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

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        xaxis_title="Year",
        yaxis_title="CO₂eq (Mt)"
    )

    print("saving figure 5")
    save_figures(
        fig,
        output_dir,
        name="fig5_base_reference_emissions"
    )

    if not dev_mode:
        data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig5_base_reference_emissions"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_base_reference_emissions(df, str(out))
