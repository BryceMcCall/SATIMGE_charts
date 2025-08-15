# charts/chart_generators/fig4_2035_stacked_bar_by_scenarios.py

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


def generate_fig4_2035_stacked_bar_by_scenarios(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4")

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

    df_f4 = df[df["IPCC_Category_L1"] == "1 Energy"].copy()
    df_f4["SectorGroup"] = df_f4["Sector"].apply(map_sector_group)

    total_2035 = (
        df_f4[df_f4["Year"] == 2035]
        .groupby("Scenario")["CO2eq"]
        .sum()
        .sort_values()
    )
    total_2035_no_base = total_2035.drop("NDC_BASE-RG", errors="ignore")

    first_scen = total_2035_no_base.head(1).index.tolist()
    last_scen = total_2035_no_base.tail(1).index.tolist()
    middle = total_2035_no_base.iloc[1:-1]
    sample_size = min(15, len(middle))
    middle_sample = middle.sample(n=sample_size, random_state=42).index.tolist()
    selected_scenarios = first_scen + middle_sample + last_scen + ["NDC_BASE-RG"]

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

    scenario_order = (
        fig4_grouped
        .groupby("Scenario")["CO2eq"]
        .sum()
        .sort_values()
        .index
        .tolist()
    )

    fig4_pivot = (
        fig4_grouped
        .pivot(index="Scenario", columns="SectorGroup", values="CO2eq")
        .fillna(0)
        .reindex(scenario_order)
    )

    fig4 = go.Figure()
    sector_order = ["All others", "Refineries", "Transport", "Industry", "Power"]
    for sector in sector_order:
        if sector in fig4_pivot.columns:
            fig4.add_trace(go.Bar(
                x=fig4_pivot.index,
                y=fig4_pivot[sector],
                name=sector
            ))

    fig4.add_trace(go.Scatter(
        x=["NDC_BASE-RG"],
        y=[fig4_pivot.loc["NDC_BASE-RG"].sum()],
        mode="text",
        text=["2024"],
        textposition="top center",
        showlegend=False,
        textfont=dict(size=12, color="black", family="Arial Black")
    ))

    fig4 = apply_common_layout(fig4)
    fig4.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="CO₂e emissions in 2035 (MtCO₂e)",
        xaxis=dict(
            tickangle=90,
            title=dict(text="Scenario", standoff=10),
        ),
        barmode="stack",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.20,
            xanchor="center", x=0.5
        )
)


    print("saving figure 4")
    save_figures(fig4, output_dir, name="fig4_2035_stacked_bar_by_scenarios")

    if not dev_mode:
        fig4_grouped.to_csv(Path(output_dir) / "fig4_data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig4_2035_stacked_bar_by_scenarios"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_2035_stacked_bar_by_scenarios(df, str(out))
