# charts/chart_generators/fig4_41_transport_emissions_by_subsector.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

# ───────────────── config ─────────────────
cfg = project_root / "config.yaml"
dev_mode = False
if cfg.exists():
    dev_mode = yaml.safe_load(open(cfg, "r", encoding="utf-8")).get("dev_mode", False)

def _short_scenario_label(code: str) -> str:
    s = str(code)
    if "FreiM" in s:  return "WEM + Freight Modal Shift"
    if "PassM" in s:  return "WEM + Passenger Modal Shift"
    return "WEM"

_SUBSECTOR_PRETTY = {
    "Aviation-Domestic": "Domestic Aviation",
    "Aviation-Intl":     "Intl. Aviation",
    "FreightRail":       "Freight - Rail",
    "FreightRoad":       "Freight - Road",
    "PassPriv":          "Private Transport",
    "PassPub":           "Public Transport",
    "TraOther":          "Other",
    "OtherFreight":      "Other Freight",
}

# order for stacking & legend
_ORDERED_SUBSECTORS = [
    "Domestic Aviation",
    "Intl. Aviation",
    "Freight - Rail",
    "Freight - Road",
    "Private Transport",
    "Public Transport",
    "Other",
    "Other Freight",
]

# same palette as before, different pairing for better balance
COLOR_MAP = {
    "Domestic Aviation": "#F6AE2D",  # deep blue-slate
    "Intl. Aviation":    "#9dbfe8",  # pale sky
    "Freight - Rail":    "#d8b6d9",  # mid-sky
    "Freight - Road":    "#a678b4",  # orange (dominant category)
    "Private Transport": "#b1d79b",  # steel blue (large but cooler)
    "Public Transport":  "#a1d6c7",  # cool slate
    "Other":             "#ea9daa",  # amber highlight for small cap
    "Other Freight":     "#86BBD8",  # sky
}

def generate_fig(df: pd.DataFrame, outdir: str) -> None:
    print("▶ Generating transport emissions by subsector (stacked)")
    df = df.rename(columns={"Subsector (group) 2": "Subsector"})
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce").fillna(0)
    df["ScenarioLabel"] = df["Scenario"].apply(_short_scenario_label)
    df["SubsectorPretty"] = df["Subsector"].map(_SUBSECTOR_PRETTY).fillna(df["Subsector"])
    df = df[df["Year"].between(2024, 2035)]

    fig = px.bar(
        df,
        x="ScenarioLabel", y="MtCO2-eq",
        color="SubsectorPretty",
        facet_col="Year",
        barmode="relative",
        category_orders={
            "ScenarioLabel": ["WEM", "WEM + Freight Modal Shift", "WEM + Passenger Modal Shift"],
            "SubsectorPretty": _ORDERED_SUBSECTORS,
        },
        color_discrete_map=COLOR_MAP,
        labels={"MtCO2-eq": "Mt CO₂-eq", "ScenarioLabel": ""},
    )

    fig = apply_common_layout(fig)

    # legend at bottom (centered, horizontal)
    fig.update_layout(
        legend_title_text="",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.6,
            xanchor="center", x=0.5,
            font=dict(size=18),
            title_font=dict(size=16),
            bgcolor="rgba(255,255,255,0.85)",
            itemwidth=40,
        ),
        margin=dict(l=60, r=40, t=40, b=210),  # extra bottom space for legend
        bargap=0.35,
        font=dict(size=18),
    )

    # tidy facet headers and axes
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=16)))
    fig.update_xaxes(tickangle=-90, tickfont=dict(size=18))
    fig.update_yaxes(matches="y", dtick=10, title=dict(text="CO₂-eq Emissions (Mt)", font=dict(size=20)))
    # Keep the y-axis title only on the leftmost facet (2024)
    for i, yaxis in enumerate(fig.select_yaxes()):
        if i > 0:  # yaxis = first facet; yaxis2, yaxis3, ... = the rest
            yaxis.update(title_text="")

    fig.update_traces(marker_line_width=0.5, marker_line_color="white")

    Path(outdir).mkdir(parents=True, exist_ok=True)
    if not dev_mode:
        save_figures(fig, outdir, name="fig4_41_transport_emissions_by_subsector")
        df.to_csv(Path(outdir) / "fig4_41_transport_emissions_by_subsector_data.csv", index=False)

if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "4_41_FreiM_PassM_WEM_emissions_subsect.csv"
    outdir = project_root / "outputs" / "charts_and_data" / "fig4_41_transport_emissions_by_subsector"
    generate_fig(pd.read_csv(data_path), str(outdir))
