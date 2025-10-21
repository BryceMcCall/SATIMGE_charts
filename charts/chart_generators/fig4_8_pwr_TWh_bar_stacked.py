# charts/chart_generators/fig4_8_pwr_TWh_bar_stacked.py
#
# Stacked bars of total generation (TWh) by technology for WEM across all years.
# Uses the shared style + color palette (same colors as the capacity/TWh family charts).

# charts/chart_generators/fig4_8_pwr_TWh_bar_stacked.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

_E2CANON = {
    "ECoal": "Coal",
    "EOil": "Oil",
    "EGas": "Natural Gas",
    "ENuclear": "Nuclear",
    "EHydro": "Hydro",
    "EBiomass": "Biomass",
    "EWind": "Wind",
    "EPV": "Solar PV",
    "ECSP": "Solar CSP",
    "EHybrid": "Hybrid",
    "Imports": "Imports",
}
STACK_ORDER = [
    "Coal", "Oil", "Natural Gas", "Nuclear",
    "Hydro", "Biomass", "Wind",
    "Solar PV", "Solar CSP", "Hybrid", "Imports",
]

def generate_fig4_8_pwr_TWh_bar_stacked(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 4.8: Power — WEM generation by technology (TWh)")
    print(f"📂 Output directory: {output_dir}")

    df = df.copy()
    scen_col = next((c for c in df.columns if c.lower() == "scenario"), None)
    if scen_col:
        df = df[df[scen_col].astype(str).str.contains("BASE|WEM", case=False, na=False)].copy()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df[df["Year"].between(2024, 2035)]
    df["TWh (FlowOut)"] = pd.to_numeric(df["TWh (FlowOut)"], errors="coerce").fillna(0.0)

    df["Subsector"] = df["Subsector"].map(_E2CANON).fillna(df["Subsector"])
    seen = [s for s in STACK_ORDER if s in set(df["Subsector"].unique())]
    color_map = {s: color_for("fuel", s) for s in seen}

    year_order = sorted(df["Year"].dropna().unique().tolist())

    fig = px.bar(
        df,
        x="Year",
        y="TWh (FlowOut)",
        color="Subsector",
        barmode="stack",
        category_orders={"Year": year_order, "Subsector": seen},
        color_discrete_map=color_map,
        labels={"Year": "", "TWh (FlowOut)": "Generation (TWh)", "Subsector": ""},
    )

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02),
        margin=dict(l=70, r=180, t=40, b=90),
        yaxis=dict(title=dict(text="Generation (TWh)", font=dict(size=24))),
        bargap=0.15,
    )

    # ==== Requested tweaks ====
    # 1) Show ALL years as x-axis tick labels
    fig.update_xaxes(
        tickmode="array",
        tickvals=year_order,
        ticktext=[str(y) for y in year_order],
        tickangle=-90,
    )

    # 2) Minor ticks/grid on y-axis (adjust dtick_minor to taste)
    fig.update_yaxes(
        minor=dict(showgrid=True, ticks="outside", dtick=10),  # 10 TWh minor grid
    )

    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only")
        return

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    save_figures(fig, output_dir, name="fig4_8_pwr_TWh_bar_stacked")
    df.to_csv(out_dir / "fig4_8_pwr_TWh_bar_stacked_data.csv", index=False)

    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / "fig4_8_pwr_TWh_bar_stacked_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_8_pwr_TWh_bar_stacked.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}. "
            "Export WEM TWh table there (Subsector, Year, TWh (FlowOut))."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_8_pwr_TWh_bar_stacked"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_8_pwr_TWh_bar_stacked(df, str(out))
