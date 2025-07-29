
from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio

def save_figures(fig: go.Figure, output_dir: str, name: str) -> None:
    """
    Save the figure as high-resolution PNG only (scale=2.0).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / f"{name}_report.png"
    print(f"💾 saving high-res PNG to {png_path.name}")
    fig.write_image(str(png_path), format="png", scale=2.0, width=1200, height=800)
