# charts/chart_generators/fig5_3_9_ee_twh.py

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


def _first_existing(df: pd.DataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of the expected columns found: {candidates}")

def generate_fig5_3_9_ee_twh(df: pd.DataFrame, output_dir: str) -> None:
    """
    Energy Efficiency electricity consumption by end-use (TWh), with in-bar values.
    Expects columns similar to:
      - 'Scenario'
      - 'TechDescription' ∈ {Residential, Industry, Commerce/Commercial}
      - 'Year'
      - 'TWh (FlowIn)' (preferred) or 'TWh (FlowOut)'
    """
    print("generating figure 5.3.9: EE electricity (TWh) with labels")
    print(f"🛠️ dev_mode = {dev_mode}")
    print(f"📂 Output directory: {output_dir}")

    # Column harmonisation
    y_col = _first_existing(df, ["TWh (FlowIn)", "TWh (FlowOut)"])
    tech_col = _first_existing(df, ["TechDescription", "TechDesc", "Tech"])
    scen_col = "Scenario"
    year_col = "Year"

    # Basic cleaning
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce").fillna(0.0)

    # Keep milestone years if present, else keep all
    milestone = [2024, 2030, 2035]
    if df[year_col].isin(milestone).any():
        df = df[df[year_col].isin(milestone)]

    # Normalise TechDescription & Scenario labels
    tech_map = {"Commerce": "Commercial", "Com": "Commercial"}
    df[tech_col] = df[tech_col].replace(tech_map)

    def scen_map(s: str) -> str:
        if s == "NDC_BASE-RG":
            return "WEM"
        if s == "NDC_BASE-EE-RG":
            return "WEM-EE"
        return map_scenario_key(s)

    df["ScenarioLabel"] = df[scen_col].astype(str).apply(scen_map)

    # Color map from sector palette
    techs = df[tech_col].dropna().astype(str).unique().tolist()
    color_map = {}
    for t in techs:
        # Use sector colors; fallback to label itself
        key = "Commercial" if t.lower().startswith("com") else t
        color_map[t] = color_for("sector", key)

    # Stack order to resemble your example (bottom→top)
    stack_order = [t for t in ["Residential", "Industry", "Commercial"] if t in techs]

    # Plot
    fig = px.bar(
        df,
        x="ScenarioLabel",
        y=y_col,
        color=tech_col,
        facet_col=year_col,
        facet_col_wrap=3,
        barmode="stack",
        category_orders={tech_col: stack_order},
        color_discrete_map=color_map,
        labels={y_col: "TWh", "ScenarioLabel": ""},
        text=y_col,  # per-segment labels
    )

    # Shared style + label formatting
    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        font=dict(size=14),
        margin=dict(l=40, r=180, t=40, b=120),
        yaxis=dict(dtick=20, title=dict(text="Electricity (TWh)", font=dict(size=23))),
        bargap=0.45,
    )
    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=18),
        cliponaxis=False,
    )

    # Clean facet titles and rotate x labels
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=21)))
    fig.update_xaxes(tickangle=-90)

    # Save
    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
    else:
        print("💾 saving figure and data")
        save_figures(fig, output_dir, name="fig5_3_9_ee_twh")

        gallery_dir = project_root / "outputs" / "gallery"
        gallery_dir.mkdir(parents=True, exist_ok=True)
        src_img = Path(output_dir) / "fig5_3_9_ee_twh_report.png"
        if src_img.exists():
            shutil.copy(src_img, gallery_dir / src_img.name)

        # Export exact plotting table
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        df.to_csv(Path(output_dir) / "fig5_3_9_ee_twh_data.csv", index=False)


if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.3.9_EE_TWh.csv"
    df = pd.read_csv(data_path)

    out = project_root / "outputs" / "charts_and_data" / "fig5_3_9_ee_twh"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_3_9_ee_twh(df, str(out))
