# charts/common/style.py

from __future__ import annotations
from pathlib import Path
from typing import Iterable, Optional
import yaml
import plotly.graph_objects as go

# ───────────────────────── Project config (optional) ──────────────────────────
ROOT = Path(__file__).resolve().parents[2]
_CFG_PATH = ROOT / "config.yaml"
if _CFG_PATH.exists():
    with open(_CFG_PATH, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f)
    _PROJ = _CFG.get("project", {})
else:
    _PROJ = {}

# ─────────────────────────────────── Fonts ────────────────────────────────────
# Prefer Aptos if present; otherwise use close sans-serif fallbacks.
FONT_FAMILY = "Aptos, Arial, Segoe UI, Calibri, Helvetica, sans-serif"

# ───────────────────────────── Base palettes ──────────────────────────────────
# Fuels / energy sources (curated; add as needed)
FUEL_COLORS = {
    # Fossils & liquids
    "Coal":             "#2E2E2E",  # near-black
    "Oil":              "#5B4636",  # crude brown (generic oil if used)
    "Diesel":           "#8B5E34",  # diesel brown
    "Gasoline":         "#C97C28",  # amber
    "Kerosene/Jet":     "#A1662F",  # bronze
    "LPG":              "#7A4F9A",  # violet
    "Natural Gas":      "#1E90FF",  # blue
    "Syngas":           "#4F81BD",  # steel blue

    # Low-carbon / renewables
    "Electricity":      "#7E57C2",  # amethyst
    "Hydrogen":         "#00AEEF",  # hydrogen cyan
    "Biomass":          "#8FBC8F",  # sage green
    "Bioethanol":       "#3CB371",  # biofuel green
    "Hydro":            "#2B6CB0",  # deep hydro blue
    "Wind":             "#7F8C8D",  # cool grey
    "Solar PV":         "#FDB813",  # solar yellow
    "Solar CSP":        "#F39C12",  # solar orange
    "Geothermal":       "#C0392B",  # hot red
    "Waste":            "#6E7D57",  # olive grey
    "Wood/Wood Waste":  "#8D6E63",  # wood brown

    # Other buckets seen in legends
    "Imports":          "#F5B041",  # goldenrod
    "Hybrid":           "#8E44AD",  # distinct purple
    "AutoGen-Chemical": "#48C9B0",  # teal

    # Fallback
    "Other":            "#9E9E9E",  # neutral grey
}

# Sectors (aligned to common energy system reporting)
SECTOR_COLORS = {
    "Power":        "#6A1B9A",  # generation/supply
    "Electricity":  "#6A1B9A",  # alias
    "Industry":     "#FF7F0E",
    "IPPU":         "#FF7F0E",  # align with industry/process
    "Transport":    "#D62728",
    "Residential":  "#2E7D32",
    "Commercial":   "#0097A7",
    "Buildings":    "#1B998B",
    "Agriculture":  "#7CB342",
    "AFOLU":        "#7CB342",  # alias
    "Waste":        "#616161",
    "Mining":       "#A1887F",
    "Other Energy": "#BCBD22",
    "Refineries":   "#FF7F0E",  # industry-aligned

    # Extra labels seen in electricity-use charts
    "Supply":       "#4E79A7",  # steel blue
    "Commerce":     "#0097A7",  # same hue as Commercial
}

# Scenario GROUPS (used to colour individual scenarios)
# NDC appears in most names, so it is intentionally ignored for colour selection.
SCENARIO_GROUP_COLORS = {
    "BASE":        "#7F7F7F",  # neutral grey
    "CPP":         "#1F77B4",  # blue
    "High Carbon": "#8C564B",  # brown/red
    "Low Carbon":  "#2CA02C",  # green
}

# Scenario FAMILIES (for plots grouped by family)
SCENARIO_FAMILY_COLORS = {
    "BASE":         "#7F7F7F",
    "CPP1":         "#1F77B4",  # deep blue
    "CPP2":         "#2E86C1",  # mid blue
    "CPP3":         "#5DADE2",  # light blue
    "CPP4 Variant": "#85C1E9",  # pale blue
    "High Carbon":  "#8C564B",
    "Low Carbon":   "#2CA02C",
}

# Optional explicit overrides for particular scenario names (usually keep empty)
SCENARIO_COLORS: dict[str, str] = {
    # "NDC_BASE-LG": "#8AC41F",
    # "NDC_BASE-RG": "#1E1BD3",
    # "NDC_BASE-HG": "#D46820",
}

DEFAULT_COLOR = "#9E9E9E"

# Distinct fallback cycle for any unseen categories
FALLBACK_CYCLE = [
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF",
    "#393B79", "#637939", "#8C6D31", "#843C39", "#7B4173",
]

# ─────────────── Aliases / normalizers (extend as you discover labels) ───────
FUEL_ALIASES = {
    # Canonical single tokens
    "COAL": "Coal",
    "OIL": "Oil",
    "NUCLEAR": "Nuclear",
    "HYDRO": "Hydro",
    "WIND": "Wind",
    "PV": "Solar PV",
    "CSP": "Solar CSP",
    "BIOMASS": "Biomass",
    "BIOETHANOL": "Bioethanol",
    "DIESEL": "Diesel",
    "GASOLINE": "Gasoline",
    "GAS": "Natural Gas",
    "NG": "Natural Gas",
    "LNG": "Natural Gas",
    "HYDROGEN": "Hydrogen",
    "H2": "Hydrogen",
    "ELECTRIC": "Electricity",
    "ELECTRICITY": "Electricity",
    "KEROSENE": "Kerosene/Jet",
    "JET": "Kerosene/Jet",
    "IMPORTS": "Imports",
    "AUTOGEN-CHEMICAL": "AutoGen-Chemical",
    "HYBRID": "Hybrid",

    # E-prefixed tech labels from legends
    "ECOAL": "Coal",
    "EOIL": "Oil",
    "ENUCLEAR": "Nuclear",
    "EHYDRO": "Hydro",
    "EWIND": "Wind",
    "EPV": "Solar PV",
    "ECSP": "Solar CSP",
    "EBIOMASS": "Biomass",
    "EBIOETHANOL": "Bioethanol",
    "EGAS": "Natural Gas",
    "EDIESEL": "Diesel",
    "EGASOLINE": "Gasoline",
    "EKEROSENE": "Kerosene/Jet",
    "EHYBRID": "Hybrid",
    "EIMPORTS": "Imports",
}

SECTOR_ALIASES = {
    "POWER": "Power",
    "ELECTRICITY SUPPLY": "Power",
    "RES": "Residential",
    "COM": "Commercial",
    "COMMERCE": "Commercial",
    "SUPPLY": "Supply",
    "TRN": "Transport",
    "IPPU": "IPPU",
}

# Filled from dataframe for robust scenario→group/family mapping
SCENARIO_TO_GROUP: dict[str, str] = {}
SCENARIO_TO_FAMILY: dict[str, str] = {}

# ───────────────────────────── Color utilities ────────────────────────────────
def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def _adjust_brightness(hex_color: str, factor: float) -> str:
    """factor > 1 → lighter, factor < 1 → darker."""
    r, g, b = _hex_to_rgb(hex_color)
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return _rgb_to_hex((r, g, b))

def _assign_from_cycle(existing: dict, key: str) -> str:
    used = set(existing.values())
    for c in FALLBACK_CYCLE:
        if c not in used:
            existing[key] = c
            return c
    existing[key] = DEFAULT_COLOR
    return DEFAULT_COLOR

def _norm(s: Optional[str]) -> str:
    return (s or "").strip()

def _norm_fuel(label: str) -> str:
    """
    Normalise fuel/tech labels:
      - case-insensitive
      - ignore spaces / hyphens
      - handle E-prefixed forms (ECoal → Coal, EPV → Solar PV, …)
    """
    s = _norm(label)
    if not s:
        return s

    key = s.upper()
    # direct alias first
    if key in FUEL_ALIASES:
        return FUEL_ALIASES[key]

    # try compacted forms (strip spaces/hyphens)
    compact = key.replace(" ", "").replace("-", "")
    if compact in FUEL_ALIASES:
        return FUEL_ALIASES[compact]

    # generic E-prefix handler: ECOAL → COAL, EPV → PV, etc.
    if compact.startswith("E"):
        base = compact[1:]
        if base in FUEL_ALIASES:
            return FUEL_ALIASES[base]
        # common special cases if not already caught
        if base == "PV":
            return "Solar PV"
        if base == "CSP":
            return "Solar CSP"
        # fallback: title-case the base (ECOAL → Coal)
        return base.title()

    return s

def _growth_code(s: str) -> Optional[str]:
    su = s.upper()
    for code in ("LG", "RG", "HG"):
        if f"-{code}" in su or su.endswith(code):
            return code
    return None

def _group_from_name(s: str) -> str:
    """Infer Scenario Group from scenario name, deliberately ignoring 'NDC'."""
    su = s.upper()
    if "CPP" in su: return "CPP"
    if "HIGH CARBON" in su: return "High Carbon"
    if "LOW CARBON" in su or "NET ZERO" in su or "NETZERO" in su or "NZ" in su: return "Low Carbon"
    if "BASE" in su: return "BASE"
    return "BASE"

def _family_from_name(s: str) -> str:
    """Heuristic family parser for cases without explicit column."""
    su = s.upper()
    if "CPP1" in su: return "CPP1"
    if "CPP2" in su: return "CPP2"
    if "CPP3" in su: return "CPP3"
    if "CPP4" in su: return "CPP4 Variant"
    if "HIGH CARBON" in su: return "High Carbon"
    if "LOW CARBON" in su: return "Low Carbon"
    if "BASE" in su: return "BASE"
    return "BASE"

# ───────────────────────────── Public color API ───────────────────────────────
def color_for(kind: str, name: str) -> str:
    """
    kind ∈ {'fuel','sector','scenario','scenario_family','scenario_group'}
    """
    name = _norm(name)
    if not name:
        return DEFAULT_COLOR

    if kind == "fuel":
        label = _norm_fuel(name)
        if label not in FUEL_COLORS:
            return _assign_from_cycle(FUEL_COLORS, label)
        return FUEL_COLORS[label]

    if kind == "sector":
        label = SECTOR_ALIASES.get(name.upper(), name)
        if label not in SECTOR_COLORS:
            return _assign_from_cycle(SECTOR_COLORS, label)
        return SECTOR_COLORS[label]

    if kind == "scenario_group":
        grp = name
        if grp not in SCENARIO_GROUP_COLORS:
            return _assign_from_cycle(SCENARIO_GROUP_COLORS, grp)
        return SCENARIO_GROUP_COLORS[grp]

    if kind == "scenario_family":
        fam = name
        if fam not in SCENARIO_FAMILY_COLORS:
            return _assign_from_cycle(SCENARIO_FAMILY_COLORS, fam)
        return SCENARIO_FAMILY_COLORS[fam]

    if kind == "scenario":
        # 1) explicit override wins
        if name in SCENARIO_COLORS:
            return SCENARIO_COLORS[name]
        # 2) base hue from Scenario Group (from df map if available, else heuristic)
        grp = SCENARIO_TO_GROUP.get(name) or _group_from_name(name)
        base = SCENARIO_GROUP_COLORS.get(grp, DEFAULT_COLOR)
        # 3) apply LG/RG/HG variant
        gc = _growth_code(name)
        if gc == "LG":  return _adjust_brightness(base, 1.25)
        if gc == "HG":  return _adjust_brightness(base, 0.80)
        return base

    return DEFAULT_COLOR

def color_sequence(kind: str, names: Iterable[str]) -> list[str]:
    return [color_for(kind, n) for n in names]

# ──────────────── Data-driven palette extension from dataframe ────────────────
def extend_palettes_from_df(df) -> None:
    """
    Scan a dataframe and ensure colors exist for all seen labels.
    Columns (if present) used:
      - Fuels: 'Commodity_Name' or 'Commodity'
      - Sectors: 'Sector'
      - Scenario families: 'ScenarioFamily'
      - Scenario groups: 'ScenarioGroup' or 'Scenario_Group'
      - Scenarios: 'Scenario'
    Also fills SCENARIO_TO_GROUP / SCENARIO_TO_FAMILY maps.
    """
    # Fuels
    for col in ("Commodity_Name", "Commodity"):
        if col in df.columns:
            names = sorted({_norm_fuel(x) for x in df[col].dropna().astype(str).unique()})
            for n in names:
                _ = color_for("fuel", n)
            break

    # Sectors
    if "Sector" in df.columns:
        names = sorted({SECTOR_ALIASES.get(str(x).upper(), str(x))
                        for x in df["Sector"].dropna().astype(str).unique()})
        for n in names:
            _ = color_for("sector", n)

    # Scenario families (distinct from groups)
    fam_col = "ScenarioFamily" if "ScenarioFamily" in df.columns else None
    if fam_col:
        fams = sorted({str(x) for x in df[fam_col].dropna().astype(str).unique()})
        for n in fams:
            _ = color_for("scenario_family", n)
        if "Scenario" in df.columns:
            for scen, fam in df[["Scenario", fam_col]].dropna().astype(str).values:
                SCENARIO_TO_FAMILY.setdefault(scen, fam)

    # Scenario groups (preferred base for scenario hues)
    grp_col = "ScenarioGroup" if "ScenarioGroup" in df.columns else ("Scenario_Group" if "Scenario_Group" in df.columns else None)
    if grp_col:
        grps = sorted({str(x) for x in df[grp_col].dropna().astype(str).unique()})
        for n in grps:
            if n not in SCENARIO_GROUP_COLORS:
                _assign_from_cycle(SCENARIO_GROUP_COLORS, n)
        if "Scenario" in df.columns:
            for scen, grp in df[["Scenario", grp_col]].dropna().astype(str).values:
                SCENARIO_TO_GROUP.setdefault(scen, grp)

    # Scenarios (ensure every scenario now resolves to a colour)
    if "Scenario" in df.columns:
        for n in sorted({str(x) for x in df["Scenario"].dropna().astype(str).unique()}):
            _ = color_for("scenario", n)

# ───────────────────────────── Common Plotly layout ───────────────────────────
def apply_common_layout(fig: go.Figure, image_type: str = "report") -> go.Figure:
    """
    Apply consistent fonts, spacing, and grid.
    image_type: 'dev' (quick previews) or 'report' (high-res export scaling)
    """
    scale_map = {"dev": 1.0, "report": 2.0}
    scale = scale_map.get(image_type, 1.0)

    base_font   = 13 * scale
    title_font  = 18 * scale
    legend_font = 12 * scale
    tick_font   = int(base_font * 0.8)

    fig.update_layout(
        template="simple_white",
        height=int(600 * scale),
        font=dict(family=FONT_FAMILY, size=base_font, color="black"),
        margin=dict(l=80, r=80, t=60, b=int(100 * scale)),
        title=dict(
            font=dict(family=FONT_FAMILY, size=title_font),
            x=0.5, xanchor="center",
            pad=dict(b=80)
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=legend_font, family=FONT_FAMILY),
        ),
        # subtle footer band (room for caption/logo if re-enabled later)
        shapes=[
            dict(
                type="rect", xref="paper", yref="paper",
                x0=0, x1=1, y0=-0.30, y1=0,
                fillcolor="white", line=dict(color="lightgrey"), layer="below",
            )
        ]
    )

    fig.update_xaxes(
        showgrid=True, gridwidth=0.6, gridcolor="lightgrey",
        tickangle=0, ticks="outside", ticklen=5,
        tickfont=dict(size=tick_font, family=FONT_FAMILY),
        title_font=dict(size=title_font, family=FONT_FAMILY),
        tickmode="linear", dtick=5,
        showline=True, mirror=True, linecolor="lightgrey", linewidth=1.2,
        minor=dict(
            ticks="outside", showgrid=True, gridcolor="whitesmoke",
            ticklen=3, tick0=0, dtick=1
        )
    )

    fig.update_yaxes(
        showgrid=True, gridwidth=0.6, gridcolor="lightgrey",
        ticks="outside", ticklen=5,
        tickfont=dict(size=tick_font, family=FONT_FAMILY),
        title_font=dict(size=title_font, family=FONT_FAMILY),
        rangemode="tozero",
        showline=True, mirror=True, linecolor="lightgrey", linewidth=1.2,
        minor=dict(
            ticks="outside", showgrid=True, gridcolor="whitesmoke",
            ticklen=3, tick0=0, dtick=25000
        )
    )
    return fig
