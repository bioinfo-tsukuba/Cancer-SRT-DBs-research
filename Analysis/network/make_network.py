# -*- coding: utf-8 -*-
"""
DB–DB network with three panels (fully local):
(A) GSM Jaccard
(B) Actual shared errors (edges), nodes: outer=carriers, inner=carriers∩shared-errors
(C) Carrier Jaccard (edges), nodes: outer=carriers only

【仕様】
- 誤りペアは `cancer_srt_corrections` の "A -> B" を優先（後方互換: `metadata_errors` の 1{"A";"B"}）。
- GSM は `original_data_source_1..5` を総なめ（後方互換: `original data sources`）。
- `unverified_flag == "not_confirmed"` は除外。
- 出力は out_networks/ 以下（PNG/SVG/CSV）。完全ローカル実行。
"""

import os, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['svg.fonttype'] = 'none' # SVGでテキストをフォント情報として保存
import networkx as nx

# ============== Config ==============
DATA_XLSX   = "chccsrtdb_analysis.xlsx"
SHEET_NAME  = 0

# 必須カラム
COL_DB      = "Database_name"
COL_UNIT    = "Record_unit"

# 新仕様カラム
COL_CORR    = "cancer_srt_corrections"   # "A -> B" を ; 区切りで複数可
SRC_SPLIT_COLS = [f"original_data_source_{i}" for i in range(1, 6)]
COL_UNVER   = "unverified_flag"          # "not_confirmed" は除外

# 後方互換カラム
COL_ERR_OLD = "metadata_errors"          # 1{"A";"B"} 形式
COL_SRC_OLD = "original data sources"    # セミコロン区切り

OUT_DIR     = "out_networks"
PNG_A       = os.path.join(OUT_DIR, "db_panel_A_jaccard.png")
SVG_A       = os.path.join(OUT_DIR, "db_panel_A_jaccard.svg")
PNG_B       = os.path.join(OUT_DIR, "db_panel_B_errors_dualred_with_base.png")
SVG_B       = os.path.join(OUT_DIR, "db_panel_B_errors_dualred_with_base.svg")
CSV_EDGE    = os.path.join(OUT_DIR, "db_db_error_edge_metrics.csv")
CSV_NODE    = os.path.join(OUT_DIR, "db_error_node_summary_dualred.csv")

# Panel C 出力
PNG_C       = os.path.join(OUT_DIR, "db_panel_C_carry_jaccard_with_base.png")
SVG_C       = os.path.join(OUT_DIR, "db_panel_C_carry_jaccard_with_base.svg")
CSV_EDGE_C  = os.path.join(OUT_DIR, "db_db_carry_edge_metrics.csv")
CSV_NODE_C  = os.path.join(OUT_DIR, "db_carry_node_summary.csv")
# Panel B 追加の出力...追加部分1
CSV_EDGE_B  = os.path.join(OUT_DIR, "db_panel_B_error_edges.csv")               # DBペアごとの共有数（最小改修①相当）
CSV_B_DETAIL = os.path.join(OUT_DIR, "db_panel_B_shared_error_items.csv")       # 明細（DB_A, DB_B, GSM, error_pair）
CSV_B_SUMMARY = os.path.join(OUT_DIR, "db_panel_B_shared_error_summary.csv")    # 明細の再集計（保険）


os.makedirs(OUT_DIR, exist_ok=True)

DO_LOWER, DO_STRIP, DO_NFKC = True, True, False
SEED = 42
K_FOR_LAYOUT = 1.8
SCALE_FOR_LAYOUT = 5
PAD = 0.2

EDGE_MIN_SHARED_GSM = 1
EDGE_MIN_SHARED_ERR = 1

# 背景やノード表示のトグル
SHOW_BASE_GSM_EDGES = True      # AのGSMエッジをB/Cの背景に敷く
SHOW_BASE_TOTAL_NODE = True     # 総GSM（白ノード）をB/Cの背景に描く

# Colors
PINK   = (1.0, 0.71, 0.76, 0.5)   # outer: carriers（B/Cで共通）
RED    = (1.0, 0.08, 0.58, 0.7)   # inner: carriers ∩ shared-error（Bのみ）
OUTLINE_PINK = "none"
OUTLINE_RED  = "none"
BASE_WHITE_NODE = (1, 1, 1)
BASE_GRAY_EDGE  = (0.75, 0.75, 0.75) # 使用されない

# ===== 抽出用パターン =====
PAT_PAIR_OLD_STRICT = re.compile(r'1\{\s*"([^"]*)"\s*;\s*"([^"]*)"\s*\}')
Q = r'["\uFF02\u201C\u201D\u300C\u300D\u300E\u300F]'
PAT_PAIR_OLD_LOOSE  = re.compile(
    rf'[1\uFF11]\s*[\{{\uFF5B]\s*{Q}([^"{Q}]*){Q}\s*[\u003B\uFF1B]\s*{Q}([^"{Q}]*){Q}\s*[\}}\uFF5D]'
)
PAT_ARROW = re.compile(r'^\s*(.*?)\s*->\s*(.*?)\s*$')
PAT_GSM  = re.compile(r"(GSM\d+)", re.IGNORECASE)

# ===== ユーティリティ =====
def normalize_text(s: str) -> str:
    if s is None: return ""
    import unicodedata
    s = str(s)
    if DO_NFKC: s = unicodedata.normalize("NFKC", s)
    if DO_STRIP: s = s.strip()
    if DO_LOWER: s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s

def _split_semicolons(cell):
    if pd.isna(cell): return []
    return [t.strip() for t in str(cell).split(";") if t is not None and t.strip()!=""]

# ---- 誤りペア抽出（新→旧の順で優先）----
def extract_pairs_from_corr_arrow(cell):
    pairs = []
    for tok in _split_semicolons(cell):
        m = PAT_ARROW.match(tok)
        if m:
            pairs.append((m.group(1), m.group(2)))
    return pairs

def extract_pairs_from_metadata_errors(cell):
    if pd.isna(cell): return []
    s = str(cell)
    pairs = PAT_PAIR_OLD_STRICT.findall(s)
    if not pairs:
        pairs = PAT_PAIR_OLD_LOOSE.findall(s)
    return pairs

def extract_primary_pairs_row(row):
    if COL_CORR in row and pd.notna(row[COL_CORR]):
        ps = extract_pairs_from_corr_arrow(row[COL_CORR])
        if ps: return ps
    if COL_ERR_OLD in row and pd.notna(row[COL_ERR_OLD]):
        ps = extract_pairs_from_metadata_errors(row[COL_ERR_OLD])
        if ps: return ps
    return []

# ---- GSM 抽出（新→旧）----
def _extract_gsms_from_cell(cell):
    if pd.isna(cell): return []
    return [m.upper() for m in PAT_GSM.findall(str(cell))]

def extract_gsms_row(row):
    gsms = set()
    has_split = False
    for col in SRC_SPLIT_COLS:
        if col in row:
            has_split = True
            gsms.update(_extract_gsms_from_cell(row[col]))
    if has_split and gsms:
        return sorted(gsms)
    if COL_SRC_OLD in row and pd.notna(row[COL_SRC_OLD]):
        for tok in _split_semicolons(row[COL_SRC_OLD]):
            gsms.update(_extract_gsms_from_cell(tok))
    return sorted(gsms)

# ====== コア構築 ======
def build_structures(df: pd.DataFrame):
    """
    - Record_unit==sample のみ
    - unverified_flag=='not_confirmed' は除外
    - db_to_gsms: DB -> {GSM}
    - dbgsm_to_errors: (DB, GSM) -> { "a -> b"(正規化) }
    """
    db_to_gsms, dbgsm_to_errors = {}, {}
    for _, r in df.iterrows():
        if str(r.get(COL_UNIT, "")).strip().lower() != "sample":
            continue
        if COL_UNVER in df.columns:
            if str(r.get(COL_UNVER, "")).strip().lower() == "not_confirmed":
                continue

        db = str(r.get(COL_DB))
        gsms = extract_gsms_row(r)
        pairs = extract_primary_pairs_row(r)

        if gsms:
            db_to_gsms.setdefault(db, set()).update(gsms)
        if gsms and pairs:
            seen = set()
            for a, b in pairs:
                ep = f"{normalize_text(a)} -> {normalize_text(b)}"
                if ep in seen:
                    continue
                seen.add(ep)
                for g in gsms:
                    dbgsm_to_errors.setdefault((db, g), set()).add(ep)

    db_to_gsms = {db: s for db, s in db_to_gsms.items() if s}
    return db_to_gsms, dbgsm_to_errors

#旧compute_edge_and_node_dualred関数, 直下の関数に差し替え
#def compute_edge_and_node_dualred(db_to_gsms, dbgsm_to_errors):
#    dbs = list(db_to_gsms.keys())
#    edge_rows=[]
#    internal_error_gsms = {db:set() for db in dbs}
#    shared_error_gsms   = {db:set() for db in dbs}
#
#    # 内部誤りGSM
#    for (db,g), errs in dbgsm_to_errors.items():
#        if errs:
#            internal_error_gsms[db].add(g)
#
#    # DBペア計算
#    for i in range(len(dbs)):
#        for j in range(i+1, len(dbs)):
#            A,B = dbs[i], dbs[j]
#            GA,GB = db_to_gsms[A], db_to_gsms[B]
#            inter = GA & GB
#            shared_gsm = len(inter)
#            shared_err = 0
#            if shared_gsm > 0:
#                for g in inter:
#                    ea = dbgsm_to_errors.get((A,g), set())
#                    eb = dbgsm_to_errors.get((B,g), set())
#                    ov = ea & eb
#                    if ov:
#                        shared_err += len(ov)
#                        shared_error_gsms[A].add(g)
#                        shared_error_gsms[B].add(g)
#                jacc = shared_gsm / len(GA | GB)
#            else:
#                jacc = 0.0
#            edge_rows.append([A,B,len(GA),len(GB),shared_gsm,shared_err,jacc])
#
#    edge_df = pd.DataFrame(edge_rows, columns=[
#        "DB_A","DB_B","size_A","size_B","shared_gsm","shared_gsm_error","jaccard"
#    ])
#
#    node_rows=[]
#    for db in dbs:
#        total = len(db_to_gsms[db])
#        n_internal = len(internal_error_gsms.get(db,set()))
#        n_shared   = len(shared_error_gsms.get(db,set()))
#        node_rows.append([db,total,n_internal,n_shared,
#                          (n_internal/total if total else 0.0),
#                          (n_shared/total if total else 0.0),
#                          (n_shared/n_internal if n_internal else 0.0)])
#    node_df = pd.DataFrame(node_rows, columns=[
#        "DB","total_gsm","internal_error_gsm","shared_error_gsm",
#        "frac_internal_of_total","frac_shared_of_total","frac_shared_of_internal"
#    ])
#    return edge_df, node_df, internal_error_gsms, shared_error_gsms

def compute_edge_and_node_dualred(db_to_gsms, dbgsm_to_errors):
    dbs = list(db_to_gsms.keys())
    edge_rows=[]
    internal_error_gsms = {db:set() for db in dbs}
    shared_error_gsms   = {db:set() for db in dbs}
    shared_err_items = []  # ← 追加：明細行を貯める（DB_A, DB_B, GSM, error_pair）

    # 内部誤りGSM
    for (db,g), errs in dbgsm_to_errors.items():
        if errs:
            internal_error_gsms[db].add(g)

    # DBペア計算
    for i in range(len(dbs)):
        for j in range(i+1, len(dbs)):
            A,B = dbs[i], dbs[j]
            GA,GB = db_to_gsms[A], db_to_gsms[B]
            inter = GA & GB
            shared_gsm = len(inter)
            shared_err = 0
            if shared_gsm > 0:
                for g in inter:
                    ea = dbgsm_to_errors.get((A,g), set())
                    eb = dbgsm_to_errors.get((B,g), set())
                    ov = ea & eb
                    if ov:
                        # 共有エラーをカウントし、明細を記録
                        for ep in ov:
                            shared_err += 1
                            shared_error_gsms[A].add(g)
                            shared_error_gsms[B].add(g)
                            shared_err_items.append({"DB_A":A,"DB_B":B,"GSM":g,"error_pair":ep})
                jacc = shared_gsm / len(GA | GB)
            else:
                jacc = 0.0
            edge_rows.append([A,B,len(GA),len(GB),shared_gsm,shared_err,jacc])

    edge_df = pd.DataFrame(edge_rows, columns=[
        "DB_A","DB_B","size_A","size_B","shared_gsm","shared_gsm_error","jaccard"
    ])

    node_rows=[]
    for db in dbs:
        total = len(db_to_gsms[db])
        n_internal = len(internal_error_gsms.get(db,set()))
        n_shared   = len(shared_error_gsms.get(db,set()))
        node_rows.append([db,total,n_internal,n_shared,
                          (n_internal/total if total else 0.0),
                          (n_shared/total if total else 0.0),
                          (n_shared/n_internal if n_internal else 0.0)])
    node_df = pd.DataFrame(node_rows, columns=[
        "DB","total_gsm","internal_error_gsm","shared_error_gsm",
        "frac_internal_of_total","frac_shared_of_total","frac_shared_of_internal"
    ])

    # 追加：明細DataFrameも返す
    detail_df = pd.DataFrame(shared_err_items, columns=["DB_A","DB_B","GSM","error_pair"])
    return edge_df, node_df, internal_error_gsms, shared_error_gsms, detail_df


def build_graphs(db_to_gsms, edge_df):
    G_A, G_B = nx.Graph(), nx.Graph()
    for db, gs in db_to_gsms.items():
        G_A.add_node(db, size=len(gs)); G_B.add_node(db, size=len(gs))
    for r in edge_df.itertuples(index=False):
        if r.shared_gsm >= EDGE_MIN_SHARED_GSM:
            G_A.add_edge(r.DB_A, r.DB_B, shared=r.shared_gsm, jacc=r.jaccard)
        if r.shared_gsm_error >= EDGE_MIN_SHARED_ERR:
            G_B.add_edge(r.DB_A, r.DB_B, err=r.shared_gsm_error)
    return G_A, G_B

def compute_positions(G_A):
    for _,_,d in G_A.edges(data=True):
        d["weight"] = max(d.get("jacc",0.0), 1e-6)
    pos = nx.spring_layout(G_A, seed=SEED, weight="weight", k=K_FOR_LAYOUT, scale=SCALE_FOR_LAYOUT)
    xs = [p[0] for p in pos.values()] or [0,1]
    ys = [p[1] for p in pos.values()] or [0,1]
    minx,maxx = (min(xs), max(xs)) if xs else (0,1)
    miny,maxy = (min(ys), max(ys)) if ys else (0,1)
    rngx = (maxx-minx) or 1.0
    rngy = (maxy-miny) or 1.0
    for n in pos:
        x,y = pos[n]
        pos[n] = ((x-minx)/rngx, (y-miny)/rngy)
    return pos

# ===== 描画 =====
def draw_panel_A(G,pos,out_png,out_svg):
    sizes  = [300+12*G.nodes[n]["size"] for n in G.nodes()]
    max_sh = max([d["shared"] for _,_,d in G.edges(data=True)], default=1)
    widths = [1+4*(d["shared"]/max_sh) for _,_,d in G.edges(data=True)]
    vals   = np.array([d["jacc"] for _,_,d in G.edges(data=True)]) if G.number_of_edges()>0 else np.array([0])
    cmap=mpl.cm.Blues; norm=mpl.colors.Normalize(vmin=0,vmax=1) # viridis -> Blues
    colors=[cmap(norm(v)) for v in vals]
    fig,ax=plt.subplots(figsize=(14,12))
    nx.draw_networkx_nodes(G,pos,node_size=sizes,node_color=(1.0,1.0,1.0),
                           edgecolors=(0.2,0.2,0.3),ax=ax)
    nx.draw_networkx_edges(G,pos,width=widths,edge_color=colors,alpha=0.9,ax=ax)
    nx.draw_networkx_labels(G,pos,font_size=15,ax=ax,clip_on=False) # font_size=10 -> 15
    sm=mpl.cm.ScalarMappable(cmap=cmap,norm=norm); sm.set_array([])
    cbar=plt.colorbar(sm,ax=ax,fraction=0.046,pad=0.04)
    cbar.set_label("Jaccard similarity (GSM sets)", fontsize=18) # fontsize追加
    cbar.ax.tick_params(labelsize=15)  # 目盛りフォントサイズ追加
    ax.set_xlim(-PAD,1+PAD); ax.set_ylim(-PAD,1+PAD)
    ax.set_title("(A) GSM similarity (Jaccard); width = #shared GSMs"); ax.axis("off")
    plt.tight_layout(); plt.savefig(out_png,dpi=300,pad_inches=0.5)
    plt.savefig(out_svg, format="svg", pad_inches=0.5)
    plt.close()
    print(f"[SAVE] {out_png}")

def draw_panel_B(G_err,pos,out_png,out_svg, *, G_base, db_to_gsms,
                 db_to_carry, shared_error_gsms):
    fig,ax=plt.subplots(figsize=(14,12))

    # 背景: AのGSMエッジ -> コメントアウトする
    #if SHOW_BASE_GSM_EDGES and G_base.number_of_edges()>0:
    #    max_shared = max([d["shared"] for _,_,d in G_base.edges(data=True)], default=1)
    #    base_widths = [0.5 + 2.0*(d["shared"]/max_shared) for _,_,d in G_base.edges(data=True)]
    #    nx.draw_networkx_edges(G_base, pos, width=base_widths, edge_color=BASE_GRAY_EDGE, alpha=0.25, ax=ax)

    # エラー共有エッジ
    if G_err.number_of_edges()>0:
        max_err=max([d["err"] for _,_,d in G_err.edges(data=True)], default=1)
    else:
        max_err=1
    widths=[0.8+4*(d["err"]/max_err) for _,_,d in G_err.edges(data=True)]
    vals=np.array([d["err"] for _,_,d in G_err.edges(data=True)]) if G_err.number_of_edges()>0 else np.array([0])
    vmax=max(vals) if len(vals)>0 else 1.0
    cmap=mpl.cm.Reds; norm=mpl.colors.Normalize(vmin=0.0, vmax=max(1.0,float(vmax))) # inferno -> Reds
    colors=[cmap(norm(v)) for v in vals]
    nx.draw_networkx_edges(G_err, pos, width=widths, edge_color=colors, alpha=0.9, ax=ax)

    # ノード: base total -> outer=carriers -> inner=carriers∩shared-errors
    nodes = list(G_err.nodes())
    BASE  = [300+12*len(db_to_gsms.get(n, set())) for n in nodes]
    outer_counts = np.array([len(db_to_carry.get(n, set())) for n in nodes])         # キャリア数
    inner_counts = np.array([len(shared_error_gsms.get(n, set())) for n in nodes])   # 実際共有エラーGSM数

    OUTER = np.where(outer_counts == 0, 0, 200 + 12*outer_counts)
    INNER = np.where(inner_counts == 0, 0,  80 + 12*inner_counts)

    if SHOW_BASE_TOTAL_NODE:
        nx.draw_networkx_nodes(G_err, pos, node_size=BASE, node_color=BASE_WHITE_NODE,
                               edgecolors=(0.8,0.8,0.8), linewidths=0.8, ax=ax)
    nx.draw_networkx_nodes(G_err, pos, node_size=OUTER, node_color=PINK,
                           edgecolors=OUTLINE_PINK, linewidths=0.8, ax=ax)
    nx.draw_networkx_nodes(G_err, pos, node_size=INNER, node_color=RED,
                           edgecolors=OUTLINE_RED, linewidths=0.6, ax=ax)

    nx.draw_networkx_labels(G_err, pos, font_size=15, ax=ax, clip_on=False) # font_size=10 -> 15

    sm=mpl.cm.ScalarMappable(cmap=cmap,norm=norm); sm.set_array([])
    cbar=plt.colorbar(sm,ax=ax,fraction=0.046,pad=0.04)
    cbar.set_label("Count of shared (GSM×error-pair)", fontsize=18) # fontsize追加
    cbar.ax.tick_params(labelsize=15)  # 目盛りフォントサイズ追加

    ax.set_xlim(-PAD,1+PAD); ax.set_ylim(-PAD,1+PAD)
    ax.set_title("(B) Actual error sharing; nodes: outer=carriers, inner=carriers∩shared-errors")
    ax.axis("off")
    plt.tight_layout(); plt.savefig(out_png,dpi=300,pad_inches=0.5)
    plt.savefig(out_svg, format="svg", pad_inches=0.5)
    plt.close()
    print(f"[SAVE] {out_png}")

# ===== Panel C: carriers Jaccard（ノードは外側=キャリアのみ） =====
def compute_carry_sets(shared_error_gsms, db_to_gsms):
    """
    U_err: どこかのDB間で“誤り共有”として観測されたGSMの全体集合
    db_to_carry: DBごとのキャリアGSM集合（A_i ∩ U_err）
    """
    U_err = set()
    for _, gs in shared_error_gsms.items():
        U_err.update(gs)
    db_to_carry = {db: (gs & U_err) for db, gs in db_to_gsms.items()}
    db_to_carry = {db: s for db, s in db_to_carry.items() if s}  # 空は除去
    return U_err, db_to_carry

def compute_carry_edges(db_to_carry):
    """
    DBペアごとの J_carry = |P_i ∩ P_j| / |P_i ∪ P_j|
    """
    dbs = list(db_to_carry.keys())
    rows = []
    for i in range(len(dbs)):
        for j in range(i+1, len(dbs)):
            A, B = dbs[i], dbs[j]
            PA, PB = db_to_carry[A], db_to_carry[B]
            inter = PA & PB
            uni   = PA | PB
            shared_carry = len(inter)
            jacc_carry   = (shared_carry / len(uni)) if len(uni) > 0 else 0.0
            rows.append([A, B, len(PA), len(PB), shared_carry, jacc_carry])

    edge_df = pd.DataFrame(rows, columns=[
        "DB_A","DB_B","size_carry_A","size_carry_B","shared_carry_gsm","jaccard_carry"
    ])
    return edge_df

def build_graph_carry(db_to_gsms, db_to_carry, edge_df_carry):
    G_C = nx.Graph()
    for db, gs in db_to_gsms.items():
        G_C.add_node(db, size=len(gs), size_carry=len(db_to_carry.get(db, set())))
    for r in edge_df_carry.itertuples(index=False):
        if r.shared_carry_gsm >= EDGE_MIN_SHARED_ERR:
            G_C.add_edge(r.DB_A, r.DB_B, shared_carry=r.shared_carry_gsm, jacc=r.jaccard_carry)
    return G_C

def draw_panel_C(G_C, pos, out_png, out_svg, *,
                 G_base, db_to_gsms, db_to_carry):
    fig, ax = plt.subplots(figsize=(14,12))

    # 背景: AのGSMエッジ -> コメントアウトする
    #if SHOW_BASE_GSM_EDGES and G_base.number_of_edges()>0:
    #    max_shared = max([d["shared"] for _,_,d in G_base.edges(data=True)], default=1)
    #    base_widths = [0.5 + 2.0*(d["shared"]/max_shared) for _,_,d in G_base.edges(data=True)]
    #    nx.draw_networkx_edges(G_base, pos, width=base_widths, edge_color=BASE_GRAY_EDGE, alpha=0.25, ax=ax)

    # キャリアJaccardのエッジ（色=Jaccard, 幅=共有キャリア数）
    if G_C.number_of_edges()>0:
        max_sh = max([d.get("shared_carry", 0) for _,_,d in G_C.edges(data=True)], default=1)
    else:
        max_sh = 1
    widths = [1 + 4*(d.get("shared_carry", 0)/max_sh) for _,_,d in G_C.edges(data=True)]
    vals   = np.array([d.get("jacc", 0.0) for _,_,d in G_C.edges(data=True)]) if G_C.number_of_edges()>0 else np.array([0.0])
    cmap = mpl.cm.Blues; norm = mpl.colors.Normalize(vmin=0, vmax=1) # viridis -> Blues
    colors = [cmap(norm(v)) for v in vals]
    nx.draw_networkx_edges(G_C, pos, width=widths, edge_color=colors, alpha=0.9, ax=ax)

    # ノード: base total -> outer=carriers（内側は描かない）
    nodes = list(G_C.nodes())
    BASE  = [300 + 12*len(db_to_gsms.get(n, set())) for n in nodes]
    outer_counts = np.array([len(db_to_carry.get(n, set())) for n in nodes])
    OUTER = np.where(outer_counts == 0, 0, 200 + 12*outer_counts)

    if SHOW_BASE_TOTAL_NODE:
        nx.draw_networkx_nodes(G_C, pos, node_size=BASE, node_color=BASE_WHITE_NODE,
                               edgecolors=(0.8,0.8,0.8), linewidths=0.8, ax=ax)
    nx.draw_networkx_nodes(G_C, pos, node_size=OUTER, node_color=PINK,
                           edgecolors=OUTLINE_PINK, linewidths=0.8, ax=ax)

    nx.draw_networkx_labels(G_C, pos, font_size=15, ax=ax, clip_on=False) # font_size=10 -> 15

    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Jaccard similarity (error-observed GSM carriers)", fontsize=18) # fontsize追加
    cbar.ax.tick_params(labelsize=15)  # 目盛りフォントサイズ追加

    ax.set_xlim(-PAD, 1+PAD); ax.set_ylim(-PAD, 1+PAD)
    ax.set_title("(C) Carrier Jaccard; nodes: outer=carriers")
    ax.axis("off")
    plt.tight_layout(); plt.savefig(out_png, dpi=300, pad_inches=0.5)
    plt.savefig(out_svg, format="svg", pad_inches=0.5)
    plt.close()
    print(f"[SAVE] {out_png}")

# ============== Main ==============
def main():
    if not os.path.exists(DATA_XLSX):
        raise SystemExit(f"[ERROR] Input file not found: {DATA_XLSX}")
    df = pd.read_excel(DATA_XLSX, sheet_name=SHEET_NAME)

    for col in (COL_DB, COL_UNIT):
        if col not in df.columns:
            raise SystemExit(f"[ERROR] Missing column {col}")

    db_to_gsms, dbgsm_to_errors = build_structures(df)
    # edge_df, node_df, internal_error_gsms, shared_error_gsms = compute_edge_and_node_dualred(db_to_gsms, dbgsm_to_errors)を以下に変更
        # 変更（detail_df を受け取る）
    edge_df, node_df, internal_error_gsms, shared_error_gsms, detail_df = compute_edge_and_node_dualred(db_to_gsms, dbgsm_to_errors)
    edge_df.to_csv(CSV_EDGE, index=False, encoding="utf-8-sig")
    node_df.to_csv(CSV_NODE, index=False, encoding="utf-8-sig")

    # 追加：パネルB用の共有数CSV（最小改修①）
    (
        edge_df.loc[:, ["DB_A","DB_B","shared_gsm_error"]]
               .rename(columns={"shared_gsm_error":"shared_err_count"})
    ).to_csv(CSV_EDGE_B, index=False, encoding="utf-8-sig")

    # 追加：明細CSVと、保険のサマリ再集計
    if not detail_df.empty:
        detail_df.to_csv(CSV_B_DETAIL, index=False, encoding="utf-8-sig")
        (detail_df.groupby(["DB_A","DB_B"]).size()
                 .reset_index(name="shared_err_count")
        ).to_csv(CSV_B_SUMMARY, index=False, encoding="utf-8-sig")


    G_A, G_B = build_graphs(db_to_gsms, edge_df)
    pos = compute_positions(G_A)

    # 先に「キャリア集合」を計算（B/C のノード外側を統一）
    U_err, db_to_carry = compute_carry_sets(shared_error_gsms, db_to_gsms)

    # Panel A
    draw_panel_A(G_A, pos, PNG_A, SVG_A)

    # Panel B（outer=carriers, inner=carriers∩shared-errors）
    draw_panel_B(G_B, pos, PNG_B, SVG_B, G_base=G_A,
                 db_to_gsms=db_to_gsms,
                 db_to_carry=db_to_carry,
                 shared_error_gsms=shared_error_gsms)

    # Panel C（outer=carriers のみ）
    edge_df_carry = compute_carry_edges(db_to_carry)
    edge_df_carry.to_csv(CSV_EDGE_C, index=False, encoding="utf-8-sig")

    # ノードサマリ（C）
    node_rows_c=[]
    for db in sorted(db_to_gsms.keys()):
        total = len(db_to_gsms.get(db, set()))
        n_car = len(db_to_carry.get(db, set()))
        node_rows_c.append([
            db, total, n_car,
            (n_car/total if total else 0.0),
        ])
    node_df_c = pd.DataFrame(node_rows_c, columns=[
        "DB","total_gsm","carrier_gsm","frac_carrier_of_total"
    ])
    node_df_c.to_csv(CSV_NODE_C, index=False, encoding="utf-8-sig")

    G_C = build_graph_carry(db_to_gsms, db_to_carry, edge_df_carry)
    draw_panel_C(G_C, pos, PNG_C, SVG_C,
                 G_base=G_A,
                 db_to_gsms=db_to_gsms,
                 db_to_carry=db_to_carry)

if __name__=="__main__":
    main()