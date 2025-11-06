# charts/chart_generators/fig4_49_power_cap_out_emis.py
from __future__ import annotations
"""
Fig 4.49 — 2 rows (scatter + stacked bars)

Row 1: National CO₂-eq emissions (Mt) — markers by curtailed status
Row 2: Capacity (GW) — stacked by technology with custom stack order

Key choices:
- Use RAW scenario keys for x to avoid double counting when pretty labels collide.
- Pretty labels are used only as ticktext.
- '_CPP4S' → 'CPPS Variant' and '_CPP4' → 'CPPS' (longest key wins).
- Canonicalise tech names from dataset labels like: EBattery, EPumpStorage, ECoal, ...
- Enforce stack order (bottom → top).

Inputs:
  data/processed/4_49_power_capacity_output_emissions_curtailment_scatter_stacked_bar.csv
Outputs:
  outputs/charts_and_data/fig4_49_power_cap_out_emis/{png,svg,csv}
"""

import sys, re
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── project path for shared utilities ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout, extend_palettes_from_df, color_for
from charts.common.save import save_figures

# ── Desired stack order (bottom → top) ────────────────────────────────────────
STACK_ORDER = [
    "Coal", "Oil", "Natural Gas", "Nuclear",
    "Hydro", "Biomass",
    "Wind", "Solar PV", "Solar CSP", "Hybrid",
    "Imports",
]
COLOR_OVERRIDES = {
    "Battery": "#61E75F",   # distinct violet; try "#8E44AD" if you prefer deeper
    "Pumped Storage": "#0984E3",  # bright blue
}

# ── Family display names (longest keys first to avoid false matches) ──────────
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
        if pat in s:
            budget = val; break
    if budget is None and re.search(r"-8-(?:NZ-)?RG", s):
        budget = 8.0

    is_nz = "-NZ-" in s.upper()
    parts = [fam_name] + (["Net Zero"] if is_nz else [])
    label = " · ".join(parts) + (f" ({budget:g} Gt budget)" if budget is not None else "")
    return MANUAL_SCENARIO_LABELS.get(raw, MANUAL_SCENARIO_LABELS.get(label, label))

# ── helpers ───────────────────────────────────────────────────────────────────
def _norm_col(df: pd.DataFrame, name: str) -> str:
    key = name.lower().replace(" ", "")
    for c in df.columns:
        if c.lower().replace(" ", "") == key:
            return c
    raise KeyError(name)

def canonical_tech(s: str) -> str:
    """
    Map dataset labels to canonical names consistent with STACK_ORDER & palette.
    Dataset examples (as provided): EBattery, EPumpStorage, EOil, ECSP, EHydro,
    EHybrid, EBiomass, EGas, EPV, EWind, ENuclear, ECoal.
    """
    t = str(s).strip()
    u = t.upper().strip()

    # Drop leading 'E' prefix used in electricity tech labels
    if u.startswith("E") and len(u) > 1:
        u = u[1:]
    u = u.replace(" ", "")

    ALIASES = {
        "COAL": "Coal",
        "OIL": "Oil",
        "GAS": "Natural Gas",
        "NATURALGAS": "Natural Gas",
        "NUCLEAR": "Nuclear",
        "HYDRO": "Hydro",
        "HYDROPOWER": "Hydro",
        "BIOMASS": "Biomass",
        "WIND": "Wind",
        "WINDPOWER": "Wind",
        "PV": "Solar PV",
        "SOLARPV": "Solar PV",
        "SOLAR": "Solar PV",
        "CSP": "Solar CSP",
        "SOLARCSP": "Solar CSP",
        "HYBRID": "Hybrid",
        "IMPORTS": "Imports",
        "PUMPSTORAGE": "Pumped Storage",
        "PUMPEDSTORAGE": "Pumped Storage",
        "BAT": "Battery",
        "BATTERY": "Battery",
        "BATTERIES": "Battery",
    }
    return ALIASES.get(u, t.strip())

# ── main generator ────────────────────────────────────────────────────────────
def generate_fig4_49(df: pd.DataFrame, output_dir: str) -> None:
    scen_col = _norm_col(df, "Scenario")
    curt_col = _norm_col(df, "NDC scenarios sasol curtailed")
    emis_col = _norm_col(df, "MtCO2-eq ALL")

    # capacity column (tolerant)
    cap_col = None
    for cand in ("Capacity (GW)", "Capacity", "capacity_gw"):
        try:
            cap_col = _norm_col(df, cand); break
        except KeyError:
            continue

    tech_col = next(
        (c for c in ["Subsector (group) 5", "Subsector (group) 4",
                     "Subsector", "Power sector technology"] if c in df.columns),
        None
    )
    if tech_col is None:
        raise KeyError("Technology column not found (e.g., 'Subsector (group) 5').")

    # Extend palette using CANONICAL names to ensure consistent colours
    can_techs = df[tech_col].astype(str).map(canonical_tech)
    extend_palettes_from_df(pd.DataFrame({"Commodity": can_techs.str.upper().str.replace(" ", "", regex=False)}))

    # Emissions table (one y per scenario x curtailed-status)
    emis_df = (
        df[[scen_col, emis_col, curt_col]]
        .dropna(subset=[scen_col, emis_col])
        .groupby([scen_col, curt_col], as_index=False)[emis_col]
        .min()
    )
    scen_order_raw = emis_df.sort_values(emis_col)[scen_col].tolist()

    # Capacity table grouped by canonical tech
    cap_pvt = pd.DataFrame(columns=[scen_col, "TechCanon", "y"])
    if cap_col:
        tmp = df.dropna(subset=[scen_col, tech_col, cap_col]).copy()
        tmp["TechCanon"] = tmp[tech_col].astype(str).map(canonical_tech)
        cap_pvt = tmp.groupby([scen_col, "TechCanon"], as_index=False)[cap_col].sum()

    # ── figure (2 rows) ────────────────────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.07, row_heights=[0.45, 0.55],
        subplot_titles=("Scenarios below 300Mt", "")
    )

    # Row 1: emissions scatter (use RAW keys for x)
    curt_color = {"Curtailed": "#E07B39", "Not curtailed": "#33A352"}
    for status, sub in emis_df.groupby(curt_col, dropna=False):
        label = str(status) if pd.notna(status) else "Not specified"
        fig.add_scatter(
            x=sub[scen_col], y=sub[emis_col], mode="markers",
            name=label, legendgroup="curt", showlegend=True,
            marker=dict(color=curt_color.get(label, "#7f7f7f"), size=10, line=dict(width=0)),
            row=1, col=1
        )

    # Row 2: capacity bars (custom stack order, bottom→top)
    if not cap_pvt.empty:
        all_techs = list(cap_pvt["TechCanon"].unique())
        ordered_techs = [t for t in STACK_ORDER if t in all_techs] + \
                        sorted([t for t in all_techs if t not in STACK_ORDER])
        for tech in ordered_techs:
            sub = cap_pvt[cap_pvt["TechCanon"] == tech]
            fig.add_bar(
                x=sub[scen_col],
                y=sub[cap_col],
                name=tech,
                marker=dict(color=COLOR_OVERRIDES.get(tech, color_for("fuel", tech))),
                legendgroup="tech",
                showlegend=True,
                row=2, col=1,
            )

    # ── layout & axes ──────────────────────────────────────────────────────────
    apply_common_layout(fig)
    n = len(scen_order_raw)
    fig.update_layout(
        barmode="stack",
        height=1000, width=1400,
        margin=dict(l=90, r=240, t=60, b=160),
        legend=dict(
            orientation="v", x=1.02, xanchor="left", y=1.0, yanchor="top",
            bgcolor="rgba(255,255,255,0)", font=dict(size=18)
        ),
    )

    # Y-axis titles (CO₂ subscript + line break)
    fig.update_yaxes(title_text="National CO<sub>2</sub>-eq<br>Emissions (Mt)",
                     title_font=dict(size=20), row=1, col=1)
    fig.update_yaxes(title_text="Capacity (GW)",
                     title_font=dict(size=20), row=2, col=1)

    # (Optional) Example: control major/minor y ticks
    # fig.update_yaxes(tickmode="linear", tick0=0, dtick=50,
    #                  minor=dict(tick0=0, dtick=10, showgrid=True, gridcolor="rgba(0,0,0,0.08)"),
    #                  row=1, col=1)
    # fig.update_yaxes(tickmode="linear", tick0=0, dtick=20,
    #                  minor=dict(tick0=0, dtick=5, showgrid=True, gridcolor="rgba(0,0,0,0.08)"),
    #                  row=2, col=1)

    # X ticks: pretty labels only as ticktext; remove side padding on category axis
    ticks_raw    = scen_order_raw
    ticks_pretty = [pretty_label(s) for s in scen_order_raw]
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(
        tickmode="array", tickvals=ticks_raw, ticktext=ticks_pretty, tickangle=-90,
        categoryorder="array", categoryarray=ticks_raw,
        range=[-0.5, max(n - 0.5, 0)],
        row=2, col=1
    )
    fig.update_xaxes(range=[-0.5, max(n - 0.5, 0)], row=1, col=1)

    # ── save + sidecar CSVs ────────────────────────────────────────────────────
    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig4_49_power_cap_out_emis"
    save_figures(fig, str(out_dir), name=base)

    emis_df.rename(columns={scen_col:"Scenario", emis_col:"MtCO2eq", curt_col:"Curtailed"}).to_csv(
        out_dir / f"{base}_emissions.csv", index=False
    )
    if not cap_pvt.empty:
        cap_pvt.rename(columns={scen_col:"Scenario", "TechCanon":"Tech", cap_col:"Capacity_GW"}).to_csv(
            out_dir / f"{base}_capacity.csv", index=False
        )

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = PROJECT_ROOT / "data" / "processed" / "4_49_power_capacity_output_emissions_curtailment_scatter_stacked_bar.csv"
    df_in = pd.read_csv(data_path)

    # light numeric coercion for csvs with thousands commas
    for c in df_in.columns:
        if df_in[c].dtype == object:
            try:
                df_in[c] = pd.to_numeric(df_in[c].str.replace(",", ""), errors="ignore")
            except Exception:
                pass

    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_49_power_cap_out_emis"
    generate_fig4_49(df_in, str(out_dir))
