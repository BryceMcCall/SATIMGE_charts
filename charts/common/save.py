
# save.py

from pathlib import Path
import shutil
import plotly.graph_objects as go

def _find_project_root(start: Path) -> Path:
    """
    Walk up a few levels to find the project root by looking for markers.
    Falls back to start if nothing obvious is found.
    """
    markers = {"config.yaml", "outputs"}
    cur = start
    for _ in range(6):
        if any((cur / m).exists() for m in markers):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start

def save_figures(fig: go.Figure, output_dir: str, name: str) -> None:
    """
    Save a high-resolution PNG to the chart-specific folder AND to outputs/gallery.
    """
    # 1) Resolve paths
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Figure file name
    png_name = f"{name}_report.png"
    png_path = output_dir / png_name

    # 2) Save to chart folder
    print(f"💾 saving high-res PNG to {png_path}")
    fig.write_image(str(png_path), format="png", scale=2.0, width=1200, height=800)

    # 3) Also save/copy to gallery
    project_root = _find_project_root(Path(__file__).resolve().parent)
    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    gallery_path = gallery_dir / png_name

    try:
        # copy to ensure exact same bytes; overwrite if exists
        shutil.copy2(png_path, gallery_path)
        print(f"🖼️  copied to gallery: {gallery_path}")
    except Exception as e:
        # Fallback: write directly if copy fails for any reason
        print(f"⚠️ copy to gallery failed ({e}); writing image directly to gallery.")
        fig.write_image(str(gallery_path), format="png", scale=2.0, width=1200, height=800)
        print(f"🖼️  wrote directly to gallery: {gallery_path}")
