# charts/common/style.py

import yaml
from pathlib import Path
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
_CFG_PATH = ROOT / "config.yaml"
if _CFG_PATH.exists():
    with open(_CFG_PATH) as f:
        _CFG = yaml.safe_load(f)
    _PROJ = _CFG.get("project", {})
else:
    _PROJ = {}

# ──────────────────────────────────────────────────────────────
def apply_common_layout(fig: go.Figure, scale: float = 1.0) -> go.Figure:
    """
    Apply standard styling and layout to the figure.
    - No project name, no logo, no footer caption
    - Legend directly below plot
    - Fonts scale with resolution
    """

    base_font = 14 * scale
    title_font = 20 * scale
    legend_font = 13 * scale
    tick_font = int(base_font * 1.2)

    fig.update_layout(
        template="simple_white",
        height=int(600 * scale),
        font=dict(family="Arial", size=base_font),
        margin=dict(l=80, r=80, t=80, b=int(120 * scale)),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.10,  # move closer to x-axis
            xanchor="center",
            x=0.5,
            font=dict(size=legend_font)
        ),
        shapes=[
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, x1=1,
                y0=-0.2, y1=0,
                fillcolor="white",
                line=dict(color="lightgrey"),
                layer="below",
            )
        ]
    )

    # X-axis
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgrey",
        tickangle=0,
        title_font=dict(family="Arial", size=title_font),
        tickfont=dict(size=tick_font),
        tickmode="linear",  # ensures consistent spacing
        dtick=5,            # adjust if needed (e.g. 5-year steps)
        # leave range control to generator unless issues arise
    )

    # Y-axis
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgrey",
        title_font=dict(family="Arial", size=title_font),
        tickfont=dict(size=base_font),
        rangemode="tozero",  # avoids overshooting upper limit
    )


    return fig
