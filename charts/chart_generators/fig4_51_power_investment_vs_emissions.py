# charts/chart_generators/fig4_51_power_investment_vs_emissions.py
from __future__ import annotations
"""
Fig 4.51 — 2 rows (stacked bars + stacked bars)

Row 1: Power emissions (MtCO₂-eq) — stacked by subsector/technology
Row 2: Cumulative investment in POWER — stacked by subsector/technology

Input:
  data/processed/4_51_power_cumulative_investment_needs_stacked_bar.csv
Required columns (case/space tolerant):
  - Scenario
  - Subsector
  - Investment in POWER
  - MtCO2-eq ALL (copy 2)
"""

import sys, re
from pathlib import Path
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout, extend_palettes_from_df, color_for
from charts.common.save import save_figures

# Bottom → top
STACK_ORDER = [
    "Coal", "Oil", "Natural Gas", "Nuclear",
    "Hydro", "Biomass",
    "Wind", "Solar PV", "Solar CSP", "Hybrid",
    "PumpStorage", "Battery",
    "Distribution", "Transmission",
    "Imports", "Exports",
]

COLOR_OVERRIDES = {
    "Battery": "#6C5CE7",
    "PumpStorage": "#556B2F",
    "Distribution": "#B8BDC9",
    "Transmission": "#A5ACB8",
    "Imports": "#D9B38C",
    "Exports": "#E09C9C",
}

FAMILY_NAMES = {
    "CPP4S": "CPPS Variant",
    "CPP4":  "CPPS",
    "BASE":  "WEM",
    "CPP1":  "CPP-IRP",
    "CPP2":  "CPP-IRPLight",
    "CPP3":  "CPP-SAREM",
    "LCARB": "Low Carbon",
    "HCARB": "High Carbon",
}
MANUAL_SCENARIO_LABELS: dict[str, str] = {}

def pretty_label(raw: str) -> str:
    s = str(raw)
    fam = next((k for k in sorted(FAMILY_NAMES, key=len, reverse=True) if f"_{k}" in s), None)
    fam_name = FAMILY_NAMES.get(fam, s)
    budget = None
    for pat, val in [
        ("-105-", 10.5), ("-095-", 9.5), ("-0925-", 9.25), ("-0875-", 8.75),
        ("-085-", 8.5), ("-0825-", 8.25), ("-0775-", 7.75), ("-075-", 7.5),
        ("-10-", 10.0), ("-09-", 9.0), ("-08-", 8.0),
    ]:
        if pat in s: budget = val; break
    if budget is None and re.search(r"-8-(?:NZ-)?RG", s):
        budget = 8.0
    is_nz = "-NZ-" in s.upper()
    parts = [fam_name] + (["Net Zero"] if is_nz else [])
    label = " · ".join(parts) + (f" ({budget:g} Gt budget)" if budget is not None else "")
    return MANUAL_SCENARIO_LABELS.get(raw, MANUAL_SCENARIO_LABELS.get(label, label))

def _norm_col(df: pd.DataFrame, name: str) -> str:
    key = name.lower().replace(" ", "")
    for c in df.columns:
        if c.lower().replace(" ", "") == key:
            return c
    raise KeyError(name)

def canonical_subsector(s: str) -> str:
    t = str(s).strip()
    u = t.upper().replace(" ", "")
    if u.startswith("E") and len(u) > 1:
        u2 = u[1:]
    else:
        u2 = u
    ALIASES = {
        "COAL": "Coal", "OIL": "Oil",
        "GAS": "Natural Gas", "NATURALGAS": "Natural Gas",
        "NUCLEAR": "Nuclear",
        "HYDRO": "Hydro", "HYDROPOWER": "Hydro",
        "BIOMASS": "Biomass",
        "WIND": "Wind", "WINDPOWER": "Wind",
        "PV": "Solar PV", "SOLARPV": "Solar PV", "SOLAR": "Solar PV",
        "CSP": "Solar CSP", "SOLARCSP": "Solar CSP",
        "HYBRID": "Hybrid",
        "PUMPSTORAGE": "PumpStorage", "PUMPEDSTORAGE": "PumpStorage",
        "BAT": "Battery", "BATTERY": "Battery",
        "DISTRIBUTION": "Distribution",
        "TRANSMISSION": "Transmission",
        "IMPORTS": "Imports",
        "EXPORTS": "Exports",
    }
    return ALIASES.get(u2, t)

def generate_fig4_51(df: pd.DataFrame, output_dir: str) -> None:
    scen_col   = _norm_col(df, "Scenario")
    sub_col    = _norm_col(df, "Subsector")
    invest_col = _norm_col(df, "Investment in POWER")
    emis_col   = _norm_col(df, "MtCO2-eq ALL (copy 2)")

    df = df.copy()
    df[sub_col] = df[sub_col].astype(str).str.strip().replace({"": pd.NA})

    # Palette from canonical names
    can_sub = df[sub_col].astype(str).map(canonical_subsector)
    extend_palettes_from_df(pd.DataFrame({"Commodity": can_sub.str.upper().str.replace(" ", "", regex=False)}))

    # Build emissions stacked by tech
    tmp_e = df.dropna(subset=[scen_col, sub_col, emis_col]).copy()
    tmp_e["SubCanon"] = tmp_e[sub_col].map(canonical_subsector)
    emis_pvt = tmp_e.groupby([scen_col, "SubCanon"], as_index=False)[emis_col].sum()

    # Scenario order: by total emissions ascending (so subplot 1 sorts x)
    total_emis = emis_pvt.groupby(scen_col, as_index=False)[emis_col].sum()
    scen_order = total_emis.sort_values(emis_col)[scen_col].tolist()

    # Investment stacked by tech
    tmp_i = df.dropna(subset=[scen_col, sub_col, invest_col]).copy()
    tmp_i["SubCanon"] = tmp_i[sub_col].map(canonical_subsector)
    inv_pvt = tmp_i.groupby([scen_col, "SubCanon"], as_index=False)[invest_col].sum()

    # Make figure
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.07, row_heights=[0.40, 0.60],
        subplot_titles=("Scenarios (sorted by emissions)", "")
    )

    # helper to avoid duplicate legend entries across both rows
    seen: set[str] = set()
    def add_stack(tr_df: pd.DataFrame, value_col: str, row: int) -> None:
        all_items = list(tr_df["SubCanon"].unique())
        ordered = [s for s in STACK_ORDER if s in all_items] + \
                  sorted([s for s in all_items if s not in STACK_ORDER])
        for sub in ordered:
            subdf = (tr_df[tr_df["SubCanon"] == sub]
                     .set_index(scen_col).reindex(scen_order).reset_index())
            show = sub not in seen
            fig.add_bar(
                x=subdf[scen_col], y=subdf[value_col],
                name=sub,
                marker=dict(color=COLOR_OVERRIDES.get(sub, color_for("fuel", sub))),
                legendgroup="tech", showlegend=show,
                row=row, col=1
            )
            seen.add(sub)

    # Row 1: emissions stacked
    add_stack(emis_pvt, emis_col, row=1)

    # Row 2: investment stacked
    add_stack(inv_pvt, invest_col, row=2)

    # Layout / axes
    apply_common_layout(fig)
    n = len(scen_order)
    fig.update_layout(
        barmode="stack",
        height=1000, width=1400,
        margin=dict(l=90, r=240, t=60, b=170),
        legend=dict(
            orientation="v", x=1.02, xanchor="left", y=1.0, yanchor="top",
            bgcolor="rgba(255,255,255,0)", font=dict(size=18)
        ),
    )

    # Y titles
    fig.update_yaxes(title_text="Power emissions<br>(MtCO<sub>2</sub>-eq)",
                     title_font=dict(size=20), row=1, col=1)
    fig.update_yaxes(title_text="Cumulative investment<br>in power",
                     title_font=dict(size=20), row=2, col=1)

    # X ticks (pretty labels only at bottom) + no side padding
    ticks_raw    = scen_order
    ticks_pretty = [pretty_label(s) for s in scen_order]
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(
        tickmode="array", tickvals=ticks_raw, ticktext=ticks_pretty, tickangle=-90,
        categoryorder="array", categoryarray=ticks_raw,
        range=[-0.5, max(n - 0.5, 0)], row=2, col=1
    )
    fig.update_xaxes(range=[-0.5, max(n - 0.5, 0)], row=1, col=1)

    # Save + sidecars
    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig4_51_power_investment_vs_emissions"
    save_figures(fig, str(out_dir), name=base)

    emis_pvt.rename(columns={scen_col:"Scenario", "SubCanon":"Subsector", emis_col:"Emissions_MtCO2eq"}).to_csv(
        out_dir / f"{base}_emissions_by_subsector.csv", index=False
    )
    inv_pvt.rename(columns={scen_col:"Scenario", "SubCanon":"Subsector", invest_col:"Investment"}).to_csv(
        out_dir / f"{base}_investment_by_subsector.csv", index=False
    )

if __name__ == "__main__":
    data_path = PROJECT_ROOT / "data" / "processed" / "4_51_power_cumulative_investment_needs_stacked_bar.csv"
    df_in = pd.read_csv(data_path)
    for c in df_in.columns:
        if df_in[c].dtype == object:
            try:
                df_in[c] = pd.to_numeric(df_in[c].str.replace(",", ""), errors="ignore")
            except Exception:
                pass
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_51_power_investment_vs_emissions"
    generate_fig4_51(df_in, str(out_dir))
