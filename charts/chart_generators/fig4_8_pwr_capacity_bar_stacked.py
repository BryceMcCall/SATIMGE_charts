# charts/chart_generators/fig4_8_pwr_capacity_bar_stacked.py
#
# Stacked bars of installed capacity (GW) by technology for WEM across 2024–2035.
# Mirrors styling of the TWh generator (legend, colors, x labels, minor grid).

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

# ── project root on path ────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

# ── config (dev mode) ───────────────────────────────────────────────
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# ── label mapping & stack order ─────────────────────────────────────
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
    "Hydro", "Biomass",
    "Wind", "Solar PV", "Solar CSP", "Hybrid",
    "Imports",
]

# ── generator ───────────────────────────────────────────────────────
def generate_fig4_8_pwr_capacity_bar_stacked(df: pd.DataFrame, output_dir: str) -> None:
    """
    Inputs:
      df columns -> 'Subsector', 'Year', 'Capacity (GW)' [and optional 'Scenario']
    Filters to 2024–2035 and (if present) WEM/BASE scenarios.
    """
    print("generating figure 4.9: Power — WEM capacity by technology (GW)")
    print(f"📂 Output directory: {output_dir}")

    df = df.copy()

    # optional scenario filter
    scen_col = next((c for c in df.columns if c.lower() == "scenario"), None)
    if scen_col:
        df = df[df[scen_col].astype(str).str.contains("BASE|WEM", case=False, na=False)]

    # types + range
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df[df["Year"].between(2024, 2035)]
    df["Capacity (GW)"] = pd.to_numeric(df["Capacity (GW)"], errors="coerce").fillna(0.0)

    # canonical tech labels + colors
    df["Subsector"] = df["Subsector"].map(_E2CANON).fillna(df["Subsector"])
    seen_techs = [s for s in STACK_ORDER if s in set(df["Subsector"].unique())]
    color_map = {s: color_for("fuel", s) for s in seen_techs}

    years = sorted(df["Year"].dropna().unique().tolist())

    fig = px.bar(
        df,
        x="Year",
        y="Capacity (GW)",
        hover_data={"Subsector": True},
        hover_name="Subsector",
        color="Subsector",
        barmode="stack",
        category_orders={"Year": years, "Subsector": seen_techs},
        color_discrete_map=color_map,
        labels={"Year": "", "Capacity (GW)": "Capacity (GW)", "Subsector": ""},
    )

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02),
        margin=dict(l=70, r=180, t=40, b=90),
        yaxis=dict(title=dict(text="Capacity (GW)", font=dict(size=24))),
        bargap=0.15,
    )

    # show all years as ticks; rotate
    fig.update_xaxes(
        tickmode="array",
        tickvals=years,
        ticktext=[str(y) for y in years],
        tickangle=-90,
    )

    # minor grid on y-axis; adjust dtick to taste
    fig.update_yaxes(minor=dict(showgrid=True, ticks="outside", dtick=5))

    fig.show()

    fig.write_html("outputs/charts_and_data/fig4_8_pwr_capacity_bar_stacked/fig4_8_interactive.html")


    if dev_mode:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    # save
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    save_figures(fig, output_dir, name="fig4_8_pwr_capacity_bar_stacked")
    df.to_csv(out_dir / "fig4_8_pwr_capacity_bar_stacked_data.csv", index=False)

    # optional gallery copy
    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    src_img = out_dir / "fig4_8_pwr_capacity_bar_stacked_report.png"
    if src_img.exists():
        shutil.copy2(src_img, gallery_dir / src_img.name)

# ── CLI entry ───────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_8_pwr_capacity_bar_stacked.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found at {data_path}. "
            "Export your WEM capacity table there (Subsector, Year, Capacity (GW))."
        )
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig4_8_pwr_capacity_bar_stacked"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig4_8_pwr_capacity_bar_stacked(df, str(out))
