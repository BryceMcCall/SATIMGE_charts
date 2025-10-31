from __future__ import annotations
"""
Fig 4.49 — Vertical stack:
 • Top: emissions scatter (colour = curtailed/not curtailed)
 • Middle: capacity by technology (stacked bars, GW)
 • Bottom: electricity sent out (stacked bars, TWh)
Input : data/processed/4_49_power_capacity_output_emissions_curtailment_scatter_stacked_bar.csv
Output: outputs/charts_and_data/fig4_49_power_cap_out_emis/{png,svg}
"""

import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── safe import path -----------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout, extend_palettes_from_df, color_for
from charts.common.save import save_figures

# ── Pretty labels (inline) -----------------------------------------------------
FAMILY_NAMES = {
    "BASE":  "WEM",
    "CPP1":  "CPP-IRP",
    "CPP2":  "CPP-IRPLight",
    "CPP3":  "CPP-SAREM",
    "CPP4":  "CPPS",
    "LCARB": "Low Carbon",
    "HCARB": "High Carbon",
}
MANUAL_SCENARIO_LABELS: dict[str, str] = {}
import re
def pretty_label(raw: str) -> str:
    s = str(raw)
    fam = next((k for k in FAMILY_NAMES if f"_{k}" in s), None)
    fam_name = FAMILY_NAMES.get(fam, s)
    budget = None
    for pat, val in [("-105-",10.5),("-095-",9.5),("-0925-",9.25),("-0875-",8.75),
                     ("-085-",8.5),("-0825-",8.25),("-0775-",7.75),("-075-",7.5),
                     ("-10-",10.0),("-09-",9.0),("-08-",8.0)]:
        if pat in s:
            budget = val; break
    if budget is None and re.search(r"-8-(?:NZ-)?RG", s):
        budget = 8.0
    is_nz = "-NZ-" in s.upper()
    parts = [fam_name] + (["Net Zero"] if is_nz else [])
    label = " · ".join(parts) + (f" ({budget:g} Gt budget)" if budget is not None else "")
    return MANUAL_SCENARIO_LABELS.get(raw, MANUAL_SCENARIO_LABELS.get(label, label))

# ── helpers --------------------------------------------------------------------
def _norm_col(df: pd.DataFrame, name: str) -> str:
    key = name.lower().replace(" ", "")
    for c in df.columns:
        if c.lower().replace(" ", "") == key:
            return c
    raise KeyError(name)

def _fuel_disp(s: str) -> str:
    return s  # let style.color_for("fuel", ...) handle aliases (EPV->Solar PV etc.)

# ── generator ------------------------------------------------------------------
def generate_fig4_49(df: pd.DataFrame, output_dir: str) -> None:
    scen_col = _norm_col(df, "Scenario")
    curt_col = _norm_col(df, "NDC scenarios sasol curtailed")
    emis_col = _norm_col(df, "MtCO2-eq ALL")

    # tolerant names for capacity & sent-out
    cap_col = None
    for cand in ("Capacity (GW)", "Capacity", "capacity_gw"):
        try: cap_col = _norm_col(df, cand); break
        except KeyError: pass
    out_col = None
    for cand in ("elec sent out SA grid", "TWh sent out", "Sent out (TWh)", "elec_sent_out"):
        try: out_col = _norm_col(df, cand); break
        except KeyError: pass
    if out_col is None:
        raise KeyError("Could not find the TWh 'sent out' column in the CSV.")

    tech_col = next((c for c in ["Subsector (group) 5", "Subsector (group) 4", "Subsector", "Power sector technology"] if c in df.columns), None)
    if tech_col is None:
        raise KeyError("Technology column not found (e.g., 'Subsector (group) 5').")

    extend_palettes_from_df(pd.DataFrame({"Commodity": df[tech_col].astype(str).str.upper().str.replace(" ","",regex=False)}))

    # Emissions per scenario (keep one point per scenario/status)
    emis_df = (
        df[[scen_col, emis_col, curt_col]]
        .dropna(subset=[scen_col, emis_col])
        .groupby([scen_col, curt_col], as_index=False)[emis_col].min()
    )
    emis_df["ScenarioPretty"] = emis_df[scen_col].map(pretty_label)
    scen_order = emis_df.sort_values(emis_col)[scen_col].tolist()

    # Capacity & Sent-out long frames
    cap_pvt = pd.DataFrame(columns=[scen_col, tech_col, "y"])
    if cap_col is not None:
        cap_pvt = (df.dropna(subset=[scen_col, tech_col, cap_col])
                     .groupby([scen_col, tech_col], as_index=False)[cap_col].sum())
    out_pvt = (df.dropna(subset=[scen_col, tech_col, out_col])
                 .groupby([scen_col, tech_col], as_index=False)[out_col].sum())

    # order scenarios
    from pandas.api.types import CategoricalDtype
    cat = CategoricalDtype(categories=scen_order, ordered=True)
    for _d in (cap_pvt, out_pvt):
        _d[scen_col] = _d[scen_col].astype(cat)
        _d.sort_values([scen_col, tech_col], inplace=True)

    # figure with THREE rows  ───────────────────────────────────────────────────
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=("Scenarios below 300", "", ""),
        row_heights=[0.33, 0.33, 0.34],
    )

    # Top: emissions scatter
    curt_color = {"Curtailed": "#E07B39", "Not curtailed": "#33A352"}
    for status, sub in emis_df.groupby(curt_col, dropna=False):
        label = str(status) if pd.notna(status) else "Not specified"
        fig.add_scatter(
            x=[pretty_label(s) for s in sub[scen_col]],
            y=sub[emis_col],
            mode="markers",
            name=label,
            marker=dict(color=curt_color.get(label, "#7f7f7f"), size=10, line=dict(width=0)),
            showlegend=True,
            legendgroup="curt",
            row=1, col=1
        )

    # Middle: Capacity (GW)
    if not cap_pvt.empty:
        for tech, sub in cap_pvt.groupby(tech_col):
            disp = _fuel_disp(str(tech))
            fig.add_bar(
                x=[pretty_label(s) for s in sub[scen_col]],
                y=sub[cap_col],
                name=str(tech).lstrip("E"),
                marker=dict(color=color_for("fuel", disp)),
                showlegend=True,
                legendgroup="tech",
                row=2, col=1
            )

    # Bottom: TWh sent out  ─────────────────────────────────────────────────────
    for tech, sub in out_pvt.groupby(tech_col):
        disp = _fuel_disp(str(tech))
        fig.add_bar(
            x=[pretty_label(s) for s in sub[scen_col]],
            y=sub[out_col],
            name=str(tech).lstrip("E"),
            marker=dict(color=color_for("fuel", disp)),
            showlegend=False,          # keep one tech legend only (middle row)
            legendgroup="tech",
            row=3, col=1
        )

    # Layout & axes
    apply_common_layout(fig)
    fig.update_layout(
        barmode="stack",
        height=1400, width=1400,                # taller to fit row 3 + ticks
        margin=dict(l=90, r=240, t=60, b=160),
        legend=dict(orientation="v", x=1.02, xanchor="left", y=1.0, yanchor="top",
                    bgcolor="rgba(255,255,255,0)")
    )
    fig.update_yaxes(title_text="National emissions (MtCO2-eq)", row=1, col=1)
    fig.update_yaxes(title_text="Capacity (GW)",                  row=2, col=1)
    fig.update_yaxes(title_text="TWh sent out",                   row=3, col=1)

    # Only bottom shows x ticks; rotate for space
    ticks = [pretty_label(s) for s in scen_order]
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(showticklabels=False, row=2, col=1)
    fig.update_xaxes(tickmode="array", tickvals=ticks, ticktext=ticks, tickangle=-90, row=3, col=1)

    # Save & sidecar csv
    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig4_49_power_cap_out_emis"
    save_figures(fig, str(out_dir), name=base)
    emis_df.rename(columns={scen_col:"Scenario", emis_col:"MtCO2eq", curt_col:"Curtailed"}) \
           .to_csv(out_dir / f"{base}_emissions.csv", index=False)
    if not cap_pvt.empty:
        cap_pvt.rename(columns={scen_col:"Scenario", tech_col:"Tech", cap_col:"Capacity_GW"}) \
               .to_csv(out_dir / f"{base}_capacity.csv", index=False)
    out_pvt.rename(columns={scen_col:"Scenario", tech_col:"Tech", out_col:"TWh_sent_out"}) \
          .to_csv(out_dir / f"{base}_sentout.csv", index=False)

# ── CLI ------------------------------------------------------------------------
if __name__ == "__main__":
    data_path = PROJECT_ROOT / "data" / "processed" / "4_49_power_capacity_output_emissions_curtailment_scatter_stacked_bar.csv"
    df_in = pd.read_csv(data_path)
    # light numeric coercion for csvs with commas
    for c in df_in.columns:
        if df_in[c].dtype == object:
            try: df_in[c] = pd.to_numeric(df_in[c].str.replace(",", ""), errors="ignore")
            except Exception: pass
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_49_power_cap_out_emis"
    generate_fig4_49(df_in, str(out_dir))
