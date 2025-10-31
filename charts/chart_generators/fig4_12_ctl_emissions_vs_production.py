# charts/chart_generators/fig4_12_ctl_emissions_vs_production.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import yaml

# ── safe import path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from charts.common.style import apply_common_layout, apply_square_legend
from charts.common.save import save_figures


def _load_ctl_data(df: pd.DataFrame | None, csv_hint: str | Path | None) -> pd.DataFrame:
    if csv_hint:
        p = Path(csv_hint)
        if p.exists():
            return pd.read_csv(p)
    for p in [
        project_root / "data" / "raw" / "CTL_emis_prod.csv",
        project_root / "data" / "processed" / "CTL_emis_prod.csv",
        Path.cwd() / "CTL_emis_prod.csv",
    ]:
        if p.exists():
            return pd.read_csv(p)
    if df is not None and {"Year", "Value", "TechDescription", "Commodity"} <= set(df.columns):
        return df.loc[:, ["Year", "Value", "TechDescription", "Commodity"]].copy()
    raise FileNotFoundError("CTL_emis_prod.csv not found and no suitable dataframe provided.")


def generate_fig4_12_ctl_emissions_vs_production(
    df: pd.DataFrame | None,
    output_dir: str,
    *,
    csv_path: str | Path | None = None,
    image_name: str = "fig4_12_ctl_emissions_vs_production",
    # knobs
    y_title_size: int = 18,
    y1_tick_size: int = 12,
    y2_tick_size: int = 12,
    legend_font_size: int = 12,
    legend_square_size: int = 14,
    legend_x: float = 1.12,
    margin_r: int = 170,
) -> None:

    data = _load_ctl_data(df, csv_path)
    data["Year"] = data["Year"].astype(int)

    emis = data.query("Commodity == 'CO2eq'").copy()
    prod = data.query(
        "Commodity == 'Liquid Fuels' and `TechDescription` == 'Liquid Fuels Production'"
    ).copy()

    label_map = {
        "Coal boiler process": "Coal boiler emissions",
        "Gasification process": "Gasification emissions",
        "Gas reforming": "Gas reforming emissions",
        "FT process": "Fischer Tropsch emissions",
        "Gas turbine process": "Gas Turbine emissions",
        "Liquid Fuels Production": "Liquid Fuels Production (Secunda)",
    }
    emis["SeriesLabel"] = emis["TechDescription"].map(label_map).fillna(emis["TechDescription"])
    prod_label = label_map["Liquid Fuels Production"]

    emis_order = [
        "Coal boiler emissions",
        "Gasification emissions",
        "Gas reforming emissions",
        "Fischer Tropsch emissions",
        "Gas Turbine emissions",
    ]
    legend_order = emis_order + [prod_label]

    color_map = {
        "Coal boiler emissions":   "#1B9E77",
        "Gasification emissions":  "#2CA02C",
        "Gas reforming emissions": "#9C89C9",
        "Fischer Tropsch emissions":"#FF7F0E",
        "Gas Turbine emissions":   "#A34A3A",
        prod_label:                "#000000",
    }

    fig = go.Figure()
    apply_common_layout(fig, image_type="report")

    # emissions (left)
    for name in emis_order:
        sdf = emis.loc[emis["SeriesLabel"] == name].sort_values("Year")
        if sdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sdf["Year"], y=sdf["Value"],
            mode="lines",
            name=name,
            line=dict(color=color_map[name], width=3),
            hovertemplate=f"{name}<br>Year=%{{x}}<br>CO2-eq=%{{y:.3f}} Mt<extra></extra>",
        ))

    # production (right, dotted)
    sp = prod.sort_values("Year")
    fig.add_trace(go.Scatter(
        x=sp["Year"], y=sp["Value"],
        mode="lines",
        name=prod_label,
        line=dict(color=color_map[prod_label], width=3, dash="dot"),
        hovertemplate=f"{prod_label}<br>Year=%{{x}}<br>Production=%{{y:.1f}} PJ<extra></extra>",
        yaxis="y2",
    ))

    # axes + legend
    x_years = list(range(2024, 2036))
    fig.update_layout(
        margin=dict(l=80, r=margin_r, t=30, b=80),
        legend=dict(
            x=legend_x, y=0.85,
            xanchor="left", yanchor="middle",
            orientation="v",
            font=dict(size=legend_font_size),
            bgcolor="rgba(255,255,255,0)",
        ),
        xaxis=dict(
            title="",
            tickmode="array",
            tickvals=x_years,
            ticktext=[str(y) for y in x_years],
            dtick=1,
            range=[2024, 2035],
            tickangle=-45,
        ),
        yaxis=dict(
            rangemode="tozero",
            showgrid=True,
            zeroline=False,
            dtick=2,
            minor=dict(dtick=1),
            tickfont=dict(size=y1_tick_size),
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False,
            rangemode="tozero",
            dtick=20,
            tickfont=dict(size=y2_tick_size),
            linecolor="#999",
        ),
        title_text="",
    )
    fig.update_layout(
        yaxis_title_text="CO₂-eq Emissions (Mt)",
        yaxis_title_font=dict(size=y_title_size),
        yaxis2_title_text="Secunda Production (PJ)",
        yaxis2_title_font=dict(size=y_title_size),
    )

    # square legend with chosen order and square size
    apply_square_legend(fig, order=legend_order, size=legend_square_size)

    save_figures(fig, output_dir, image_name)


if __name__ == "__main__":
    cfg_path = project_root / "config.yaml"
    dev_mode = False
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            _CFG = yaml.safe_load(f)
        dev_mode = _CFG.get("dev_mode", False)

    out = project_root / "outputs" / "charts_and_data" / "fig4_12_ctl_emissions_vs_production"
    out.mkdir(parents=True, exist_ok=True)

    generate_fig4_12_ctl_emissions_vs_production(
        df=None,
        output_dir=str(out),
        csv_path=None,
        y_title_size=20,
        y1_tick_size=18,
        y2_tick_size=18,
        legend_font_size=20,
        legend_square_size=16,
        legend_x=1.12,
        margin_r=170,
    )
