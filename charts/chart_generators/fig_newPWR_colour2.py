# charts/chart_generators/fig_newPWR_colour2.py
# Power: New Build + Total Capacity (stacked bars)
# Colours come from charts.common.style (fuel palette + E-prefix aliases)

from __future__ import annotations
from pathlib import Path
import sys
import yaml
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CFG = {}
_cfg_path = PROJECT_ROOT / "config.yaml"
if _cfg_path.exists():
    with open(_cfg_path, "r", encoding="utf-8") as fh:
        _CFG = yaml.safe_load(fh)

DEV_MODE = _CFG.get("dev_mode", False)
ACTIVE_SCENARIO = _CFG.get("active_scenario", "NDC_BASE-RG")
YEAR_START = int(_CFG.get("year_start", 2024))
YEAR_END   = int(_CFG.get("year_end", 2035))

def generate_fig_newPWR_colour2(df: pd.DataFrame, output_dir: str):
    # Note: we DO include AutoGen-Chemical here because it appears in your legend
    pwr_exclude = {"ETrans", "EDist", "EBattery", "EPumpStorage", "Demand"}

    mask = (
        (df["Scenario"] == ACTIVE_SCENARIO) &
        (df["Sector"] == "Power") &
        (df["Year"].between(YEAR_START, YEAR_END)) &
        (~df["Subsector"].isin(pwr_exclude))
    )
    d = df.loc[mask, ["Year", "Subsector", "Indicator", "SATIMGE"]].copy()

    supply_order = [
        "ECoal", "ENuclear", "EHydro", "EGas", "EOil", "EBiomass",
        "EWind", "EPV", "ECSP", "AutoGen-Chemical", "EHybrid", "Imports"
    ]
    present_supply = [s for s in supply_order if s in set(d["Subsector"])]
    color_map = {s: color_for("fuel", s) for s in present_supply}

    # New build
    new_build = (
        d[d["Indicator"] == "NewCapacity"]
        .groupby(["Year", "Subsector"], as_index=False)["SATIMGE"].sum()
    )
    fig1 = px.bar(
        new_build, x="Year", y="SATIMGE", color="Subsector",
        category_orders={"Subsector": present_supply},
        color_discrete_map=color_map,
    )

    # Total capacity
    total_cap = (
        d[d["Indicator"] == "Capacity"]
        .groupby(["Year", "Subsector"], as_index=False)["SATIMGE"].sum()
    )
    fig2 = px.bar(
        total_cap, x="Year", y="SATIMGE", color="Subsector",
        category_orders={"Subsector": present_supply},
        color_discrete_map=color_map,
    )

    # Combine
    fig = make_subplots(
        rows=1, cols=2, shared_yaxes=False,
        subplot_titles=("New Build", "Total Capacity")
    )
    for tr in fig1.data:
        tr.showlegend = False  # legend on the right chart only
        fig.add_trace(tr, row=1, col=1)
    for tr in fig2.data:
        tr.showlegend = True
        fig.add_trace(tr, row=1, col=2)

    apply_common_layout(fig, image_type="report")
    fig.update_layout(
        barmode="stack",
        width=1000, height=500,
        legend_title_text="",
        xaxis=dict(tickmode="linear", dtick=1, tickangle=45),
        xaxis2=dict(tickmode="linear", dtick=1, tickangle=45),
    )

    if DEV_MODE:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    save_figures(fig, output_dir, name="newPwR_doubleChart_colour2")
    new_build.to_csv(Path(output_dir) / "new_build_data.csv", index=False)
    total_cap.to_csv(Path(output_dir) / "total_capacity_data.csv", index=False)
