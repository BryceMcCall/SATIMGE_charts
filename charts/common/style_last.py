# charts/common/style_last.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional
import plotly.graph_objects as go

SizeMode = Literal["full", "half"]
DPI = 300  # "effective" DPI target for raster export (png)

@dataclass(frozen=True)
class WordA4ModerateSpec:
    # A4 in inches
    page_w_in: float = 8.27
    page_h_in: float = 11.69

    # Word "Moderate" margins in inches
    margin_l_in: float = 1.25
    margin_r_in: float = 0.75
    margin_t_in: float = 1.00
    margin_b_in: float = 1.00

    # standard aspect ratio
    aspect_w: float = 2.0
    aspect_h: float = 1.0

    # gap between two charts when placed side-by-side
    gutter_in: float = 0.20

    @property
    def content_w_in(self) -> float:
        return self.page_w_in - (self.margin_l_in + self.margin_r_in)

    def canvas_px(self, mode: SizeMode, dpi: int = DPI) -> tuple[int, int]:
        if mode == "full":
            w_in = self.content_w_in
        elif mode == "half":
            w_in = (self.content_w_in - self.gutter_in) / 2.0
        else:
            raise ValueError(f"Unknown mode: {mode}")

        h_in = w_in * (self.aspect_h / self.aspect_w)
        return int(round(w_in * dpi)), int(round(h_in * dpi))


def apply_final_export_style(
    fig: go.Figure,
    *,
    size_mode: SizeMode = "full",
    dpi: int = DPI,
    title: Optional[str] = None,
) -> tuple[go.Figure, int, int]:
    """
    Final pass applied right before export:
    - Enforce 2:1 canvas sized for Word A4 Moderate margins (full-width or half-width)
    - Standardise font sizes in *absolute px terms* (so they don't drift per-chart)
    - Keep legends readable and inside safe margins
    Returns (fig, width_px, height_px)
    """
    spec = WordA4ModerateSpec()
    width_px, height_px = spec.canvas_px(size_mode, dpi=dpi)

    # Font sizes tuned for this canvas; adjust once here, globally.
    # (These are "final truth" sizes; your earlier layout helper can still do general styling.)
    base_font = 32
    title_font = 32
    tick_font = 16
    legend_font = 32

    if title is not None:
        fig.update_layout(title=title)

    fig.update_layout(
        width=width_px,
        height=height_px,
        font=dict(size=base_font),
        title=dict(font=dict(size=title_font), x=0.5, xanchor="center"),
        # tighter margins because the canvas is already "Word-fit"
        margin=dict(l=110, r=40, t=55, b=65),

    )

    fig.update_xaxes(tickfont=dict(size=tick_font), title_font=dict(size=base_font))
    fig.update_yaxes(tickfont=dict(size=tick_font), title_font=dict(size=base_font))

    return fig, width_px, height_px
