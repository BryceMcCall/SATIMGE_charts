# charts/chart_generators/fig5_3_2_pwr_scen_families_bar_generation_twh.py

import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

# ───────────────────────── Safe Import Path ─────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

# ───────────────────────── Config ─────────────────────────
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    print("⚠️ config.yaml not found — defaulting dev_mode = False")
    dev_mode = False


# ───────────────────────── Helper Mapping ─────────────────────────

FAMILY_NAMES = {
    "BASE":  "WEM",
    "CPP1":  "CPP-IRP",
    "CPP2":  "CPP-IRPLight",
    "CPP3":  "CPP-SAREM",
    "CPP4":  "CPPS",
    "LCARB": "Low carbon",
    "HCARB": "High carbon",
}
FAMILY_ORDER = ["HCARB", "CPP4","BASE", "CPP2",  "CPP3","LCARB", "CPP1"]

def _map_scen_family(scen: str) -> str:
    s = str(scen).strip().upper()
    for key, label in FAMILY_NAMES.items():
        if f"_{key}" in s:
            return label
    return "Other"



# ───────────────────────── Generator ─────────────────────────
def generate_fig5_3_2_pwr_scen_families_bar_generation_twh(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate stacked bar chart showing total generation (TWh)
    across scenario families for milestone years (2024, 2030, 2035).
    """
    print("generating figure 5.3.2: Power Sector Scenario Families Generation (TWh)")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Ensure numeric & clean
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["TWh (FlowOut)"] = pd.to_numeric(df["TWh (FlowOut)"], errors="coerce").fillna(0)
    df = df[df["Year"].between(2024, 2035)]
    df["Scenario"] = df["Scenario"].astype(str).str.strip()

    # Harmonize subsector / technology names
    df["Subsector"] = df["Subsector"].replace({
        "ECoal": "Coal", "EOil": "Oil", "EGas": "Natural Gas", "ENuclear": "Nuclear",
        "EHydro": "Hydro", "EBiomass": "Biomass", "EWind": "Wind",
        "EPV": "Solar PV", "ECSP": "Solar CSP", "EHybrid": "Hybrid",
        "EBattery": "Battery Storage", "EPumpStorage": "Pumped Storage",
        "Imports": "Imports"
    })

    # Apply robust family mapping
    df["ScenarioFamily"] = df["Scenario"].apply(_map_scen_family)

    keep_families = [FAMILY_NAMES[k] for k in FAMILY_ORDER]
    df = df[df["ScenarioFamily"].isin(keep_families)]
    scenario_order = [f for f in keep_families if f in df["ScenarioFamily"].unique()]


    # Build color map and stack order
    subsectors = df["Subsector"].unique()
    color_map = {s: color_for("fuel", s) for s in subsectors}

    stack_order = [
        "Coal", "Oil", "Natural Gas", "Nuclear", "Hydro", "Biomass",
        "Wind", "Solar PV", "Solar CSP", "Hybrid",
        "Battery Storage", "Pumped Storage", "Imports"
    ]
    stack_order = [s for s in stack_order if s in subsectors]


    # Plot
    fig = px.bar(
        df,
        x="ScenarioFamily",
        y="TWh (FlowOut)",
        color="Subsector",
        facet_col="Year",
        facet_col_wrap=3,
        barmode="stack",
        category_orders={
            "ScenarioFamily": scenario_order,
            "Subsector": stack_order,
        },
        color_discrete_map=color_map,
        labels={"TWh (FlowOut)": "Generation (TWh)", "ScenarioFamily": ""},
    )

    # Apply shared style (same as capacity)
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
            dtick=20,
            title=dict(text="Generation (TWh)", font=dict(size=25)),
            minor=dict(dtick=5)
        ),
        bargap=0.45
    )

    # Clean facet titles to show just year
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=21)))
    fig.update_xaxes(tickangle=-45)

    # Save chart + CSV
    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig5_3_2_pwr_scen_families_bar_generation_twh")

        gallery_dir = project_root / "outputs" / "gallery"
        gallery_dir.mkdir(parents=True, exist_ok=True)
        src_img = Path(output_dir) / "fig5_3_2_pwr_scen_families_bar_generation_twh_report.png"
        if src_img.exists():
            shutil.copy(src_img, gallery_dir / src_img.name)

        df.to_csv(Path(output_dir) / "fig5_3_2_pwr_scen_families_bar_generation_twh_data.csv", index=False)


# ───────────────────────── Entry Point ─────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.3.1_pwr_scen_families_TWh.csv"
    df = pd.read_csv(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig5_3_2_pwr_scen_families_bar_generation_twh"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_3_2_pwr_scen_families_bar_generation_twh(df, str(out))
