# charts/chart_generators/fig4_5_emissions_stacked_growth_rates.py
# Emissions by GDP growth rate (stacked by category), faceted by year
from __future__ import annotations
import sys
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
    from charts.common.style import apply_common_layout as _apply_common_layout  # noqa
except Exception:
    _apply_common_layout = _fallback_apply_common_layout

def _fallback_save(fig, output_dir: str, name: str):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    try:
        import plotly.io as pio
        pio.write_image(fig, out / f"{name}.png", scale=3, width=1800, height=1000)
    except Exception:
        pass
    fig.write_html(out / f"{name}.html", include_plotlyjs="cdn")

try:
    from charts.common.save import save_figures as _save_figures  # noqa
except Exception:
    def _save_figures(fig, output_dir: str, name: str):
        _fallback_save(fig, output_dir, name)

# --- Category order & colours (Power first, Land last) ---
CAT_ORDER = [
    "A.Electricity",
    "B.Liquid fuels supply",
    "C.Industry (combustion and process)",
    "D.Transport",
    "E.Other energy",
    "F.Agriculture (non-energy)",
    "H.Waste",
    "G.Land",
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


# fallback tableau 10 colors, reordered to match CAT_ORDER
# COLOR_MAP = {
#     "A.Electricity":                    "#4E79A7",  # deep blue
#     "B.Liquid fuels supply":            "#76B7B2",  # teal
#     "C.Industry (combustion and process)": "#59A14F",  # green
#     "D.Transport":                      "#EDC948",  # warm gold
#     "E.Other energy":                   "#F28E2B",  # copper/orange
#     "F.Agriculture (non-energy)":       "#E15759",  # red-coral
#     "G.Land":                           "#B07AA1",  # violet
#     "H.Waste":                          "#9C755F",  # brown
# }

X_ORDER = ["Low growth", "Ref growth", "High growth"]
YEAR_ORDER = [2024, 2030, 2035]

BASE_FONT   = 18  # general font size (ticks, legend, facet labels)
Y_TITLE_FONT = 22 # y-axis title font size
MAJOR_DTICK = 50  # more y ticks
MINOR_DTICK = 10

def generate_fig4_5_emissions_stacked_growth_rates(df: pd.DataFrame, output_dir: str) -> None:
    print("▶ Generating Fig 4.5 — emissions by GDP growth rate (stacked, facets 2024/2030/2035)")

    df = df.rename(columns={
        "NDC GHG emisssion cats short": "Category",
        "Scenario: GDP growth rate": "Growth",
    })
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce").fillna(0.0)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)
    df = df[df["Year"].isin(YEAR_ORDER)].copy()

    df["Category"] = pd.Categorical(df["Category"], categories=CAT_ORDER, ordered=True)
    df["Growth"] = pd.Categorical(df["Growth"], categories=X_ORDER, ordered=True)
    df["Year"] = pd.Categorical(df["Year"], categories=YEAR_ORDER, ordered=True)

    # Global y-range across all facets (handles negative Land)
    tmp = df.copy()
    tmp["pos"] = tmp["MtCO2-eq"].clip(lower=0)
    tmp["neg"] = tmp["MtCO2-eq"].clip(upper=0)
    bounds = tmp.groupby(["Year", "Growth"])[["pos", "neg"]].sum()
    ymin = float(bounds["neg"].min())
    ymax = float(bounds["pos"].max())
    pad = 0.02 * (ymax - ymin)
    y_range = [ymin - pad, ymax + pad]

    fig = px.bar(
        df,
        x="Growth",
        y="MtCO2-eq",
        color="Category",
        facet_col="Year",
        facet_col_wrap=3,
        category_orders={"Category": CAT_ORDER, "Growth": X_ORDER, "Year": YEAR_ORDER},
        color_discrete_map=COLOR_MAP,
        barmode="relative",
        labels={"Growth": "", "MtCO2-eq": "CO₂-eq Emissions (Mt)", "Category": "IPCC category L1", "Year": ""},
        title="",
    )

    fig = _apply_common_layout(fig)

    # Legend on RHS
    fig.update_layout(
        font=dict(size=BASE_FONT),
        legend=dict(
            title_text="",
            font=dict(size=BASE_FONT),
            orientation="v",
            x=1.02, xanchor="left",
            y=1.0,  yanchor="top",
            bgcolor="rgba(255,255,255,0.9)",
            traceorder="normal",
        ),
        margin=dict(l=90, r=260, t=50, b=90),
        bargap=0.25,
    )

    # Axes: shared scale, more ticks/minor ticks, rotate x labels -90
    fig.update_yaxes(
        range=y_range,
        matches="y",
        dtick=MAJOR_DTICK,
        minor=dict(showgrid=True, dtick=MINOR_DTICK),
        tickfont=dict(size=BASE_FONT),
    )
    fig.update_xaxes(title_text="", tickangle=-45, tickfont=dict(size=BASE_FONT))

    # Y-axis title only on first facet; smaller font
    fig.layout.yaxis.title.text = "CO₂-eq Emissions (Mt)"
    fig.layout.yaxis.title.font.size = Y_TITLE_FONT
    for ax_name in [k for k in fig.layout if k.startswith("yaxis") and k != "yaxis"]:
        getattr(fig.layout, ax_name).title.text = ""

    # Clean facet labels to plain years (no '=') & enlarge facet label font
    for a in fig.layout.annotations:
        if a.text:
            a.text = a.text.replace("Year=", "").replace("=", "").strip()
        a.font.size = BASE_FONT

    # subtle white separators between stacks
    fig.update_traces(marker_line_color="white", marker_line_width=0.5)

    outdir = Path(output_dir); outdir.mkdir(parents=True, exist_ok=True)
    _save_figures(fig, output_dir, name="fig4_5_emissions_stacked_growth_rates_rhs_sharedY")
    df.to_csv(outdir / "fig4_5_emissions_stacked_growth_rates_data.csv", index=False)

if __name__ == "__main__":
    csv_path = PROJECT_ROOT / "data" / "processed" / "4_5_emissions_bar_growth_rates.csv"
    out_dir  = PROJECT_ROOT / "outputs" / "charts_and_data" / "fig4_5_emissions_stacked_growth_rates"
    out_dir.mkdir(parents=True, exist_ok=True)
    if csv_path.exists():
        generate_fig4_5_emissions_stacked_growth_rates(pd.read_csv(csv_path), str(out_dir))
    else:
        print(f"⚠️ Data not found: {csv_path}")

