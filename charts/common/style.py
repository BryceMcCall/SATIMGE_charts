# charts/common/style.py

import yaml
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────────────────────
# Load project metadata from config.yaml
ROOT = Path(__file__).resolve().parents[2]
_CFG_PATH = ROOT / "config.yaml"
if _CFG_PATH.exists():
    with open(_CFG_PATH) as f:
        _CFG = yaml.safe_load(f)
    _PROJ = _CFG.get("project", {})
else:
    _PROJ = {}

PROJECT_NAME = _PROJ.get("name", "")
_logo_cfg    = _PROJ.get("logo_path")
if _logo_cfg:
    lp = Path(_logo_cfg)
    LOGO_PATH = lp if lp.is_absolute() else (ROOT / lp)
else:
    LOGO_PATH = None

def apply_common_layout(fig: go.Figure) -> go.Figure:
    """
    Apply standard styling, plus a footer band with:
      • italic, dark‐blue caption at y=-0.06 (larger font)
      • logo below it at y=-0.13
      • explicit grid lines
      • larger axis title fonts
    """
    # Base layout + footer shape
    fig.update_layout(
        template="simple_white",
        font=dict(family="Arial", size=14),
        margin=dict(l=80, r=80, t=80, b=160),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        shapes=[
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, x1=1,
                y0=-0.16, y1=0,
                fillcolor="white",
                line=dict(color="lightgrey"),
                layer="below",
            )
        ]
    )

    # X-axis: grid + horizontal ticks + larger title
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgrey",
        tickmode="linear",
        tickangle=90,
        automargin=True,
        title_font=dict(family="Arial", size=20)
    )
    # Y-axis: grid + larger title
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgrey",
        title_font=dict(family="Arial", size=20)
    )

    # Build footer caption text: project name + Mon YYYY
    caption_items = []
    if PROJECT_NAME:
        caption_items.append(PROJECT_NAME)
    caption_items.append(datetime.now().strftime("%b %Y"))
    caption = " | ".join(caption_items)

    # Footer caption (italic, dark blue), larger font
    fig.add_annotation(
        text=f"<i>{caption}</i>",
        xref="paper", yref="paper",
        x=1.0, y=-0.06,
        xanchor="right", yanchor="middle",
        showarrow=False,
        font=dict(family="Arial", size=16, color="darkblue")
    )

    # Footer logo (below caption)
    if LOGO_PATH and LOGO_PATH.exists():
        fig.add_layout_image(
            dict(
                source=LOGO_PATH.as_posix(),
                xref="paper", yref="paper",
                x=1.0, y=-0.13,
                xanchor="right", yanchor="middle",
                sizex=0.10, sizey=0.10,
                layer="above"
            )
        )

    return fig
