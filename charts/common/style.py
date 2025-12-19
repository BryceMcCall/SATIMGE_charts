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
FONT_FAMILY = "Aptos, Segoe UI, Arial, Calibri, Helvetica, sans-serif"

# ───────────────────────────── Base palettes ──────────────────────────────────
FUEL_COLORS = {
    "Coal":           "#505457",  # dark grey/black
    "Oil":            "#A0522D",  # brown (sienna)
    "Natural Gas":    "#D62728",  # red
    "Nuclear":        "#D765C0",  # light pink
    "Hydro":          "#1E90FF",  # medium blue
    "Pumped Storage": "#3232F3",  # dark blue
    "Battery":        "#90EE90",  # light green
    "Biomass":        "#2CA02C",  # green
    "Biowood":        "#2CA02C",  # green
    "Wind":           "#17BECF",  # teal/cyan
    "Solar PV":       "#FFD700",  # golden yellow
    "Solar CSP":      "#FF7F0E",  # orange
    "Imports":        "#8C564B",  # muted brown
    "Other":          "#E377C2",  # magenta

    # Additional techs retained from previous palette
    "Diesel":           "#8B5E34",
    "Gasoline":         "#C97C28",
    "Kerosene/Jet":     "#A1662F",
    "LPG":              "#FF9F1C",
    "Syngas":           "#4F81BD",
    "Hydrogen":         "#00AEEF",
    "Electricity":      "#7E57C2",
    "Bioethanol":       "#3CB371",
    "Geothermal":       "#C0392B",
    "Waste":            "#6E7D57",
    "Wood/Wood Waste":  "#8D6E63",
    "Hybrid":           "#8E44AD",
    "AutoGen-Chemical": "#48C9B0",
}

# Sectors (unchanged)
SECTOR_COLORS = {
    "Power":        "#6A1B9A",
    "Electricity":  "#6A1B9A",
    "Industry":     "#FF7F0E",
    "IPPU":         "#FF7F0E",
    "Transport":    "#D62728",
    "Residential":  "#2E7D32",
    "Commercial":   "#0097A7",
    "Buildings":    "#1B998B",
    "Agriculture":  "#7CB342",
    "AFOLU":        "#7CB342",
    "Waste":        "#616161",
    "Mining":       "#A1887F",
    "Other Energy": "#BCBD22",
    "Refineries":   "#FF7F0E",
    "Supply":       "#4E79A7",
    "Commerce":     "#0097A7",
}

# Scenario GROUPS
SCENARIO_GROUP_COLORS = {
    "BASE":        "#7F7F7F",
    "CPP":         "#1F77B4",
    "High Carbon": "#8C564B",
    "Low Carbon":  "#2CA02C",
}

# Scenario FAMILIES
SCENARIO_FAMILY_COLORS = {
    "BASE":         "#7F7F7F",
    "CPP1":         "#1F77B4",
    "CPP2":         "#2E86C1",
    "CPP3":         "#5DADE2",
    "CPP4 Variant": "#85C1E9",
    "High Carbon":  "#8C564B",
    "Low Carbon":   "#2CA02C",
}

SCENARIO_COLORS: dict[str, str] = {}
DEFAULT_COLOR = "#9E9E9E"

FALLBACK_CYCLE = [
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF",
    "#393B79", "#637939", "#8C6D31", "#843C39", "#7B4173",
]

# ─────────────── Aliases ───────────────
FUEL_ALIASES = {
    "COAL": "Coal", "NUCLEAR": "Nuclear", "HYDRO": "Hydro", "WIND": "Wind",
    "PV": "Solar PV", "CSP": "Solar CSP", "BIOMASS": "Biomass",
    "BIOETHANOL": "Bioethanol", "DIESEL": "Diesel", "GASOLINE": "Gasoline",
    "GAS": "Natural Gas", "NG": "Natural Gas", "LNG": "Natural Gas",
    "HYDROGEN": "Hydrogen", "H2": "Hydrogen",
    "BATTERY": "Battery", "STORAGE": "Battery",
    "PUMPED": "Pumped Storage", "PUMPED STORAGE": "Pumped Storage",
    "ELECTRIC": "Electricity", "ELECTRICITY": "Electricity",
    "KEROSENE": "Kerosene/Jet", "JET": "Kerosene/Jet",
    "OIL": "Oil",
    "IMPORTS": "Imports", "EIMPORTS": "Imports",
    "AUTOGEN-CHEMICAL": "AutoGen-Chemical", "HYBRID": "Hybrid",

    "ECOAL": "Coal", "ENUCLEAR": "Nuclear", "EHYDRO": "Hydro", "EWIND": "Wind",
    "EPV": "Solar PV", "ECSP": "Solar CSP", "EBIOMASS": "Biomass",
    "EBIOETHANOL": "Bioethanol", "EGAS": "Natural Gas", "EDIESEL": "Diesel",
    "EGASOLINE": "Gasoline", "EKEROSENE": "Kerosene/Jet", "EOIL": "Oil",
    "EBATTERY": "Battery", "ESTORAGE": "Battery",
    "EPUMPED": "Pumped Storage", "EPUMPEDSTORAGE": "Pumped Storage",
    "EHYBRID": "Hybrid",
}

SECTOR_ALIASES = {
    "POWER": "Power", "ELECTRICITY SUPPLY": "Power",
    "RES": "Residential", "COM": "Commercial", "COMMERCE": "Commercial",
    "SUPPLY": "Supply", "TRN": "Transport", "IPPU": "IPPU",
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
    s = _norm(label)
    if not s:
        return s
    key = s.upper()
    if key in FUEL_ALIASES:
        return FUEL_ALIASES[key]
    compact = key.replace(" ", "").replace("-", "")
    if compact in FUEL_ALIASES:
        return FUEL_ALIASES[compact]
    if compact.startswith("E"):
        base = compact[1:]
        return FUEL_ALIASES.get(base, base.title() if base else s)
    return s

def _growth_code(s: str) -> Optional[str]:
    su = s.upper()
    for code in ("LG", "RG", "HG"):
        if f"-{code}" in su or su.endswith(code):
            return code
    return None

def _group_from_name(s: str) -> str:
    su = s.upper()
    if "CPP" in su: return "CPP"
    if "HIGH CARBON" in su: return "High Carbon"
    if "LOW CARBON" in su or "NET ZERO" in su or "NETZERO" in su or "NZ" in su: return "Low Carbon"
    if "BASE" in su: return "BASE"
    return "BASE"

def _family_from_name(s: str) -> str:
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
        if name in SCENARIO_COLORS:
            return SCENARIO_COLORS[name]
        grp = SCENARIO_TO_GROUP.get(name) or _group_from_name(name)
        base = SCENARIO_GROUP_COLORS.get(grp, DEFAULT_COLOR)
        gc = _growth_code(name)
        if gc == "LG":  return _adjust_brightness(base, 1.25)
        if gc == "HG":  return _adjust_brightness(base, 0.80)
        return base

    return DEFAULT_COLOR

def color_sequence(kind: str, names: Iterable[str]) -> list[str]:
    return [color_for(kind, n) for n in names]

# ──────────────── Data-driven palette extension from dataframe ────────────────
def extend_palettes_from_df(df) -> None:
    for col in ("Commodity_Name", "Commodity"):
        if col in df.columns:
            names = sorted({_norm_fuel(x) for x in df[col].dropna().astype(str).unique()})
            for n in names:
                _ = color_for("fuel", n)
            break

    if "Sector" in df.columns:
        names = sorted({SECTOR_ALIASES.get(str(x).upper(), str(x))
                        for x in df["Sector"].dropna().astype(str).unique()})
        for n in names:
            _ = color_for("sector", n)

    fam_col = "ScenarioFamily" if "ScenarioFamily" in df.columns else None
    if fam_col:
        fams = sorted({str(x) for x in df[fam_col].dropna().astype(str).unique()})
        for n in fams:
            _ = color_for("scenario_family", n)
        if "Scenario" in df.columns:
            for scen, fam in df[["Scenario", fam_col]].dropna().astype(str).values:
                SCENARIO_TO_FAMILY.setdefault(scen, fam)

    grp_col = "ScenarioGroup" if "ScenarioGroup" in df.columns else ("Scenario_Group" if "Scenario_Group" in df.columns else None)
    if grp_col:
        grps = sorted({str(x) for x in df[grp_col].dropna().astype(str).unique()})
        for n in grps:
            if n not in SCENARIO_GROUP_COLORS:
                _assign_from_cycle(SCENARIO_GROUP_COLORS, n)
        if "Scenario" in df.columns:
            for scen, grp in df[["Scenario", grp_col]].dropna().astype(str).values:
                SCENARIO_TO_GROUP.setdefault(scen, grp)

    if "Scenario" in df.columns:
        for n in sorted({str(x) for x in df["Scenario"].dropna().astype(str).unique()}):
            _ = color_for("scenario", n)

# ───────────────────────────── Common Plotly layout ───────────────────────────
def apply_common_layout(fig: go.Figure, image_type: str = "report") -> go.Figure:
    scale_map = {"dev": 1.0, "report": 2.0}
    scale = scale_map.get(image_type, 1.0)

    base_font   = 13 * scale
    title_font  = 18 * scale
    legend_font = 12 * scale
    tick_font   = int(base_font * 0.8)
    axis_title_font = int(title_font * 0.8)

    fig.update_layout(
        template="simple_white",
        #height=int(600 * scale),
        font=dict(family=FONT_FAMILY, size=base_font, color="black"),
        margin=dict(l=80, r=80, t=60, b=int(100 * scale)),
        title=dict(font=dict(family=FONT_FAMILY, size=title_font),
                   x=0.5, xanchor="center", pad=dict(b=80)),
        legend=dict(orientation="h",
                    yanchor="bottom", y=-0.32,
                    xanchor="center", x=0.5,
                    font=dict(size=legend_font, family=FONT_FAMILY)),
    )

    fig.update_xaxes(
        showgrid=True, gridwidth=0.6, gridcolor="lightgrey",
        tickangle=0, ticks="outside", ticklen=5,
        tickfont=dict(size=tick_font, family=FONT_FAMILY),
        title_font=dict(size=axis_title_font, family=FONT_FAMILY),
        tickmode="auto", dtick=None,
        showline=True, mirror=True, linecolor="lightgrey", linewidth=1.2,
        minor=dict(ticks="outside", showgrid=True, gridcolor="whitesmoke",
                   ticklen=3, tick0=0, dtick=1)
    )

    fig.update_yaxes(
        showgrid=True, gridwidth=0.6, gridcolor="lightgrey",
        ticks="outside", ticklen=5,
        tickfont=dict(size=tick_font, family=FONT_FAMILY),
        title_font=dict(size=axis_title_font, family=FONT_FAMILY),
        rangemode="tozero",
        showline=True, mirror=True, linecolor="lightgrey", linewidth=1.2,
        minor=dict(ticks="outside", showgrid=True, gridcolor="whitesmoke",
                   ticklen=3, tick0=0, dtick=25000)
    )

    return fig
