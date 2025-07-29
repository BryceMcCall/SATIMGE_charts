
# generate_charts.py (simplified)
import shutil
from pathlib import Path

OUT_BASE = Path("outputs/charts_and_data")
HIGH_DIR = Path("outputs/gallery/high_res")

def copy_high_res_images(chart_dir):
    chart_dir = Path(chart_dir)
    HIGH_DIR.mkdir(parents=True, exist_ok=True)
    print("Copying report PNGs only...")

    # Only copy high-res PNGs
    for f in chart_dir.iterdir():
        if f.name.endswith("_report.png"):
            shutil.copy(f, HIGH_DIR / f.name)

