# charts/chart_generators/fig4_49_power_sentout_emis.py
from __future__ import annotations
"""
Fig 4.49 — 2 rows (scatter + bars)

Row 1: National CO₂-eq emissions (Mt) — markers by curtailed status
Row 2: Electricity sent out to SA grid (TWh) — one bar per scenario

Notes:
- Uses RAW scenario keys for x (prevents double-counting when pretty labels collide).
- Pretty labels are used only as ticktext.
- Family names: '_CPP4S' → 'CPPS Variant', '_CPP4' → 'CPPS' (longest key matched first).
- Styling: legend font 18, y-title fonts 20, CO₂ subscript + line break, no side padding on x.
"""

import sys, re
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── project root for shared utils ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures


# ── Family display names (longest keys first) ─────────────────────────────────
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


# ── main generator ────────────────────────────────────────────────────────────
def generate_fig4_49_sentout(df: pd.DataFrame, output_dir: str) -> None:
    scen_col = _norm_col(df, "Scenario")
    curt_col = _norm_col(df, "NDC scenarios sasol curtailed")
    emis_col = _norm_col(df, "MtCO2-eq ALL")

    # tolerate common variants for “elec sent out SA grid”
    sentout_col = None
    for cand in [
        "elec sent out SA grid",
        "elec sent out sa grid",
        "Electricity sent out (SA grid)",
        "Electricity sent out SA grid",
        "Elec sent out SA grid",
        "TWh sent out",
        "Sent out (TWh)",
    ]:
        try:
            sentout_col = _norm_col(df, cand); break
        except KeyError:
            continue
    if sentout_col is None:
        raise KeyError("Could not find 'elec sent out SA grid' column in the dataset.")

    # Emissions table for row 1 and scenario ordering (use min per scenario across curtailed flag)
    emis_df = (
        df[[scen_col, emis_col, curt_col]]
        .dropna(subset=[scen_col, emis_col])
        .groupby([scen_col, curt_col], as_index=False)[emis_col].min()
    )
    scen_order_raw = emis_df.sort_values(emis_col)[scen_col].tolist()

    # Sent-out per scenario (sum if there are multiple tech rows per scenario)
    sent_df = (df[[scen_col, sentout_col]]
               .dropna(subset=[scen_col, sentout_col])
               .groupby(scen_col, as_index=False)[sentout_col].sum())

    # ── figure (2 rows) ────────────────────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.07, row_heights=[0.45, 0.55],
        subplot_titles=("Scenarios below 300Mt", "")
    )

    # Row 1: emissions scatter (raw x)
    curt_color = {"Curtailed": "#E07B39", "Not curtailed": "#33A352"}
    for status, sub in emis_df.groupby(curt_col, dropna=False):
        label = str(status) if pd.notna(status) else "Not specified"
        fig.add_scatter(
            x=sub[scen_col], y=sub[emis_col],
            mode="markers", name=label,
            marker=dict(color=curt_color.get(label, "#7f7f7f"), size=10, line=dict(width=0)),
            legendgroup="curt", showlegend=True,
            row=1, col=1
        )

    # Row 2: bars for electricity sent out (raw x)
    # choose a clear neutral colour for the single metric
    bar_color = "#4C78A8"
    # align the bar x with overall scenario order
    sent_df = sent_df.set_index(scen_col).reindex(scen_order_raw).reset_index()
    fig.add_bar(
        x=sent_df[scen_col], y=sent_df[sentout_col],
        name="Electricity sent out", marker=dict(color=bar_color),
        showlegend=False, row=2, col=1
    )

    # ── layout & axes ──────────────────────────────────────────────────────────
    apply_common_layout(fig)
    n = len(scen_order_raw)
    fig.update_layout(
        barmode="group",
        height=1000, width=1400,
        margin=dict(l=90, r=240, t=60, b=160),
        legend=dict(
            orientation="v", x=1.02, xanchor="left", y=1.0, yanchor="top",
            bgcolor="rgba(255,255,255,0)", font=dict(size=18)
        ),
    )

    # Y-titles (CO₂ subscript + line break on row 1)
    fig.update_yaxes(title_text="National CO<sub>2</sub>-eq<br>Emissions (Mt)",
                     title_font=dict(size=20), row=1, col=1)
    fig.update_yaxes(title_text="Electricity sent out (TWh)",
                     title_font=dict(size=20), row=2, col=1)

    # (Optional) Set major/minor tick intervals:
    # fig.update_yaxes(tickmode="linear", tick0=0, dtick=50,
    #                  minor=dict(tick0=0, dtick=10, showgrid=True, gridcolor="rgba(0,0,0,0.08)"),
    #                  row=1, col=1)
    # fig.update_yaxes(tickmode="linear", tick0=0, dtick=10,
    #                  minor=dict(tick0=0, dtick=2, showgrid=True, gridcolor="rgba(0,0,0,0.08)"),
    #                  row=2, col=1)

    # X ticks: pretty labels as ticktext; remove side padding to avoid whitespace
    ticks_raw    = scen_order_raw
    ticks_pretty = [pretty_label(s) for s in scen_order_raw]
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(
        tickmode="array", tickvals=ticks_raw, ticktext=ticks_pretty, tickangle=-90,
        categoryorder="array", categoryarray=ticks_raw,
        range=[-0.5, max(n - 0.5, 0)], row=2, col=1
    )
    fig.update_xaxes(range=[-0.5, max(n - 0.5, 0)], row=1, col=1)

    # ── save + sidecar CSVs ────────────────────────────────────────────────────
    out_dir = Path(output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    base = "fig4_49_power_sentout_emis"
    save_figures(fig, str(out_dir), name=base)

    # exports
    emis_df.rename(columns={scen_col:"Scenario", emis_col:"MtCO2eq", curt_col:"Curtailed"}) \
           .to_csv(out_dir / f"{base}_emissions.csv", index=False)
    sent_df.rename(columns={scen_col:"Scenario", sentout_col:"SentOut_TWh"}) \
           .to_csv(out_dir / f"{base}_sentout.csv", index=False)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = PROJECT_ROOT / "data" / "processed" / "4_49_power_capacity_output_emissions_curtailment_scatter_stacked_bar.csv"
    df_in = pd.read_csv(data_path)

    # light numeric coercion for csvs with commas
    for c in df_in.columns:
        if df_in[c].dtype == object:
            try:
                df_in[c] = pd.to_numeric(df_in[c].str.replace(",", ""), errors="ignore")
            except Exception:
                pass

    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_49_power_sentout_emis"
    generate_fig4_49_sentout(df_in, str(out_dir))
