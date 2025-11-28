#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Completely local script: DB network drawing (x=earliest fixed / y=optimal dispersion "time_optim")
- LAYOUT_MODE:
  - "time_optim": x=earliest fixed, y=spring initialization + optimal dispersion with proximity x repulsion (★recommended)
  - "barycenter": y=crossing reduction (barycenter) + time layer band (Y/M/D) / x=earliest
  - "hierarchy":  y=data supply hierarchy (data_source upstream → downstream) / x=earliest
  - "spring":     x=earliest fixed + y=spring (traditional version without repulsion adjustment)
- citing=dot line / data_source=solid line. Shared errors (shared_err_count) are overlaid with semi-transparent thick bands.
- pos_nudge.csv can be used for manual offsetting (internal_key or Database_name, dx, dy)
- Edge drawing logic remains unchanged (no modifications)
"""

import sys, math, warnings, unicodedata, re, random, pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict, Counter

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib
matplotlib.rcParams['svg.fonttype'] = 'none' # Save text as font information in SVG
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, num2date, YearLocator, DateFormatter
from matplotlib import cm, colors as mcolors
from matplotlib import font_manager as fm, rcParams
from matplotlib.font_manager import FontProperties
from matplotlib import transforms as mtransforms
from matplotlib.lines import Line2D # Introduced to add legend
from matplotlib.patches import FancyArrowPatch # overlay arrow zorder adjustment


def _to_naive_datetime(dt):
    """Convert datetime/Timestamp to naive datetime without timezone"""
    if dt is None:
        return None
    # pandas.Timestamp
    if isinstance(dt, pd.Timestamp):
        # if tz attached, remove tz information
        if dt.tz is not None:
            dt = dt.tz_localize(None)
        return dt.to_pydatetime()
    # standard datetime
    if isinstance(dt, datetime):
        return dt.replace(tzinfo=None)
    return dt

def _num2date_naive(x):
    """Return a naive datetime by removing the timezone from the result of matplotlib.dates.num2date (which includes UTC)"""
    return num2date(x).replace(tzinfo=None)


# ========= User Settings =========
HISTORY_XLSX = "history_db.xlsx"
ERRORS_XLSX  = "db_panel_B_shared_error_summary.xlsx" # shared error data

OUTPUT_DIR   = "db_graph_outputs"
FIG_PNG      = "timeline_network.png"
FIG_SVG      = "timeline_network.svg"  # editable SVG for Inkscape
EXPORT_SVG   = True                    # whether to export SVG
SVG_TEXT_AS_PATH = False               # if True, text is converted to paths (harder to edit, more stable display)
NODE_CSV     = "nodes.csv"
EDGE_CSV     = "edges.csv"
GRAPH_PKL    = "graph.gpickle"

# Font (specify local font if needed)
FONT_PATH = None  # e.g., r"C:\Windows\Fonts\meiryo.ttc" / "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# ---- Layout selection ----
LAYOUT_MODE = "time_optim"   # "time_optim" / "barycenter" / "hierarchy" / "spring". We recommend "time_optim".

# (time_optim) fixed x, optimal dispersion y parameters
SPRING_SEED = 42
HYBRID_SPRING_K = 50 # initial = 50
HYBRID_SPRING_ITER = 600
HYBRID_SPRING_SCALE_Y = 36.0
HYBRID_USE_INIT_POS = True

# (time_optim) vertical decorrelation for near x
NEAR_X_DAYS        = 70     # Repulsion target if x is close within this number of days, initial 35
MIN_Y_GAP_NEAR_X   = 1.7   # Minimum vertical gap to secure for close x, initial = 0.85
Y_SPREAD_PASSES    = 6
Y_SPREAD_COOLING   = 0.6

# (A) barycenter（y=crossing reduction + time layer bands）. Not used in the default layout="time_optim".
TIME_UNIT   = "M"           # "Y" / "M" / "D"
BARYCENTER_ITERS = 16
BARYCENTER_GAP   = 1.2
VERTICAL_BANDS_BY_TIME = True
TIME_BAND_STEP   = 3.5
TIME_BAND_ZIGZAG = True
YEAR_SUBLAYERS = True
YEAR_SUBLAYERS_K = 3
YEAR_SUBLAYER_Y_OFFSET = 0.35
EDGE_GROUP_BUNDLE = True
EDGE_CURVE_BASE   = 0.12 # initial 0.12
EDGE_CURVE_SPREAD = 0.20 # initial 0.20

# (B) hierarchy（y=supply → use hierarchy）. not used in the default layout="time_optim".
HIER_LAYER_STEP_Y = 3.0
HIER_INTRA_GAP_Y  = 1.0
HIER_ITERS        = 12

# ---- Drawing ----
FIG_SIZE = (26, 14)
DPI = 260
LABEL_MAXLEN = 28
MIN_DEGREE_FOR_LABEL = 1
NODE_SIZE = 500.0
PAD_DAYS = 90
PAD_FRAC_Y = 0.12
ARROWSIZE = 30
OVERLAY_WIDTH_CT = 2.2  # citing: dot line
OVERLAY_WIDTH_DS = 2.2  # data_source: solid line
CITING_ALPHA   = 0.55
DATASRC_ALPHA  = 0.75

# === Year label/grid settings ===
SHOW_XLABEL = True
XLABEL_FONTSIZE = 20
XLABEL_TEXT = "Estimated first online date (Year)"

SHOW_YEAR_TICKS = True     # Separate x-axis by year
YEAR_TICK_STEP = 1         # 1 year intervals (can be coarser with 2 or 5)
YEAR_FORMAT = "%Y"         # Format for tick labels

SHOW_YEAR_GRID = True      # Vertical grid lines for each year
YEAR_GRID_ALPHA = 0.5

SHOW_YEAR_BANDS = False    # Alternate light vertical bands for each year (set True for better visibility)
YEAR_BAND_ALPHA = 0.05

# Year number text (numbers corresponding to vertical lines or bands) displayed along the bottom edge of the figure
SHOW_YEAR_NUMBERS = True
YEAR_NUMBER_STEP = 1          # 1: every year, 2 or 5 to thin out
YEAR_NUMBERS_AT = "mid"       # "mid"=placed in the middle of the year (7/1), "lines"=on the vertical line at the beginning of the year (1/1)
YEAR_NUMBER_FONTSIZE = 20
YEAR_NUMBER_OFFSET_AX = 0.01  # Offset from the bottom edge (axis coordinates). Greater than 0 to avoid clipping
YEAR_NUMBER_ROTATE = 0        # Rotate if necessary, e.g., 90
# ---- heat (shared error bands) ----
HEAT_CMAP_NAME = "Reds"
HEAT_VMAX_MODE = "max"      # "max" or "p95"
HEAT_ALPHA     = 0.7
HEAT_LINE_BASE = 6.0
HEAT_LINE_GAIN = 3.0

# ---- Input extension ----
CREATE_HEAT_ONLY_EDGES = True
CREATE_NODES_FROM_ERRORS = True 
# CREATE_NODES_FROM_ERRORS = True:Not effective in our case, 
# since nodes added only from errors_df have no earliest date, and 
# these nodes will be placed at a default x-position slightly before the earliest dated database.
# In our case there are no such nodes, so the option is kept set to True for potential future use.

# ---- Manual offset CSV ----
POS_NUDGE_CSV = "pos_nudge.csv"    # internal_key or Database_name, dx, dy
WRITE_AUDIT = True

# Node appearance and scale
BASE_WHITE_NODE = (0.95, 0.95, 0.95)  # Light white-gray
EDGE_GRAY = (0.8, 0.8, 0.8)          # Light gray for edges
NODE_SIZE_SCALE = 3.0                # Node size scale (3x)
NODE_EDGE_LINEWIDTH = 1.2            # Edge line width

# Label font size (for adjustment)
LABEL_FONT_SIZE = 20                 # Slightly larger than default

# --- Option to display x-axis as arrow ---
XAXIS_AS_ARROW = True
XAXIS_ARROW_MUTSCALE = 40       # Arrowhead size
XAXIS_ARROW_LINEWIDTH = 5     # Axis line width
XAXIS_ARROW_EXTRA_DAYS = -180   # Extra margin for arrow tip (days), extends to around the middle of 2025
XAXIS_ARROW_LEFT_EXTRA_DAYS = 90  # How many days to extend to the left (positive extends left), extended by 90 days to cover 2022 from the start
FORCE_RIGHT_YEAR = 2025         # Extend axis label and arrow at least to this year (None to disable)
HIDE_BOX_SPINES = True          # Hide box spines
HIDE_X_TICKS = True             # Hide original x-axis tick lines and marks (year numbers are displayed as text along the bottom edge)

# ============================

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def _setup_font() -> FontProperties:
    rcParams['axes.unicode_minus'] = False
    try:
        rcParams['svg.fonttype'] = 'path' if SVG_TEXT_AS_PATH else 'none'
        # Embed text as is as much as possible (effective in some Matplotlib environments)
        rcParams['text.usetex'] = False
    except Exception:
        pass
    if FONT_PATH:
        p = Path(FONT_PATH)
        if p.exists():
            try:
                fm.fontManager.addfont(str(p))
                fp = FontProperties(fname=str(p))
                rcParams['font.family'] = fp.get_name()
                return fp
            except Exception:
                pass
    for name in ["IPAexGothic","Noto Sans CJK JP","Noto Sans JP","Yu Gothic","Meiryo","Hiragino Sans","MS Gothic","TakaoGothic"]:
        if name in {f.name for f in fm.fontManager.ttflist}:
            rcParams['font.family'] = name
            return FontProperties(family=name)
    return FontProperties(family=rcParams.get('font.family', 'sans-serif'))

# -------- no normalization/parsing --------
_ZW_CHARS = "".join(["\u200B","\u200C","\u200D","\uFEFF"])
_PUNCT_TAIL = r"[.\u3002\uFF0E,\uFF0C;\uFF1B:\uFF1A、。．；：]+$"
_SPLIT_RE = re.compile(r"[;,、，]+")
_WS = re.compile(r"\s+")

def canon_key(name: str) -> str:
    if name is None or (isinstance(name, float) and math.isnan(name)): return ""
    s = str(name)
    s = unicodedata.normalize("NFKC", s)
    s = s.translate({ord(c): None for c in _ZW_CHARS})
    s = s.replace("\u00A0"," ").strip().strip('"').strip("'").strip()
    s = s.replace("—","-").replace("–","-").replace("―","-").replace("‐","-")
    s = s.replace("_"," ").replace("&"," and ").replace("＆"," and ")
    s = re.sub(r"\s*/\s*","/", s)
    s = re.sub(_PUNCT_TAIL,"", s)
    s = _WS.sub(" ", s).strip()
    return s.casefold()

def normalize_dbname(name: str) -> str:
    if pd.isna(name): return ""
    return str(name).strip().strip('"').strip("'")

def parse_ref_list(cell) -> List[str]:
    if pd.isna(cell): return []
    raw = str(cell).strip()
    NA = {"na","n/a","none","null","nan","-","—",""," ",
          "なし","無し","不明","unknown","not available","no data",
          "db_a","db_b","dba","dbb","db a","db b"}
    if raw.lower() in NA: return []
    items = [normalize_dbname(x) for x in _SPLIT_RE.split(raw)]
    out = []
    for t in items:
        t = t.strip().strip('"').strip("'")
        if not t or t.lower() in NA: continue
        out.append(t)
    return out

def try_parse_date(s: str):
    if pd.isna(s) or str(s).strip()=="":
        return None
    t = str(s).strip()
    try:
        t2 = (t.replace("年","-").replace("月","-").replace("日","")
                .replace(".","-").replace("/","-"))
        parts = t2.split("-")
        if len(parts)==2: t2 = f"{parts[0]}-{parts[1]}-01"
        return datetime.fromisoformat(t2)
    except Exception:
        pass
    for f in ["%Y-%m-%d","%Y/%m/%d","%Y.%m.%d","%Y-%m","%Y/%m","%Y.%m","%Y%m%d"]:
        try:
            dt = datetime.strptime(t,f)
            if f in ("%Y-%m","%Y/%m","%Y.%m"): dt = dt.replace(day=1)
            return dt
        except Exception:
            continue
    return None

def pick_earliest(row: pd.Series):
    cands = []
    for col in ["earlist","earliest"]:
        if col in row and not pd.isna(row[col]):
            dt = try_parse_date(row[col]); dt and cands.append(dt)
    for col in ["preprint","publish","internet_archive","archive","posted","first_seen"]:
        if col in row and not pd.isna(row[col]):
            dt = try_parse_date(row[col]); dt and cands.append(dt)
    return min(cands) if cands else None

# -------- Graph construction --------
def build_graph(history_df: pd.DataFrame, errors_df: pd.DataFrame):
    G = nx.DiGraph()
    name_col = None
    for cand in ["Database_name","database_name","DB","Name"]:
        if cand in history_df.columns: name_col = cand; break
    if not name_col: raise ValueError("Database_name column not found.")

    citing_col = "citing" if "citing" in history_df.columns else None
    ds_col     = "data_source" if "data_source" in history_df.columns else None

    bad_name_rows = []
    for idx, row in history_df.iterrows():
        raw = normalize_dbname(row[name_col])
        if _SPLIT_RE.search(raw):
            bad_name_rows.append({"row_index": idx, "raw_name": raw})

    NAME_CANON_TO_DISPLAY = {}
    for _, row in history_df.iterrows():
        raw = normalize_dbname(row[name_col])
        key = canon_key(raw)
        if not key: continue
        disp = NAME_CANON_TO_DISPLAY.setdefault(key, raw)
        dt = pick_earliest(row)
        if G.has_node(key):
            prev = G.nodes[key].get("earliest")
            if prev is None or (dt is not None and dt < prev):
                G.nodes[key]["earliest"] = dt
        else:
            G.add_node(key, label=disp, earliest=dt)

    VALID = set(G.nodes())
    skipped = []

    def add_edge(a_key: str, b_key: str, kind: str):
        if not a_key or not b_key or a_key == b_key: return
        if b_key not in VALID:
            skipped.append({"from": a_key, "to": b_key, "kind": kind, "reason":"unknown_target"}); return
        if a_key not in VALID:
            skipped.append({"from": a_key, "to": b_key, "kind": kind, "reason":"unknown_source"}); return
        # Supply b → Use a
        src, dst = b_key, a_key
        if G.has_edge(src, dst):
            kinds = set(G[src][dst].get("kinds", [])); kinds.add(kind)
            G[src][dst]["kinds"] = sorted(kinds)
            G[src][dst]["count"] = G[src][dst].get("count", 0) + 1
        else:
            G.add_edge(src, dst, kinds=[kind], count=1)

    for _, row in history_df.iterrows():
        a_key = canon_key(normalize_dbname(row[name_col]))
        if not a_key: continue
        if citing_col:
            for b_raw in parse_ref_list(row[citing_col]):
                add_edge(a_key, canon_key(b_raw), "citing")
        if ds_col:
            for b_raw in parse_ref_list(row[ds_col]):
                add_edge(a_key, canon_key(b_raw), "data_source")

    if not errors_df.empty:
        colA=colB=colC=None
        for c in ["DB_A","db_a","A"]:
            if c in errors_df.columns: colA=c; break
        for c in ["DB_B","db_b","B"]:
            if c in errors_df.columns: colB=c; break
        for c in ["shared_err_count","shared_error_count","err_shared","count"]:
            if c in errors_df.columns: colC=c; break
        if colA and colB and colC:
            for _, r in errors_df.iterrows():
                a_raw = "" if pd.isna(r[colA]) else str(r[colA])
                b_raw = "" if pd.isna(r[colB]) else str(r[colB])
                ak, bk = canon_key(a_raw), canon_key(b_raw)
                if not ak or not bk or pd.isna(r[colC]): continue
                try:
                    val = float(r[colC])
                except Exception:
                    continue
                if val <= 0: continue

                if CREATE_NODES_FROM_ERRORS:
                    if ak and ak not in G.nodes: G.add_node(ak, label=normalize_dbname(a_raw), earliest=None)
                    if bk and bk not in G.nodes: G.add_node(bk, label=normalize_dbname(b_raw), earliest=None)

                updated = False
                if G.has_edge(ak, bk):
                    G[ak][bk]["shared_err_count"] = G[ak][bk].get("shared_err_count",0)+val; updated=True
                if G.has_edge(bk, ak):
                    G[bk][ak]["shared_err_count"] = G[bk][ak].get("shared_err_count",0)+val; updated=True
                if not updated and CREATE_HEAT_ONLY_EDGES:
                    u, v = (ak, bk) if ak <= bk else (bk, ak)
                    if u in G.nodes and v in G.nodes:
                        G.add_edge(u, v, kinds=["heat_only"], count=0, shared_err_count=val)

    if WRITE_AUDIT:
        ensure_dir(Path(OUTPUT_DIR))
        if bad_name_rows:
            pd.DataFrame(bad_name_rows).to_csv(Path(OUTPUT_DIR)/"bad_database_names.csv", index=False)
            warnings.warn("There are rows in Database_name containing delimiters (,;/). Please check bad_database_names.csv.")
        if 'skipped' in locals() and skipped:
            pd.DataFrame(skipped).to_csv(Path(OUTPUT_DIR)/"skipped_unknown_references.csv", index=False)

    # Normalize earliest type (all unified to naive)
    for n, d in G.nodes(data=True):
        d["earliest"] = _to_naive_datetime(d.get("earliest"))


    nodes_df = pd.DataFrame([{
        "Database_name": G.nodes[n].get("label", n),
        "internal_key": n,
        "earliest": (G.nodes[n].get("earliest") or pd.NaT),
    } for n in G.nodes()]).sort_values(by=["earliest","Database_name"], na_position="last")

    edges_df = pd.DataFrame([{
        "source": G.nodes[u].get("label", u),
        "target": G.nodes[v].get("label", v),
        "source_key": u,
        "target_key": v,
        "kinds": ";".join(G[u][v].get("kinds", [])),
        "count": G[u][v].get("count", 1),
        "shared_err_count": G[u][v].get("shared_err_count", 0.0),
    } for u, v in G.edges()]).sort_values(["source","target"])

    return G, nodes_df, edges_df

# -------- Utilities --------
def _time_bin(dt, unit="M"):
    if dt is None: return None
    if isinstance(dt, pd.Timestamp): dt = dt.to_pydatetime()
    if unit == "Y": return (dt.year, 1)
    if unit == "D": return (dt.year, dt.month, dt.day)
    return (dt.year, dt.month)

def debug_layers(G, unit):
    bins = []
    for _, d in G.nodes(data=True):
        dt = d.get("earliest")
        if dt is None: continue
        bins.append(_time_bin(dt, unit))
    c = Counter(bins)
    print(f"[DEBUG] unit={unit} 層数={len(c)} 例: {list(c.items())[:10]}")
    return len(c), list(c.keys())

# -------- Vertical de-collision of nearby nodes (x fixed) --------
def spread_nearby_nodes_in_y(pos: Dict[str, Tuple[float, float]],
                             near_x_days=NEAR_X_DAYS,
                             min_y_gap=MIN_Y_GAP_NEAR_X,
                             passes=Y_SPREAD_PASSES,
                             cooling=Y_SPREAD_COOLING) -> Dict[str, Tuple[float, float]]:
    """Keep x fixed, apply vertical repulsion to pairs with close x to spread out dense clusters."""
    if not pos: return pos
    keys = list(pos.keys())
    xs = np.array([pos[k][0] for k in keys], dtype=float)
    ys = np.array([pos[k][1] for k in keys], dtype=float)

    # Bins refer to "±1" simultaneously to capture local clusters (allowing overlap)
    bin_w = float(near_x_days)
    bins = defaultdict(list)
    for i, x in enumerate(xs):
        b = int(round(x / bin_w))
        bins[b].append(i); bins[b-1].append(i); bins[b+1].append(i)

    for p in range(int(passes)):
        moved = np.zeros_like(ys)
        cool = (1.0 - cooling * p / max(1, passes-1)) if passes > 1 else 1.0
        for _, idxs in bins.items():
            uniq = sorted(set(idxs), key=lambda i: ys[i])
            if len(uniq) < 2: continue
            for j in range(len(uniq)-1):
                i1, i2 = uniq[j], uniq[j+1]
                if abs(xs[i1] - xs[i2]) <= near_x_days:
                    dy = ys[i2] - ys[i1]
                    if dy < min_y_gap:
                        push = (min_y_gap - dy) * 0.5 * cool
                        moved[i1] -= push
                        moved[i2] += push
        ys += moved
        ys -= np.mean(ys)
    return {k: (xs[i], float(ys[i])) for i, k in enumerate(keys)}

# -------- Layout: time_optim (x=earliest fixed / y=optimal spread) --------
def layout_time_optim(G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
    # x is fixed by earliest using date2num
    dates = [d.get("earliest") for _, d in G.nodes(data=True) if d.get("earliest") is not None]
    default_x = (date2num(min(dates)) - 30) if dates else 0.0
    x_map = {n: (date2num(d.get("earliest")) if d.get("earliest") is not None else default_x)
             for n, d in G.nodes(data=True)}

    # y is initialized by spring_layout (undirected) → centering
    pos0 = None
    if HYBRID_USE_INIT_POS:
        rng = random.Random(SPRING_SEED if SPRING_SEED is not None else 42)
        pos0 = {n: (0.0, rng.uniform(-0.05, 0.05)) for n in G.nodes()}
    pos_s = nx.spring_layout(
        G.to_undirected(),
        k=HYBRID_SPRING_K,
        iterations=HYBRID_SPRING_ITER,
        seed=SPRING_SEED,
        pos=pos0,
        scale=HYBRID_SPRING_SCALE_Y
    )
    ys = [pos_s[n][1] for n in G.nodes()] if G.number_of_nodes() else [0.0]
    y_mean = sum(ys) / len(ys) if ys else 0.0
    pos = {n: (x_map[n], pos_s[n][1] - y_mean) for n in G.nodes()}

    # Apply vertical repulsion (thinning) to nodes with close x multiple passes
    pos = spread_nearby_nodes_in_y(pos,
                                   near_x_days=NEAR_X_DAYS,
                                   min_y_gap=MIN_Y_GAP_NEAR_X,
                                   passes=Y_SPREAD_PASSES,
                                   cooling=Y_SPREAD_COOLING)
    return pos

# -------- Layout: spring (traditional: x=earliest fixed / y=spring only) --------
def layout_timeline_forcey(G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
    dates = [d.get("earliest") for _, d in G.nodes(data=True) if d.get("earliest") is not None]
    default_x = (date2num(min(dates)) - 30) if dates else 0.0
    x_map = {n: (date2num(d.get("earliest")) if d.get("earliest") is not None else default_x)
             for n, d in G.nodes(data=True)}
    pos0 = None
    if HYBRID_USE_INIT_POS:
        rng = random.Random(SPRING_SEED if SPRING_SEED is not None else 42)
        pos0 = {n: (0.0, rng.uniform(-0.05, 0.05)) for n in G.nodes()}
    pos_s = nx.spring_layout(
        G.to_undirected(),
        k=HYBRID_SPRING_K,
        iterations=HYBRID_SPRING_ITER,
        seed=SPRING_SEED,
        pos=pos0,
        scale=HYBRID_SPRING_SCALE_Y
    )
    ys = [pos_s[n][1] for n in G.nodes()] if G.number_of_nodes() else [0.0]
    y_mean = sum(ys) / len(ys) if ys else 0.0
    return {n: (x_map[n], pos_s[n][1] - y_mean) for n in G.nodes()}

# -------- Layout: barycenter (time layers) / hierarchy (supply layers) --------
def layout_timeline_barycenter(G: nx.DiGraph, unit="M", iters=16, gap=1.2):
    dates = [d.get("earliest") for _, d in G.nodes(data=True) if d.get("earliest") is not None]
    default_x = (date2num(min(dates)) - 30) if dates else 0.0
    x_map = {n: (date2num(d.get("earliest")) if d.get("earliest") is not None else default_x)
             for n, d in G.nodes(data=True)}
    layers = defaultdict(list)
    for n, d in G.nodes(data=True):
        layers[_time_bin(d.get("earliest"), unit)].append(n)
    keys = sorted(layers.keys(), key=lambda k: (9999,99,99) if k is None else tuple(k))
    init_y = nx.spring_layout(G.to_undirected(), seed=SPRING_SEED, k=HYBRID_SPRING_K)
    order = {k: sorted(layers[k], key=lambda n: init_y.get(n,(0,0))[1]) for k in keys}
    Und = G.to_undirected()
    def _median_index(target_nodes, ref_nodes):
        idx_ref = {n:i for i,n in enumerate(ref_nodes)}
        med = {}
        for n in target_nodes:
            idxs = [idx_ref[m] for m in Und.neighbors(n) if m in idx_ref]
            med[n] = (np.median(idxs) if idxs else np.inf)
        return med
    for _ in range(iters):
        for i in range(1, len(keys)):
            prev, cur = keys[i-1], keys[i]
            med = _median_index(order[cur], order[prev])
            order[cur] = sorted(order[cur], key=lambda n: med[n])
        for i in range(len(keys)-2, -1, -1):
            nxt, cur = keys[i+1], keys[i]
            med = _median_index(order[cur], order[nxt])
            order[cur] = sorted(order[cur], key=lambda n: med[n])
    layer_y = {}
    center = (len(keys) - 1) / 2.0 if VERTICAL_BANDS_BY_TIME else 0.0
    for i, k in enumerate(keys):
        band = 0.0
        if VERTICAL_BANDS_BY_TIME:
            band = (i - center) * TIME_BAND_STEP
            if TIME_BAND_ZIGZAG:
                band *= (1 if (i % 2 == 0) else -1)
        layer_y[k] = band
    pos = {}
    for k in keys:
        nodes = order[k]
        for idx, n in enumerate(nodes):
            y_base = idx * gap
            if YEAR_SUBLAYERS and unit == "Y":
                dt = G.nodes[n].get("earliest")
                if isinstance(dt, pd.Timestamp): dt = dt.to_pydatetime()
                sub = 0
                if isinstance(dt, datetime):
                    sub = min(YEAR_SUBLAYERS_K-1, (dt.month-1) * YEAR_SUBLAYERS_K // 12)
                y_base += (sub - (YEAR_SUBLAYERS_K-1)/2.0) * YEAR_SUBLAYER_Y_OFFSET
            y_base += layer_y[k]
            pos[n] = (x_map[n], y_base)
    ys = [p[1] for p in pos.values()] or [0.0]
    y_mean = sum(ys)/len(ys)
    return {n: (pos[n][0], pos[n][1]-y_mean) for n in pos}

def layout_hierarchy_by_datasource(G: nx.DiGraph,
                                   layer_step=3.0,
                                   intra_gap=1.0,
                                   iters=12) -> Dict[str, Tuple[float, float]]:
    dates = [d.get("earliest") for _, d in G.nodes(data=True) if d.get("earliest") is not None]
    default_x = (date2num(min(dates)) - 30) if dates else 0.0
    x_map = {n: (date2num(d.get("earliest")) if d.get("earliest") is not None else default_x)
             for n, d in G.nodes(data=True)}
    H = nx.DiGraph(); H.add_nodes_from(G.nodes())
    for u, v, d in G.edges(data=True):
        kinds = set(d.get("kinds", []))
        if "data_source" in kinds:
            H.add_edge(u, v)
    if H.number_of_edges() == 0:
        return layout_timeline_forcey(G)
    sccs = list(nx.strongly_connected_components(H))
    comp_index = {n:i for i, comp in enumerate(sccs) for n in comp}
    C = nx.DiGraph(); C.add_nodes_from(range(len(sccs)))
    for u, v in H.edges():
        cu, cv = comp_index[u], comp_index[v]
        if cu != cv: C.add_edge(cu, cv)
    level = {c: 0 for c in C.nodes()}
    for gen in nx.topological_generations(C):
        for node in gen:
            preds = list(C.predecessors(node))
            if preds:
                level[node] = max(level[p] for p in preds) + 1
    node_level = {n: level[comp_index[n]] for n in G.nodes()}
    max_level = max(node_level.values()) if node_level else 0
    Und = H.to_undirected()
    layers = defaultdict(list)
    for n, lv in node_level.items():
        layers[lv].append(n)
    keys = list(range(max_level+1))
    order = {lv: sorted(layers[lv], key=lambda n: x_map[n]) for lv in keys}
    def _median_index(target_nodes, ref_nodes):
        idx_ref = {n:i for i,n in enumerate(ref_nodes)}
        med = {}
        for n in target_nodes:
            idxs = [idx_ref[m] for m in Und.neighbors(n) if m in idx_ref]
            med[n] = (np.median(idxs) if idxs else np.inf)
        return med
    for _ in range(iters):
        for i in range(1, len(keys)):
            prev, cur = keys[i-1], keys[i]
            med = _median_index(order[cur], order[prev])
            order[cur] = sorted(order[cur], key=lambda n: med[n])
        for i in range(len(keys)-2, -1, -1):
            nxt, cur = keys[i+1], keys[i]
            med = _median_index(order[cur], order[nxt])
            order[cur] = sorted(order[cur], key=lambda n: med[n])
    pos = {}
    for lv in keys:
        for idx, n in enumerate(order[lv]):
            y = lv * layer_step + idx * intra_gap
            pos[n] = (x_map[n], y)
    ys = [p[1] for p in pos.values()] or [0.0]
    y_mean = sum(ys)/len(ys)
    return {n: (pos[n][0], pos[n][1]-y_mean) for n in pos}

# -------- Manual offset -------- this is a simplified version and commented out
#def apply_pos_nudges(G, pos, csv_path=POS_NUDGE_CSV):
#    p = Path(csv_path)
#    if not p.exists():
#        return pos
#    try:
#        df = pd.read_csv(p)
#    except Exception:
#        return pos
#    for _, r in df.iterrows():
#        key = str(r.get("internal_key", "")).strip()
#        if not key and not pd.isna(r.get("Database_name", None)):
#            name = str(r["Database_name"]).strip()
#            matched = [n for n,d in G.nodes(data=True) if d.get("label","")==name]
#            if matched: key = matched[0]
#            else: continue
#        if key in pos:
#            try:
#                dx = float(r.get("dx", 0.0)); dy = float(r.get("dy", 0.0))
#            except Exception:
#                dx, dy = 0.0, 0.0
#            x, y = pos[key]; pos[key] = (x + dx, y + dy)
#    return pos

# -------- Curvature (loose bundling: edge drawing remains traditional) --------
#def_time_bin has already been set, therefore this block is commented out
#def _time_bin(dt, unit="M"):
#    if dt is None: return None
#    if isinstance(dt, pd.Timestamp): dt = dt.to_pydatetime()
#    if unit == "Y": return (dt.year, 1)
#    if unit == "D": return (dt.year, dt.month, dt.day)
#    return (dt.year, dt.month)

def _build_edge_curvatures(G, unit="M"):
    if not EDGE_GROUP_BUNDLE:
        return defaultdict(lambda: EDGE_CURVE_BASE)

    def _bin_of(n):
        dt = G.nodes[n].get("earliest")
        return _time_bin(dt, unit)

    groups = defaultdict(list)
    for u, v in G.edges():
        groups[(_bin_of(u), _bin_of(v))].append((u, v))

    curv = {}
    for gid, edges in groups.items():
        n = len(edges)
        edges_sorted = sorted(edges)
        for i, (u, v) in enumerate(edges_sorted):
            if n <= 1:
                base = EDGE_CURVE_BASE
            else:
                off = i - (n-1)/2.0
                frac = off / max(1, (n-1)/2.0)
                base = EDGE_CURVE_BASE + EDGE_CURVE_SPREAD * frac

            du = G.nodes[u].get("earliest"); dv = G.nodes[v].get("earliest")
            if isinstance(du, pd.Timestamp): du = du.to_pydatetime()
            if isinstance(dv, pd.Timestamp): dv = dv.to_pydatetime()
            tweak = 0.0
            if isinstance(du, datetime) and isinstance(dv, datetime):
                month_delta = (dv.year - du.year) * 12 + (dv.month - du.month)
                tweak = max(-0.04, min(0.04, month_delta/24.0))
            curv[(u, v)] = base + tweak

    return defaultdict(lambda: EDGE_CURVE_BASE, curv)

def apply_pos_nudges(G, pos, csv_path=POS_NUDGE_CSV):
    p = Path(csv_path)
    if not p.exists():
        print("[pos_nudge] not found:", p)
        return pos

    try:
        df = pd.read_csv(p)
    except Exception as e:
        print("[pos_nudge] read_csv error:", e)
        return pos

    logs = []
    newpos = dict(pos)
    for _, r in df.iterrows():
        raw_key = str(r.get("internal_key", "")).strip()
        used_key = ""
        matched_by = ""

        if raw_key:
            used_key = raw_key
            matched_by = "internal_key"
        elif not pd.isna(r.get("Database_name", None)):
            name = str(r["Database_name"]).strip()
            cand = [n for n,d in G.nodes(data=True) if d.get("label","") == name]
            if cand:
                used_key = cand[0]
                matched_by = "Database_name"

        try:
            dx = float(str(r.get("dx", 0)).strip())
            dy = float(str(r.get("dy", 0)).strip())
        except Exception:
            dx, dy = 0.0, 0.0

        status = "skipped:not_found"
        if used_key in newpos:
            x, y = newpos[used_key]
            newpos[used_key] = (x + dx, y + dy)
            status = "applied"

        logs.append({
            "raw_internal_key": raw_key,
            "Database_name": str(r.get("Database_name", "")),
            "matched_key": used_key,
            "matched_by": matched_by,
            "dx": dx, "dy": dy,
            "status": status
        })

    try:
        ensure_dir(Path(OUTPUT_DIR))
        pd.DataFrame(logs).to_csv(Path(OUTPUT_DIR) / "pos_nudge_audit.csv", index=False)
        print("[pos_nudge] audit ->", Path(OUTPUT_DIR) / "pos_nudge_audit.csv")
    except Exception as e:
        print("[pos_nudge] audit write error:", e)

    return newpos

# -------- Drawing --------
def plot_graph(G: nx.DiGraph, pos: Dict[str, Tuple[float, float]], out_path: Path, layout_mode="time_optim"):
    fp = _setup_font()
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=DPI)

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    if xs:
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = (min(ys), max(ys)) if ys else (0.0, 1.0)
        ax.set_xlim(xmin - PAD_DAYS, xmax + PAD_DAYS)
        yr = max(1e-9, ymax - ymin)
        ax.set_ylim(ymin - yr*PAD_FRAC_Y, ymax + yr*PAD_FRAC_Y)
        x0_dt = _num2date_naive(xmin)
        x1_dt = _num2date_naive(xmax)

        # === x-axis (year) labeling ===
        if SHOW_YEAR_TICKS:
            ax.xaxis.set_major_locator(YearLocator(base=YEAR_TICK_STEP))
            ax.xaxis.set_major_formatter(DateFormatter(YEAR_FORMAT))
        if SHOW_YEAR_GRID:
            ax.grid(axis='x', which='major', alpha=YEAR_GRID_ALPHA)
        if SHOW_YEAR_BANDS:
            y_start = x0_dt.year
            y_end   = x1_dt.year + 1
            for y in range(y_start, y_end):
                x_left  = date2num(datetime(y, 1, 1))
                x_right = date2num(datetime(y + 1, 1, 1))
                if y % 2 == 0:
                    ax.axvspan(x_left, x_right, color="gray", alpha=YEAR_BAND_ALPHA, zorder=0)

        # === Draw x-axis as arrow ===
        if XAXIS_AS_ARROW and xs:
            # Arrow start and end points (x in Data coordinates, y in Axes coordinates with 0=bottom)
            trans = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)

            x_arrow_start = xmin - XAXIS_ARROW_LEFT_EXTRA_DAYS
            # The right end of the arrow is the larger of the data maximum or the end of FORCE_RIGHT_YEAR plus margin
            x_force_right = date2num(datetime(FORCE_RIGHT_YEAR, 12, 31)) if FORCE_RIGHT_YEAR else xmax
            x_arrow_end = max(xmax, x_force_right) + XAXIS_ARROW_EXTRA_DAYS

            ax.annotate(
                "", xy=(x_arrow_end, 0), xytext=(x_arrow_start, 0),
                xycoords=trans, textcoords=trans,
                arrowprops=dict(
                arrowstyle="-|>",
                mutation_scale=XAXIS_ARROW_MUTSCALE,
                lw=XAXIS_ARROW_LINEWIDTH,
                shrinkA=0, shrinkB=0,
                joinstyle="miter", 
                color="black"
                ),
                annotation_clip=False  # draw even if it goes outside the axis
            )

            x_left, x_right = ax.get_xlim()
            ax.set_xlim(x_left, max(x_right, x_arrow_end))

            # Remove box spines and existing ticks to eliminate the "box"
            if HIDE_BOX_SPINES:
                for side in ["top", "right", "left", "bottom"]:
                    ax.spines[side].set_visible(False)
            if HIDE_X_TICKS:
                ax.tick_params(axis='x', length=0)  # Remove tick marks

        # ★ Force the rightmost year to be at least FORCE_RIGHT_YEAR
        if FORCE_RIGHT_YEAR:
            x1_dt_for_labels = max(x1_dt, datetime(FORCE_RIGHT_YEAR, 1, 1))
        else:
            x1_dt_for_labels = x1_dt

        y_start = x0_dt.year
        y_end   = x1_dt_for_labels.year + 1 # ← x1_dt_for_labels is used rather than x1_dt

        trans = ax.get_xaxis_transform()  # x=data, y=axes blended transform
        y_ax  = YEAR_NUMBER_OFFSET_AX  # axis coordinates (0=bottom, 1=top)

        for y in range(y_start, y_end):
            if (y - y_start) % YEAR_NUMBER_STEP != 0:
                continue
            if YEAR_NUMBERS_AT == "lines":
                x_pos = date2num(datetime(y, 1, 1))
            else:  # "mid"
                x_pos = date2num(datetime(y, 7, 1))  # setting to the middle of the year

            ax.text(
                x_pos, y_ax, f"{y}",
                transform=trans,
                ha='center', va='bottom',
                fontsize=YEAR_NUMBER_FONTSIZE,
                rotation=YEAR_NUMBER_ROTATE
             )
    else:
        ax.margins(x=0.05, y=0.1)

    if SHOW_XLABEL:
        ax.set_xlabel(XLABEL_TEXT, fontsize=XLABEL_FONTSIZE)

    # Background stripes (to visualize layers in barycenter)
    if layout_mode.lower() == "barycenter" and VERTICAL_BANDS_BY_TIME:
        bins = {}
        for n, d in G.nodes(data=True):
            dt = d.get("earliest")
            key = _time_bin(dt, TIME_UNIT)
            bins.setdefault(key, []).append(n)
        keys = sorted(bins.keys(), key=lambda k: (9999,99,99) if k is None else tuple(k))
        center = (len(keys) - 1) / 2.0 if keys else 0.0
        max_nodes_in_layer = max((len(bins[k]) for k in keys), default=1)
        layer_height = max(1.0, BARYCENTER_GAP * max_nodes_in_layer)
        for k_i, k in enumerate(keys):
            band = (k_i - center) * TIME_BAND_STEP
            if TIME_BAND_ZIGZAG: band *= (1 if (k_i % 2 == 0) else -1)
            y0 = band - layer_height*0.55
            y1 = band + layer_height*0.55
            ax.axhspan(y0, y1, alpha=0.05, color="gray")

    # Edge classification
    cite_edges, data_edges, both_edges = [], [], []
    for u, v, d in G.edges(data=True):
        kinds = set(d.get("kinds", []))
        if "citing" in kinds and "data_source" in kinds:
            both_edges.append((u, v))
        elif "data_source" in kinds:
            data_edges.append((u, v))
        elif "citing" in kinds:
            cite_edges.append((u, v))

    # heat normalization
    vals = [float(G[u][v].get("shared_err_count", 0.0)) for u, v in G.edges()]
    vmax = 1.0
    if vals:
        vmax = max(1.0, float(np.percentile(vals, 95)) if HEAT_VMAX_MODE == "p95" else max(vals))
    norm = mcolors.Normalize(vmin=0.0, vmax=vmax)
    cmap = matplotlib.colormaps.get_cmap(HEAT_CMAP_NAME)

    # === Color scale bar setting (inherit alpha as much as possible)===
    try:
        # Create a ListedColormap with fixed alpha for the colorbar
        _colors = cmap(np.linspace(0, 1, 256))
        _colors[:, -1] = HEAT_ALPHA  # the same transparency as shared error bands
        cmap_for_cb = mcolors.ListedColormap(_colors)
    except Exception:
        # If it fails, use the raw cmap (appearance will be opaque)
        cmap_for_cb = cmap

    mappable = cm.ScalarMappable(norm=norm, cmap=cmap_for_cb)
    mappable.set_array([])  # may be needed for older Matplotlib versions

    # Add a faint colorbar on the right side (pad/fraction minimize layout impact)
    cbar = fig.colorbar(
        mappable, ax=ax,
        location="right",
        pad=0.02,        # space between axis and colorbar
        fraction=0.035   # colorbar width
    )
    # Label (note when p95-capped)
    _cap_note = " (p95-capped)" if HEAT_VMAX_MODE == "p95" else ""
    cbar.set_label(f"Shared errors{_cap_note}", rotation=90, fontsize=20) 
    # Ticks are automatic, but ensure starting at 0
    try:
        ticks = cbar.get_ticks()
        if ticks is not None and len(ticks) > 0 and ticks[0] > 0:
            cbar.set_ticks([0] + list(ticks))
    except Exception:
        pass

    cbar.ax.tick_params(labelsize=16) 
    

    node_radius_pts = 0.5 * math.sqrt(NODE_SIZE * NODE_SIZE_SCALE) + 2.0 # unify the appearance after scaling

    def _heat_color_and_width(u, v):
        val = float(G[u][v].get("shared_err_count", 0.0))
        if val > 0:
            rgba = list(cmap(norm(val))); rgba[3] = HEAT_ALPHA
            w = HEAT_LINE_BASE + HEAT_LINE_GAIN * math.sqrt(val)
        else:
            rgba = (0,0,0,0); w = 0.0
        return tuple(rgba), w

    curv_map = _build_edge_curvatures(G, unit=TIME_UNIT)

    overlay_drawn = [] # used to control drawing order
    def _draw_edge(u, v, style, color, width, alpha, curve):
        conn = (f"arc3,rad={curve}" if curve else None)
        # thick line (heat)
        color_heat, w_heat = _heat_color_and_width(u, v)
        if w_heat > 0:
            try:
                nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=ax,
                    arrows=True, arrowstyle="-", style="solid",
                    width=w_heat, edge_color=color_heat,
                    connectionstyle=conn, arrowsize=1,
                    min_source_margin=node_radius_pts, min_target_margin=node_radius_pts)
            except TypeError:
                nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=ax,
                    arrows=True, arrowstyle="-", style="solid",
                    width=w_heat, edge_color=color_heat,
                    connectionstyle=conn, arrowsize=1)
        # thin line (overlay)
        try:
            nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=ax,
                arrows=True, arrowstyle="-|>",
                style=style, width=width, edge_color=color, alpha=alpha,
                connectionstyle=conn, arrowsize=ARROWSIZE,
                min_source_margin=node_radius_pts, min_target_margin=node_radius_pts)
        except TypeError:
            nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=ax,
                arrows=True, arrowstyle="-|>",
                style=style, width=width, edge_color=color, alpha=alpha,
                connectionstyle=conn, arrowsize=ARROWSIZE)
        
        overlay_drawn.append((u, v))

    # data_source (solid line) + both first
    for (u, v) in (data_edges + both_edges):
        _draw_edge(u, v, style="solid", color=(0.05,0.05,0.05),
                   width=OVERLAY_WIDTH_DS, alpha=DATASRC_ALPHA, curve=curv_map[(u,v)])
    # citing (dotted line)
    for (u, v) in cite_edges:
        _draw_edge(u, v, style="dotted", color=(0.18,0.18,0.18),
                   width=OVERLAY_WIDTH_CT, alpha=CITING_ALPHA, curve=curv_map[(u,v)])

    # heat_only (band only)
    heat_only_edges = [(u, v) for u, v, d in G.edges(data=True) if "heat_only" in set(d.get("kinds", []))]
    for (u, v) in heat_only_edges:
        conn = (f"arc3,rad={curv_map[(u,v)]}" if curv_map else None)
        color, w = _heat_color_and_width(u, v)
        if w > 0:
            try:
                nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=ax,
                    arrows=True, arrowstyle="-", style="solid", width=w, edge_color=color,
                    connectionstyle=conn, arrowsize=1,
                    min_source_margin=node_radius_pts, min_target_margin=node_radius_pts)
            except TypeError:
                nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=ax,
                    arrows=True, arrowstyle="-", style="solid", width=w, edge_color=color,
                    connectionstyle=conn, arrowsize=1)
    
    # === overlay (solid and dotted lines) arrows to front ===
    for p in ax.patches:
        if isinstance(p, FancyArrowPatch):
            style = p.get_arrowstyle()
            # Different attributes depending on ArrowStyle type, so safely check with string
            if "-|>" in str(style):
                p.set_zorder(10)

    # --- Add legend ---
    legend_elements = [
        # citation + data resource (solid line)
        Line2D(
            [0,1], [0,0],
            color=(0.05, 0.05, 0.05),
            lw=OVERLAY_WIDTH_DS,
            linestyle="solid",
            marker=r"$\rightarrow$",
            markersize=12,
            markevery=[1],
            label="citation + data resource (from data source → user)"
        ),

        # citation only (dotted line)
        Line2D(
            [0,1], [0,0],
            color=(0.18, 0.18, 0.18),
            lw=OVERLAY_WIDTH_CT,
            linestyle="dotted",
            marker=r"$\rightarrow$",
            markersize=12,
            markevery=[1],
            label="citation only (from cited work → citing work)"
        )
    ]


    ax.legend(handles=legend_elements,
              loc="upper left",  # position can be changed as desired
              frameon=False, 
              fontsize=20)


    # Nodes and labels
    nx.draw_networkx_nodes(
    G, pos, ax=ax,
    node_size=NODE_SIZE * NODE_SIZE_SCALE,
    node_color=BASE_WHITE_NODE,
    edgecolors=EDGE_GRAY,
    linewidths=NODE_EDGE_LINEWIDTH
    )
    und = G.to_undirected(); deg = dict(und.degree())
    labels = {}
    for n, d in G.nodes(data=True):
        if deg.get(n, 0) >= MIN_DEGREE_FOR_LABEL:
            disp = d.get("label", n) or str(n)
            s = (str(disp).replace("\u200B","").replace("\u200C","").replace("\u200D","").replace("\uFEFF","").strip())
            if not s: s = str(n)
            if len(s) > LABEL_MAXLEN: s = s[:LABEL_MAXLEN-1] + "…"
            labels[n] = s
    try:
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=LABEL_FONT_SIZE, fontproperties=fp, ax=ax)
    except Exception:
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=LABEL_FONT_SIZE, font_family=fp.get_name(), ax=ax)

    # Axis: even with time_optim, draw time series (x-axis) as dates
    fig.autofmt_xdate()
    ax.xaxis_date()
    ax.set_yticks([])

    # Disable clipping
    for coll in list(ax.collections):
        try: coll.set_clip_on(False); coll.set_clip_box(None)
        except: pass
    for artist in list(ax.patches) + list(ax.artists):
        try: artist.set_clip_on(False); artist.set_clip_box(None)
        except: pass
    for txt in list(ax.texts):
        try: txt.set_clip_on(False); txt.set_clip_box(None)
        except: pass

    ttl = f"Database Network (x=time, layout={layout_mode}"
    if layout_mode.lower()=="barycenter":
        ttl += f", unit={TIME_UNIT}"
    ttl += ")"
    ax.set_title(ttl)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.06)  # recommend: adjust around 0.05 to 0.08
    # PNG (raster)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight", pad_inches=0.25)
    # === Add: SVG (vector; for Inkscape editing) ===
    if EXPORT_SVG:
        svg_path = out_path.with_suffix(".svg") if FIG_SVG is None else (out_path.parent / FIG_SVG)
        # SVG does not require DPI (vector). If white background is not needed, facecolor="none" can be used.
        fig.savefig(svg_path, format="svg", bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


# -------- Main --------
def main(history_xlsx=HISTORY_XLSX, errors_xlsx=ERRORS_XLSX):
    # Temporarily added near the beginning of main -> permanent logging later
    from pathlib import Path
    print("POS_NUDGE_CSV ->", Path(POS_NUDGE_CSV).resolve(), "exists?", Path(POS_NUDGE_CSV).exists())

    ensure_dir(Path(OUTPUT_DIR))
    history_df = pd.read_excel(history_xlsx)
    try:
        errors_df = pd.read_excel(errors_xlsx)
    except Exception:
        warnings.warn(f"{errors_xlsx} could not be loaded. Shared errors are skipped.")
        errors_df = pd.DataFrame()

    G, nodes_df, edges_df = build_graph(history_df, errors_df)

    # Position calculation
    lm = LAYOUT_MODE.lower()
    if lm == "time_optim":
        pos = layout_time_optim(G)
    elif lm == "hierarchy":
        pos = layout_hierarchy_by_datasource(G,
                                             layer_step=HIER_LAYER_STEP_Y,
                                             intra_gap=HIER_INTRA_GAP_Y,
                                             iters=HIER_ITERS)
    elif lm == "barycenter":
        debug_layers(G, TIME_UNIT)
        pos = layout_timeline_barycenter(G, unit=TIME_UNIT, iters=BARYCENTER_ITERS, gap=BARYCENTER_GAP)
    else:
        pos = layout_timeline_forcey(G)

    # Apply manual offset (optional)
    pos = apply_pos_nudges(G, pos, POS_NUDGE_CSV)

    # Drawing
    plot_graph(G, pos, Path(OUTPUT_DIR) / FIG_PNG, layout_mode=lm)

    # Save
    nodes_df.to_csv(Path(OUTPUT_DIR) / NODE_CSV, index=False)
    edges_df.to_csv(Path(OUTPUT_DIR) / EDGE_CSV, index=False)
    with open(Path(OUTPUT_DIR) / GRAPH_PKL, "wb") as f:
        pickle.dump(G, f)

    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    print(f"Saved: {OUTPUT_DIR}/{FIG_PNG}")
    if EXPORT_SVG:
        print(f"Saved: {OUTPUT_DIR}/{FIG_SVG}")
    print(f"Saved: {OUTPUT_DIR}/{NODE_CSV}, {OUTPUT_DIR}/{EDGE_CSV}, {OUTPUT_DIR}/{GRAPH_PKL}")

if __name__ == "__main__":
    if len(sys.argv)==3:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv)==2:
        main(sys.argv[1], ERRORS_XLSX)
    else:
        main()