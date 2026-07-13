#!/usr/bin/env python3
"""MVP 產線(A骨架+C列解析+D組裝+E裁圖+K佇列;契約=MVP_CONTRACT.md):
一份 PDF → SCHEMA JSON(每有值欄位帶 prov)+ 裁圖 PNG + needs_review 佇列檔。

    /opt/homebrew/bin/python3 pipeline.py <pdf> [outdir]   # 單檔(fitz 在 homebrew python)
    /opt/homebrew/bin/python3 pipeline.py --smoke [outdir] # dev 端到端+守恆對帳
    /opt/homebrew/bin/python3 pipeline.py --selftest       # D 組裝 19 條單元測試(合成)
    # outdir 預設 product/;產出 <outdir>/<brand>/<stem>.json + .review.json + _crops/

鐵律:只 import core/、不改綁定;綁定版本釘 V=12(v8=S2-1 全字母+v10=S2-2L1
量表碼歸隊+v12=S2-1延伸③塊內尺寸繼承;v9=E-1 懸空側枝、v11=E-1 預留;凍結
說明=output/v12_FREEZE.md)。extract_page 逐碼判定鏡射 m3_scan.scan_page(v12)
——鏡射若漂移,守恆對帳逐頁必紅(九欄逐頁 vs 凍結 output/s21ext_dev_v12.csv)。
A:bindings=逐筆 x_aligned 綁定紀錄(id=b:頁:序)。
C:specByCode=每偵測碼一列 {code,size,surface,priceBand,packing,prov}(id=s:頁:序);
  surface/priceBand/packing=首做,dev 只自測結構,正確率=I,I 前不做成品宣稱。
D:assemble()=合併鍵 code∪同色樣實例(色名/幾何永不當鍵)、體制 B 需正面證據其餘
  A 形式無損、衝突不猜進佇列;可追溯守恆=mergedFrom/derivedFrom 雙向帳零遺失
  (設計+測試案例=D_DESIGN.md)。
E:fitz clip 裁圖(aligned Variant 100%+nameHint 目標+骨架檔全色樣),純輸出。
K:佇列落檔 .review.json(items=流動佇列零增減;骨架色樣另列標明非入庫)。
D5 色名標籤 v2(2026-07-10,audit.md D1 拍板):照片級色樣(h>CAP_BIG_H)圖說=
  貼緣窄帶(上 CAP_TOP/下 CAP_BOT;dev 實測:真圖說貼緣、帶外=頁面文字/規格表)
  +排已偵測碼+非拉丁 token 濾;窄帶排除的名形 token 落 <stem>.capcodes.json
  (S2-1 漏抓線索,非產品輸出)。僅標籤層(cap→color.en),不碰綁定/佇列/凍結。
"""
import csv
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "core"))  # core/ 互相 import 必須同層

import fitz  # noqa: E402

from census import SIZE_RE  # noqa: E402
from m1_scan import norm  # noqa: E402
from m2_scan import BAND_RE, build_vocabs, code_candidates, pseudo_suspects  # noqa: E402
from m3_scan import (_same_row_side, doc_icon_stats, doc_name_index,  # noqa: E402
                     fold_x, icon_sus, is_name, name_bind, page_good_names,
                     page_sizes, row_size)
from spike_geom import assign_words, extract_swatches  # noqa: E402

V = 12  # 綁定版本釘死(v12=v10+S2-1延伸③塊內尺寸繼承,使用者親驗切版 2026-07-12,
#         凍結=output/v12_FREEZE.md;v9=E-1 懸空側枝、v11=E-1 併主幹預留,皆不入
#         主幹);要動=動綁定,先停下回報

# D5 色名標籤 v2 窄帶(label 層常數;dev 全集掃描選值,平台期 30-35/16-20 非刀口):
# 照片級色樣的真圖說貼緣(上緣外=標題行較寬、下緣通常緊接規格表故窄),
# 帶外詞=頁面文字(Level 表格行 15-60pt/Marazzi 底部圖說塊)→ 不進 color.en
CAP_BIG_H, CAP_TOP, CAP_BOT = 150, 35, 16

# D|L2 塌縮守衛門檻(通案四;工作包#7 緊急補丁,凍結)。塌縮=cluster 跨頁∧色名衝突
# ∧ mergedFrom≥此值 → 降級佇列不出 Variant。校準(dev/assembly_probe.py --sig 12,
# 全 7 語料):跨頁∧衝突 cluster 大小有淨空隙——非塌縮上界=19(Topcer General)、
# 塌縮下界=30(Provenza);20 落隙中,命中恰 4 塊 V=12 產線既存塌縮、0 誤旗。
# 前瞻:v13 誘發塌縮(A02G 119/Rice 44/Uniche 27)皆≥20。凍結後不動;正規 L2 修法
# 於 v13 世界複校準(見 output/l2_collapse_design.md §3.4/緊急補丁節)。
L2_COLLAPSE_MIN = 20

# D|單頁過併守衛門檻(通案四;段1,凍結)。單頁塌縮=一大 hub 版塊(情境/純碼索引頁)被
# 整頁不同碼 x-align 吞併成單一巨 cluster,色名不衝突(同一版塊同色名)→ 跨頁守衛(需
# pages≥2∧衝突)照不到,改以「主色樣 area%」承重:hub 版塊佔頁面積大,合法小色片矩陣則小。
# 判別子=單頁 ∧ mergedFrom≥L2_COLLAPSE_MIN ∧ 主色樣 area%(cluster 內最大色樣 bbox 佔頁
# 面積%)≥此值 → 整團降級 singlepage_overmerge_suspect。校準(dev/pkgB_hub_sep.py --floor 2,
# 全 7 語料 v12):單頁∧≥20 母體僅 Ariostea p152(area% 7.015/8.483=過併下界);合法單頁
# hub 上界=Ergon Woodtouch p13 area% 2.359=隙下界。空隙 [2.36, 7.02],5.0 落隙中、0 誤旗。凍結。
AREA_T = 5.0

# 案1(外審修正案,工作包#10):sub-20 真塌縮與合法團在 size 軸零邊際(非塌縮上界 19=
# 真塌縮 19 同值)→ 正解=撤銷超出已校準安全區的自動合併權限,不找新判別器(通案五)。
# ①不確定帶 [L2_BORDERLINE_MIN,L2_COLLAPSE_MIN):跨頁∧色名衝突→佇列
#   borderline_merge_suspect(不硬判塌縮/合法)。②爆炸半徑:跨頁 cluster 頁數/吞併
#   超出已確認合法上界→佇列 assembly_merge_radius_suspect。單頁域歸段1守衛(AREA_T),
#   半徑不碰(合法單頁 25 綁定存在=Ariostea 0general v13)。失敗方向=寧不合併(鐵律2)。
# 校準(dev/assembly_probe.py --borderline,全 7 語料×v12/v13,共 84 檔;總帳=
# output/l2_borderline_merge_ledger.md):帶=真塌縮 {A02G-18(5p),Topcer General-19(4p),
# Uniche-19(3p,v13)} vs 合法衝突上界 16(Level 型)→下緣 18、空隙 17 淨空;半徑=合法
# 上界 5 頁(MILANO70/Ariostea 3general)/24 綁定(Level)、上方空隙 [6,7]/[25,41]、病理側
# 下界 8 頁/42 綁定(Topcer VICTORIAN DESIGNS=dev 1021 塌縮姊妹檔)。宣告+校準+凍結不調。
L2_BORDERLINE_MIN = 18
L2_AUTO_MERGE_MAX_PAGES = 5
L2_AUTO_MERGED_FROM_MAX = 24

KNOWN_GAPS = [  # MVP 契約紅字:偵測缺口使產品整筆靜默缺席,下游勿當完整清單
    "S2-1 B類全字母SKU未偵測(Emil型單頁漏74%)——產品整筆缺席不報警",
    "S2-3 一次性/低重複長碼未偵測(0general型單檔273筆)——產品整筆缺席不報警",
    "S2-1 C類低重複純數字碼未偵測(Iris/41Zero42型)——產品整筆缺席不報警",
    "S2-2 量表碼殘留:v10 L1 已修 band 家族型(A102/A107,c7 GT 實錘)——"
    "殘餘=無家族字母/B-A'雙漏毒碼型(T104 屬此,dev 1 例),GT 監看",
    "S2-1 純B碼頁(頁上無含數字錨)整頁靜默漏(PietraEssenza p21 型26碼)——佇列零記錄",
    "SCH-3 總目錄一檔多系列未切分——seriesName僅檔名級",
    # D 延後決定(I 後專門回報兩數字再定案,見 D_DESIGN.md §二之二)
    "D 體制A/B:1碼1尺寸臨界一律A形式(doc級投票未做)——體制錯置率待 I",
    "D 合併:色名不當合併鍵(SCH-3 未做)——同色無共同碼時分列多個 Variant,比例待 I",
    # 2026-07-10 使用者裁決(照片級 8 筆審後),文案經核可
    "E 裁圖:photo_level 未過濾——場景照(房間/家具)不可當產品圖(裁決 2026-07-10),"
    "過濾票 E-1 排 I 後;拼磚版面頁(Topcer 型)幾何無法格級綁定,"
    "該型輸出=整版拼貼圖非單色樣,待 I 頻率定切分票",
    "color.en 殘餘溢收(多語圖說串/多產品圖說塊,SCH-2/圖說切分層)——"
    "溢收 Variant 照出但帶 colorQuality=needs_review 旗標,下游勿直接信該色名",
    # 2026-07-11 外審行動③
    "跨文件實體解析未實作:同一系列跨型錄(總目錄+單系列)/跨年版(2024+2025)"
    "會產生重複且可能衝突的系列與 Variant 記錄,下游不得假設已去重"
    "——修復時點=全池普查後由使用者排",
]


def prov(pdf, page=None, bbox=None, method=""):
    return {"pdf": pdf, "page": page,
            "bbox": [round(v, 1) for v in bbox] if bbox else None, "method": method}


def norm_size(tok):
    # ponytail: 粗正規化(x/×統一、去空白、統一小寫)=MVP 契約範圍;cm/mm/吋
    # 換算與逗號小數歸一屬 allSizes 正規化票,MVP 後補
    return tok.lower().replace("×", "x").replace(" ", "")


# ---- C|specByCode 列欄解析(新抽取規則;正確率=I 給數,dev 只驗結構)----

NUM_RE = re.compile(r"^\d{1,4}(?:[.,]\d{1,3})?$")  # packing 值候選(純數,尺寸有x不會中)
PACK_HDRS = [  # 欄標頭字界匹配(對 raw token,²→2;單位詞=產業通用,非樣本寫死)
    ("pcsBox", re.compile(r"\b(?:PZ|PCS|PIECES|PZZ)\b")),
    ("m2Box", re.compile(r"\b(?:MQ|M2|SQM)\b")),
    ("kgBox", re.compile(r"\bKG\b")),
]


def code_row_words(w, words, fold):
    """碼字的同列同折縫側詞(幾何同 m3_scan._same_row_side,與 row_size 一致)。"""
    h = max(w[3] - w[1], 1)
    cyw = (w[1] + w[3]) / 2
    side = (w[0] + w[2]) / 2 < fold if fold else None
    return [u for u in words if u != w and _same_row_side(u, cyw, h, fold, side)]


def doc_finish_vocab(spec, codes_doc, alpha_vocab):
    """surface 候選詞(零詞表寫死,per-doc 結構訊號):dev 泛用詞表(跨檔工業詞彙,
    is_name 的反面=非色名/系列名)∩ 本檔 ≥3 個碼列出現 → 該檔 finish 詞彙。
    # ponytail: 泛用詞表若混入高頻非 finish 詞會誤收;精度歸 I,dev 只驗結構"""
    cnt = Counter()
    for page in spec:
        words = page.get_text("words")
        fold = fold_x(page)
        for w in words:
            if norm(w[4]) not in codes_doc:
                continue
            toks = {norm(u[4]) for u in code_row_words(w, words, fold)}
            for t in toks:
                if t.isalpha() and len(t) >= 3 and t in alpha_vocab:
                    cnt[t] += 1
    return {t for t, n in cnt.items() if n >= 3}


def col_field(u, words, fold):
    """packing 數字 token → 上方 x 重疊的最近欄標頭 → 欄位名;無標頭=None(不猜)。"""
    cy = (u[1] + u[3]) / 2
    side = (u[0] + u[2]) / 2 < fold if fold else None
    best = None
    for v in words:
        if (v[1] + v[3]) / 2 >= cy or min(u[2], v[2]) - max(u[0], v[0]) <= 0:
            continue
        if fold and ((v[0] + v[2]) / 2 < fold) != side:
            continue
        t = v[4].upper().replace("²", "2")
        for field, rx in PACK_HDRS:
            if rx.search(t):
                d = cy - (v[1] + v[3]) / 2
                if best is None or d < best[0]:
                    best = (d, field)
                break
    return best[1] if best else None


def spec_row(w, size, words, fold, pdf_name, pno, band_set, finish_vocab):
    """一個碼字 → SpecRow(SCHEMA §1)。抽不到的欄=null,不猜。"""
    cx = (w[0] + w[2]) / 2
    row = sorted(code_row_words(w, words, fold), key=lambda u: u[0])
    seen, sf = set(), []
    for u in row:  # 去重(矩陣列同詞多欄);排全小寫=散文非標籤(重用 is_name 已驗
        t = norm(u[4])  # 排版訊號);泛用詞混入(WHITE/BOX 型)=已知缺陷,修法屬
        # finish 訊號升級票,dev 不做詞黑名單(=寫死樣本長相)
        if t in finish_vocab and not u[4].islower() and t not in seen:
            seen.add(t)
            sf.append(u[4])
    surface = " ".join(sf) or None
    bands = [(abs((u[0] + u[2]) / 2 - cx), norm(u[4]))
             for u in row if norm(u[4]) in band_set]  # 同一筆 S2-2 分流紀錄接回
    packing = {}
    for u in row:
        if NUM_RE.match(u[4]):
            f = col_field(u, words, fold)
            if f and f not in packing:  # ponytail: 同欄位多數字取最左(box 區在 pallet 左)
                packing[f] = u[4].replace(",", ".")
    return {"code": norm(w[4]), "size": norm_size(size) if size else None,
            "surface": surface, "priceBand": min(bands)[1] if bands else None,
            "packing": packing or None,
            "prov": prov(pdf_name, pno, w[:4], "spec_row_v6")}


# ---- D|Stage 5 組裝(設計/測試案例=D_DESIGN.md;正確率=I 給數)----

def _latin(t):
    """v2:非拉丁字母 token(多語圖說 ДЕКОРЫ 型)不進色名。0x24F=拉丁擴展 B 上界。"""
    return not any(ord(c) > 0x24F and c.isalpha() for c in t)


def color_quality(cen):
    """色名品質旗標(聲明層;2026-07-10 裁決:溢收 Variant 照出但標記不擋)。
    needs_review=溢收訊號命中(≥4 token/長度>30/含非拉丁)=audit.md §① severe 判準
    ——下游勿直接信該色名,人工看;clean=無溢收訊號(不保證正確,正確率=I)。"""
    if len(cen.split()) >= 4 or len(cen) > 30 or not _latin(cen):
        return "needs_review"
    return "clean"


def caption_name(ws, alpha_vocab):
    """色樣圖說詞 → color.en 標籤(僅標籤,永不當合併鍵)。is_name 規則:
    非泛用詞、非全小寫、字母 ≥3;v2 加非拉丁濾;y→x 序連接(STEEL WHITE 型)。
    無 → None。"""
    toks = [w for w in sorted(ws, key=lambda w: (round(w[1]), w[0]))
            if is_name(w[4], alpha_vocab) and _latin(w[4])]
    return " ".join(w[4] for w in toks) or None


def assemble(bindings, spec_rows, review, band_letters=frozenset(), pseudo=frozenset(),
             page_dims=None):
    """D 組裝:綁定紀錄+spec 列 → Variant/VariantSize。
    合併鍵=同色樣實例 ∪ 同碼(SCHEMA PK);色名/幾何永不當鍵(寧可不合不誤合)。
    體制:B 需正面證據(色組恰 1 碼且 ≥2 已知尺寸)→ Variant.code=碼;
    其餘一律 A 形式(無損:碼保留在 orderCode);混合訊號 → A 形式+regime_conflict。
    可追溯守恆(硬斷言):綁定認領互斥覆蓋、spec 列認領互斥、佇列只增不減。
    S2-2 延伸 L2 v2(D 加固,2026-07-12 核可;s22ext_design 修正案 v2):
    嫌疑碼=C3 條件——P(首字母∈band_letters)∧ 跨 ≥2 色樣 ∧ ∃≥2 色樣另有
    他碼 ∧ 橋接(∃色樣對除該碼外無共同碼)→ 不作合併鍵、綁定逐筆降級佇列
    (merge_key_suspect,帶 prov+swatch,資料無損)。P=承重(dev 分離:C0
    誤中 779→C3 誤中 0);已知限制=P 為 L1/L2 共模單點(裁決①)。v10 上游
    歸隊後本防線於 dev/c7 觸發集=∅(純備援;SL-6 注入案=活體證明)。
    S2-5(2026-07-12,工作包#3 線③):pseudo=m2_scan.pseudo_suspects 嫌疑碼集
    ——命中之 Variant 加鍵 pseudoCodeSuspect=[嫌疑碼](出但標記;無中者無鍵,
    綁定/佇列/統計零變化=T26 註記惰性斷言)。
    回傳 (variants, review_out, stats)。"""
    sw_of = lambda b: (b["swatch"]["page"], tuple(b["swatch"]["bbox"]))  # noqa: E731
    code_sw, sw_codes = {}, {}
    for b in bindings:
        code_sw.setdefault(b["code"], set()).add(sw_of(b))
        sw_codes.setdefault(sw_of(b), set()).add(b["code"])
    suspects = set()
    for c, ss in code_sw.items():
        if not (c and c[0] in band_letters and len(ss) >= 2):
            continue
        if sum(1 for s in ss if sw_codes[s] - {c}) < 2:
            continue
        sl = sorted(ss)
        if any(sw_codes[a] & sw_codes[b2] == {c}
               for i9, a in enumerate(sl) for b2 in sl[i9 + 1:]):
            suspects.add(c)                                  # 橋接=結構冗餘雙保險
    demoted = [{"reason": "merge_key_suspect", "code": b["code"],
                "swatch": b["swatch"], "prov": b["prov"]}
               for b in bindings if b["code"] in suspects]
    bindings = [b for b in bindings if b["code"] not in suspects]
    parent = {}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        parent.setdefault(a, a)
        parent.setdefault(b, b)
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for b in bindings:
        union(b["id"], ("sw", b["swatch"]["page"], tuple(b["swatch"]["bbox"])))
        union(b["id"], ("code", b["code"]))
    clusters, order = {}, []
    for b in bindings:
        r = find(b["id"])
        if r not in clusters:
            clusters[r] = []
            order.append(r)
        clusters[r].append(b)
    # 通案四 L2 塌縮守衛(assembly_collapse_suspect):cluster 層後驗塌縮簽名=跨頁(≥2)
    # ∧色名衝突(len(colors)>1 or len(raws)>1)∧ mergedFrom≥L2_COLLAPSE_MIN → 整團降級
    # 佇列、不出 Variant(失敗方向=寧不合併不自信錯綁;綁定帶 prov/swatch 無損)。溯源=
    # A102/L2 塌縮同層兩度漏網、SL-6~8 之非 band 缺口結構性補位(l2_collapse_design.md)。
    # 段1 單頁過併守衛(singlepage_overmerge_suspect):單頁塌縮(hub 版塊吞併整頁不同碼,
    # 同色名→跨頁守衛照不到)以「主色樣 area%」承重=cluster 內最大色樣 bbox 佔頁面積%。
    # page_dims={頁號:頁面積};None(合成單元測試預設)→ area%=0=單頁分支惰性(不誤動)。
    def main_area_pct(bl_):
        if not page_dims:
            return 0.0
        seen, best = {}, 0.0
        for b in bl_:
            sw = b["swatch"]
            k = (sw["page"], tuple(sw["bbox"]))
            if k in seen:
                continue
            seen[k] = 1
            pa = page_dims.get(sw["page"])
            if not pa:
                continue
            x0, y0, x1, y1 = sw["bbox"]
            best = max(best, 100.0 * max(0.0, x1 - x0) * max(0.0, y1 - y0) / pa)
        return best

    collapse_demoted, kept, collapsed_ids = [], [], set()
    n_collapse, n_singlepage, n_borderline, n_radius = 0, 0, 0, 0
    for r in order:
        bl = clusters[r]
        pages = {b["swatch"]["page"] for b in bl}
        cols = {b["color"] for b in bl if b["color"]}
        raws = {b.get("colorRaw", b["color"]) for b in bl if b.get("colorRaw", b["color"])}
        conflict = len(cols) > 1 or len(raws) > 1
        reason = None
        if len(bl) >= L2_COLLAPSE_MIN:
            if len(pages) >= 2 and conflict:
                reason, n_collapse = "assembly_collapse_suspect", n_collapse + 1
            elif len(pages) == 1 and main_area_pct(bl) >= AREA_T:
                reason, n_singlepage = "singlepage_overmerge_suspect", n_singlepage + 1
        elif len(pages) >= 2 and conflict and len(bl) >= L2_BORDERLINE_MIN:
            # 案1①|次臨界不確定帶:同塌縮簽名、大小 [18,20)=零邊際帶,撤銷自動合併
            reason, n_borderline = "borderline_merge_suspect", n_borderline + 1
        if reason is None and len(pages) >= 2 and (
                len(pages) > L2_AUTO_MERGE_MAX_PAGES
                or len(bl) > L2_AUTO_MERGED_FROM_MAX):
            # 案1②|爆炸半徑:無衝突簽名也不得超已確認合法上界自動合併(Topcer DESI 型)
            reason, n_radius = "assembly_merge_radius_suspect", n_radius + 1
        if reason:
            for b in bl:
                collapse_demoted.append({"reason": reason, "code": b["code"],
                                         "swatch": b["swatch"], "prov": b["prov"]})
                collapsed_ids.add(b["id"])
        else:
            kept.append(r)
    order = kept
    bindings = [b for b in bindings if b["id"] not in collapsed_ids]
    rows_by_code = {}
    for r in spec_rows:
        rows_by_code.setdefault(r["code"], []).append(r)
    variants, extra, claimed = [], [], set()

    def mkvs(size, order_code, src, fb_prov):
        for r in src:
            assert r["id"] not in claimed, "spec 列重複認領"
            claimed.add(r["id"])
        one = lambda k: (lambda vals: vals.pop() if len(vals) == 1 else None)(  # noqa: E731
            {r[k] for r in src if r[k]})  # 值衝突 → null 不猜(原始列都在 specByCode)
        return {"size": size, "finish": one("surface"), "orderCode": order_code,
                "priceBand": one("priceBand"), "derivedFrom": [r["id"] for r in src],
                "prov": src[0]["prov"] if src else fb_prov}

    for root in order:
        bl = clusters[root]
        codes = sorted({b["code"] for b in bl})
        known = {c: sorted({r["size"] for r in rows_by_code.get(c, []) if r["size"]})
                 for c in codes}
        regime_b = len(codes) == 1 and len(known[codes[0]]) >= 2
        vss = []
        for c in codes:
            crows = rows_by_code.get(c, [])
            nones = [r for r in crows if r["size"] is None]
            if known[c]:
                for k, s in enumerate(known[c]):
                    src = [r for r in crows if r["size"] == s] + (nones if k == 0 else [])
                    vss.append(mkvs(s, None if regime_b else c, src, bl[0]["prov"]))
            else:  # 全 None:碼不得丟
                vss.append(mkvs(None, c, nones, bl[0]["prov"]))
        colors = sorted({b["color"] for b in bl if b["color"]})
        # v2 雙軌:衝突偵測用 raw(v1 全帶圖說)——窄帶裁剪使一側證人變 null 時,
        # 殘存名不得補位離隊(單證人補位=自信錯值,違反「不確定一律進佇列」)
        raws = sorted({b.get("colorRaw", b["color"]) for b in bl
                       if b.get("colorRaw", b["color"])})
        if len(raws) > 1 or len(colors) > 1:  # 同碼異色名:不挑邊+佇列=上游錯綁偵測器
            extra.append({"reason": "code_color_conflict", "codes": codes,
                          "candidates": colors if len(colors) > 1 else raws,
                          "prov": bl[0]["prov"]})
        if len(codes) >= 2 and any(len(known[c]) >= 2 for c in codes):
            extra.append({"reason": "regime_conflict", "codes": codes,
                          "detail": {c: known[c] for c in codes}, "prov": bl[0]["prov"]})
        color_en = colors[0] if (len(colors) == 1 and len(raws) <= 1) else None
        ps = sorted(pseudo.intersection(codes))
        variants.append({
            **({"pseudoCodeSuspect": ps} if ps else {}),  # S2-5 出但標記(無中無鍵)
            "code": codes[0] if regime_b else None,
            "color": {"en": color_en, "zh": None,
                      **({"prov": next(b["prov"] for b in bl if b["color"])}
                         if color_en else {})},
            "colorQuality": color_quality(color_en) if color_en else None,
            "variantSizes": vss,
            "swatch": bl[0]["swatch"],  # E 裁圖主色樣;全部實例在 mergedFrom
            "swatchCrop": None,  # E
            "mergedFrom": [{"id": b["id"], "swatch": b["swatch"], "prov": b["prov"]}
                           for b in bl],
            "prov": bl[0]["prov"]})
    got = Counter(m["id"] for v in variants for m in v["mergedFrom"])
    assert (sum(got.values()) == len(bindings) and len(got) == len(bindings)
            and all(n == 1 for n in got.values())), "綁定認領未達互斥覆蓋"
    col_n = Counter(v["color"]["en"] for v in variants if v["color"]["en"])
    sp_demoted = sum(1 for d in collapse_demoted
                     if d["reason"] == "singlepage_overmerge_suspect")
    bd_demoted = sum(1 for d in collapse_demoted
                     if d["reason"] == "borderline_merge_suspect")
    rad_demoted = sum(1 for d in collapse_demoted
                      if d["reason"] == "assembly_merge_radius_suspect")
    # 通案四硬閘(獨立後驗,對最終 variants):單頁 ∧ ≥N ∧ 主色樣 area%≥AREA_T 者若逃逸=bug
    sp_escaped = sum(1 for v in variants
                     if len({m["swatch"]["page"] for m in v["mergedFrom"]}) == 1
                     and len(v["mergedFrom"]) >= L2_COLLAPSE_MIN
                     and main_area_pct(v["mergedFrom"]) >= AREA_T)
    stats = {"n_variants": len(variants), "merged_bindings": len(bindings),
             "d_demoted": len(demoted),
             "assembly_collapse_demoted": (len(collapse_demoted) - sp_demoted
                                           - bd_demoted - rad_demoted),        # 跨頁塌縮
             "assembly_collapse_clusters": n_collapse,
             "singlepage_overmerge_demoted": sp_demoted,                       # 段1 單頁過併
             "singlepage_overmerge_clusters": n_singlepage,
             "singlepage_escaped": sp_escaped,
             "assembly_borderline_demoted": bd_demoted,                        # 案1① 次臨界帶
             "assembly_borderline_clusters": n_borderline,
             "assembly_merge_radius_demoted": rad_demoted,                     # 案1② 爆炸半徑
             "assembly_merge_radius_clusters": n_radius,
             "claimed_rows": len(claimed),
             "same_color_unmerged": sum(n - 1 for n in col_n.values() if n > 1),
             "conflicts": Counter(e["reason"] for e in extra + demoted + collapse_demoted)}
    return variants, review + demoted + extra + collapse_demoted, stats


def extract_page(page, pdf_name, codes_doc, alpha_vocab, name_ctx, icon_ctx, row_ctx):
    """鏡射 m3_scan.scan_page(v6)逐碼判定,回傳 (variants, review, spec_rows,
    sizes, counts)。counts 供守恆對帳:與凍結 CSV 同名欄逐頁必須一致。"""
    name_idx, aligned_doc = name_ctx
    band_set, finish_vocab = row_ctx
    sws = extract_swatches(page, version=3)
    sus = {i for i, r in enumerate(sws) if icon_sus(r, icon_ctx)}
    words = page.get_text("words")
    sizes = page_sizes(words, V)
    fold = fold_x(page)
    pno = page.number + 1
    code_rows = []  # (w, sw_idx, ok_x, demoted)
    cap = {i: [] for i in range(len(sws))}  # 圖說詞(D5 color.en 標籤用,v2 窄帶)
    cap_raw = {i: [] for i in range(len(sws))}  # v1 全帶圖說(僅衝突偵測,不輸出)
    cap_ex = []  # v2 窄帶排除的名形 token → capcodes sidecar(S2-1 漏抓線索)
    for w, i, d in assign_words(page, sws, V):
        if (i is not None and d <= max(1.5 * sws[i].height, 40)
                and not (fold and (((w[0] + w[2]) / 2 < fold)
                                   != ((sws[i].x0 + sws[i].x1) / 2 < fold)))):
            cap_raw[i].append(w)
            r = sws[i]
            cy = (w[1] + w[3]) / 2
            dt, db = abs(cy - r.y0), abs(r.y1 - cy)
            near = dt <= CAP_TOP if dt <= db else db <= CAP_BOT
            if norm(w[4]) in codes_doc:
                pass  # 已偵測碼不是圖說詞(防碼洩入色名;S2-1 落地後尤要)
            elif r.height > CAP_BIG_H and not near:
                # 照片級色樣:帶外=頁面文字非圖說;名形 token 留線索不留色名
                if is_name(w[4], alpha_vocab) and _latin(w[4]) and len(norm(w[4])) <= 8:
                    cap_ex.append({"token": w[4], "page": pno,
                                   "bbox": [round(x, 1) for x in w[:4]]})
            else:
                cap[i].append(w)  # 圖說幾何同 doc_name_index(帶距+同折縫側)
        if norm(w[4]) not in codes_doc:
            continue
        cx = (w[0] + w[2]) / 2
        ok_x = i is not None and sws[i].x0 - 2 <= cx <= sws[i].x1 + 2
        demoted = ok_x and i in sus  # M5-2:疑似小圖形上的對齊 → 降級進佇列
        ok_blk = V >= 7 and i is not None and d == -2.0  # M5-3 塊綁哨兵(V=6 惰性)
        if ok_blk and i in sus:  # 塊綁到疑似小圖形 → 照 M5-2 降級(雙軌皮帶)
            ok_blk, demoted = False, True
        code_rows.append((w, i, ok_x and not demoted, demoted, ok_blk))
    n_codes = len(code_rows)
    aligned = sum(ok for _, _, ok, _, _ in code_rows)
    blk = sum(b for *_, b in code_rows)
    hints = {}  # M5-1:名鍵=佇列內建議答案,不離隊;頁級閘門同 scan_page(v7:計 blk)
    if n_codes >= 5 and aligned + blk <= 0.2 * n_codes:
        good = page_good_names(words, codes_doc, alpha_vocab, fold)
        for w, i, ok_x, _, ok_blk in code_rows:
            if not ok_x and not ok_blk and norm(w[4]) not in aligned_doc:
                h = name_bind(w, words, name_idx, alpha_vocab, fold, good)
                if h is not None:
                    hints[id(w)] = h
    bindings, review, spec_rows, with_size = [], [], [], 0
    for w, i, ok_x, demoted, ok_blk in code_rows:
        size = row_size(sizes, w, V, fold)
        with_size += size is not None
        sr = spec_row(w, size, words, fold, pdf_name, pno,
                      band_set, finish_vocab)  # C:每偵測碼一列
        sr["id"] = f"s:{pno}:{len(spec_rows)}"  # 確定性身分證(D 可追溯守恆)
        spec_rows.append(sr)
        if ok_x or ok_blk:
            bindings.append({
                "id": f"b:{pno}:{len(bindings)}",
                "code": norm(w[4]),
                "color": caption_name(cap[i], alpha_vocab),  # 標籤,非鍵;首做=I 驗
                "colorRaw": caption_name(cap_raw[i], alpha_vocab),  # 衝突偵測用,不落 JSON
                "swatch": {"page": pno, "bbox": [round(v, 1) for v in sws[i]]},
                "prov": prov(pdf_name, pno, w[:4],
                             "geom_v7_block" if ok_blk else "geom_v6_x_aligned")})
        else:
            item = {"code": norm(w[4]),
                    "reason": ("icon_demoted" if demoted else
                               "orphan" if i is None else "not_x_aligned"),
                    "prov": prov(pdf_name, pno, w[:4], "geom_v6_queue")}
            if id(w) in hints:  # ponytail: 假說給 (頁,色樣序);bbox 回解=K 佇列產線化
                item["nameHint"] = {"page": hints[id(w)][0] + 1,
                                    "swatchIdx": hints[id(w)][1]}
            review.append(item)
    counts = dict(n_sw=len(sws), n_codes=n_codes, code_x_aligned=aligned,
                  code_orphan=sum(1 for _, i, _, _, _ in code_rows if i is None),
                  code_icon_demoted=sum(d for *_, d, _ in code_rows),
                  code_name_bound=len(hints),
                  code_needs_review=n_codes - aligned - blk, code_with_size=with_size,
                  **({"code_block_bound": blk} if V >= 7 else {}))  # 同 scan_page 欄位閘
    assert len(bindings) == aligned + blk and len(review) == n_codes - aligned - blk
    assert len(spec_rows) == n_codes  # C 守恆:specByCode 每偵測碼一列
    size_toks = [(norm_size(tok), pno) for _, _, _, tok in sizes]
    sw_info = [{"page": pno, "bbox": [round(x, 1) for x in r],
                "caption": caption_name(cap[i], alpha_vocab)}
               for i, r in enumerate(sws)]  # E/K:骨架檔色樣裁圖用
    return bindings, review, spec_rows, size_toks, counts, sw_info, cap_ex


def extract_pdf(pdf_path, vocabs):
    """一份 PDF → (json_doc, review_items, per_page_counts)。"""
    code_vocab, alpha_vocab = vocabs
    doc = fitz.open(pdf_path)
    spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
    codes_doc, routed = code_candidates(doc, code_vocab, len(spec), V,
                                        alpha_vocab)  # v8:停用詞補充(v≤7 不用)
    band_set = routed.get("band", set())
    # C 語境守恆:priceBand 接的是 S2-2「同一筆分流紀錄」;分流 token 不得同時是
    # 綁定候選(kept 與 routed 由 route_junk 構造互斥,這裡守住不變量)
    assert band_set.isdisjoint(codes_doc), "band token 語境打架"
    name_ctx = doc_name_index(spec, codes_doc, alpha_vocab, V)
    icon_ctx = doc_icon_stats(spec, V)  # M5-2b 版本閘佈線:V=12→舊中位逐位;切 V=13 時自動 med_ex
    row_ctx = (band_set, doc_finish_vocab(spec, codes_doc, alpha_vocab))
    name = pdf_path.name
    bindings, review_a, by_code, page_counts, first_seen = [], [], [], [], {}
    n_sw_total, sw_info, cap_ex_doc = 0, [], []
    for page in spec:
        b, r, sr, toks, c, si, ce = extract_page(page, name, codes_doc, alpha_vocab,
                                                 name_ctx, icon_ctx, row_ctx)
        bindings += b
        review_a += r
        by_code += sr
        n_sw_total += c["n_sw"]
        sw_info += si
        cap_ex_doc += ce
        page_counts.append({"doc": name, "page": page.number + 1, **c})
        for tok, pno in toks:
            first_seen.setdefault(tok, pno)
    sus = pseudo_suspects(doc, codes_doc, pdf_path.stem, alpha_vocab,
                          code_vocab)  # S2-5 旗標(出但標記,不影響綁定/佇列)
    page_dims = {p.number + 1: (p.rect.width * p.rect.height) for p in spec}  # 段1 area%
    variants, review, stats = assemble(bindings, by_code, review_a,
                                       {t[0] for t in band_set},  # L2 v2 P 脈絡
                                       pseudo=sus, page_dims=page_dims)
    stats["sw_info"] = sw_info
    stats["cap_excluded"] = cap_ex_doc
    json_doc = {
        "pipelineStage": "MVP(A+C+D+E+K)",  # C/D 新規則正確率未驗(I 給數)
        "bindingVersion": f"v{V}",
        "dHardening": 4,  # 2=S2-2 L2 v2 合併鍵 C3(merge_key_suspect);3=通案四跨頁塌縮守衛
        # (工作包#7;assembly_collapse_suspect;跨頁∧色名衝突∧≥L2_COLLAPSE_MIN);4=段1 單頁
        # 過併守衛(singlepage_overmerge_suspect;單頁∧≥L2_COLLAPSE_MIN∧主色樣 area%≥AREA_T)
        "knownGaps": KNOWN_GAPS,
        # 無碼廠骨架(Sodai 型):0 綁定 ∧ 有色樣 → 只出骨架,色樣假說全在佇列。
        # 案1 註:有綁定但全數被守衛撤權(Topcer General 19 全落佇列)≠無碼廠——佇列
        # 本身(帶 prov/swatch)即人工材料,不翻骨架(骨架裁全頁色樣、K/E 形狀丕變)。
        "seriesSkeleton": bool(not variants and not bindings and n_sw_total),
        "brand": {"value": pdf_path.parent.name, "prov": prov(name, method="folder")},
        "series": [{
            "seriesName": {"en": {"value": pdf_path.stem, "prov": prov(name, method="filename")},
                           "zh": None},
            "allSizes": [{"size": t, "prov": prov(name, p, method="size_re_union")}
                         for t, p in sorted(first_seen.items())],
            "specByCode": by_code,
            "variants": variants,
        }],
        "needsReviewCount": len(review),
    }
    return json_doc, review, page_counts, stats


def crop_png(doc, page_no, bbox, path):
    """E:fitz clip 裁圖(純輸出,不碰任何綁定/組裝結果)。
    # ponytail: naive RGB 150dpi;ICC 色彩管理+同圖多引用去重=MVP 後補件"""
    doc[page_no - 1].get_pixmap(clip=fitz.Rect(bbox), dpi=150).save(path)


def write_out(pdf_path, outdir, vocabs):
    """寫出三件:SCHEMA JSON + K 佇列檔(items=流動中佇列原樣落檔,零增減)+
    E 裁圖(aligned Variant 100%;nameHint 目標;骨架檔全色樣=佇列非入庫)。"""
    json_doc, review, page_counts, stats = extract_pdf(pdf_path, vocabs)
    d = Path(outdir) / pdf_path.parent.name
    cname = f"{pdf_path.stem}_crops"
    cdir = d / cname
    shutil.rmtree(cdir, ignore_errors=True)  # 裁圖可重生,清舊防殘留
    cdir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    name = pdf_path.name
    for k, v in enumerate(json_doc["series"][0]["variants"]):  # E:主色樣(實例全在 mergedFrom)
        sw = v["swatch"]
        fn = f"v{k:03d}_p{sw['page']}.png"
        crop_png(doc, sw["page"], sw["bbox"], cdir / fn)
        v["swatchCrop"] = {"png": f"{cname}/{fn}",
                           "prov": prov(name, sw["page"], sw["bbox"], "fitz_clip_150dpi")}
    sw_cache = {}  # K:名鍵假說目標解析 bbox+裁圖(加速人工複查)
    for k, item in enumerate(review):
        h = item.get("nameHint")
        if not h:
            continue
        pno = h["page"]
        if pno not in sw_cache:  # 索引釘 v3 幾何(同 doc_name_index)
            sw_cache[pno] = extract_swatches(doc[pno - 1], version=3)
        r = sw_cache[pno][h["swatchIdx"]]
        h["bbox"] = [round(x, 1) for x in r]
        fn = f"q{k:03d}_p{pno}_sw{h['swatchIdx']}.png"
        crop_png(doc, pno, h["bbox"], cdir / fn)
        h["crop"] = f"{cname}/{fn}"
    skel = []
    if json_doc["seriesSkeleton"]:  # 無碼廠:全 spec 頁色樣裁圖供人工建檔——佇列非入庫
        for j, s in enumerate(stats["sw_info"]):
            fn = f"sk{j:03d}_p{s['page']}.png"
            crop_png(doc, s["page"], s["bbox"], cdir / fn)
            skel.append({**s, "crop": f"{cname}/{fn}",
                         "source": "skeleton_doc_swatch",
                         "status": "queue_only_not_ingested"})
    review_doc = {"pdf": name, "bindingVersion": f"v{V}",
                  "items": review,  # 筆數=掃描佇列,K 不新增不刪減
                  "skeletonSwatches": skel}
    (d / f"{pdf_path.stem}.json").write_text(
        json.dumps(json_doc, indent=1, ensure_ascii=False))
    (d / f"{pdf_path.stem}.review.json").write_text(
        json.dumps(review_doc, indent=1, ensure_ascii=False))
    if stats["cap_excluded"]:  # v2 窄帶排除 token → S2-1 線索 sidecar(非產品輸出)
        agg = {}
        for x in stats["cap_excluded"]:
            a = agg.setdefault(x["token"], {"token": x["token"], "n": 0, "pages": [],
                                            "firstProv": {"page": x["page"], "bbox": x["bbox"]}})
            a["n"] += 1
            if x["page"] not in a["pages"]:
                a["pages"].append(x["page"])
        (d / f"{pdf_path.stem}.capcodes.json").write_text(json.dumps({
            "pdf": name,
            "hint": "S2-1 線索:照片級色樣圖說窄帶外排除的名形 token(≤8 字母)——"
                    "含 B 類漏抓真 SKU 與色名雜訊,僅供偵測缺口修復,非產品輸出",
            "tokens": sorted(agg.values(), key=lambda a: -a["n"])},
            indent=1, ensure_ascii=False))
    return json_doc, review, page_counts, stats


def check_prov(json_doc, review):
    """prov 完整性:有值欄位必附 {pdf,page,bbox,method}(頁面抽取欄 bbox 必填;
    檔名/資料夾級欄 page/bbox=None 誠實留空)。回傳缺陷清單。"""
    bad = []
    for s in json_doc["series"]:
        for v in s["variants"]:
            if not (v["prov"]["pdf"] and v["prov"]["page"] and v["prov"]["bbox"]
                    and v["prov"]["method"]):
                bad.append(("variant", v["code"]))
            c = v.get("swatchCrop")  # E:aligned Variant 100% 有裁圖+prov
            if not (c and c["png"] and c["prov"]["page"] and c["prov"]["bbox"]):
                bad.append(("swatchCrop", v["code"]))
            if v["color"]["en"] is not None and not v["color"].get("prov"):
                bad.append(("color", v["color"]["en"]))
            for m in v["mergedFrom"]:
                if not (m["prov"]["page"] and m["prov"]["bbox"]):
                    bad.append(("mergedFrom", m["id"]))
            for vs in v["variantSizes"]:
                if not (vs["prov"]["page"] and vs["prov"]["bbox"]):
                    bad.append(("variantSize", v["code"]))
        for a in s["allSizes"]:
            if not (a["prov"]["pdf"] and a["prov"]["page"]):
                bad.append(("allSize", a["size"]))
        for r in s["specByCode"]:
            if not (r["prov"]["pdf"] and r["prov"]["page"] and r["prov"]["bbox"]
                    and r["prov"]["method"]):
                bad.append(("specRow", r["code"]))
    for r in review:
        if not (r["prov"]["pdf"] and r["prov"]["page"] and r["prov"]["bbox"]):
            bad.append(("review", r["code"]))
    return bad


def spec_row_stats(json_doc):
    """C 結構自測:抽到率計數+格式合法性缺陷(正確率不在此,I 給數)。"""
    n = Counter()
    bad = []
    for s in json_doc["series"]:
        for r in s["specByCode"]:
            n["rows"] += 1
            for k in ("size", "surface", "priceBand", "packing"):
                n[k] += r[k] is not None
            if r["priceBand"] and not re.fullmatch(r"[A-Z]\d{1,3}", r["priceBand"]):
                bad.append(("priceBand", r["priceBand"]))  # v10:L1 歸隊使 3 位數
                # 家族成員(A105/A107 型)成為合法 priceBand 值;此為輸出格式
                # sanity 檢查非偵測規則,上限隨 band 宇宙擴至 \d{1,3}
            if r["surface"] and not all(norm(t).isalpha() for t in r["surface"].split()):
                bad.append(("surface", r["surface"]))
            for k, v in (r["packing"] or {}).items():
                n["pk_" + k] += 1
                try:
                    float(v)
                except ValueError:
                    bad.append(("packing", v))
    return n, bad


def smoke(outdir):
    """dev 端到端:catalogs/ 全跑 → 守恆對帳(逐頁計數 vs 凍結 s21ext_dev_v12.csv,
    一筆不多不少)+ prov 完整性 + JSON/佇列筆數對帳 + C 結構自測。"""
    with open("output/s21ext_dev_v12.csv", newline="") as f:
        frozen_rows = list(csv.DictReader(f))
    frozen = {(r["doc"], int(r["page"])): r for r in frozen_rows}
    assert len(frozen) == len(frozen_rows), "凍結 CSV (doc,page) 鍵撞"
    keys = ["n_sw", "n_codes", "code_x_aligned", "code_block_bound", "code_orphan",
            "code_icon_demoted", "code_name_bound", "code_needs_review", "code_with_size"]
    vocabs = build_vocabs()
    got, mismatch, prov_bad, fmt_bad, skel, crop_missing = {}, [], [], [], [], []
    tot = {"variants": 0, "review": 0, "sizes": 0}
    c_stat, d_stat, d_conf, e_crop = Counter(), Counter(), Counter(), Counter()
    asm = Counter()  # 通案四 組裝層守恆:跨頁/hub 吞併上限 + 塌縮逃逸偵測
    for pdf in sorted(Path("catalogs").rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        json_doc, review, page_counts, stats = write_out(pdf, outdir, vocabs)
        prov_bad += check_prov(json_doc, review)
        # E/K 落檔驗證:裁圖檔案實際存在、nameHint 已解析 bbox+crop、佇列檔筆數守恆
        bdir = Path(outdir) / pdf.parent.name
        for v in json_doc["series"][0]["variants"]:
            e_crop["variant"] += 1
            if not (bdir / v["swatchCrop"]["png"]).is_file():
                crop_missing.append(v["swatchCrop"]["png"])
            # 通案四:每 Variant 跨頁/吞併量;塌縮逃逸=跨頁∧color=None∧≥門檻(守衛後應=0)
            vp = len({m["swatch"]["page"] for m in v["mergedFrom"]})
            asm["max_pages"] = max(asm["max_pages"], vp)
            asm["max_merge"] = max(asm["max_merge"], len(v["mergedFrom"]))
            if vp >= 2 and v["color"]["en"] is None and len(v["mergedFrom"]) >= L2_COLLAPSE_MIN:
                asm["escaped_collapse"] += 1
            # 案1 硬閘:次臨界帶([18,20) 跨頁∧無名)/超半徑(>5頁 ∨ 跨頁>24綁定)出貨=0
            if (vp >= 2 and v["color"]["en"] is None
                    and L2_BORDERLINE_MIN <= len(v["mergedFrom"]) < L2_COLLAPSE_MIN):
                asm["escaped_borderline"] += 1
            if (vp > L2_AUTO_MERGE_MAX_PAGES
                    or (vp >= 2 and len(v["mergedFrom"]) > L2_AUTO_MERGED_FROM_MAX)):
                asm["escaped_radius"] += 1
        for item in review:
            if "nameHint" in item:
                e_crop["nameHint"] += 1
                if not (item["nameHint"].get("bbox")
                        and (bdir / item["nameHint"]["crop"]).is_file()):
                    crop_missing.append(("nameHint", item["code"]))
        rv_doc = json.loads((bdir / f"{pdf.stem}.review.json").read_text())
        assert len(rv_doc["items"]) == len(review)  # K:落檔=流動佇列,零增減
        for s_ in rv_doc["skeletonSwatches"]:
            e_crop["skeleton"] += 1
            if not (bdir / s_["crop"]).is_file():
                crop_missing.append(s_["crop"])
        n, bad = spec_row_stats(json_doc)
        c_stat += n
        fmt_bad += bad
        d_conf += stats["conflicts"]
        d_stat += Counter({k: stats[k] for k in
                           ("n_variants", "merged_bindings", "d_demoted",
                            "assembly_collapse_demoted", "assembly_collapse_clusters",
                            "singlepage_overmerge_demoted", "singlepage_overmerge_clusters",
                            "assembly_borderline_demoted", "assembly_borderline_clusters",
                            "assembly_merge_radius_demoted", "assembly_merge_radius_clusters",
                            "claimed_rows", "same_color_unmerged")})
        asm["escaped_singlepage"] += stats["singlepage_escaped"]  # 通案四硬閘(段1)
        d_stat["cap_excluded"] += len(stats["cap_excluded"])
        if json_doc["seriesSkeleton"]:
            skel.append(pdf.parent.name)
        tot["variants"] += sum(len(s["variants"]) for s in json_doc["series"])
        tot["review"] += len(review)
        tot["sizes"] += sum(len(s["allSizes"]) for s in json_doc["series"])
        for c in page_counts:
            got[(c["doc"], c["page"])] = c
            fr = frozen.get((c["doc"], c["page"]))
            if fr is None:
                mismatch.append((c["doc"], c["page"], "頁不在凍結 CSV"))
            else:
                diff = {k: (c[k], int(fr[k])) for k in keys if c[k] != int(fr[k])}
                if diff:
                    mismatch.append((c["doc"], c["page"], diff))
        print(pdf.parent.name, pdf.name, "done", flush=True)
    missing = set(frozen) - set(got)
    n_al = sum(int(r["code_x_aligned"]) + int(r["code_block_bound"])
               for r in frozen_rows)  # v7+:綁定=x對齊+塊綁(mergedFrom 雙路)
    n_rv = sum(int(r["code_needs_review"]) for r in frozen_rows)
    n_cd = sum(int(r["n_codes"]) for r in frozen_rows)
    n_dx = sum(d_conf.values())  # D 新增佇列項(regime/color conflict)
    print(f"\n[smoke] pages={len(got)}/{len(frozen)}  頁級計數不一致={len(mismatch)}"
          f"  凍結有但產線漏頁={len(missing)}")
    print(f"  A 守恆:Σ mergedFrom={d_stat['merged_bindings']}+L2 降級 {d_stat['d_demoted']}"
          f"+跨頁塌縮 {d_stat['assembly_collapse_demoted']}+單頁過併 {d_stat['singlepage_overmerge_demoted']}"
          f"+次臨界 {d_stat['assembly_borderline_demoted']}+超半徑 {d_stat['assembly_merge_radius_demoted']}"
          f"=凍結綁定總數 {n_al}"
          f"  佇列={tot['review']}=A {tot['review'] - n_dx} (凍結 review {n_rv})+D 衝突 {n_dx}")
    print(f"  D 組裝:Variant={d_stat['n_variants']}  認領 spec 列={d_stat['claimed_rows']}"
          f"  衝突佇列={dict(d_conf)}  同色未合併={d_stat['same_color_unmerged']}"
          f"  骨架檔={skel}")
    print(f"  ★通案四 組裝層守恆:最大 Variant 跨頁={asm['max_pages']}  最大吞併={asm['max_merge']}"
          f"  跨頁塌縮團={d_stat['assembly_collapse_clusters']} 團/{d_stat['assembly_collapse_demoted']} 綁定"
          f"  單頁過併團={d_stat['singlepage_overmerge_clusters']} 團/{d_stat['singlepage_overmerge_demoted']} 綁定"
          f"\n    案1:次臨界帶={d_stat['assembly_borderline_clusters']} 團/{d_stat['assembly_borderline_demoted']} 綁定"
          f"  超半徑={d_stat['assembly_merge_radius_clusters']} 團/{d_stat['assembly_merge_radius_demoted']} 綁定"
          f"  逃逸(跨頁塌縮={asm['escaped_collapse']}/單頁過併={asm['escaped_singlepage']}"
          f"/次臨界={asm['escaped_borderline']}/超半徑={asm['escaped_radius']}) (硬閘=0)")
    print(f"  E 裁圖:variant={e_crop['variant']} (契約=aligned Variant 100%)"
          f"  nameHint={e_crop['nameHint']}  骨架色樣={e_crop['skeleton']}"
          f"  缺檔={len(crop_missing)}")
    print(f"  K 佇列落檔:items 總數={tot['review']} (=掃描佇列 {n_rv}+D 衝突 {n_dx},零增減)")
    print(f"  prov 缺陷={len(prov_bad)}  allSizes 條目={tot['sizes']}"
          f"  capExcluded(S2-1 線索)={d_stat['cap_excluded']}")
    nr = c_stat["rows"] or 1
    print(f"  C|specByCode 列數={c_stat['rows']} (凍結 n_codes 總數 {n_cd})  格式缺陷={len(fmt_bad)}")
    print(f"    抽到率(dev 結構自測,非正確率——正確率=I):size={c_stat['size']/nr:.1%}"
          f"  surface={c_stat['surface']/nr:.1%}  priceBand={c_stat['priceBand']/nr:.1%}"
          f"  packing={c_stat['packing']/nr:.1%}"
          f" (pcs={c_stat['pk_pcsBox']} m2={c_stat['pk_m2Box']} kg={c_stat['pk_kgBox']})")
    for m in mismatch[:10]:
        print("  MISMATCH", m)
    for b in fmt_bad[:10]:
        print("  FORMAT", b)
    if missing:
        print("  MISSING", sorted(missing)[:10])
    ok = (not mismatch and not missing and not prov_bad and not fmt_bad
          and not crop_missing                   # E:裁圖檔案零缺
          and d_stat["merged_bindings"] + d_stat["d_demoted"]
          + d_stat["assembly_collapse_demoted"]
          + d_stat["singlepage_overmerge_demoted"]
          + d_stat["assembly_borderline_demoted"]
          + d_stat["assembly_merge_radius_demoted"] == n_al  # D 守恆:原始綁定零遺失
          # (SL-6~8 + 塌縮/單頁過併/次臨界/超半徑降級=逐筆帶 prov/swatch 落佇列,資料無損)
          and tot["review"] - n_dx == n_rv       # 佇列只增不減(A 項全數保留)
          and asm["escaped_collapse"] == 0       # ★通案四硬閘:零跨頁塌縮 Variant 出貨
          and asm["escaped_singlepage"] == 0     # ★通案四硬閘:零單頁過併 Variant 出貨
          and asm["escaped_borderline"] == 0     # ★通案四硬閘(案1):零次臨界帶出貨
          and asm["escaped_radius"] == 0         # ★通案四硬閘(案1):零超半徑出貨
          and c_stat["rows"] == n_cd)
    print("smoke", "OK" if ok else "FAILED")
    return 0 if ok else 1


def selftest():
    """D 組裝規則單元測試(合成資料,不碰 corpus)。T 編號對 D_DESIGN.md §二。"""
    P = {"pdf": "t.pdf", "page": 1, "bbox": [0, 0, 1, 1], "method": "t"}

    def B(k, code, sw, color=None, page=1):
        return {"id": f"b:{page}:{k}", "code": code,
                "swatch": {"page": page, "bbox": sw}, "color": color, "prov": P}

    def S(k, code, size, page=1, band=None, surf=None):
        return {"id": f"s:{page}:{k}", "code": code, "size": size, "surface": surf,
                "priceBand": band, "packing": None, "prov": P}

    sw1, sw2 = [0, 0, 10, 10], [20, 0, 30, 10]
    VS = lambda v: {(x["size"], x["orderCode"]) for x in v["variantSizes"]}  # noqa: E731

    # T1 體制A 正例:3 碼同色樣各一尺寸 → code=null、orderCode 各就位
    vs, rv, st = assemble([B(0, "C1", sw1), B(1, "C2", sw1), B(2, "C3", sw1)],
                          [S(0, "C1", "60x60"), S(1, "C2", "60x120"), S(2, "C3", "30x60")], [])
    assert len(vs) == 1 and vs[0]["code"] is None and not rv
    assert VS(vs[0]) == {("60x60", "C1"), ("60x120", "C2"), ("30x60", "C3")}
    print("T1 PASS 體制A")
    # T2 體制B 正例:1 碼 3 尺寸 → code=碼、orderCode 全 null
    vs, rv, st = assemble([B(0, "C1", sw1)],
                          [S(0, "C1", "60x60"), S(1, "C1", "60x120"), S(2, "C1", "30x60")], [])
    assert vs[0]["code"] == "C1" and not rv
    assert VS(vs[0]) == {("60x60", None), ("60x120", None), ("30x60", None)}
    print("T2 PASS 體制B")
    # T3 臨界 1碼1尺寸 → A 形式、無佇列項
    vs, rv, st = assemble([B(0, "C1", sw1)], [S(0, "C1", "60x60")], [])
    assert vs[0]["code"] is None and VS(vs[0]) == {("60x60", "C1")} and not rv
    print("T3 PASS 臨界→A形式")
    # T4 反例|混合訊號 → A 形式無損展開 + regime_conflict 進佇列
    vs, rv, st = assemble([B(0, "C1", sw1), B(1, "C2", sw1)],
                          [S(0, "C1", "60x60"), S(1, "C1", "60x120"), S(2, "C2", "30x60")], [])
    assert vs[0]["code"] is None
    assert VS(vs[0]) == {("60x60", "C1"), ("60x120", "C1"), ("30x60", "C2")}
    assert [r["reason"] for r in rv] == ["regime_conflict"]
    print("T4 PASS 混合訊號擋下")
    # T5 邊界|None 尺寸不算 B 證據、併入該碼首 VS 認領
    vs, rv, st = assemble([B(0, "C1", sw1)], [S(0, "C1", None), S(1, "C1", "60x60")], [])
    assert vs[0]["code"] is None and len(vs[0]["variantSizes"]) == 1
    assert set(vs[0]["variantSizes"][0]["derivedFrom"]) == {"s:1:0", "s:1:1"}
    print("T5 PASS None不算B證據")
    # T6 邊界|全 None → 碼保留在 orderCode
    vs, rv, st = assemble([B(0, "C1", sw1)], [S(0, "C1", None)], [])
    assert VS(vs[0]) == {(None, "C1")}
    print("T6 PASS 全None碼不丟")
    # T7 跨頁同碼合併 → 1 Variant、mergedFrom 兩筆
    vs, rv, st = assemble([B(0, "C1", sw1, page=3), B(0, "C1", sw2, page=5)],
                          [S(0, "C1", "60x60", page=3)], [])
    assert len(vs) == 1 and {m["id"] for m in vs[0]["mergedFrom"]} == {"b:3:0", "b:5:0"}
    print("T7 PASS 跨頁code合併")
    # T8 反例|同碼異色名 → 合併但 color=null + code_color_conflict
    vs, rv, st = assemble([B(0, "C1", sw1, "WHITE", page=3), B(0, "C1", sw2, "BLACK", page=5)],
                          [S(0, "C1", "60x60", page=3)], [])
    assert len(vs) == 1 and vs[0]["color"]["en"] is None
    assert [r["reason"] for r in rv] == ["code_color_conflict"]
    print("T8 PASS 異色名不挑邊")
    # T9 邊界|折縫:同頁同碼左右色樣照樣以 code 合併;同頁異碼同色名 → 不合
    vs, rv, st = assemble([B(0, "C1", sw1), B(1, "C1", sw2)], [S(0, "C1", "60x60")], [])
    assert len(vs) == 1
    vs, rv, st = assemble([B(0, "C1", sw1, "WHITE"), B(1, "C2", sw2, "WHITE")],
                          [S(0, "C1", "60x60"), S(1, "C2", "60x60")], [])
    assert len(vs) == 2 and not rv
    print("T9 PASS 幾何不參與合併")
    # T10 反例|色名非鍵:跨頁同色名異碼 → 寧可不合(2 Variants)
    vs, rv, st = assemble([B(0, "C1", sw1, "WHITE", page=3), B(0, "C2", sw2, "WHITE", page=9)],
                          [S(0, "C1", "60x60", page=3), S(0, "C2", "120x120", page=9)], [])
    assert len(vs) == 2 and st["same_color_unmerged"] == 1 and not rv
    print("T10 PASS 色名不觸發合併")
    # T11 (碼,尺寸) 去重:3 列 → 1 VS 認領 3 列
    vs, rv, st = assemble([B(0, "C1", sw1)],
                          [S(0, "C1", "60x60"), S(1, "C1", "60x60"), S(2, "C1", "60x60")], [])
    assert len(vs[0]["variantSizes"]) == 1
    assert len(vs[0]["variantSizes"][0]["derivedFrom"]) == 3
    print("T11 PASS 去重認領")
    # T12 欄值衝突 → null 不猜(原始列仍在 specByCode,不在 assemble 動)
    vs, rv, st = assemble([B(0, "C1", sw1)],
                          [S(0, "C1", "60x60", band="T31"), S(1, "C1", "60x60", band="T14")], [])
    assert vs[0]["variantSizes"][0]["priceBand"] is None
    vs, rv, st = assemble([B(0, "C1", sw1)],
                          [S(0, "C1", "60x60", band="T31"), S(1, "C1", "60x60", band="T31")], [])
    assert vs[0]["variantSizes"][0]["priceBand"] == "T31"
    print("T12 PASS 衝突→null")
    # T13 無碼廠:0 綁定 → variants=[]、佇列原樣(nameHint 全在)
    q = [{"code": "X1", "reason": "orphan", "prov": P, "nameHint": {"page": 2, "swatchIdx": 0}}]
    vs, rv, st = assemble([], [S(0, "X1", "60x60")], q)
    assert vs == [] and rv == q and st["claimed_rows"] == 0
    print("T13 PASS 骨架路徑")
    # T14 反例守門|nameHint 唯一也不晉升(assemble 無任何 nameHint→Variant 通道)
    vs, rv, st = assemble([], [], [{"code": "X1", "reason": "orphan", "prov": P,
                                    "nameHint": {"page": 2, "swatchIdx": 0}}])
    assert vs == [] and rv[0]["nameHint"] == {"page": 2, "swatchIdx": 0}
    print("T14 PASS 假說不入庫")
    # T15 混合檔:2 aligned + 佇列 30 筆 → 恰 2 Variants、佇列只增不減
    q30 = [{"code": f"X{k}", "reason": "orphan", "prov": P} for k in range(30)]
    vs, rv, st = assemble([B(0, "C1", sw1), B(1, "C2", sw2)],
                          [S(0, "C1", "60x60"), S(1, "C2", "60x60")], q30)
    assert len(vs) == 2 and rv[:30] == q30 and len(rv) == 30
    print("T15 PASS 混合檔")
    # T16-T18 color.en 標籤(is_name 規則:非泛用詞、非全小寫、字母≥3)
    W = lambda x0, y0, x1, y1, t: (x0, y0, x1, y1, t)  # noqa: E731
    vocab = {"RETT"}
    assert caption_name([W(0, 0, 40, 8, "PLASTER"), W(45, 0, 70, 8, "Rett."),
                         W(0, 10, 30, 18, "60x60")], vocab) == "PLASTER"
    print("T16 PASS color.en 正例")
    assert caption_name([W(0, 0, 40, 8, "naturale"), W(45, 0, 70, 8, "Rett.")], vocab) is None
    print("T17 PASS color.en 反例(散文/泛用詞→null)")
    assert caption_name([W(45, 0, 90, 8, "WHITE"), W(0, 0, 40, 8, "STEEL")], vocab) == "STEEL WHITE"
    print("T18 PASS color.en x序連接")
    # T19 可追溯守恆(綜合):Σ mergedFrom=綁定數、認領互斥覆蓋、佇列只增不減
    bs = [B(0, "C1", sw1, "WHITE"), B(1, "C2", sw2, "GREY"),
          B(0, "C1", [40, 0, 50, 10], "WHITE", page=2)]  # C1 跨頁合併(B 型)
    rows = [S(0, "C1", "60x60"), S(1, "C2", "60x120"),
            S(0, "C1", "90x90", page=2), S(1, "C9", "30x30", page=2)]  # C9=未對齊碼
    vs, rv, st = assemble(bs, rows, q)
    assert sum(len(v["mergedFrom"]) for v in vs) == len(bs) == st["merged_bindings"]
    got_ids = sorted(m["id"] for v in vs for m in v["mergedFrom"])
    assert got_ids == sorted(b["id"] for b in bs)  # 覆蓋∧互斥(零遺失、零重複)
    claimed = [d for v in vs for x in v["variantSizes"] for d in x["derivedFrom"]]
    assert sorted(claimed) == ["s:1:0", "s:1:1", "s:2:0"]  # C9 列不認領、其餘恰一次
    assert rv == q  # 佇列只增不減(本例無衝突→零新增)
    assert {v["code"] for v in vs} == {None, "C1"}  # C1 跨頁2尺寸=B;C2=A形式
    print("T19 PASS 可追溯守恆")
    # T20 color.en 非拉丁濾(v2):西里爾等多語 token 不進色名
    assert caption_name([W(0, 0, 40, 8, "ДЕКОРЫ"), W(45, 0, 90, 8, "STEEL")], vocab) == "STEEL"
    assert _latin("BIANCO") and not _latin("Изделия")
    print("T20 PASS color.en 非拉丁濾")
    # T21 v2 雙軌守門|raw 衝突時 trimmed 單證人不得補位離隊(色名 None+佇列)
    b1, b2 = B(0, "C1", sw1, "JUNKA"), B(1, "C1", sw2, None, page=2)
    b1["colorRaw"], b2["colorRaw"] = "JUNKA LONG", "OTHER RAW"
    vs, rv, st = assemble([b1, b2], [S(0, "C1", "60x60"), S(0, "C1", "90x90", page=2)], [])
    assert vs[0]["color"]["en"] is None
    assert any(r["reason"] == "code_color_conflict" for r in rv)
    print("T21 PASS 雙軌守門(單證人補位)")
    # T22 colorQuality 聲明旗標:溢收→needs_review、正常→clean、無色名→None
    vs, _, _ = assemble([B(0, "C1", sw1, "STEEL")], [S(0, "C1", "60x60")], [])
    assert vs[0]["colorQuality"] == "clean"
    vs, _, _ = assemble([B(0, "C2", sw2, "AAA BBB CCC DDD")], [S(1, "C2", "60x60")], [])
    assert vs[0]["colorQuality"] == "needs_review"
    vs, _, _ = assemble([B(0, "C3", sw1, None)], [S(0, "C3", "60x60")], [])
    assert vs[0]["colorQuality"] is None
    print("T22 PASS colorQuality 旗標")
    # T23|SL-6 v2(裁決①條件一):「B/A' 雙偽逃逸+L2 接住」注入構造=備援活體證明
    #     A 部:L1 層實測逃逸——band 家族存在、A991 兩實例不同列(A' max=1)且
    #     不與 band 欄對齊(B 偽)→ v10 kept 仍含 A991(L1 雙偽漏網證明)
    da = fitz.open()
    pa_ = da.new_page(width=600, height=800)
    for x, y, t in [(500, 100, "A11"), (500, 130, "A28"), (500, 160, "A86"),
                    (100, 300, "A991"), (300, 500, "A991")]:
        pa_.insert_text((x, y), t, fontsize=10)
    ka, ra = code_candidates(da, set(), 5, 10, frozenset())
    assert "A991" in ka and ra["band"] == {"A11", "A28", "A86"}, (ka, ra)
    #     B 部:L2 接住——A991 鏈 2 色樣(各有專屬碼)、P={'A'} → 不成嵌合
    bs = [B(0, "A991", [0, 0, 10, 10]), B(1, "MX1A", [0, 0, 10, 10]),
          B(2, "A991", [20, 0, 30, 10]), B(3, "MX2B", [20, 0, 30, 10])]
    vs, rv, st = assemble(bs, [], [], {"A"})
    assert len(vs) == 2 and st["d_demoted"] == 2 and st["merged_bindings"] == 2
    assert [r["reason"] for r in rv] == ["merge_key_suspect"] * 2
    assert all(r["code"] == "A991" and r["swatch"] and r["prov"] for r in rv)
    assert sorted(s["orderCode"] for v in vs for s in v["variantSizes"]) == ["MX1A", "MX2B"]
    #     C 部:P 對偶(Level/A02G 保護)——同構造無家族字母 → L2 不動(C3 之 P 承重)
    vs, rv, st = assemble(bs, [], [], frozenset())
    assert st["d_demoted"] == 0 and len(vs) == 1
    #     D 部:橋接對偶——色樣對另共享 CC1(交集≠{A991})→ 不中(矩陣跨頁合併保護)
    bs2 = bs + [B(4, "CC1", [0, 0, 10, 10]), B(5, "CC1", [20, 0, 30, 10])]
    vs, rv, st = assemble(bs2, [], [], {"A", "C"})
    assert st["d_demoted"] == 0 and len(vs) == 1
    print("T23 PASS L2 v2 備援活體證明:雙偽逃逸+L2 接住(SL-6;含 P/橋接雙對偶)")
    # T24|SL-7 合法跨頁同碼合併:P 成立但無他碼(∃≥2 不成立)→ 照舊合併
    bs = [B(0, "C1", [0, 0, 10, 10], page=1), B(1, "C1", [0, 0, 10, 10], page=2)]
    vs, rv, st = assemble(bs, [], [], {"C"})
    assert len(vs) == 1 and st["d_demoted"] == 0 and len(vs[0]["mergedFrom"]) == 2
    print("T24 PASS L2 合法跨頁合併不拆(SL-7)")
    # T25|SL-8 A107 型:碼鏈 3 色樣、2 有專屬碼 1 無 → 不成嵌合、3 筆降級
    bs = [B(0, "A917", [0, 0, 10, 10]), B(1, "MX1A", [0, 0, 10, 10]),
          B(2, "A917", [20, 0, 30, 10]), B(3, "MX2B", [20, 0, 30, 10]),
          B(4, "A917", [40, 0, 50, 10])]
    vs, rv, st = assemble(bs, [], [], {"A"})
    assert len(vs) == 2 and st["d_demoted"] == 3
    assert sorted(s["orderCode"] for v in vs for s in v["variantSizes"]) == ["MX1A", "MX2B"]
    print("T25 PASS L2 存在量化+橋接(SL-8)")
    # T26|S2-5 偽碼旗標(工作包#3 線③):出但標記——旗標碼所在 Variant 帶
    #     pseudoCodeSuspect,其餘 Variant 無此鍵;綁定/佇列/統計零變化
    #     (註記惰性=剝鍵後與無旗標調用深等)
    bs = [B(0, "MILANO70", sw1), B(1, "C1", sw2)]
    ss = [S(0, "MILANO70", "60x60"), S(1, "C1", "30x60")]
    vs, rv, st = assemble(bs, ss, [], frozenset(), pseudo={"MILANO70"})
    fl = [v for v in vs if v.get("pseudoCodeSuspect")]
    assert len(vs) == 2 and len(fl) == 1 and fl[0]["pseudoCodeSuspect"] == ["MILANO70"]
    assert not any("pseudoCodeSuspect" in v for v in vs if v is not fl[0])  # 反例:C1 無鍵
    vs0, rv0, st0 = assemble(bs, ss, [], frozenset())
    strip = lambda v: {k: x for k, x in v.items() if k != "pseudoCodeSuspect"}  # noqa: E731
    assert [strip(v) for v in vs] == [strip(v) for v in vs0] and rv == rv0 and st == st0
    print("T26 PASS S2-5 偽碼旗標:出但標記+註記惰性(反例含)")
    # T27|通案四 L2 塌縮守衛(工作包#7 緊急補丁;精華=dev/l2_collapse_selftest_draft AC-1~4)
    #     hub 色樣(p1 掛 10 碼)+各碼再現 p2(橋接)→ 20 綁定/跨 2 頁單一 cluster
    def collapse_bs(n, cp1, cp2):
        swH = [0, 0, 100, 100]
        return ([B(k, f"X{k}", swH, cp1, page=1) for k in range(n)]
                + [B(n + k, f"X{k}", [10 * k, 0, 10 * k + 9, 9], cp2, page=2) for k in range(n)])
    # AC-1 塌縮(20 綁定∧跨頁∧衝突)→ 整團降級 assembly_collapse_suspect、0 塌縮 Variant
    vs, rv, st = assemble(collapse_bs(10, "RED", "BLUE"), [], [])
    dem = [r for r in rv if r["reason"] == "assembly_collapse_suspect"]
    assert len(dem) == 20 and st["assembly_collapse_demoted"] == 20 and st["assembly_collapse_clusters"] == 1
    assert all(r["swatch"] and r["prov"] for r in dem)  # 資料無損
    assert not any(len({m["swatch"]["page"] for m in v["mergedFrom"]}) >= 2
                   and v["color"]["en"] is None and len(v["mergedFrom"]) >= L2_COLLAPSE_MIN for v in vs)
    assert sum(len(v["mergedFrom"]) for v in vs) + len(dem) == 20  # 守恆
    # AC-2 對偶|無色名衝突之大跨頁合併(同色 20 綁定)→ 守衛不動(需正面衝突證據)
    _, rv2, st2 = assemble(collapse_bs(10, "RED", "RED"), [], [])
    assert st2["assembly_collapse_demoted"] == 0
    # AC-3 對偶|未達下緣(16 綁定=Level 型合法衝突上界)→ 不動、仍走既有
    #     code_color_conflict(18/19 帶內案例移 T29=案1 語意翻轉,2026-07-13 外審)
    _, rv3, st3 = assemble(collapse_bs(8, "RED", "BLUE"), [], [])
    assert st3["assembly_collapse_demoted"] == 0 and st3["assembly_borderline_demoted"] == 0
    assert any(r["reason"] == "code_color_conflict" for r in rv3)
    # AC-4 SL-6(A102)併行|單頁列向嵌合→SL-6 降級 2、塌縮守衛不重複觸發(單頁→非跨頁)
    bs = [B(0, "A991", sw1), B(1, "MX1A", sw1), B(2, "A991", sw2), B(3, "MX2B", sw2)]
    _, rv4, st4 = assemble(bs, [], [], {"A"})
    assert st4["d_demoted"] == 2 and st4["assembly_collapse_demoted"] == 0
    print("T27 PASS L2 塌縮守衛:塌縮降級+無衝突/未達N/SL-6併行對偶(通案四)")
    # T28|通案四 段1 單頁過併守衛(精華=dev/singlepage_overmerge_selftest_draft AC-1~4)
    #     單頁 hub(1 大色樣掛 N 碼、同色→跨頁守衛照不到)以主色樣 area% 承重
    swBig = [0, 0, 100, 100]                       # area 10000
    PD = {1: 100000.0, 2: 100000.0}                # swBig area%=10.0(≥AREA_T=5.0)
    sp = lambda n, sw=swBig: [B(k, f"X{k}", sw, "GREY", page=1) for k in range(n)]  # noqa: E731
    # AC-1 單頁 hub 大 area% ∧ ≥N → 整團降級 singlepage_overmerge_suspect、0 逃逸、守恆
    vs, rv, st = assemble(sp(L2_COLLAPSE_MIN), [], [], page_dims=PD)
    dm = [r for r in rv if r["reason"] == "singlepage_overmerge_suspect"]
    assert (len(dm) == L2_COLLAPSE_MIN and st["singlepage_overmerge_demoted"] == L2_COLLAPSE_MIN
            and st["singlepage_overmerge_clusters"] == 1 and st["singlepage_escaped"] == 0)
    assert all(r["swatch"] and r["prov"] for r in dm)  # 資料無損
    assert sum(len(v["mergedFrom"]) for v in vs) + len(dm) == L2_COLLAPSE_MIN  # 守恆
    # AC-2 對偶|小 area%(20x20→0.4%)→ 不動(area% 承重、非只憑大小)
    _, _, st_b = assemble(sp(L2_COLLAPSE_MIN, [0, 0, 20, 20]), [], [], page_dims=PD)
    assert st_b["singlepage_overmerge_demoted"] == 0
    # AC-3 對偶|未達 N → 不動
    _, _, st_c = assemble(sp(L2_COLLAPSE_MIN - 1), [], [], page_dims=PD)
    assert st_c["singlepage_overmerge_demoted"] == 0
    # AC-4 對偶|跨頁同色大 area% ≥N(同碼橋接;12+12=24 綁定=半徑上界內)→ 單頁守衛
    #     不越界 ∧ 跨頁守衛同色不動 ∧ 半徑上界不誤動(案1 後大小自 40 縮 24 保持原意)
    cross = sp(12) + [B(12 + k, f"X{k}", swBig, "GREY", page=2) for k in range(12)]
    _, _, st_d = assemble(cross, [], [], page_dims=PD)
    assert (st_d["singlepage_overmerge_demoted"] == 0 and st_d["assembly_collapse_demoted"] == 0
            and st_d["assembly_merge_radius_demoted"] == 0)
    print("T28 PASS 段1 單頁過併守衛:單頁降級+小area/未達N/跨頁同色三對偶(通案四)")
    # T29|案1 零邊際合併權限(外審修正案;精華=dev/l2_borderline_selftest_draft AC-1~6)
    #     ①次臨界帶 [18,20) 跨頁∧衝突→borderline_merge_suspect(不硬判塌縮/合法)
    #     ②爆炸半徑:跨頁 cluster >5 頁 ∨ >24 綁定→assembly_merge_radius_suspect
    bs19 = collapse_bs(10, "RED", "BLUE")[:-1]     # 19 綁定(Topcer/Uniche-19 型)
    vs, rv, st = assemble(bs19, [], [])
    dm = [r for r in rv if r["reason"] == "borderline_merge_suspect"]
    assert (len(dm) == 19 and st["assembly_borderline_demoted"] == 19
            and st["assembly_borderline_clusters"] == 1 and not vs)
    assert all(r["swatch"] and r["prov"] for r in dm)               # 資料無損
    assert st["assembly_borderline_demoted"] + sum(
        len(v["mergedFrom"]) for v in vs) == 19                     # 守恆
    # 半徑|同色鏈跨 6 頁(>上限 5)→ 整團降級;5 頁上界=合法不動
    chain = lambda np_: [B(100 + 2 * i + d, f"C{i}", [0, 0, 9, 9], "RED", page=i + 1 + d)  # noqa: E731
                         for i in range(np_ - 1) for d in (0, 1)]
    vs3, _, st3r = assemble(chain(L2_AUTO_MERGE_MAX_PAGES + 1), [], [])
    assert (st3r["assembly_merge_radius_demoted"] == 2 * L2_AUTO_MERGE_MAX_PAGES
            and st3r["assembly_merge_radius_clusters"] == 1 and not vs3)
    _, _, st4r = assemble(chain(L2_AUTO_MERGE_MAX_PAGES), [], [])
    assert st4r["assembly_merge_radius_demoted"] == 0
    # 半徑|同色 2 頁 26 綁定(>上限 24)→ 降級;24 上界=合法(Level 型)不動
    _, _, st5r = assemble(collapse_bs(13, "RED", "RED"), [], [])
    assert st5r["assembly_merge_radius_demoted"] == 26
    _, _, st6r = assemble(collapse_bs(12, "RED", "RED"), [], [])
    assert st6r["assembly_merge_radius_demoted"] == 0
    # 非干涉|≥20 跨頁衝突仍走塌縮守衛(帶不搶);單頁域半徑不碰(合法單頁 25 綁定存在)
    _, _, st7r = assemble(collapse_bs(10, "RED", "BLUE"), [], [])
    assert st7r["assembly_collapse_demoted"] == 20 and st7r["assembly_borderline_demoted"] == 0
    sp26 = [B(200 + k, f"S{k}", [0, 0, 50, 50], "RED", page=1) for k in range(26)]  # 單頁 hub
    _, _, st8r = assemble(sp26, [], [])
    assert st8r["assembly_merge_radius_demoted"] == 0
    print("T29 PASS 案1 零邊際合併權限:次臨界帶+半徑+上界合法/非干涉對偶(通案四)")
    print("selftest OK(29/29)")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--selftest":
        selftest()
    elif len(sys.argv) >= 2 and sys.argv[1] == "--smoke":
        sys.exit(smoke(sys.argv[2] if len(sys.argv) > 2 else "product"))
    elif len(sys.argv) >= 2:
        p = Path(sys.argv[1])
        doc, review, _, stats = write_out(p, sys.argv[2] if len(sys.argv) > 2 else "product",
                                          build_vocabs())
        nv = sum(len(s["variants"]) for s in doc["series"])
        ns = sum(len(s["specByCode"]) for s in doc["series"])
        print(f"{p.name}: variants={nv} (自 {stats['merged_bindings']} 筆綁定合成)"
              f" specRows={ns} review={len(review)}"
              f"{' [seriesSkeleton]' if doc['seriesSkeleton'] else ''} → "
              f"{sys.argv[2] if len(sys.argv) > 2 else 'product'}/{p.parent.name}/")
    else:
        sys.exit(__doc__)
