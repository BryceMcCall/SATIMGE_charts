# charts/chart_generators/fig07_electricity_ghgs.py

import sys
from pathlib import Path

# Allow running as standalone script
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.graph_objects as go
from charts.common.style import apply_common_layout
from charts.common.save import save_figures

def generate_fig07_electricity_ghgs(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generates Figure 7: Electricity GHGs vs National GHGs (2035)
    - df: processed DataFrame (from processed_dataset.parquet or .csv)
    - output_dir: path to save images & data.csv
    """
    print("generating figure 7")

    # ── 1) USER CONFIG ────────────────────────────────────────────────
    highlight_scenario = "NDC_BASE-RG"   # 👈 Change this to highlight a different Scenario
    ndc_low, ndc_high = 320, 380         # 👈 NDC 2035 lower / upper bounds (Mt CO₂-eq)
    # ───────────────────────────────────────────────────────────────────

    # ── 2) Prepare data for 2035, CO2eq emissions ────────────────────
    data = (
        df[(df["Indicator"] == "CO2eq") & (df["Year"] == 2035)]
        .groupby(["Scenario", "Sector"])["CO2eq"]
        .sum()
        .reset_index()
    )
    elec = data[data["Sector"] == "Electricity"].copy()
    natl = data.groupby("Scenario")["CO2eq"].sum().reset_index()

    # ── 3) Build scatter plot ────────────────────────────────────────
    fig = go.Figure()

    # Plot all scenarios; highlight one in red
    for _, row in elec.iterrows():
        scen = row.Scenario
        total_natl = natl.loc[natl.Scenario == scen, "CO2eq"].iloc[0]
        is_highlight = (scen == highlight_scenario)
        fig.add_trace(go.Scatter(
            x=[row.CO2eq],
            y=[total_natl],
            mode="markers",
            name=scen,
            marker=dict(
                size=10,
                color="#d62728" if is_highlight else None,
                opacity=0.8
            ),
        ))

    # ── 4) Add NDC policy range lines ───────────────────────────────
    max_x = elec["CO2eq"].max() * 1.05
    fig.add_shape(type="line",
                  x0=0, x1=max_x,
                  y0=ndc_low, y1=ndc_low,
                  line=dict(color="black", width=2))
    fig.add_shape(type="line",
                  x0=0, x1=max_x,
                  y0=ndc_high, y1=ndc_high,
                  line=dict(color="black", width=2))

    # ── 5) Example annotations (tweak coords as needed) ─────────────
    fig.add_annotation(x=55, y=305, text="IRP 2024 plus other PAMs",
                       showarrow=True, arrowhead=2, ax=40, ay=20)
    fig.add_annotation(x=88, y=335, text="Reference/‘least cost’",
                       showarrow=True, arrowhead=2, ax=80, ay=10)
    # …add more annotations here…

    # ── 6) Apply common styling ─────────────────────────────────────
    fig = apply_common_layout(fig)

    # ── 7) Final layout tweaks ──────────────────────────────────────
    fig.update_layout(
        title="Electricity GHGs vs National GHGs (all high economic growth rate)",
        xaxis_title="Electricity sector emissions – Mt CO₂-eq",
        yaxis_title="National GHG emissions in 2035 – Mt CO₂-eq",
        legend_title="Scenario",
        margin=dict(b=120)  # extra bottom margin for logo & caption
    )

    # ── 8) Place logo & caption below x-axis ─────────────────────────
    # Remove existing images (if any)
    fig.layout.images = []

    # Logo (paper coords: y < 0 → below axis)
    fig.add_layout_image(dict(
        source="https://…/energy_systems_research_unit_logo.png",
        xref="paper", yref="paper",
        x=1.0, y=-0.05,
        xanchor="right", yanchor="top",
        sizex=0.15, sizey=0.15,
        sizing="contain",
        layer="above"
    ))

    # Caption
    fig.add_annotation(dict(
        text="Source: SATIMGE model outputs. Dashed lines = NDC 2035 range.",
        xref="paper", yref="paper",
        x=0, y=-0.12,
        showarrow=False,
        align="left",
        font=dict(size=10, color="gray")
    ))

    # ── 9) Save outputs ──────────────────────────────────────────────
    print("saving figure 7")
    save_figures(fig, output_dir, name="fig07_electricity_ghgs")

    # ── 10) Export underlying data ───────────────────────────────────
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    data.to_csv(Path(output_dir) / "data.csv", index=False)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    # Load your processed data (either .parquet or .csv)
    df = pd.read_parquet(project_root / "data/processed/processed_dataset.parquet")
    out = project_root / "outputs/charts_and_data/fig07_electricity_ghgs"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig07_electricity_ghgs(df, str(out))
