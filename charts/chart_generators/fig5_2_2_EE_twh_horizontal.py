# charts/chart_generators/fig5_3_9_ee_twh_h.py

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
import yaml, shutil

# Config
project_root = Path(__file__).resolve().parents[2]
config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

def _first(df, opts):
    for o in opts:
        if o in df.columns: return o
    raise KeyError(f"Missing expected column among: {opts}")

def _scenario_label(s: str) -> str:
    s = str(s)
    if s == "NDC_BASE-RG": return "WEM"
    if s in ("NDC_BASE-EE-RG","NDC_BASE-EE"): return "WEM-EE"
    return map_scenario_key(s)

def _norm_tech(t: str) -> str:
    tt = str(t).strip()
    if tt.lower().startswith("com"): return "Commercial"
    return tt  # Residential / Industry

def generate_fig5_3_9_ee_twh_h(df: pd.DataFrame, output_dir: str) -> None:
    """
    Horizontal stacked bars for EE Electricity (TWh) by end-use sector,
    with in-bar labels.
    """
    print("generating fig5_3_9_ee_twh_h")
    col_year = _first(df, ["Year"])
    col_scen = _first(df, ["Scenario"])
    col_tech = _first(df, ["TechDescription","TechDesc","Tech"])
    col_val  = _first(df, ["TWh (FlowIn)","TWh (FlowOut)"])

    df[col_year] = pd.to_numeric(df[col_year], errors="coerce").astype("Int64")
    df[col_val]  = pd.to_numeric(df[col_val], errors="coerce").fillna(0.0)

    milestones = [2024, 2030, 2035]
    if df[col_year].isin(milestones).any():
        df = df[df[col_year].isin(milestones)]

    df["ScenarioLabel"] = df[col_scen].apply(_scenario_label)
    df["EndUse"] = df[col_tech].apply(_norm_tech)

    enduses = df["EndUse"].unique().tolist()
    color_map = {u: color_for("sector", "Commercial" if u=="Commercial" else u) for u in enduses}
    enduse_order = [u for u in ["Residential","Industry","Commercial"] if u in enduses]

    # HORIZONTAL: x is TWh, y is scenario
    fig = px.bar(
        df,
        x=col_val, y="ScenarioLabel",
        color="EndUse",
        facet_col=col_year, facet_col_wrap=3,
        orientation="h",
        barmode="stack",
        category_orders={"EndUse": enduse_order, "ScenarioLabel": ["WEM","WEM-EE"]},
        color_discrete_map=color_map,
        labels={col_val: "TWh", "ScenarioLabel": ""},
        text=col_val,  # in-bar values
    )

    fig = apply_common_layout(fig)
    fig.update_layout(
        title="",
        legend_title_text="",
        legend=dict(orientation="v", y=1, x=1.02),
        font=dict(size=14),
        margin=dict(l=80, r=220, t=60, b=70),
        bargap=0.55, bargroupgap=0.05,
    )
    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=12),
        cliponaxis=False,
    )

    fig.update_xaxes(title_text="Electricity (TWh)")
    fig.update_yaxes(categoryorder="array", categoryarray=["WEM","WEM-EE"], title_text="")

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=21)))

    if dev_mode:
        print("dev_mode ON (no export)")
    else:
        save_figures(fig, output_dir, name="fig5_3_9_ee_twh_h")
        gallery = project_root / "outputs" / "gallery"
        gallery.mkdir(parents=True, exist_ok=True)
        src = Path(output_dir) / "fig5_3_9_ee_twh_h_report.png"
        if src.exists(): shutil.copy(src, gallery / src.name)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        df.to_csv(Path(output_dir) / "fig5_3_9_ee_twh_h_data.csv", index=False)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.3.9_EE_TWh.csv"
    df = pd.read_csv(data_path)
    out = project_root / "outputs" / "charts_and_data" / "fig5_3_9_ee_twh_h"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_3_9_ee_twh_h(df, str(out))
