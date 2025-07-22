# charts/common/style.py

import yaml
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────────────────────
# 1) Load project metadata from config.yaml
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
    Apply standard styling, plus a lower‐right caption (italic, dark blue)
    and the project logo in the bottom corner.
    """
    # Base styling
    fig.update_layout(
        template="simple_white",
        font=dict(family="Arial", size=14),
        margin=dict(l=80, r=80, t=80, b=80),
        xaxis=dict(tickmode="linear"),
        yaxis=dict(title="CO₂eq (kt)"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
    )

    # Build the caption text: project name + month & year
    caption_items = []
    if PROJECT_NAME:
        caption_items.append(PROJECT_NAME)
    caption_items.append(datetime.now().strftime("%b %Y"))
    caption = " | ".join(caption_items)

    # Add caption annotation in lower right
    fig.add_annotation(
        text=f"<i>{caption}</i>",
        xref="paper", yref="paper",
        x=1.0, y=0.0,             # bottom right
        xanchor="right", yanchor="bottom",
        showarrow=False,
        font=dict(family="Arial", size=12, color="darkblue")
    )

    # Add logo in lower right, just to the right of the caption
    if LOGO_PATH and LOGO_PATH.exists():
        fig.add_layout_image(
            dict(
                source=LOGO_PATH.as_posix(),
                xref="paper", yref="paper",
                x=1.0, y=0.0,       # align with caption
                xanchor="right", yanchor="bottom",
                sizex=0.1, sizey=0.1,
                layer="above"
            )
        )

    return fig
