# charts/chart_generators/fig5_2_1_pwr_scen_families_bar_emissions_mtco2eq.py

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
# Required family display names (and canonical order)
FAMILY_NAMES = {
    "BASE":  "WEM",           # (BASE)
    "CPP1":  "CPP-IRP",       # (CPP1)
    "CPP2":  "CPP-IRPLight",  # (CPP2)
    "CPP3":  "CPP-SAREM",     # (CPP3)
    "CPP4":  "CPPS",          # (CPP4)
    "LCARB": "Low carbon",    # (LCARB)
    "HCARB": "High carbon",   # (HCARB)
}

FAMILY_ORDER = ["BASE", "CPP1", "CPP2", "CPP3", "CPP4", "LCARB", "HCARB"]

def _map_scen_family(scen: str) -> str:
    """
    Map SATIMGE scenario codes (e.g., NDC_CPP4-RG) → your display family names.
    """
    s = str(scen).strip().upper()
    for key, label in FAMILY_NAMES.items():
        if f"_{key}" in s:
            return label
    return "Other"

# ───────────────────────── Generator ─────────────────────────
def generate_fig5_2_1_pwr_scen_families_bar_emissions_mtco2eq(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate stacked bar chart showing power sector emissions (MtCO₂-eq)
    across scenario families for milestone years (2024, 2030, 2035).
    """
    print("generating figure 5.2.1: Power Sector Scenario Families Emissions (MtCO₂-eq)")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Ensure numeric & clean
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce").fillna(0)
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

    # Keep only desired families
    keep_families = [FAMILY_NAMES[k] for k in FAMILY_ORDER]
    df = df[df["ScenarioFamily"].isin(keep_families)]

    # Build color map and stack order
    subsectors = df["Subsector"].unique()
    color_map = {s: color_for("fuel", s) for s in subsectors}

    stack_order = [
        "Coal", "Oil", "Natural Gas", "Nuclear", "Hydro", "Biomass",
        "Wind", "Solar PV", "Solar CSP", "Hybrid",
        "Battery Storage", "Pumped Storage", "Imports"
    ]
    stack_order = [s for s in stack_order if s in subsectors]

    # Define exact x-axis order based on what appears in the data (but preserving your order)
    scenario_order = [f for f in keep_families if f in df["ScenarioFamily"].unique()]

    # Ensure facet order: 2024, 2030, 2035
    year_order = [2024, 2030, 2035]
    df = df[df["Year"].isin(year_order)].copy()
    df["Year"] = pd.Categorical(df["Year"].astype(int), categories=year_order, ordered=True)


    fig = px.bar(
        df,
        x="ScenarioFamily",
        y="MtCO2-eq",
        color="Subsector",
        facet_col="Year",
        facet_col_wrap=3,
        barmode="stack",
        category_orders={
            "Year": year_order,               # 👈 facet order
            "ScenarioFamily": scenario_order,
            "Subsector": stack_order,
        },
        color_discrete_map=color_map,
        labels={"MtCO2-eq": "CO₂-eq Emissions (Mt)", "ScenarioFamily": ""},
    )


    # Apply shared style
    fig = apply_common_layout(fig)
    # Customize layout
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
        xaxis=dict(tickangle=-45, automargin=True),

        yaxis=dict(
            title=dict(text="CO₂-eq Emissions (Mt)", font=dict(size=25)),
            dtick=20,             # major ticks every 20 MtCO₂-eq
            tick0=0,
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
            ticklen=5,
            ticks="outside",
            minor=dict(
                ticks="outside",
                showgrid=True,
                gridcolor="rgba(0,0,0,0.05)",
                dtick=10           # minor gridlines every 10 MtCO₂-eq
            ),
        ),
        bargap=0.45
    )

    # Clean facet titles to show just year
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=21)))
    fig.update_xaxes(tickangle=-90)

    # Save chart + CSV
    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig5_2_1_pwr_scen_families_bar_emissions_mtco2eq")

        gallery_dir = project_root / "outputs" / "gallery"
        gallery_dir.mkdir(parents=True, exist_ok=True)
        src_img = Path(output_dir) / "fig5_2_1_pwr_scen_families_bar_emissions_mtco2eq_report.png"
        if src_img.exists():
            shutil.copy(src_img, gallery_dir / src_img.name)

        df.to_csv(Path(output_dir) / "fig5_2_1_pwr_scen_families_bar_emissions_mtco2eq_data.csv", index=False)


# ───────────────────────── Entry Point ─────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.2.1_pwr_scen_families_emissions_bar_3years.csv"
    df = pd.read_csv(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig5_2_1_pwr_scen_families_bar_emissions_mtco2eq"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_2_1_pwr_scen_families_bar_emissions_mtco2eq(df, str(out))
