# charts/chart_generators/fig4_5_netzero_cumulative_constraints.py

from __future__ import annotations
import sys, re
from pathlib import Path
import pandas as pd
import plotly.express as px

# ── safe import path (same as other fig4_5 modules)
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
        pio.write_image(fig, out / f"{name}.png", scale=3, width=1500, height=900)
    except Exception:
        pass
    fig.write_html(out / f"{name}.html", include_plotlyjs="cdn")

try:
    from charts.common.save import save_figures as _save_figures
except Exception:
    def _save_figures(fig, output_dir: str, name: str):
        _fallback_save(fig, output_dir, name)

# ── naming conventions (unchanged)
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

# ── style constants
BASE_FONT   = 18
Y_TITLE_FONT = 22
MAJOR_DTICK = 1000
MINOR_DTICK = 250

# ── keep the same budget colors you used in the attached generator
BUDGET_COLORS = {
    "7.75": "#5A8FB8",
    "8":    "#F6AE2D",
    "8.5":  "#BFD7EA",
    "9":    "#F26419",
}

def generate_fig4_5_netzero_cumulative_constraints(df: pd.DataFrame, output_dir: str) -> None:
    """
    Recreate cumulative emissions chart:
      - preserves scenario order as in CSV
      - names via pretty_label (same as other figs)
      - colors by budget using existing palette
    """
    print("▶ Generating Fig 4.5 — Net-zero cumulative constraints")

    # harmonize columns from the provided CSV
    df = df.rename(columns={
        "NDC GHG constraint level": "Budget",
        "NDC GHG": "Budget",  # handle alt header
        "MtCO2-eq cumulative": "MtCO2eqCum",
        "MtCO2-eq": "MtCO2eqCum",  # just in case
    })

    df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce")
    df["MtCO2eqCum"] = (
        df["MtCO2eqCum"]
        .astype(str)
        .str.replace("\u00A0", "", regex=False)   # strip non-breaking spaces from thousands
        .str.replace(",", "", regex=False)
    ).astype(float)

    # scenario labels + keep original order of appearance
    df["ScenarioLabel"] = df["Scenario"].astype(str).apply(pretty_label)
    x_order = list(dict.fromkeys(df["ScenarioLabel"].tolist()))
    df["ScenarioLabel"] = pd.Categorical(df["ScenarioLabel"], categories=x_order, ordered=True)

    df["BudgetLabel"] = df["Budget"].map(lambda x: f"{x:g}")

    fig = px.bar(
        df,
        x="ScenarioLabel",
        y="MtCO2eqCum",
        color="BudgetLabel",
        category_orders={"ScenarioLabel": x_order, "BudgetLabel": ["7.75", "8", "8.5", "9"]},
        color_discrete_map=BUDGET_COLORS,
        labels={"ScenarioLabel": "", "MtCO2eqCum": "MtCO₂-eq", "BudgetLabel": "NDC GHG constraint level"},
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
        margin=dict(l=90, r=560, t=50, b=120),
        bargap=0.25,
    )

    # y-axis in thousands with minor grid
    fig.update_yaxes(
        ticksuffix="",
        dtick=MAJOR_DTICK,
        minor=dict(showgrid=True, dtick=MINOR_DTICK),
        rangemode="tozero",
        title_text="CO₂-eq Emissions (Mt)",
        title_font=dict(size=Y_TITLE_FONT),
    )
    fig.update_xaxes(title_text="", tickangle=-90, tickfont=dict(size=BASE_FONT))

    # crisp edges
    fig.update_traces(marker_line_color="white", marker_line_width=0.6)

    outdir = Path(output_dir); outdir.mkdir(parents=True, exist_ok=True)
    _save_figures(fig, output_dir, name="fig4_5_netzero_cumulative_constraints")
    df.to_csv(outdir / "fig4_5_netzero_cumulative_constraints_data.csv", index=False)


if __name__ == "__main__":
    # candidate data paths
    candidates = [
        Path("/mnt/data/net_zero_cumulative_emissions_constraints.csv"),
        PROJECT_ROOT / "data" / "processed" / "net_zero_cumulative_emissions_constraints.csv",
        PROJECT_ROOT / "data" / "raw" / "net_zero_cumulative_emissions_constraints.csv",
    ]
    csv_path = next((p for p in candidates if p.exists()), None)

    # output dir
    out_dir = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_5_netzero_cumulative_constraints"
    out_dir.mkdir(parents=True, exist_ok=True)

    # robust CSV reader (handles Excel NBSP / cp1252)
    import io
    def read_csv_robust(path: Path) -> pd.DataFrame:
        for enc in ("utf-8", "utf-8-sig", "cp1252", "ISO-8859-1"):
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
        with open(path, "rb") as f:
            txt = f.read().decode("cp1252", errors="replace")
        return pd.read_csv(io.StringIO(txt))

    if csv_path is not None:
        df_in = read_csv_robust(csv_path)
        generate_fig4_5_netzero_cumulative_constraints(df_in, str(out_dir))
    else:
        raise FileNotFoundError(f"Data not found. Tried: {', '.join(str(p) for p in candidates)}")
