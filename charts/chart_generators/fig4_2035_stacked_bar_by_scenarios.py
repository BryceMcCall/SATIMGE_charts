# charts/chart_generators/fig4_2035_stacked_bar_by_scenarios.py

import sys
from pathlib import Path

# ────────────────────────────────────────────────────────
# Bootstrap for standalone runs:
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
# ────────────────────────────────────────────────────────

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
from charts.common.save import save_figures

def generate_fig4_2035_stacked_bar_by_scenarios(df: pd.DataFrame, output_dir: str) -> None:
    """
    Fig 4: Stacked bar of emissions in 2035 by scenario and sector group (18 bars total).
    - df: processed DataFrame with CO2eq, IPCC_Category_L1, Sector, Scenario, Year
    - output_dir: folder to save images & data.csv
    """
    print("generating figure 4")

    # Helper to map sectors
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

    # Keep only energy emissions
    df_f4 = df[df["IPCC_Category_L1"] == "1 Energy"].copy()
    df_f4["SectorGroup"] = df_f4["Sector"].apply(map_sector_group)

    # Step 1: Sum 2035 emissions by Scenario, excluding baseline
    total_2035 = (
        df_f4[df_f4["Year"] == 2035]
        .groupby("Scenario")["CO2eq"]
        .sum()
        .sort_values()
    )
    total_2035_no_base = total_2035.drop("NDC_BASE-RG", errors="ignore")

    # Select smallest, largest, and a random sample of up to 15 middle scenarios (so + baseline = 18 bars)
    first_scen    = total_2035_no_base.head(1).index.tolist()
    last_scen     = total_2035_no_base.tail(1).index.tolist()
    middle        = total_2035_no_base.iloc[1:-1]
    sample_size   = min(15, len(middle))
    middle_sample = middle.sample(n=sample_size, random_state=42).index.tolist()
    selected_scenarios = first_scen + middle_sample + last_scen + ["NDC_BASE-RG"]

    # Step 2: 2035 emissions by SectorGroup and Scenario (exclude 2035 for baseline)
    scen_for_2035 = [s for s in selected_scenarios if s != "NDC_BASE-RG"]
    fig4_grouped = (
        df_f4[
            (df_f4["Year"] == 2035) &
            (df_f4["Scenario"].isin(scen_for_2035))
        ]
        .groupby(["Scenario", "SectorGroup"])["CO2eq"]
        .sum()
        .reset_index()
    )

    # Step 3: Add NDC_BASE-RG 2024 emissions for comparison
    total_2024 = (
        df_f4[
            (df_f4["Year"] == 2024) &
            (df_f4["Scenario"] == "NDC_BASE-RG")
        ]
        .groupby("SectorGroup")["CO2eq"]
        .sum()
        .reset_index()
    )
    total_2024["Scenario"] = "NDC_BASE-RG"
    fig4_grouped = pd.concat([fig4_grouped, total_2024], ignore_index=True)

    # Step 4: Order scenarios by total emissions
    scenario_order = (
        fig4_grouped
        .groupby("Scenario")["CO2eq"]
        .sum()
        .sort_values()
        .index
        .tolist()
    )

    # Step 5: Pivot for stacked bar
    fig4_pivot = (
        fig4_grouped
        .pivot(index="Scenario", columns="SectorGroup", values="CO2eq")
        .fillna(0)
        .reindex(scenario_order)
    )

    # Step 6: Plot stacked bar
    fig4 = go.Figure()
    sector_order = ["All others", "Refineries", "Transport", "Industry", "Power"]
    for sector in sector_order:
        if sector in fig4_pivot.columns:
            fig4.add_trace(go.Bar(
                x=fig4_pivot.index,
                y=fig4_pivot[sector],
                name=sector
            ))

    # Annotate 2024 baseline above the NDC_BASE-RG bar
    fig4.add_trace(go.Scatter(
        x=["NDC_BASE-RG"],
        y=[fig4_pivot.loc["NDC_BASE-RG"].sum()],
        mode="text",
        text=["2024"],
        textposition="top center",
        showlegend=False,
        textfont=dict(size=12, color="black", family="Arial Black")
    ))

    # Apply common styling
    fig4 = apply_common_layout(fig4)

    # Chart-specific layout
    fig4.update_layout(
        title="Fig 4: Energy Emissions by Scenario & Sector (2035)",
        xaxis_title="",  # or "Scenario"
        barmode="stack",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    # Step 7: Save figure and data
    print("saving figure 4")
    save_figures(fig4, output_dir, name="fig4_2035_stacked_bar_by_scenarios")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    fig4_grouped.to_csv(Path(output_dir) / "fig4_data.csv", index=False)


# ────────────────────────────────────────────────────────
# Run standalone for testing
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig4_2035_stacked_bar_by_scenarios"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_2035_stacked_bar_by_scenarios(df, str(out))
