# charts/chart_generators/fig4_42_emissions_scenario_families_box.py
from __future__ import annotations
import sys
from pathlib import Path
import shutil, yaml
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Import setup ────────────────────────────────────────────────
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH  = PROJECT_ROOT / "config.yaml"
DEV_MODE = False
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        DEV_MODE = yaml.safe_load(f).get("dev_mode", False)

# ── Updated vibrant color palette ───────────────────────────────
COLOR_MAP = {
    "WEM": "#F9C74F",          # golden yellow
    "CPP-IRP": "#F3722C",      # vivid orange
    "CPP-IRPLight": "#F8961E", # amber
    "CPP-SAREM": "#25A18E",    # blue-green
    "CPPS": "#004E64",         # deep blue
    "CPPS Variant": "#7AE582", # soft green
    "Low Carbon": "#43AA8B",   # teal green
    "High Carbon": "#5fa8d3",  # slate blue
}

# ── Scenario family renaming ────────────────────────────────────
RENAME_MAP = {
    "Base": "WEM",
    "WEM": "WEM",
    "CPP1": "CPP-IRP",
    "CPP2": "CPP-IRPLight",
    "CPP3": "CPP-SAREM",
    "CPP4": "CPPS",
    "CPP4 variant": "CPPS Variant",
    "Low carbon": "Low Carbon",
    "High carbon": "High Carbon",
    "Low Carbon": "Low Carbon",
    "High Carbon": "High Carbon",
}

# ── Chart generator ─────────────────────────────────────────────
def generate_fig4_42_emissions_scenario_families_box(df: pd.DataFrame, output_dir: str) -> None:
    """
    Box plot: 2035 CO₂-eq emissions (Mt) by Scenario FamilyGroup.
    Expected columns: ['Scenario', 'Scenario: FamilyGroup', 'Year', 'MtCO2-eq']
    """

    df = df.copy()
    rename = {}
    for c in df.columns:
        lc = c.lower().strip()
        if lc.startswith("scenario:"):
            rename[c] = "FamilyGroup"
        elif lc == "scenario":
            rename[c] = "Scenario"
        elif "mtco2" in lc:
            rename[c] = "MtCO2eq"
        elif lc == "year":
            rename[c] = "Year"
    if rename:
        df = df.rename(columns=rename)

    # Filter to 2035 only
    df = df[df["Year"] == 2035].copy()
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce")

    # Apply readable scenario family names
    df["FamilyGroup"] = df["FamilyGroup"].replace(RENAME_MAP)

    # Order categories logically
    order = [
        "WEM",
        "CPP-IRP",
        "CPP-IRPLight",
        "CPP-SAREM",
        "CPPS",
        "CPPS Variant",
        "Low Carbon",
        "High Carbon",
    ]
    df["FamilyGroup"] = pd.Categorical(df["FamilyGroup"], order, ordered=True)

    # ── Plot
    fig = px.box(
        df,
        x="FamilyGroup",
        y="MtCO2eq",
        color="FamilyGroup",
        color_discrete_map=COLOR_MAP,
        points="all",
        hover_data={"Scenario": True, "MtCO2eq": ":.2f"},
        labels={
            "FamilyGroup": "",
            "MtCO2eq": "2035 CO₂-eq Emissions (Mt)",
        },
        title=None,
    )

    fig = apply_common_layout(fig)

    # ── Add horizontal 2024 emissions reference line
    emissions_2024_level = 438.9
    fig.add_hline(
        y=emissions_2024_level,
        line_dash="dash",
        line_color="black",
        line_width=2,
        annotation_text=f"Emissions level in 2024 ≈ {emissions_2024_level:.1f}",
        annotation_position="top",
        annotation_font=dict(size=18, color="dark gray"),
    )

    # ── Layout

    fig.update_traces(
        marker=dict(size=6, opacity=0.9, line=dict(width=0.3, color="white")),
        selector=dict(type="box")
    )

    fig.update_xaxes(
        tickangle=-45,
        tickfont=dict(size=20),
        ticks="outside",
        showgrid=True,
    )
    fig.update_yaxes(
        title_font=dict(size=20),
        tickfont=dict(size=18),
        ticks="outside",
        dtick=20,
        minor=dict(ticks="outside", dtick=5, showgrid=True),
        range=[200, 450],
    )

    fig.update_layout(
        legend=dict(
            orientation="v",
            x=1.02, xanchor="left",
            y=0.98, yanchor="top",
            font=dict(size=20),
            title="",
        ),
        margin=dict(l=80, r=160, t=40, b=140),
    )

    # ── Save
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not DEV_MODE:
        save_figures(fig, str(out), name="fig4_42_emissions_scenario_families_box")
        df.to_csv(out / "fig4_42_emissions_scenario_families_box_data.csv", index=False)

        gal = PROJECT_ROOT / "outputs" / "gallery"
        gal.mkdir(parents=True, exist_ok=True)
        png = out / "fig4_42_emissions_scenario_families_box_report.png"
        if png.exists():
            shutil.copy2(png, gal / png.name)

# ── CLI ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "4_42_emissions_scenario_families_2035.csv"
    if not default_csv.exists():
        raise SystemExit(f"CSV not found at {default_csv}")
    df0 = pd.read_csv(default_csv, encoding="utf-8-sig")
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_42_emissions_scenario_families_box"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_fig4_42_emissions_scenario_families_box(df0, str(out_dir))
