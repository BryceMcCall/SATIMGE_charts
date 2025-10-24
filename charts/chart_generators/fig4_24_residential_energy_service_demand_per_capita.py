# charts/chart_generators/fig4_24_residential_energy_service_demand_per_capita.py
#
# Horizontal stacked bars by service (rows: L / M / H)
# - Row headers centered via axis domains (stable placement)
# - Consistent x-axis across rows
# - Bottom-only x-axis title
# - Right-hand legend (deduplicated), adjustable spacing
# charts/chart_generators/fig4_24_residential_energy_service_demand_per_capita.py
from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---- bootstrap project root so charts.common.* works when run directly
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

FUEL_TO_CANON = {
    "Electricity": "Electricity",
    "Paraffin":    "Kerosene",
    "Gas":         "Natural Gas",
    "Biowood":        "Biowood",
    "Coal":        "Coal",
}
FUELS = ["Electricity", "Paraffin", "Gas", "Biowood", "Coal"]
INCOME_ORDER  = ["L", "M", "H"]
INCOME_LABELS = {"L": "Low income", "M": "Middle income", "H": "High income"}
SERVICE_ORDER = ["Lighting", "Cooking", "Heating", "Water heating", "Refrigeration", "Other"]

def _load_data() -> pd.DataFrame:
    candidates = [
        Path("data/processed/4_24_residential_energy_service_demand_per_capita.csv"),
        Path("data/raw/4_24_residential_energy_service_demand_per_capita.csv"),
        Path("/mnt/data/4_24_residential_energy_service_demand_per_capita.csv"),
    ]
    for p in candidates:
        if p.exists():
            df = pd.read_csv(p)
            df.columns = [str(c).strip().title() for c in df.columns]
            if "Income" not in df.columns:
                df = df.rename(columns={df.columns[0]: "Income", df.columns[1]: "Service"})
            df = df[["Income", "Service", *[c.title() for c in FUELS]]].copy()
            df["Income"]  = pd.Categorical(df["Income"], INCOME_ORDER, ordered=True)
            df["Service"] = pd.Categorical(df["Service"], SERVICE_ORDER, ordered=True)
            return df.sort_values(["Income", "Service"])

    # Fallback (from your message)
    tbl = [
        ("L","Lighting",0.184785595,0.014187913,0,0,0),
        ("L","Cooking",0.344498128,0.058121502,0.040923837,1.302338638,0.085186927),
        ("L","Heating",0.035869452,0.012623186,0.003191375,0.395459553,0.139028076),
        ("L","Water heating",0.07662962,0.110158343,0.022683267,0.364599943,0.021535939),
        ("L","Refrigeration",0.412865781,0,0,0,0),
        ("L","Other",0.278837514,0,0,0,0),
        ("M","Lighting",0.251849417,0.041028086,0,0,0),
        ("M","Cooking",0.462760545,0.011832472,0.033113407,0.972928962,0.095118839),
        ("M","Heating",0.110936354,0.042869009,0.041693022,0.295662158,0.29744257),
        ("M","Water heating",0.547699229,0.120425063,0.131721681,0.350990437,0.055835525),
        ("M","Refrigeration",0.579962714,0,0,0,0),
        ("M","Other",0.556878597,0,0,0,0),
        ("H","Lighting",0.422995811,0,0,0,0),
        ("H","Cooking",0.675127721,0.006936821,0.179827277,0.074457245,0),
        ("H","Heating",0.195439189,0.001909951,0.165384944,0.01837716,0.092771023),
        ("H","Water heating",3.319391091,0.054804705,0.602887663,0.089394494,0.01778861),
        ("H","Refrigeration",0.938610714,0,0,0,0),
        ("H","Other",1.337229944,0,0,0,0),
    ]
    df = pd.DataFrame(tbl, columns=["Income","Service",*FUELS])
    df["Income"]  = pd.Categorical(df["Income"], INCOME_ORDER, ordered=True)
    df["Service"] = pd.Categorical(df["Service"], SERVICE_ORDER, ordered=True)
    return df.sort_values(["Income","Service"])

def generate_fig4_24_residential_energy_service_demand_per_capita(_: pd.DataFrame, output_dir: str) -> None:
    df = _load_data()
    colors = {f: color_for("fuel", FUEL_TO_CANON[f]) for f in FUELS}

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
        subplot_titles=("", "", "")
    )

    # traces per row; only top row in legend (dedup)
    for r, inc in enumerate(INCOME_ORDER, start=1):
        d = df[df["Income"] == inc].set_index("Service").reindex(SERVICE_ORDER).reset_index()
        for fuel in FUELS:
            fig.add_trace(
                go.Bar(
                    name=fuel,
                    legendgroup=fuel,
                    showlegend=(r == 1),
                    orientation="h",
                    x=d[fuel], y=d["Service"],
                    marker=dict(color=colors[fuel], line=dict(color="rgba(0,0,0,0.18)", width=0.6)),
                    hovertemplate=f"<b>{fuel}</b><br>{INCOME_LABELS[inc]} — %{{y}}: %{{x:.3f}} PJ/million<extra></extra>",
                ),
                row=r, col=1
            )
        fig.update_yaxes(categoryorder="array", categoryarray=SERVICE_ORDER, row=r, col=1)

    # base layout
    fig.update_layout(
        barmode="stack",
        legend_title_text="",
        bargap=0.28,
        bargroupgap=0.0,
        margin=dict(l=150, r=170, t=30, b=80),
    )

    # theme, then legend on RHS (slightly larger)
    apply_common_layout(fig, image_type="report")
    fig.update_layout(
        legend=dict(
            orientation="v",
            x=1.02, y=1.0, xanchor="left", yanchor="top",
            font=dict(size=20),
            itemwidth=70,
            tracegroupgap=8
        )
    )

    # consistent x-axes + smaller tick font + bottom-only label
    row_totals = df[FUELS].sum(axis=1)
    xmax = float(row_totals.max() * 1.08)
    for i in (1, 2, 3):
        fig.update_xaxes(
            range=[0, xmax],
            dtick=0.5,
            tickfont=dict(size=18),   # smaller tick font
            row=i, col=1
        )
    fig.update_xaxes(minor=dict(showgrid=True, dtick=0.05), row=3, col=1)
    fig.update_xaxes(title_text="PJ/million people", row=3, col=1, title_font=dict(size=22))  # requested label
    fig.update_xaxes(title_text=None, row=1, col=1)
    fig.update_xaxes(title_text=None, row=2, col=1)

    # centered row labels via axis domains: larger + slightly higher
    def y_suffix(i: int) -> str:
        return "" if i == 1 else str(i)
    for i, inc in enumerate(INCOME_ORDER, start=1):
        fig.add_annotation(
            text=INCOME_LABELS[inc],
            xref="x domain", x=0.5,
            yref=f"y{y_suffix(i)} domain", y=1.15,   # ↑ lifted slightly
            showarrow=False, name=f"rowhdr-{inc}",
            font=dict(size=20, color="rgba(0,0,0,0.85)"),  # ↑ larger
            align="center"
        )

    # save
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "data.csv", index=False)
    save_figures(fig, str(out), name="fig4_24_residential_energy_service_demand_per_capita")

if __name__ == "__main__":
    generate_fig4_24_residential_energy_service_demand_per_capita(
        pd.DataFrame(),
        "outputs/charts_and_data/fig4_24_residential_energy_service_demand_per_capita"
    )

