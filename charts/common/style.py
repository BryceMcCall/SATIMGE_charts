
import yaml
from pathlib import Path
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
_CFG_PATH = ROOT / "config.yaml"
if _CFG_PATH.exists():
    with open(_CFG_PATH) as f:
        _CFG = yaml.safe_load(f)
    _PROJ = _CFG.get("project", {})
else:
    _PROJ = {}

def apply_common_layout(fig: go.Figure, image_type: str = "report") -> go.Figure:
    scale_map = {"dev": 1.0, "report": 2.0}
    scale = scale_map.get(image_type, 1.0)

    base_font   = 13 * scale
    title_font  = 18 * scale
    legend_font = 12 * scale
    tick_font   = int(base_font * 0.8)

    fig.update_layout(
        template="simple_white",
        height=int(600 * scale),
        font=dict(family="Times New Roman", size=base_font, color="black"),
        margin=dict(l=80, r=80, t=60, b=int(100 * scale)),
        title=dict(
            font=dict(family="Times New Roman", size=title_font),
            x=0.5, xanchor="center",
            pad=dict(b=80)
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=legend_font)
        ),
        shapes=[
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, x1=1,
                y0=-0.30, y1=0,
                fillcolor="white",
                line=dict(color="lightgrey"),
                layer="below",
            )
        ]
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=0.6,
        gridcolor="lightgrey",
        tickangle=0,
        ticks="outside",
        ticklen=5,
        tickfont=dict(size=tick_font, family="Times New Roman"),
        title_font=dict(size=title_font, family="Times New Roman"),
        tickmode="linear",
        dtick=5,
        showline=True,
        mirror=True,
        linecolor="lightgrey",
        linewidth=1.2,
        minor=dict(
            ticks="outside",
            showgrid=True,
            gridcolor="whitesmoke",
            ticklen=3,
            tick0=0,
            dtick=1
        )
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=0.6,
        gridcolor="lightgrey",
        ticks="outside",
        ticklen=5,
        tickfont=dict(size=tick_font, family="Times New Roman"),
        title_font=dict(size=title_font, family="Times New Roman"),
        rangemode="tozero",
        showline=True,
        mirror=True,
        linecolor="lightgrey",
        linewidth=1.2,
        minor=dict(
            ticks="outside",
            showgrid=True,
            gridcolor="whitesmoke",
            ticklen=3,
            tick0=0,
            dtick=25000
        )
    )

    return fig
