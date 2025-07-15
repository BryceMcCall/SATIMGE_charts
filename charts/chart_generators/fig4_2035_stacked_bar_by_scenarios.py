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
from charts.common.save  import save_figures

def generate_fig4_2035_stacked_bar_by_scenarios(df: pd.DataFrame, output_dir: str) -> None:
    """
    Fig 4: Stacked bar of 2035 energy emissions by scenario & sector group.
    - df: processed DataFrame with CO2eq, IPCC_Category_L1, Sector, Scenario, Year
    - output_dir: folder to save images & data.csv
    """
    print("generating figure 4")

    # Step 0: Helper to map sectors (same logic as fig3)
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

    # Step 1: Filter for energy emissions
    df_f4 = df[df["IPCC_Category_L1"] == "1 Energy"].copy()
    df_f4["SectorGroup"] = df_f4["Sector"].apply(map_sector_group)

        # Step 2: Select 2035 emissions by scenario & sector
    total_2035 = (
        df_f4[df_f4["Year"] == 2035]
        .groupby("Scenario")["CO2eq"]
        .sum()
        .sort_values()
    )

    # Always include the smallest and largest total-emission scenarios
    first_scen = total_2035.head(1).index.tolist()
    last_scen  = total_2035.tail(1).index.tolist()

    # Middle scenarios (exclude first & last)
    middle = total_2035.iloc[1:-1]
    # only sample as many as exist (max 18)
    sample_size   = min(18, len(middle))
    middle_sample = middle.sample(n=sample_size, random_state=42).index.tolist()

    selected = first_scen + middle_sample + last_scen

    # Step 2b: Build the 2035‐only grouped DataFrame
    fig4_grouped = (
        df_f4[
            (df_f4["Year"] == 2035) &
            (df_f4["Scenario"].isin(selected))
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
    sector_order = ["All others", "Refineries", "Transport", "Industry", "Power"]
    fig = go.Figure()
    for sector in sector_order:
        if sector in fig4_pivot.columns:
            fig.add_trace(go.Bar(
                x=fig4_pivot.index,
                y=fig4_pivot[sector],
                name=sector
            ))

    # Add 2024 label above the NDC_BASE-RG bar
    fig.add_trace(go.Scatter(
        x=["NDC_BASE-RG"],
        y=[fig4_pivot.loc["NDC_BASE-RG"].sum()],
        mode="text",
        text=["2024"],
        textposition="top center",
        showlegend=False,
        textfont=dict(size=12, color="black", family="Arial Black")
    ))

    # Step 7: Style & layout
    fig = apply_common_layout(fig, "Fig 4: Energy Emissions by Scenario & Sector (2035)")
    fig.update_layout(
        barmode="stack",
        xaxis_title="",
        yaxis_title="CO₂eq (kt)",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    # Step 8: Save images & data
    print("saving figure 4")
    save_figures(fig, output_dir, name="fig4_2035_stacked_bar_by_scenarios")
    # export data
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "data.csv").write_text("")  # ensure folder
    fig4_grouped.to_csv(Path(output_dir) / "data.csv", index=False)


# ────────────────────────────────────────────────────────
# Run standalone for testing:
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig4_2035_stacked_bar_by_scenarios"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_2035_stacked_bar_by_scenarios(df, str(out))
# ────────────────────────────────────────────────────────
