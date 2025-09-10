# generate_charts.py

import sys
from pathlib import Path
import argparse
import pkgutil
import importlib
import inspect
import shutil
import pandas as pd
import yaml

# 1) Paths
print('setting up paths')
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
CONFIG_PATH  = PROJECT_ROOT / "config.yaml"
CHARTS_DIR   = PROJECT_ROOT / "charts" / "chart_generators"
DATA_PATH    = PROJECT_ROOT / "data" / "processed" / "processed_dataset.parquet"
OUT_BASE     = PROJECT_ROOT / "outputs" / "charts_and_data"
GALLERY_BASE = PROJECT_ROOT / "outputs" / "gallery"

# 2) CLI (config only)
parser = argparse.ArgumentParser(description="Generate all SATIMGE charts")
parser.add_argument("--config", "-c", type=Path, default=CONFIG_PATH, help="Path to config.yaml")
args = parser.parse_args()

# 3) Load config (charts only from config)
print('load config file')
with open(args.config, "r", encoding="utf-8") as fh:
    tools_cfg = yaml.safe_load(fh)
charts_to_run = set(tools_cfg["charts"]["include"])
DEV_MODE = tools_cfg.get("dev_mode", False)  # still read, in case generators use it

# 4) Prepare folders
print('prepare output folders')
for d in (OUT_BASE, GALLERY_BASE):
    d.mkdir(parents=True, exist_ok=True)

# 5) Load full dataset once
print('load processed dataset')
try:
    import pyarrow.parquet as pq
    df = pq.read_table(DATA_PATH).to_pandas()
except Exception:
    df = pd.read_parquet(DATA_PATH)
print('done loading dataset')

# 6) Import style and extend palettes
print('importing sytles and palettes')
from charts.common.style import extend_palettes_from_df
extend_palettes_from_df(df)

# 7) Auto-discover modules under charts/chart_generators
print('discovering available chart modules')
import charts.chart_generators as cg_pkg
available = {name for _, name, _ in pkgutil.iter_modules(cg_pkg.__path__)}
missing = charts_to_run - available
if missing:
    print(f"⚠ Listed in config but not found: {sorted(missing)}")


def _pick_generator(module, module_name: str):
    """
    Return a callable generate_* function for the module, or (None, reason).
    Preference order:
      1) exact name: generate_{module_name}
      2) if exactly one generate_* exists, use it
      3) filter generate_* by signature (expects 2 params) → if 1, use it
      4) heuristic match on name similarity → pick best if unique
    """
    exact = f"generate_{module_name}"
    if hasattr(module, exact) and callable(getattr(module, exact)):
        return getattr(module, exact), f"{exact}"

    # all generate_* callables
    gens = [(n, getattr(module, n)) for n in dir(module)
            if n.startswith("generate_") and callable(getattr(module, n))]
    if not gens:
        return None, f"no function {exact}() and no generate_* found"

    if len(gens) == 1:
        n, fn = gens[0]
        return fn, f"{n} (only generate_*)"

    # filter by signature: prefer functions with (df, output_dir) like 2 positional/kw-only args
    def is_df_out_sig(fn):
        try:
            sig = inspect.signature(fn)
            params = [p for p in sig.parameters.values()
                      if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
            # allow optional defaults but require first two positional/keyword params to exist
            return len(params) >= 2
        except (TypeError, ValueError):
            return False

    sig_candidates = [(n, fn) for n, fn in gens if is_df_out_sig(fn)]
    if len(sig_candidates) == 1:
        n, fn = sig_candidates[0]
        return fn, f"{n} (signature match)"

    # heuristic name scoring against module_name
    base_key = module_name.lower().replace("fig", "")
    def score(name: str) -> int:
        nm = name.lower()
        s = 0
        if module_name.lower() in nm:
            s += 3
        if base_key and base_key in nm:
            s += 2
        # shorter name tends to be the main one (avoid helpers)
        s += max(0, 20 - len(nm))
        return s

    ranked = sorted(sig_candidates or gens, key=lambda t: score(t[0]), reverse=True)
    # check top two scores to avoid ties
    if len(ranked) == 1 or score(ranked[0][0]) > score(ranked[1][0]):
        n, fn = ranked[0]
        return fn, f"{n} (heuristic)"

    names = [n for n, _ in ranked[:4]]
    return None, f"ambiguous generators {names}; expected {exact}()"

# 8) Run selected modules
print('running selected chart modules')
for module_name in sorted(charts_to_run & available):
    try:
        module = importlib.import_module(f"charts.chart_generators.{module_name}")
    except Exception as e:
        print(f"❌ Failed to import {module_name}: {e}")
        continue

    fn, picked_info = _pick_generator(module, module_name)
    if fn is None:
        print(f"⚠ Skipping {module_name}: {picked_info}")
        continue

    print(f"⏳ Running {fn.__name__} for {module_name} [{picked_info}]…")

    # per-chart output folder
    chart_dir = OUT_BASE / module_name
    chart_dir.mkdir(exist_ok=True)

    # module saves figures/data into chart_dir
    try:
        fn(df, str(chart_dir))
    except Exception as e:
        print(f"❌ {module_name}: generator threw an error: {e}")
        continue

    # copy only high-res “report” PNGs to gallery (flat structure)
    try:
        for f in chart_dir.iterdir():
            if f.name.endswith("_report.png"):
                shutil.copy(f, GALLERY_BASE / f.name)
    except Exception as e:
        print(f"⚠ {module_name}: failed copying report PNGs to gallery: {e}")

    print(f"✔ {module_name} done.")
