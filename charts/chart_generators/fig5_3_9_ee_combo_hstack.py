# charts/chart_generators/fig5_3_9_ee_combo_hstack.py
# Horizontal bars, two rows, with in-bar values on BOTH charts and extra spacing.

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures
from utils.mappings import map_scenario_key
import yaml, shutil

# ─────────── Config
project_root = Path(__file__).resolve().parents[2]
cfg_path = project_root / "config.yaml"
if cfg_path.exists():
    with open(cfg_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False

# ─────────── Helpers
def _first(df, opts):
    for o in opts:
        if o in df.columns:
            return o
    raise KeyError(f"Missing expected column among: {opts}")

def _scenario_label(s: str) -> str:
    s = str(s)
    if s == "NDC_BASE-RG":
        return "WEM"
    if s in ("NDC_BASE-EE-RG", "NDC_BASE-EE"):
        return "WEM + EE"
    return map_scenario_key(s)

def _norm_fuel_group(label: str) -> str:
    t = str(label).strip()
    lo = t.lower()
    if lo.startswith("biomass"):
        return "Biomass"
    if lo.startswith("coking"):
        return "Coke"
    if lo.startswith("coal"):
        return "Coal"
    if lo.startswith("crude oil"):
        return "Oil"
    if lo.startswith("diesel") or "gasoline" in lo or "kerosene" in lo:
        return "Oil"
    if lo.startswith("gas"):
        return "Natural Gas"
    if lo.startswith("hydro"):
        return "Hydro"
    if lo.startswith("nuclear"):
        return "Nuclear"
    if lo.startswith("solar"):
        return "Solar PV"
    if lo.startswith("wind"):
        return "Wind"
    if lo.startswith("waste"):
        return "Waste"
    return t

def _norm_enduse(t: str) -> str:
    tt = str(t).strip()
    if tt.lower().startswith("com"):
        return "Commercial"
    return tt

def _latest_year(df, col="Year"):
    years = pd.to_numeric(df[col], errors="coerce").dropna().astype(int)
    return int(years.max()) if not years.empty else 2035

# ─────────── Custom Sector Color Map (for TWh chart)
SECTOR_COLOR_MAP = {
    "A.Electricity": "#2F4858",  # deep blue-slate
    "Residential": "#33658A",  # steel blue
    "Industry": "#F6AE2D",  # amber
    "Commerce": "#F26419",  # orange
    "E.Other energy": "#86BBD8",  # sky
    "Commercial": "#5A8FB8",  # mid-sky
    "H.Waste": "#8FA3B8",  # cool slate
    "G.Land": "#BFD7EA",  # pale sky
}

# ─────────── Main
def generate_fig5_3_9_ee_combo_hstack(df_pj, df_twh, output_dir: str) -> None:
    """
    Row 1: EE Primary energy difference (PJ) by fuel (horizontal, with labels)
    Row 2: EE Electricity (TWh) by sector (horizontal, with labels + custom colors)
    """
    print("generating fig5_3_9_ee_combo_hstack (updated sector colours)")
    Path(output_dir).mkdir(parents=True, exist_ok=True)


# --- Primary PJ
    pj_commod = _first(df_pj, ["Commodity Short Description (group) 4",
                            "Commodity Short Description (group)",
                            "Commodity Group", "Commodity"])
    pj_scen = _first(df_pj, ["Scenario"])
    pj_year = _first(df_pj, ["Year"])
    pj_val = _first(df_pj, ["Difference in SATIMGE", "PJ Difference", "Value", "PJ"])

    df_pj[pj_val] = pd.to_numeric(df_pj[pj_val], errors="coerce").fillna(0.0)
    df_pj["Year"] = pd.to_numeric(df_pj[pj_year], errors="coerce").astype("Int64")
    yr_pj = _latest_year(df_pj)
    df_pj = df_pj[df_pj["Year"] == yr_pj].copy()

    df_pj["Fuel"] = df_pj[pj_commod].apply(_norm_fuel_group)
    df_pj["ScenarioLabel"] = df_pj[pj_scen].apply(_scenario_label)

    # add label column combining fuel + value
    df_pj["LabelText"] = df_pj.apply(
        lambda r: f"{r['Fuel']}<br>{r[pj_val]:.1f}", axis=1
    )

    fuel_order = [f for f in
                ["Coke","Coal","Oil","Natural Gas","Nuclear","Hydro","Biomass","Wind","Solar PV","Waste"]
                if f in df_pj["Fuel"].unique()]
    fuel_colors = {f: color_for("fuel", f) for f in fuel_order}
    fuel_colors["Coke"] = "#9a8c98" 

    fig_pj = px.bar(
        df_pj,
        x=pj_val, y="ScenarioLabel",
        color="Fuel",
        orientation="h",
        barmode="stack",
        category_orders={"ScenarioLabel": ["WEM","WEM + EE"], "Fuel": fuel_order},
        color_discrete_map=fuel_colors,
        labels={pj_val: "PJ", "ScenarioLabel": ""},
        text="LabelText",  # ← now fuel + value
    )

    fig_pj.update_traces(
        texttemplate="%{text}",         # uses both lines
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=16),
        cliponaxis=False,
    )

    fig_pj.update_xaxes(rangemode="normal")

    # remove fuel legend
    fig_pj.update_layout(showlegend=False)


    # --- Electricity TWh
    twh_scen = _first(df_twh, ["Scenario"])
    twh_year = _first(df_twh, ["Year"])
    twh_tech = _first(df_twh, ["TechDescription", "TechDesc", "Tech", "NDC GHG emisssion cats short"])
    twh_val = _first(df_twh, ["TWh (FlowIn)", "TWh (FlowOut)", "Value", "TWh"])

    df_twh[twh_val] = pd.to_numeric(df_twh[twh_val], errors="coerce").fillna(0.0)
    df_twh["Year"] = pd.to_numeric(df_twh[twh_year], errors="coerce").astype("Int64")
    yr_twh = _latest_year(df_twh)
    df_twh = df_twh[df_twh["Year"] == yr_twh].copy()

    df_twh["ScenarioLabel"] = df_twh[twh_scen].apply(_scenario_label)

    # normalize to category names that match the color map
    df_twh["EndUse"] = df_twh[twh_tech].astype(str).str.strip()

    end_order = [e for e in SECTOR_COLOR_MAP.keys() if e in df_twh["EndUse"].unique()]

    fig_twh = px.bar(
        df_twh,
        x=twh_val, y="ScenarioLabel",
        color="EndUse",
        orientation="h",
        barmode="stack",
        category_orders={"ScenarioLabel": ["WEM", "WEM + EE"], "EndUse": end_order},
        color_discrete_map=SECTOR_COLOR_MAP,
        labels={twh_val: "TWh", "ScenarioLabel": ""},
        text=twh_val,
    )
    fig_twh.update_traces(
        texttemplate="%{text:.2f}",
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=18),
        cliponaxis=False,
    )

    # --- Combine vertically
    combo = make_subplots(
        rows=2, cols=1,
        shared_yaxes=True,
        vertical_spacing=0.2,
        subplot_titles=(
            f"Primary energy difference (PJ) - {yr_pj}",
            f"Electricity (TWh) - {yr_twh}",
        ),
    )
    for tr in fig_pj.data:
        combo.add_trace(tr, row=1, col=1)
    for tr in fig_twh.data:
        combo.add_trace(tr, row=2, col=1)

    # ✅ disable legend only for top chart (chart 1)
    for trace in combo.data:
        if trace.yaxis == "y" or trace.legendgroup in fuel_order:
            trace.showlegend = False

    combo = apply_common_layout(combo)
    combo.update_layout(
        barmode="stack",
        bargap=0.20,
        bargroupgap=0.15,
        legend=dict(
            orientation="h",
            y=-0.28,
            x=0.5, xanchor="center",
            title_text="",
        ),
        margin=dict(l=110, r=110, t=220, b=100),
        font=dict(size=14),
    )

    combo.update_yaxes(categoryorder="array", categoryarray=["WEM", "WEM + EE"], title_text="")
    combo.update_xaxes(title_text="", row=1, col=1, rangemode="normal")
    combo.update_xaxes(title_text="", row=2, col=1)

    combo.for_each_annotation(lambda a: a.update(font=dict(size=20)))

    if dev_mode:
        print("👩‍💻 dev_mode ON — showing chart only (no export)")
    else:
        save_figures(combo, output_dir, name="fig5_3_9_ee_combo_hstack")
        gal = project_root / "outputs" / "gallery"
        gal.mkdir(parents=True, exist_ok=True)
        src = Path(output_dir) / "fig5_3_9_ee_combo_hstack_report.png"
        if src.exists():
            shutil.copy(src, gal / src.name)
        df_pj.to_csv(Path(output_dir) / "fig5_3_9_ee_combo_hstack_primary_pj_data.csv", index=False)
        df_twh.to_csv(Path(output_dir) / "fig5_3_9_ee_combo_hstack_electricity_twh_data.csv", index=False)


if __name__ == "__main__":
    pj_path = project_root / "data" / "processed" / "5.3.9_EE_primary_energy_PJ.csv"
    twh_path = project_root / "data" / "processed" / "5.3.9_EE_TWh.csv"
    df_pj = pd.read_csv(pj_path)
    df_twh = pd.read_csv(twh_path)
    out_dir = project_root / "outputs" / "charts_and_data" / "fig5_3_9_ee_combo_hstack"
    generate_fig5_3_9_ee_combo_hstack(df_pj, df_twh, str(out_dir))
