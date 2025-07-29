# generate_charts.py

import sys
from pathlib import Path
import argparse
import pkgutil
import importlib
import shutil
import pandas as pd
import yaml

# 1) Paths
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
CONFIG_PATH  = PROJECT_ROOT / "config.yaml"
CHARTS_DIR   = PROJECT_ROOT / "charts" / "chart_generators"
DATA_PATH    = PROJECT_ROOT / "data" / "processed" / "processed_dataset.parquet"
OUT_BASE     = PROJECT_ROOT / "outputs" / "charts_and_data"
GALLERY_BASE = PROJECT_ROOT / "outputs" / "gallery"
LOW_DIR      = GALLERY_BASE / "low_res"
HIGH_DIR     = GALLERY_BASE / "high_res"

# 2) CLI: allow override of config file and chart list
parser = argparse.ArgumentParser(description="Generate all SATIMGE charts")
parser.add_argument(
    "--config", "-c", type=Path, default=CONFIG_PATH,
    help="Path to config.yaml"
)
parser.add_argument(
    "--charts", "-C", nargs="*",
    help="Override the list of charts to run (by folder name)"
)
args = parser.parse_args()

# 3) Load config
tools_cfg = yaml.safe_load(open(args.config))
charts_to_run = set(args.charts) if args.charts else set(tools_cfg["charts"]["include"])

DEV_MODE = tools_cfg.get("dev_mode", False)


# 4) Prepare folders
for d in (OUT_BASE, LOW_DIR, HIGH_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 5) Load data once
df = pd.read_parquet(DATA_PATH)

# 6) Auto-discover and run
import charts.chart_generators as cg_pkg

for finder, module_name, is_pkg in pkgutil.iter_modules(cg_pkg.__path__):
    if module_name not in charts_to_run:
        print(f"⚠ Skipping {module_name}")
        continue

    module = importlib.import_module(f"charts.chart_generators.{module_name}")
    fn_name = f"generate_{module_name}"
    if not hasattr(module, fn_name):
        print(f"⚠ Skipping {module_name}: no function {fn_name}()")
        continue

    fn = getattr(module, fn_name)
    print(f"⏳ Running {fn_name}…")

    # a) per-chart folder
    chart_dir = OUT_BASE / module_name
    chart_dir.mkdir(exist_ok=True)

    # b) call module: it should save images & write data.csv into chart_dir
    fn(df, str(chart_dir))

# c) dev mode: only save PNGs, skip CSV/SVG
for f in chart_dir.iterdir():
    if DEV_MODE:
        if "_dev" in f.stem and f.suffix.lower() == ".png":
            shutil.copy(f, LOW_DIR / f.name)
    else:
        if f.suffix.lower() in (".png", ".svg", ".jpg", ".jpeg"):
            target = LOW_DIR if "_dev" in f.stem else HIGH_DIR
            shutil.copy(f, target / f.name)

    print(f"✔ {module_name} done.")
