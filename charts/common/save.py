# charts/common/save.py

# charts/common/save.py

import os
from pathlib import Path
import yaml

# Load defaults from config.yaml if it exists
_PROJECT_ROOT = Path(__file__).parents[2]
_CFG_PATH     = _PROJECT_ROOT / "config.yaml"

if _CFG_PATH.exists():
    with open(_CFG_PATH, "r") as f:
        _cfg = yaml.safe_load(f)
    DEFAULT_FORMATS     = _cfg.get("output", {}).get("formats",    ["png"])
    DEFAULT_RESOLUTIONS = _cfg.get("output", {}).get("resolutions", {"dev": {"width":800, "height":600}})
else:
    DEFAULT_FORMATS     = ["png"]
    DEFAULT_RESOLUTIONS = {"dev": {"width":800, "height":600}}

def save_figures(fig, output_dir, name, formats=None, resolutions=None):
    """
    Save a Plotly figure at multiple formats/resolutions.
    - fig: Plotly figure
    - output_dir: folder to save into
    - name: base filename (no extension)
    - formats: list of formats (overrides config)
    - resolutions: dict of {label: {width, height}} (overrides config)
    """
    if formats    is None:
        formats    = DEFAULT_FORMATS
    if resolutions is None:
        resolutions = DEFAULT_RESOLUTIONS

    os.makedirs(output_dir, exist_ok=True)
    for fmt in formats:
        for label, size in resolutions.items():
            fname = f"{name}_{label}.{fmt}"
            path  = os.path.join(output_dir, fname)
            fig.write_image(
                path,
                format=fmt,
                width = size["width"],
                height= size["height"]
            )
