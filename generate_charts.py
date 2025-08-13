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
HIGH_DIR     = GALLERY_BASE / "high_res"

# 2) CLI (config only)
parser = argparse.ArgumentParser(description="Generate all SATIMGE charts")
parser.add_argument("--config", "-c", type=Path, default=CONFIG_PATH, help="Path to config.yaml")
args = parser.parse_args()

# 3) Load config (charts only from config)
tools_cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))
charts_to_run = set(tools_cfg["charts"]["include"])
DEV_MODE = tools_cfg.get("dev_mode", False)  # still read, in case generators use it

# 4) Prepare folders
for d in (OUT_BASE, HIGH_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 5) Load full dataset once
try:
    import pyarrow.parquet as pq
    df = pq.read_table(DATA_PATH).to_pandas()
except Exception:
    df = pd.read_parquet(DATA_PATH)

# 6) Auto-discover and run
import charts.chart_generators as cg_pkg

available = {name for _, name, _ in pkgutil.iter_modules(cg_pkg.__path__)}
missing = charts_to_run - available
if missing:
    print(f"⚠ Listed in config but not found: {sorted(missing)}")

for module_name in sorted(charts_to_run & available):
    module = importlib.import_module(f"charts.chart_generators.{module_name}")
    fn_name = f"generate_{module_name}"
    if not hasattr(module, fn_name):
        print(f"⚠ Skipping {module_name}: no function {fn_name}()")
        continue

    fn = getattr(module, fn_name)
    print(f"⏳ Running {fn_name}…")

    # per‑chart output folder
    chart_dir = OUT_BASE / module_name
    chart_dir.mkdir(exist_ok=True)

    # module saves figures/data into chart_dir
    fn(df, str(chart_dir))

    # copy only high‑res “report” PNGs to gallery/high_res
    for f in chart_dir.iterdir():
        if f.name.endswith("_report.png"):
            shutil.copy(f, HIGH_DIR / f.name)

    print(f"✔ {module_name} done.")
