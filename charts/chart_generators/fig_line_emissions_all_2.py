# charts/chart_generators/fig_line_emissions_all.py
from __future__ import annotations

import sys
from pathlib import Path
import re
import pandas as pd
import plotly.graph_objects as go
import yaml

# ── safe import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures


# ── Colours by scenario family
SCENARIO_COLORS = {
    "WEM": "#F9C74F",           # golden yellow
    "CPP-IRP": "#F3722C",       # vivid orange
    "CPP-IRPLight": "#F8961E",  # amber
    "CPP-SAREM": "#25A18E",     # blue-green
    "CPPS": "#004E64",          # deep blue
    "Low Carbon": "#7AE582",    # soft green
    "High Carbon": "#5fa8d3",   # slate blue
}

# Exact scenarios that should receive endpoint diamonds (one per family)
DOT_SCENARIOS = {
    "Low Carbon": "NDC_LCARB-RG",
    "High Carbon": "NDC_HCARB-RG",
    "WEM": "NDC_BASE-RG",
    "CPP-IRP": "NDC_CPP1-RG",
    "CPP-IRPLight": "NDC_CPP2-RG",
    "CPP-SAREM": "NDC_CPP3-RG",
    "CPPS": "NDC_CPP4-RG",
}

# Scenarios to exclude entirely (CPPS variants)
EXCLUDE_SCENARIOS = {"CPP4S", "CPP4GE", "CPP4EKH"}


def infer_family(name: str) -> str:
    """Map concrete Scenario names to high-level legend families."""
    n = str(name).upper()

    if "WEM" in n:
        return "WEM"
    if "SAREM" in n:
        return "CPP-SAREM"
    if "IRPLIGHT" in n:
        return "CPP-IRPLight"
    if "IRPFULL" in n or re.search(r"\bIRP\b", n):
        return "CPP-IRP"
    if "LCARB" in n or "LOWCARB" in n or re.search(r"\bLOW[-_ ]?CARB\b", n):
        return "Low Carbon"
    if "HCARB" in n or "HIGHCARB" in n or re.search(r"\bHIGH[-_ ]?CARB\b", n):
        return "High Carbon"

    # Default bucket for all CPP*/BASE*
    if "CPP" in n or "BASE" in n:
        return "CPPS"

    return "CPPS"


def _load_df(csv_hint: str | Path | None = None) -> pd.DataFrame:
    """Load Scenario/Year/MtCO2-eq from CSV and prepare for plotting."""
    candidates: list[Path] = []
    if csv_hint:
        candidates.append(Path(csv_hint))
    candidates += [
        PROJECT_ROOT / "data" / "raw" / "emissions_line_all_scenarios.csv",
        PROJECT_ROOT / "data" / "processed" / "emissions_line_all_scenarios.csv",
    ]

    for p in candidates:
        if p.exists():
            df = pd.read_csv(p)
            break
    else:
        raise FileNotFoundError("Could not find emissions_line_all_scenarios.csv")

    df = df.rename(columns={"MtCO2-eq": "MtCO2eq"})
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce")

    df = df[df["Year"].between(2024, 2035)].dropna(subset=["Scenario", "Year", "MtCO2eq"]).copy()
    df["ScenarioFamily"] = df["Scenario"].astype(str).map(infer_family)

    return df


def _compute_right_label_positions(dot_rows: list[dict], min_gap: float = 7.0) -> list[dict]:
    """
    Given dot rows with 'y', compute non-overlapping label y positions (top-down),
    storing as 'y_label'. Returns rows sorted by y desc.
    """
    rows = sorted(dot_rows, key=lambda d: d["y"], reverse=True)
    last_y = None
    for d in rows:
        y = float(d["y"])
        if last_y is not None and (last_y - y) < min_gap:
            y = last_y - min_gap
        d["y_label"] = y
        last_y = y
    return rows


def generate_fig_line_emissions_all(
    df_in: pd.DataFrame | None,
    output_dir: str,
    csv_hint: str | Path | None = None,
) -> None:
    """
    All scenario trajectories, coloured by ScenarioFamily.
    Includes endpoint DIAMOND markers ONLY for DOT_SCENARIOS.
    Excludes CPPS variants CPP4S/CPP4GE/CPP4EKH.
    Legend order = order the diamonds appear on the plot (top to bottom at 2035).
    Adds minor y-axis ticks and fixes y-axis range to 200–450.
    """
    print("▶ Generating: line emissions (all scenarios) — coloured by family")

    df = df_in.copy() if df_in is not None else _load_df(csv_hint)

    # Exclude CPPS variants entirely (lines + dots)
    df = df[~df["Scenario"].astype(str).str.upper().isin(EXCLUDE_SCENARIOS)].copy()
    df = df.sort_values(["Scenario", "Year"])

    fig = go.Figure()

    # 1) scenario trajectories, coloured by family
    for scen, sub in df.groupby("Scenario", sort=False):
        fam = str(sub["ScenarioFamily"].iloc[0])
        fig.add_trace(
            go.Scatter(
                x=sub["Year"],
                y=sub["MtCO2eq"],
                mode="lines",
                line=dict(color=SCENARIO_COLORS.get(fam, "#919090"), width=1.4),
                hovertemplate=f"{scen}<br>{fam}<br>%{{x}}: %{{y:.1f}} Mt<extra></extra>",
                showlegend=False,
            )
        )

    # 2) endpoint diamonds for specific scenarios + capture dot values
    dot_rows: list[dict] = []

    for fam, scen_name in DOT_SCENARIOS.items():
        sub = df[df["Scenario"].astype(str) == scen_name].sort_values("Year")
        sub = sub.dropna(subset=["Year", "MtCO2eq"])

        if sub.empty:
            print(f"⚠️ Dot scenario not found/empty: {scen_name} ({fam})")
            continue

        end_row = sub.iloc[-1]
        end_year = int(end_row["Year"])
        end_val = float(end_row["MtCO2eq"])

        dot_rows.append({"fam": fam, "scenario": scen_name, "x": end_year, "y": end_val})

        fig.add_trace(
            go.Scatter(
                x=[end_year],
                y=[end_val],
                mode="markers",
                marker=dict(
                    symbol="diamond",
                    size=18,
                    color=SCENARIO_COLORS.get(fam, "#666"),
                    line=dict(color="white", width=1.2),
                ),
                showlegend=False,
                hovertemplate=f"{scen_name}<br>{fam}<br>%{{x}}: %{{y:.1f}} Mt<extra></extra>",
            )
        )

    # Print dot values for checking
    if dot_rows:
        print("\n◆ Endpoint diamonds (fixed scenarios):")
        dots_df = pd.DataFrame(
            [{"ScenarioFamily": d["fam"], "Scenario": d["scenario"], "Year": d["x"], "MtCO2eq": d["y"]} for d in dot_rows]
        ).sort_values("MtCO2eq", ascending=False)
        print(dots_df.to_string(index=False))
        print()

    # 3) Right-hand labels (aligned column) + determine legend order from diamond positions
    ordered_families: list[str] = []
    if dot_rows:
        rows_for_labels = _compute_right_label_positions(dot_rows, min_gap=7.0)

        # Legend order: top-to-bottom by diamond y (not nudged label y)
        ordered_families = [d["fam"] for d in sorted(dot_rows, key=lambda d: d["y"], reverse=True)]

        x_label = 2035.25
        for d in rows_for_labels:
            fig.add_annotation(
                x=x_label,
                y=d["y_label"],
                xref="x",
                yref="y",
                text=f"{d['y']:.0f}",
                showarrow=False,
                font=dict(size=22, color=SCENARIO_COLORS.get(d["fam"], "#333")),
                xanchor="left",
                align="left",
            )

        # extend x-range to make room for labels
        fig.update_xaxes(range=[2024, 2035.6])
    else:
        # fallback: use DOT_SCENARIOS order if no diamonds found
        ordered_families = list(DOT_SCENARIOS.keys())

    # 4) legend: coloured squares (dummy marker traces), ordered by diamond appearance
    for fam in ordered_families:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=fam,
                marker=dict(
                    symbol="square",
                    size=30,  # bigger legend squares
                    color=SCENARIO_COLORS.get(fam, "#666"),
                    line=dict(color="white", width=0.8),
                ),
                showlegend=True,
                hoverinfo="skip",
            )
        )

    # ── Layout & styling
    apply_common_layout(fig, image_type="report")

    fig.update_layout(
        title_text="",
        legend_title_text="",
        legend=dict(
            traceorder="normal",
            orientation="v",
            x=1.02, xanchor="left",
            y=0.80, yanchor="middle",
            itemsizing="constant",
        ),
        margin=dict(l=92, r=200, t=8, b=48),  # extra right margin for RHS labels
    )

    YEARS = list(range(2024, 2036))
    fig.update_xaxes(
        title="",
        tickangle=-45,
        tickfont=dict(size=18),
        ticklabeloverflow="allow",
        tickmode="array",
        tickvals=YEARS,
        ticktext=[str(y) for y in YEARS],
    )

    # y-axis range + minor ticks
    fig.update_yaxes(
        title="CO₂eq Emissions (Mt)",
        tickformat=".0f",
        title_font=dict(size=22),
        range=[200, 450],
    )

    # Minor y-axis ticks + minor gridlines (supported in newer Plotly)
    fig.update_yaxes(
        minor=dict(
            ticks="outside",
            ticklen=4,
            tickwidth=1,
            showgrid=True,
            griddash="dot",
            gridwidth=0.6,
            dtick=10,
        )
    )

    save_figures(fig, output_dir, name="fig_line_emissions_all")

    # Also write a data snapshot (unless dev_mode true)
    cfg_path = PROJECT_ROOT / "config.yaml"
    dev_mode = False
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            dev_mode = bool(yaml.safe_load(f).get("dev_mode", False))
    if not dev_mode:
        df.to_csv(Path(output_dir) / "data.csv", index=False)

    print("✓ Saved fig_line_emissions_all")


if __name__ == "__main__":
    outdir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig_line_emissions_all"
    outdir.mkdir(parents=True, exist_ok=True)
    generate_fig_line_emissions_all(None, str(outdir))
