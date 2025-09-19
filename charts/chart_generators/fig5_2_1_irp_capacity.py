# charts/chart_generators/fig5_2_1_irp_capacity.py

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures
from utils.mappings import map_scenario_key
import yaml
import shutil

# ────────────────────────── Config ────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"

if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    print("⚠️ config.yaml not found — defaulting dev_mode = False")
    dev_mode = False


def generate_fig5_2_1_irp_capacity(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate stacked bar chart for IRP comparison of installed capacity
    in 2024, 2030, and 2035.
    """
    print("generating figure 5.2.1-4: IRP capacity comparison")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Ensure numeric
    df["Year"] = df["Year"].astype(int)
    df["Capacity (GW)"] = pd.to_numeric(df["Capacity (GW)"], errors="coerce").fillna(0)

    # Keep only milestone years
    df = df[df["Year"].isin([2024, 2030, 2035])]

    # Harmonize subsector labels
    df["Subsector"] = df["Subsector"].replace({
        "ECoal": "Coal", "EOil": "Oil", "EGas": "Gas", "ENuclear": "Nuclear",
        "EHydro": "Hydro", "EBiomass": "Biomass", "EWind": "Wind",
        "EPV": "Solar PV", "ECSP": "CSP", "EHybrid": "Hybrid",
        "EBattery": "Battery Storage", "EPumpStorage": "Pumped Storage",
        "Imports": "Imports"
    })

    # Map scenarios
    def local_map(scen: str) -> str:
        if scen == "NDC_BASE-RG":
            return "WEM"
        elif scen == "NDC_BASE-IRPFull-RG":
            return "WEM-IRP"
        else:
            return map_scenario_key(scen)

    df["ScenarioLabel"] = df["Scenario"].apply(local_map)

    # Build color map
    subsectors = df["Subsector"].unique()
    color_map = {s: color_for("fuel", s) for s in subsectors}

    # Define stack order (Coal at bottom)
    stack_order = [
        "Coal", "Oil", "Gas", "Nuclear", "Hydro", "Biomass",
        "Wind", "Solar PV", "CSP", "Hybrid",
        "Battery Storage", "Pumped Storage", "Imports"
    ]
    stack_order = [s for s in stack_order if s in subsectors]

    # Plot
    fig = px.bar(
        df,
        x="ScenarioLabel",
        y="Capacity (GW)",
        color="Subsector",
        facet_col="Year",
        facet_col_wrap=3,
        barmode="stack",
        category_orders={"Subsector": stack_order},
        color_discrete_map=color_map,
        labels={"Capacity (GW)": "GW", "ScenarioLabel": ""},
    )

    # Apply style
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        font=dict(size=14),
        margin=dict(l=40, r=180, t=40, b=120),
        yaxis=dict(
            dtick=10,
            title=dict(text="Capacity (GW)", font=dict(size=21))
        )
    )
        # After apply_common_layout and other updates
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        font=dict(size=14),
        margin=dict(l=40, r=180, t=40, b=120),
        yaxis=dict(
            dtick=10,
            title=dict(text="Capacity (GW)", font=dict(size=21))
        ),
        bargap=0.45  # <── increase gap → bars thinner (default is 0.2)
    )

    # Clean facet titles
    fig.for_each_annotation(lambda a: a.update(
        text=a.text.split("=")[-1],
        font=dict(size=21)
    ))

    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-90)

    # Save
    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig5_2_1_irp_capacity")

        # Copy main image into gallery
        gallery_dir = project_root / "outputs" / "gallery"
        gallery_dir.mkdir(parents=True, exist_ok=True)
        src_img = Path(output_dir) / "fig5_2_1_irp_capacity.png"
        if src_img.exists():
            shutil.copy(src_img, gallery_dir / src_img.name)

        # Export CSV
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        df.to_csv(Path(output_dir) / "fig5_2_1_irp_capacity_data.csv", index=False)


if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.2.1_4_pwr_irp_capacity.csv"
    df = pd.read_csv(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig5_2_1_irp_capacity"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_2_1_irp_capacity(df, str(out))
