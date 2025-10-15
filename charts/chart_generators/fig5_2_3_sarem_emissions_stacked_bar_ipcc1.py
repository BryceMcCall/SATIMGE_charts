# charts/chart_generators/fig5_2_3_sarem_emissions_stacked_bar_ipcc1.py
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import yaml
import shutil

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout
from charts.common.save import save_figures

config_path = project_root / "config.yaml"
if config_path.exists():
    with open(config_path) as f:
        _CFG = yaml.safe_load(f)
    dev_mode = _CFG.get("dev_mode", False)
else:
    dev_mode = False


def _short_scenario_label(code: str) -> str:
    s = str(code).replace("NDC_BASE-", "").replace("-RG", "")
    if "SAREM" in s:
        return "WEM + SAREM"
    return "WEM"


def generate_fig5_2_3_sarem_emissions_stacked_bar_ipcc1(df: pd.DataFrame, output_dir: str) -> None:
    print("generating figure 5.2.3: SAREM Emissions comparison (WEM vs WEM + SAREM)")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["MtCO2-eq"] = pd.to_numeric(df["MtCO2-eq"], errors="coerce").fillna(0)
    df = df[df["Year"].between(2025, 2035)]
    df = df[df["IPCC_Category_L1"].notna()]
    df = df[df["IPCC_Category_L1"] != "nan"]
    df["IPCC_Category_L1"] = df["IPCC_Category_L1"].astype(str)
    df["ScenarioLabel"] = df["Scenario"].apply(_short_scenario_label)

    color_map = {
        "1 Energy": "#1f77b4",
        "2 Industrial Processes and Product Use": "#ff7f0e",
        "3 Agriculture": "#2ca02c",
        "4 LULUCF": "#9467bd",
        "5 Waste": "#8c564b",
    }

    fig = px.bar(
        df,
        x="ScenarioLabel",
        y="MtCO2-eq",
        color="IPCC_Category_L1",
        facet_col="Year",
        facet_col_wrap=None,
        barmode="relative",
        category_orders={"ScenarioLabel": ["WEM", "WEM + SAREM"], "IPCC_Category_L1": list(color_map.keys())},
        color_discrete_map=color_map,
        labels={"MtCO2-eq": "MtCO₂-eq", "ScenarioLabel": ""},
    )

    fig = apply_common_layout(fig)

    fig.update_layout(
        title="",
        legend_title_text="IPCC category L1",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5,
            font=dict(size=20),
            title_font=dict(size=20),
            bgcolor="rgba(255,255,255,0.8)",
            itemsizing="constant",
            itemwidth=40,
            traceorder="normal",
        ),
        font=dict(size=20),
        margin=dict(l=50, r=50, t=40, b=160),
        yaxis=dict(
            dtick=50,
            title=dict(text="Emissions (MtCO₂-eq)", font=dict(size=20)),
            title_standoff=10,
            gridcolor="rgba(0,0,0,0.08)",
            zeroline=True,
            zerolinewidth=1.2,
            zerolinecolor="grey",
        ),
        bargap=0.45,
    )

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=18)))
    fig.update_xaxes(tickangle=-90, tickfont=dict(size=20))
    fig.update_yaxes(matches="y")
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")

    if not dev_mode:
        save_figures(fig, output_dir, name="fig5_2_3_sarem_emissions_stacked_bar_ipcc1")
        df.to_csv(Path(output_dir) / "fig5_2_3_sarem_emissions_stacked_bar_ipcc1_data.csv", index=False)


if __name__ == "__main__":
    data_path = project_root / "data" / "processed" / "5.2.1_SAREM_emissions_stacked_bar_ipcc1.csv"
    out = project_root / "outputs" / "charts_and_data" / "fig5_2_3_sarem_emissions_stacked_bar_ipcc1"
    out.mkdir(parents=True, exist_ok=True)
    generate_fig5_2_3_sarem_emissions_stacked_bar_ipcc1(pd.read_csv(data_path), str(out))
