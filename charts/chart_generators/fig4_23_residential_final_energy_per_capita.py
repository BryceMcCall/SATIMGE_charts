# charts/chart_generators/fig4_23_residential_final_energy_per_capita.py

#
# Residential final energy per capita (PJ per million people)
# - Robust import bootstrap so you can run this file directly
# - Uses shared palette via charts.common.style.color_for
# charts/chart_generators/fig4_23_residential_final_energy_per_capita.py
#

from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------------------
# Make project imports work when running this file directly
# ---------------------------------------------------------------------
def _add_project_root_to_syspath():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "charts" / "common").is_dir():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return
_add_project_root_to_syspath()

from charts.common.style import apply_common_layout, color_for
from charts.common.save import save_figures

# Map display labels to canonical palette keys (shared across the project)
FUEL_TO_CANON = {
    "Electricity": "Electricity",
    "Paraffin":    "Kerosene/Jet",
    "Gas":         "Natural Gas",
    "Wood":        "Wood/Wood Waste",
    "Coal":        "Coal",
}
STACK_ORDER = ["Electricity", "Paraffin", "Gas", "Wood", "Coal"]  # bottom → top


def _load_data() -> pd.DataFrame:
    """Read CSV if available; else use inline fallback (updated numbers)."""
    candidates = [
        Path("data/processed/4_23_residential_energy_use_per_capita.csv"),
        Path("data/raw/4_23_residential_energy_use_per_capita.csv"),
        Path("/mnt/data/4_23_residential_energy_use_per_capita.csv"),
    ]
    for p in candidates:
        if p.exists():
            df = pd.read_csv(p)
            df.columns = [str(c).strip().title() for c in df.columns]
            if "Income" not in df.columns:
                df = df.rename(columns={df.columns[0]: "Income"})
            df = df[df["Income"].isin(["Low", "Middle", "High"])]
            df = df.set_index("Income").reindex(["Low", "Middle", "High"]).reset_index()
            return df[["Income", *STACK_ORDER]].copy()

    # Fallback (updated data provided)
    return pd.DataFrame({
        "Income":      ["Low Income", "Middle Income", "High Income"],
        "Electricity": [1.382092571, 2.475388670, 6.840282213],
        "Paraffin":    [0.217569996, 0.224525641, 0.009334124],
        "Gas":         [0.120505032, 0.345676364, 0.662756547],
        "Wood":        [2.143612712, 1.568836142, 0.091731238],
        "Coal":        [0.260245266, 0.441064903, 0.092156952],
    })


def generate_fig4_23_residential_final_energy_per_capita(_: pd.DataFrame, output_dir: str) -> None:
    # ---------------- Data ----------------
    df = _load_data()
    colors = {f: color_for("fuel", FUEL_TO_CANON[f]) for f in STACK_ORDER}

    # ---------------- Figure ----------------
    fig = go.Figure()
    for fuel in STACK_ORDER:
        fig.add_trace(
            go.Bar(
                name=fuel,
                x=df["Income"],
                y=df[fuel],
                marker=dict(
                    color=colors[fuel],
                    line=dict(color="rgba(0,0,0,0.18)", width=0.6),  # subtle segment borders
                ),
                hovertemplate=f"<b>{fuel}</b><br>%{{x}}: %{{y:.3f}} PJ/million<extra></extra>",
            )
        )

    # Totals above bars
    totals = df[STACK_ORDER].sum(axis=1)
    for x, y in zip(df["Income"], totals):
        fig.add_annotation(x=x, y=y, yshift=10, text=f"{y:.2f}", showarrow=False, font=dict(size=14))

    # Base layout (no title)
    fig.update_layout(
        barmode="stack",
        xaxis_title=None,
        yaxis_title="PJ/million people",
        legend_title_text="",
        margin=dict(l=70, r=140, t=20, b=60),
        bargap=0.45,
        bargroupgap=0.02,
        title=None,  # explicitly no title
    )

    # Apply shared theme
    apply_common_layout(fig, image_type="report")

    # Force legend to the right (override theme)
    fig.update_layout(
        legend=dict(
            orientation="v",
            x=1.02, y=1.0,       # right/top
            xanchor="left", yanchor="top",
            traceorder="normal",
        )
    )

    # Denser y-axis ticks
    ymax = float(totals.max() * 1.12)
    fig.update_yaxes(range=[0, ymax], dtick=1, minor=dict(showgrid=True, dtick=0.2))
    fig.update_xaxes(tickangle=0)

    # ---------------- Save ----------------
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "data.csv", index=False)
    save_figures(fig, str(out_dir), name="fig4_23_residential_final_energy_per_capita")


if __name__ == "__main__":
    generate_fig4_23_residential_final_energy_per_capita(
        pd.DataFrame(),
        "outputs/charts_and_data/fig4_23_residential_final_energy_per_capita",
    )
