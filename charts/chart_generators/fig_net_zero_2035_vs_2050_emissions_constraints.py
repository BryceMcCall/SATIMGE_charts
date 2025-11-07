# charts/chart_generators/fig4_5_netzero_2035_2050_constraints.py
from __future__ import annotations
import sys, re
from pathlib import Path
import pandas as pd
import plotly.express as px

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _fallback_apply_common_layout(fig):
    fig.update_layout(template="plotly_white", paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(showline=True, linewidth=1, linecolor="rgba(0,0,0,0.2)", gridcolor="rgba(0,0,0,0.08)")
    fig.update_yaxes(showline=True, linewidth=1, linecolor="rgba(0,0,0,0.2)", gridcolor="rgba(0,0,0,0.08)")
    return fig

try:
    from charts.common.style import apply_common_layout as _apply_common_layout
except Exception:
    _apply_common_layout = _fallback_apply_common_layout

def _fallback_save(fig, output_dir: str, name: str):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    try:
        import plotly.io as pio
        pio.write_image(fig, out / f"{name}.png", scale=3, width=1800, height=800)
    except Exception:
        pass
    fig.write_html(out / f"{name}.html", include_plotlyjs="cdn")

try:
    from charts.common.save import save_figures as _save_figures
except Exception:
    def _save_figures(fig, output_dir: str, name: str):
        _fallback_save(fig, output_dir, name)

FAMILY_NAMES = {
    "CPP4S": "CPPS Variant",
    "CPP4": "CPPS",
    "BASE": "WEM",
    "CPP1": "CPP-IRP",
    "CPP2": "CPP-IRPLight",
    "CPP3": "CPP-SAREM",
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

BASE_FONT   = 18
Y_TITLE_FONT = 22
MAJOR_DTICK = 50
MINOR_DTICK = 10
FACET_YEARS = [2035, 2050]

# one color per constraint level (keep consistent with earlier examples)
BUDGET_COLORS = {
    "7.75": "#5A8FB8",
    "8":    "#F6AE2D",
    "8.5":    "#BFD7EA",
    "9":    "#F26419",
}

def generate_fig4_5_netzero_2035_2050_constraints(df: pd.DataFrame, output_dir: str) -> None:
    print("▶ Generating Fig 4.5 — Net-zero constraints (2035 vs 2050)")

    df = df.rename(columns={
        "NDC GHG constraint level": "Budget",
        "MtCO2-eq": "MtCO2eq",
    })

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2eq"] = pd.to_numeric(df["MtCO2eq"], errors="coerce")
    df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce")
    df = df[df["Year"].isin(FACET_YEARS)].dropna(subset=["Scenario", "MtCO2eq", "Budget"]).copy()

    # pretty labels for scenarios (x-axis text)
    df["ScenarioLabel"] = df["Scenario"].astype(str).apply(pretty_label)

    # budget label used for colors/legend (single color per level)
    df["BudgetLabel"] = df["Budget"].map(lambda x: f"{x:g}")

    df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce")
    df["BudgetLabel"] = df["Budget"].map(lambda x: f"{x:g}")

    # === order scenarios in DESCENDING budget (then ScenarioLabel) ===
    df["ScenarioLabel"] = df["Scenario"].astype(str).apply(pretty_label)
    x_order = (
        df.sort_values(["Budget", "ScenarioLabel"], ascending=[False, True])  # DESC by budget
        .loc[:, "ScenarioLabel"]
        .drop_duplicates()
        .tolist()
    )
    df["ScenarioLabel"] = pd.Categorical(df["ScenarioLabel"], categories=x_order, ordered=True)

    fig = px.bar(
        df,
        x="ScenarioLabel",
        y="MtCO2eq",
        color="BudgetLabel",
        facet_col="Year",
        facet_col_wrap=2,
        category_orders={
            "Year": [2035, 2050],
            "BudgetLabel": ["7.75", "8", "8.5", "9"],
            "ScenarioLabel": x_order,
        },
        color_discrete_map=BUDGET_COLORS,
        labels={"ScenarioLabel": "", "MtCO2eq": "CO₂-eq (Mt)", "BudgetLabel": "Constraint (Gt budget)", "Year": ""},
        title="",
    )

    fig = _apply_common_layout(fig)

    fig.update_layout(
        font=dict(size=BASE_FONT),
        legend=dict(
            title=dict(text="Cumulative CO₂-eq<br>budget (Gt)", font=dict(size=20)),
            font=dict(size=20),
            orientation="v",
            x=1.02, xanchor="left",
            y=1.0,  yanchor="top",
            bgcolor="rgba(255,255,255,0.9)",
            traceorder="normal",
        ),
        margin=dict(l=90, r=260, t=50, b=120),
        bargap=0.25,
    )

    fig.update_yaxes(
        matches="y",
        dtick=MAJOR_DTICK,
        minor=dict(showgrid=True, dtick=MINOR_DTICK),
        tickfont=dict(size=BASE_FONT),
    )
    fig.update_xaxes(title_text="", tickangle=-90, tickfont=dict(size=BASE_FONT))

    # Y title only on first facet
    fig.layout.yaxis.title.text = "CO₂-eq Emissions (Mt)"
    fig.layout.yaxis.title.font.size = Y_TITLE_FONT
    for ax_name in [k for k in fig.layout if k.startswith("yaxis") and k != "yaxis"]:
        getattr(fig.layout, ax_name).title.text = ""

    # Clean facet titles to plain years (no '=')
    for a in fig.layout.annotations:
        if a.text:
            a.text = a.text.replace("Year=", "").replace("=", "").strip()
        a.font.size = BASE_FONT

    fig.update_traces(marker_line_color="white", marker_line_width=0.5)

    outdir = Path(output_dir); outdir.mkdir(parents=True, exist_ok=True)
    _save_figures(fig, output_dir, name="fig4_5_netzero_2035_2050_constraints_by_budget")
    df.to_csv(outdir / "fig4_5_netzero_2035_2050_constraints_by_budget_data.csv", index=False)


if __name__ == "__main__":
    candidates = [
        Path("/mnt/data/net_zero_2035_vs_2050_emissions_constraints.csv"),
        PROJECT_ROOT / "data" / "processed" / "net_zero_2035_vs_2050_emissions_constraints.csv",
    ]
    csv_path = next((p for p in candidates if p.exists()), None)
    out_dir  = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_5_netzero_2035_2050_constraints"
    out_dir.mkdir(parents=True, exist_ok=True)

    if csv_path:
        generate_fig4_5_netzero_2035_2050_constraints(pd.read_csv(csv_path), str(out_dir))
    else:
        print(f"⚠️ Data not found. Tried: {', '.join(str(p) for p in candidates)}")
