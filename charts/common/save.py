# charts/common/save.py

from pathlib import Path

import plotly.graph_objects as go

from charts.common.style_last import apply_final_export_style


def save_figures(fig: go.Figure, output_dir: str, name: str) -> None:
    """
    Save the figure as a standardised report-ready PNG.

    Standardisation happens in charts/common/style_last.py, applied as the final step
    so generator modules don't need per-figure tweaks.
    """
    # Global switch: "full" (margin-to-margin) or "half" (two-up side-by-side)
    SIZE_MODE = "full"   # "full" or "half"
    DPI = 300            # used to compute the canvas in pixels
    PNG_SCALE = 1.0      # keep 1.0 if size is already set via dpi->px in style_last

    # Apply final export styling (2:1 aspect, Word A4 Moderate fit, standard fonts)
    fig, width, height = apply_final_export_style(
        fig,
        size_mode=SIZE_MODE,
        dpi=DPI,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / f"{name}_report.png"
    print(f"💾 saving standardised PNG to {png_path.name}")
    fig.write_image(
        str(png_path),
        format="png",
        width=width,
        height=height,
        scale=PNG_SCALE,
    )

    import time

    t0 = time.time()
    print(f"💾 saving standardised PNG to {png_path.name} (w={width}, h={height})")
    fig.write_image(str(png_path), format="png", width=width, height=height, scale=PNG_SCALE)
    print(f"✅ PNG written in {time.time() - t0:.1f}s")

