# charts/chart_generators/fig_elecsentoutdemand_colour2.py
# Electricity "Sent out" (supply mix) + "Electricity use" (by sector)
# Uses palettes/aliases from charts.common.style

from __future__ import annotations
from pathlib import Path
import sys
import yaml
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots

# ensure project root on sys.path if run directly
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

# ── Config / switches ─────────────────────────────────────────────────────────
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

# ── Generator ─────────────────────────────────────────────────────────────────
def generate_fig_elecsentoutdemand_colour2(df: pd.DataFrame, output_dir: str):
    """
    Creates a 2-panel figure:
      LHS: Power sent-out by supply tech (stacked area, TWh)
      RHS: Electricity use by sector (stacked bars, TWh)
    All colours come from charts.common.style (fuel+sector palettes).
    """
    # Sub-techs we don’t want as "supply" in sent-out
    pwr_exclude = {"ETrans", "EDist", "EBattery", "EPumpStorage", "Demand",
                   "AutoGen-Chemical", "AutoGen-Chemcials"}  # keep excluded here

    # --------------------- Left panel: Sent out (supply) ----------------------
    mask = (
        (df["Scenario"] == ACTIVE_SCENARIO) &
        (df["Sector"] == "Power") &
        (df["Year"].between(YEAR_START, YEAR_END)) &
        (~df["Subsector"].isin(pwr_exclude)) &
        (df["Indicator"] == "FlowOut") &
        (df["Commodity"].isin(["ELCC", "Electricity"]))  # handle both spellings
    )
    df_pwr_out = (
        df.loc[mask, ["Year", "Subsector", "SATIMGE"]]
          .groupby(["Year", "Subsector"], as_index=False)["SATIMGE"].sum()
    )
    # Convert GJ → TWh
    df_pwr_out["SATIMGE"] = df_pwr_out["SATIMGE"] * (1 / 3.6)

    # canonical order; we’ll drop the ones not present
    supply_order = [
        "ECoal", "ENuclear", "EHydro", "EGas", "EOil", "EBiomass",
        "EWind", "EPV", "ECSP", "EHybrid", "Imports"
    ]
    present_supply = [s for s in supply_order if s in set(df_pwr_out["Subsector"])]

    # map each legend label → hex via style.py (handles E-prefix, aliases, etc.)
    color_map_supply = {s: color_for("fuel", s) for s in present_supply}

    fig_left = px.area(
        df_pwr_out,
        x="Year", y="SATIMGE",
        color="Subsector",
        category_orders={"Subsector": present_supply},
        color_discrete_map=color_map_supply,
    )

    # --------------------- Right panel: Electricity use -----------------------
    sectors_order = ["Industry", "Residential", "Commerce", "Transport", "Supply", "Agriculture"]

    m2 = (
        (df["Scenario"] == ACTIVE_SCENARIO) &
        (df["Sector"].isin(sectors_order)) &
        (df["Year"].between(YEAR_START, YEAR_END)) &
        (df["Indicator"] == "FlowIn") &
        (df["Short Description"].isin(["Electricity", "ELCC"]))
    )
    df_use = (
        df.loc[m2, ["Year", "Sector", "SATIMGE"]]
          .groupby(["Year", "Sector"], as_index=False)["SATIMGE"].sum()
    )
    df_use["SATIMGE"] = df_use["SATIMGE"] * (1 / 3.6)

    present_sectors = [s for s in sectors_order if s in set(df_use["Sector"])]
    color_map_sectors = {s: color_for("sector", s) for s in present_sectors}

    fig_right = px.bar(
        df_use,
        x="Year", y="SATIMGE",
        color="Sector",
        category_orders={"Sector": present_sectors},
        color_discrete_map=color_map_sectors,
    )

    # --------------------- Combine & style ------------------------------------
    fig = make_subplots(
        rows=1, cols=2, shared_yaxes=True,
        subplot_titles=("Sent out", "Electricity use")
    )
    for tr in fig_left.data:
        tr.showlegend = True
        fig.add_trace(tr, row=1, col=1)
    for tr in fig_right.data:
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

    # --------------------- Save -----------------------------------------------
    if DEV_MODE:
        print("👩‍💻 dev_mode ON — preview only (no files written)")
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    save_figures(fig, output_dir, name="ElecTWh_sentOut_consumed_colour2")
    # data drops (handy for QA)
    df_pwr_out.to_csv(Path(output_dir) / "sentout_data.csv", index=False)
    df_use.to_csv(Path(output_dir) / "use_data.csv", index=False)
