# charts/common/style.py

import yaml
from pathlib import Path
from datetime import datetime
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

_logo_cfg = _PROJ.get("logo_path")
if _logo_cfg:
    lp = Path(_logo_cfg)
    LOGO_PATH = lp if lp.is_absolute() else (ROOT / lp)
else:
    LOGO_PATH = None

# ──────────────────────────────────────────────────────────────
def apply_common_layout(fig: go.Figure, scale: float = 1.0) -> go.Figure:
    """
    Apply standard styling and layout to the figure.
    - Footer includes date only (no project name)
    - Logo included below the caption
    - Fonts scale with resolution
    """

    base_font = 14 * scale
    title_font = 20 * scale
    caption_font = 16 * scale
    legend_font = 13 * scale
    tick_font = int(base_font * 1.2)

    fig.update_layout(
        template="simple_white",
        height=int(600 * scale),
        font=dict(family="Arial", size=base_font),
        margin=dict(l=80, r=80, t=80, b=int(200 * scale)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=legend_font)
        ),
        shapes=[
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, x1=1,
                y0=-0.4, y1=0,
                fillcolor="white",
                line=dict(color="lightgrey"),
                layer="below",
            )
        ]
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgrey",
        tickangle=0,
        title_font=dict(family="Arial", size=title_font),
        tickfont=dict(size=tick_font)
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgrey",
        title_font=dict(family="Arial", size=title_font),
        tickfont=dict(size=base_font)
    )

    # Footer: date only
    caption = datetime.now().strftime("%b %Y")

    fig.add_annotation(
        text=f"<i>{caption}</i>",
        xref="paper", yref="paper",
        x=1.0, y=-0.18,
        xanchor="right", yanchor="middle",
        showarrow=False,
        font=dict(family="Arial", size=caption_font, color="darkblue")
    )

    # Logo below caption
    if LOGO_PATH and LOGO_PATH.exists():
        fig.add_layout_image(
            dict(
                source=LOGO_PATH.as_posix(),
                xref="paper", yref="paper",
                x=1.0,
                y=-0.32 if scale >= 2.0 else -0.29,
                xanchor="right",
                yanchor="middle",
                sizex=0.10, sizey=0.10,
                layer="above"
            )
        )

    return fig
