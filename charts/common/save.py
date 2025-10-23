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


def _write(fig: go.Figure, path: Path, fmt: str, **kwargs) -> None:
    fig.write_image(str(path), format=fmt, **kwargs)
    print(f"✅ wrote {fmt.upper()} → {path}")


def save_figures(fig: go.Figure, output_dir: str, name: str) -> None:
    """
    Save a high-resolution PNG AND an SVG to the chart-specific folder,
    and mirror both into outputs/gallery.

    Creates:
      <output_dir>/<name>_report.png
      <output_dir>/<name>_report.svg
      <project_root>/outputs/gallery/<name>_report.png
      <project_root>/outputs/gallery/<name>_report.svg
    """
    # Ensure consistent canvas for both formats
    width, height, scale = 1200, 800, 2.0
    fig.update_layout(width=width, height=height)

    # Paths
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    png_name = f"{name}_report.png"
    svg_name = f"{name}_report.svg"
    png_path = output_dir / png_name
    svg_path = output_dir / svg_name

    # Write to chart folder
    print(f"💾 saving PNG to {png_path}")
    _write(fig, png_path, "png", width=width, height=height, scale=scale)
    print(f"💾 saving SVG to {svg_path}")
    _write(fig, svg_path, "svg")  # no scale needed for SVG

    # Mirror into gallery
    project_root = _find_project_root(Path(__file__).resolve().parent)
    gallery_dir = project_root / "outputs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)

    for src, name_ in [(png_path, png_name), (svg_path, svg_name)]:
        dst = gallery_dir / name_
        try:
            shutil.copy2(src, dst)
            print(f"🖼️  copied to gallery: {dst}")
        except Exception as e:
            print(f"⚠️ copy failed ({e}); writing directly to gallery.")
            if src.suffix.lower() == ".png":
                _write(fig, dst, "png", width=width, height=height, scale=scale)
            else:
                _write(fig, dst, "svg")
