# charts/chart_generators/fig3b_ndc_emissions_by_sector.py

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


def generate_fig3b_ndc_emissions_by_sector(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 3b")

    subset = df[
        (df["CO2eq"] != 0.0) &
        (df["Scenario"] == "NDC_BASE-RG") &
        (df["Year"].isin([2024, 2035]))
    ].copy()

    def map_sector_group(sector):
        if sector in ["Industry", "Process emissions"]:
            return "Industry"
        elif sector == "Power":
            return "Power"
        elif sector == "Transport":
            return "Transport"
        elif sector == "Refineries":
            return "Refineries"
        else:
            return "All others"

    subset["SectorGroup"] = subset["Sector"].apply(map_sector_group)

    data = (
        subset
        .groupby(["Year", "SectorGroup"])["CO2eq"]
        .sum()
        .reset_index()
    )

    pivot = data.pivot(index="SectorGroup", columns="Year", values="CO2eq").fillna(0)
    pivot["diff"] = pivot[2035] - pivot[2024]
    pivot["label"] = (
        pivot.index + " (" + pivot["diff"].round(0).astype(int).astype(str) + ")"
    )
    label_map = pivot["label"].to_dict()
    data["SectorLabel"] = data["SectorGroup"].map(label_map)

    order_df = (
        data[data["Year"] == 2035][["SectorGroup", "SectorLabel"]]
        .drop_duplicates()
    )
    order_df["abs_diff"] = order_df["SectorLabel"].map(pivot["diff"].abs().to_dict())
    ordered_labels = order_df.sort_values("abs_diff")["SectorLabel"].tolist()

    fig = go.Figure()
    d2024 = data[data["Year"] == 2024]
    fig.add_trace(go.Bar(
        x=d2024["CO2eq"],
        y=d2024["SectorLabel"],
        name="2024",
        orientation="h",
        marker_color="red"
    ))

    d2035 = data[data["Year"] == 2035]
    fig.add_trace(go.Bar(
        x=d2035["CO2eq"],
        y=d2035["SectorLabel"],
        name="2035",
        orientation="h",
        marker_color="blue"
    ))

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="Fig 3b: NDC_BASE-RG Emissions by Aggregate Sector Group (Δ 2035–2024)",
        barmode="group",
        xaxis_title="CO₂eq (Mt)",
        yaxis_title="Sector Group (Δ 2035–2024)",
        yaxis=dict(
            categoryorder="array",
            categoryarray=ordered_labels
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=[0, 50000, 100000, 150000, 200000],
            ticktext=["0", "50", "100", "150", "200"],
            range=[0, 200000],
            tickfont=dict(size=12),
        )
    )

    print("saving figure 3b")
    save_figures(fig, output_dir, name="fig3b_ndc_emissions_by_sector")

    if not dev_mode:
        data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig3b_ndc_emissions_by_sector"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig3b_ndc_emissions_by_sector(df, str(out))
