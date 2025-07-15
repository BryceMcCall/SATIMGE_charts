# charts/chart_generators/fig3_ndc_emissions_by_sector.py

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
from charts.common.save  import save_figures

def generate_fig3_ndc_emissions_by_sector(df: pd.DataFrame, output_dir: str) -> None:
    """
    Fig 3: NDC_BASE-RG Emissions by Aggregate Sector Group (Sorted by Δ 2035–2024)
    - df: processed DataFrame with CO2eq, Scenario, Sector, Year
    - output_dir: folder to save images and data.csv
    """
    print("generating figure 3")

    # Step 1: Filter and group sectors
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

    # Step 2: Aggregate emissions
    data = subset.groupby(["Year", "SectorGroup"])["CO2eq"]\
                 .sum().reset_index()

    # Step 3: Calculate differences and labels
    pivot = data.pivot(index="SectorGroup", columns="Year", values="CO2eq")\
                .fillna(0)
    pivot["diff"] = pivot[2035] - pivot[2024]
    pivot["label"] = (
        pivot.index
        + " ("
        + pivot["diff"].round(0).astype(int).astype(str)
        + ")"
    )
    label_map = pivot["label"].to_dict()
    data["SectorLabel"] = data["SectorGroup"].map(label_map)

    # Step 4: Determine sort order by absolute diff
    order_df = (
        data[data["Year"] == 2035][["SectorGroup", "SectorLabel"]]
        .drop_duplicates()
    )
    order_df["abs_diff"] = order_df["SectorLabel"].map(
        pivot["diff"].abs().to_dict()
    )
    ordered_label_list = (
        order_df.sort_values("abs_diff")["SectorLabel"]
        .tolist()
    )

    # Step 5: Build the figure
    fig = go.Figure()
    # 2024: red circle
    part_2024 = data[data["Year"] == 2024]
    fig.add_trace(go.Scatter(
        x=part_2024["CO2eq"],
        y=part_2024["SectorLabel"],
        mode="markers",
        name="2024",
        marker=dict(size=10, color="red", symbol="circle")
    ))
    # 2035: blue X
    part_2035 = data[data["Year"] == 2035]
    fig.add_trace(go.Scatter(
        x=part_2035["CO2eq"],
        y=part_2035["SectorLabel"],
        mode="markers",
        name="2035",
        marker=dict(size=10, color="blue", symbol="x")
    ))

    # Step 6: Style & layout
    fig = apply_common_layout(
        fig,
        "Fig 3: NDC_BASE-RG Emissions by Aggregate Sector Group (Δ 2035–2024)"
    )
    # override axis settings for our custom ordering
    fig.update_layout(
        xaxis_title="CO₂eq (kt)",
        yaxis_title="Sector Group (Δ 2035–2024)",
        yaxis=dict(categoryorder="array", categoryarray=ordered_label_list)
    )

    # Step 7: Save
    print("saving figure 3")
    save_figures(fig, output_dir, name="fig3_ndc_emissions_by_sector")

    # Export the data used
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "data.csv").write_text("")  # ensure folder exists
    data.to_csv(Path(output_dir) / "data.csv", index=False)


# ────────────────────────────────────────────────────────
# Allows direct execution for testing:
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig3_ndc_emissions_by_sector"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig3_ndc_emissions_by_sector(df, str(out))
# ────────────────────────────────────────────────────────
