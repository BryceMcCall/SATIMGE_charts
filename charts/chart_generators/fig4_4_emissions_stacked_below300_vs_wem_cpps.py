# charts/chart_generators/fig4_4_emissions_stacked_below300_vs_wem_cpps.py
# Figure 4.4 — Emissions in 2035: <300 MtCO2eq scenarios vs WEM/CPPs
# Expected columns:
#   - "NDC GHG emisssion cats short"   (A.Electricity … H.Waste)
#   - "Scenario"                       (e.g. NDC_CPP4-0925-RG)
#   - "MtCO2-eq"                       (numeric)

from __future__ import annotations

import re
import sys
from pathlib import Path
from collections import defaultdict
import pandas as pd
import plotly.express as px

# ───────────────────────── project root & optional helpers ─────────────────────────
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # …/SATIMGE_charts

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Try shared style/save utilities; otherwise fall back to light stubs.
def _fallback_apply_common_layout(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor="rgba(0,0,0,0.2)", gridcolor="rgba(0,0,0,0.08)")
    fig.update_yaxes(showline=True, linewidth=1, linecolor="rgba(0,0,0,0.2)", gridcolor="rgba(0,0,0,0.08)")
    return fig

try:
    from charts.common.style import apply_common_layout as _apply_common_layout  # type: ignore
except Exception:
    _apply_common_layout = _fallback_apply_common_layout

def _fallback_save(fig, output_dir: str, name: str):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    try:
        import plotly.io as pio
        pio.write_image(fig, out / f"{name}.png", scale=3, width=1700, height=950)
    except Exception:
        pass
    fig.write_html(out / f"{name}.html", include_plotlyjs="cdn")

try:
    from charts.common.save import save_figures as _save_figures  # type: ignore
except Exception:
    def _save_figures(fig, output_dir: str, name: str):
        _fallback_save(fig, output_dir, name)

# ───────────────────────── constants ─────────────────────────
CAT_ORDER = [
    "A.Electricity",
    "B.Liquid fuels supply",
    "C.Industry (combustion and process)",
    "D.Transport",
    "E.Other energy",
    "F.Agriculture (non-energy)",
    "G.Land",
    "H.Waste",
]


COLOR_MAP = {
    "A.Electricity": "#2F4858",  # deep blue-slate
    "B.Liquid fuels supply": "#33658A",  # steel blue
    "C.Industry (combustion and process)": "#F6AE2D",  # amber
    "D.Transport": "#F26419",  # orange
    "E.Other energy": "#86BBD8",  # sky
    "F.Agriculture (non-energy)": "#5A8FB8",  # mid-sky (derived)
    "H.Waste": "#8FA3B8",  # cool slate (derived)
    "G.Land": "#BFD7EA",  # pale sky (top-friendly)
}

BASE_FONT = 17  # legend, axis titles, tick labels

# ── Scenario family → display name
FAMILY_NAMES = {
    "BASE":  "WEM",
    "CPP1":  "CPP-IRP",
    "CPP2":  "CPP-IRPLight",
    "CPP3":  "CPP-SAREM",
    "CPP4":  "CPPS",
    "LCARB": "Low carbon",
    "HCARB": "High carbon",
}

# Optional manual one-offs (raw or auto label → desired)
MANUAL_SCENARIO_LABELS: dict[str, str] = {
    # "NDC_BASE-085-NZ-RG": "WEM · Net Zero (8.5 Gt budget)",
}


# ───────────────────────── helpers ─────────────────────────
def _parse_budget_gt(s: str) -> str | None:
    """
    Extract a budget token and return 'X.xx Gt budget'.
      - 3–4 digits (e.g., 775, 0875, 0925) -> divide by 100 (7.75, 8.75, 9.25)
      - 2 digits (e.g., 08) -> integer Gt (8 Gt)
    """
    m = re.search(r"-(\d{2,4})(?!\d)", s)  # last numeric token like -0875, -08
    if not m:
        return None
    token = m.group(1)
    if len(token) >= 3:
        gt = float(token) / 100.0
        text = f"{gt:.2f}".rstrip("0").rstrip(".")
        return f"{text} Gt budget"
    return f"{int(token)} Gt budget"

def _family_from_run(s: str) -> str:
    s = s.upper()
    m_cpp = re.search(r"CPP\s*([1-4])|CPP([1-4])", s)
    if m_cpp:
        num = m_cpp.group(1) or m_cpp.group(2)
        return f"CPP{num}"
    if "WEM" in s or "BASE" in s:
        return "WEM"
    if "LCARB" in s or "LOWCARB" in s:
        return "Low-carbon"
    return "Scenario"

import re

def pretty_label(raw: str) -> str:
    s = str(raw)

    # Family detection (order matters a bit less; we look for _FAMILY)
    fam = None
    for k in FAMILY_NAMES.keys():
        if f"_{k}" in s:
            fam = k
            break
    fam_name = FAMILY_NAMES.get(fam, s)

    # Budget token detection (longest-first to avoid partial matches)
    budget_patterns = [
        ("-105-", 10.5),
        ("-095-", 9.5),
        ("-0925-", 9.25),
        ("-0875-", 8.75),
        ("-085-", 8.5),
        ("-0825-", 8.25),
        ("-0775-", 7.75),
        ("-075-", 7.5),
        ("-10-", 10.0),
        ("-09-", 9.0),
        ("-08-", 8.0),
    ]
    budget = None
    for pat, val in budget_patterns:
        if pat in s:
            budget = val
            break
    # Special case like CPP4-8-NZ-RG (single '8')
    if budget is None and re.search(r"-8-(?:NZ-)?RG", s):
        budget = 8.0

    # Net Zero?
    is_nz = "-NZ-" in s.upper()

    # Compose label
    parts = [fam_name]
    if is_nz:
        parts.append("Net Zero")
    label = " · ".join(parts)
    if budget is not None:
        label += f" ({budget:g} Gt budget)"

    # Allow manual overrides by raw or by the auto label
    if raw in MANUAL_SCENARIO_LABELS:
        return MANUAL_SCENARIO_LABELS[raw]
    if label in MANUAL_SCENARIO_LABELS:
        return MANUAL_SCENARIO_LABELS[label]
    return label


def _scenario_key_for_filter(s: str) -> str:
    s = s.upper()
    if "BASE" in s or "WEM" in s:
        return "WEM"
    if "CPP" in s:
        return "CPP"
    return "OTHER"

def _make_unique_labels(labels: list[str]) -> list[str]:
    """
    Ensure labels are unique (required by pandas Categorical).
    For duplicates, append ' · v2', ' · v3', ... in encounter order.
    """
    counts = {}
    unique = []
    for lab in labels:
        n = counts.get(lab, 0) + 1
        counts[lab] = n
        if n == 1:
            unique.append(lab)
        else:
            unique.append(f"{lab} · v{n}")
    return unique

# ───────────────────────── main generator ─────────────────────────
def generate_fig4_4_emissions_stacked_below300_vs_wem_cpps(df: pd.DataFrame, output_dir: str) -> None:
    """
    Stacked bars of 2035 emissions by category for:
       • all scenarios with total < 300 MtCO₂-eq, plus
       • WEM/BASE and CPP families for comparison.
    Sorted by descending total emissions.
    X-axis labels use pretty_label() and are guaranteed unique.
    Also prints & saves a duplicate-label mapping report.
    """
    print("▶ Generating Fig 4.4 — emissions stacked: <300 vs WEM/CPPs")
    df = df.rename(columns={"NDC GHG emisssion cats short": "Category"})
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce").fillna(0.0)
    df["Scenario"] = df["Scenario"].astype(str)
    df["Category"] = pd.Categorical(df["Category"], categories=CAT_ORDER, ordered=True)

    # Totals for filter/sort
    totals = df.groupby("Scenario", as_index=False)["MtCO2-eq"].sum().rename(columns={"MtCO2-eq": "Total"})
    totals["Family"] = totals["Scenario"].apply(_scenario_key_for_filter)

    # Keep: <300 OR (Family in {WEM, CPP})
    keep = totals[(totals["Total"] < 300) | (totals["Family"].isin(["WEM", "CPP"]))].copy()
    keep = keep.sort_values("Total", ascending=False)
    ordered_scenarios = keep["Scenario"].tolist()

    plot_df = df[df["Scenario"].isin(ordered_scenarios)].copy()
    plot_df["Scenario"] = pd.Categorical(plot_df["Scenario"], categories=ordered_scenarios, ordered=True)

    # Build base labels (may contain duplicates)
    base_labels = [pretty_label(s) for s in ordered_scenarios]

    # Duplicate report (console + CSV)
    rev = defaultdict(list)
    for raw, lab in zip(ordered_scenarios, base_labels):
        rev[lab].append(raw)
    dups = {lab: raws for lab, raws in rev.items() if len(raws) > 1}
    if dups:
        print("⚠️ Duplicate pretty labels detected (will add v2/v3 suffixes):")
        for lab, raws in dups.items():
            print(f"  '{lab}':")
            for idx, r in enumerate(raws, start=1):
                print(f"     - v{idx} → {r}")
        pd.DataFrame(
            [(lab, i+1, r) for lab, L in dups.items() for i, r in enumerate(L)],
            columns=["pretty_label", "v_index", "raw_scenario"],
        ).to_csv(Path(output_dir) / "fig4_4_duplicate_label_mapping.csv", index=False)

    # Now uniquify labels for plotting
    unique_labels = _make_unique_labels(base_labels)

    # Map each scenario to its unique label (1:1 with order)
    scen_to_label = dict(zip(ordered_scenarios, unique_labels))
    plot_df["Scenario_label"] = plot_df["Scenario"].astype(str).map(scen_to_label)

    # Preserve order for the categorical x axis
    label_order = unique_labels
    plot_df["Scenario_label"] = pd.Categorical(plot_df["Scenario_label"], categories=label_order, ordered=True)

    fig = px.bar(
        plot_df,
        x="Scenario_label",
        y="MtCO2-eq",
        color="Category",
        category_orders={"Category": CAT_ORDER, "Scenario_label": label_order},
        color_discrete_map=COLOR_MAP,
        barmode="relative",
        labels={
            "Scenario_label": "",
            "MtCO2-eq": "Emissions in 2035 (MtCO₂-eq)",
            "Category": "",
        },
        title="",
    )

    # Common styling
    fig = _apply_common_layout(fig)
    fig.update_layout(
        font=dict(size=BASE_FONT),  # global
        # RIGHT-HAND legend (vertical)
        legend=dict(
            title_text="",
            font=dict(size=BASE_FONT),
            orientation="v",
            x=1.02, xanchor="left",
            y=1.0,  yanchor="top",
            bgcolor="rgba(255,255,255,0.85)",
        ),
        margin=dict(l=80, r=260, t=60, b=160),  # restore right margin for RHS legend
        bargap=0.15,
    )
    fig.update_yaxes(
        title_text="Emissions in 2035 (MtCO₂-eq)",
        title_font=dict(size=BASE_FONT),
        tickfont=dict(size=BASE_FONT),
        dtick=40,
        minor=dict(dtick=10, showgrid=True),
    )
    fig.update_xaxes(
        title_text="",
        tickangle=-75,
        tickfont=dict(size=BASE_FONT),
        automargin=True,
    )

    # Subtle borders for stacks
    fig.update_traces(marker_line_color="white", marker_line_width=0.5)

    # Save
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    _save_figures(fig, output_dir, name="fig4_4_emissions_stacked_below300_vs_wem_cpps")
    plot_df.to_csv(outdir / "fig4_4_emissions_stacked_below300_vs_wem_cpps_data.csv", index=False)

# ───────────────────────── CLI ─────────────────────────
if __name__ == "__main__":
    default_csv = PROJECT_ROOT / "data" / "processed" / "4.4_bar_emissions_under_300Mt_WEM_CPP4.csv"
    default_out = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_4_emissions_stacked_below300_vs_wem_cpps"
    default_out.mkdir(parents=True, exist_ok=True)

    if default_csv.exists():
        _df = pd.read_csv(default_csv)
        generate_fig4_4_emissions_stacked_below300_vs_wem_cpps(_df, str(default_out))
    else:
        print(f"⚠️ Data not found at: {default_csv}")


