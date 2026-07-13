#!/usr/bin/env python3
"""M3 掃描:v2/v3/v4 ablation + 指標修正(M3-M1)+ 尺寸關聯覆蓋(M3-R1b)。

    python3 core/m3_scan.py <corpus_dir> <v2|v3|v4|v5> <out.csv>

M3-M1:主指標=GT 真實正確率(掃描外);本表 bound-ok/far 僅輔助(已知系統性高估,
M2 實測 v1 +45.2pt / v2 +20.5pt)。仲裁佇列訊號 = needs_review(綁定非 x 對齊或孤兒),
不再用 far(對真錯誤 recall=0)。
M3-R1b:row_size()——code→同列(±1.5×字高)最近尺寸 token;同列無 → 上方 4×字高內
最近的左側尺寸 token(多行儲存格)。variantSizes 的列向來源。
M4-R1b2(v4,綁定規則不變、僅尺寸關聯):
  (1) 複合尺寸整 token 解析(33x120x3,2x3,2→33x120;三段 33x120x5/93x93x8mm 由
      「不進候選」變「取頭段」——dev 實測 86 個複合 token 中 15 碎片、其餘全漏);
  (2) 折縫過濾:spread 頁(寬/高>1.2,dev 實測 spread 1.41-1.63 vs 單頁 0.71-0.85)
      同側才可關聯(修跨頁同列污染:Provenza p33 EK6M 抓左頁 60x120);
  (3) above 分支欄親和:x 重疊候選優先於左側列標籤(修跨列串位:P36631 型抓別欄標頭)。
M4-ID(v4,色名身分鍵):doc 級色名索引(色樣圖說帶 alpha token→色樣);非 x 對齊碼
  → 同列(±1.5×字高、同折縫側)「可區分」色名 → 全 doc 唯一色樣才綁(name_bound)。
  M5-1(2026-07-09 裁決):name_bound=佇列內假說、不離隊——held-out 45%(27/60,
  單 token 色名跨系列碰撞)無資格繞過安全網;needs_review = 全部非 x 對齊碼,
  name_bound 只作為掛在佇列項上的建議答案加速人工複查。可區分=
  per-page 統計:同列碼數 ≤ max(3, 頁碼數/3)——系列/材質詞(Lume×21 列)排除,
  防整頁錯綁單一色樣。結構性證據(entity key),非距離啟發式。
M4-3(v4,assign_words 詞級):x 對齊全無(僅剩鬆散同列)→ orphan(誠實放棄),
  取代 v3 硬綁回退;佇列成員不變(review = n_codes - aligned - named 兩項輸入不動),
  變的只是「錯值 → None」。觸發優先序:x 對齊 → 色名救援(M4-ID)→ orphan。
S2-2(v5,僅候選收集、綁定/佇列規則=v4):code_candidates 分流 junk(價格帶家族/
  單位/厚度/尺寸洩漏 → routed 保留,SCHEMA §7 過濾≠刪除)。詳 m2_scan.route_junk。
M5-2(v6=v5+疑似小圖形降級,綁定/候選不動):x 對齊到疑似版面小圖形(返回鈕/表頭
  icon)的碼「降級進佇列」——不刪色樣、不改指派,只把 ok_x 記為否使其落入
  needs_review(錯殺=複查成本,非資料毀損;與 M5-1 同哲學)。判定=icon_sus
  (dev 零誤傷校準),doc 級統計=doc_icon_stats。
M5-3(v7=v6+列首色樣版型救援;I 批診斷=Marazzi 主力版型,I_REPORT §4):
  spike_geom.m53_blocks 閘 ON 時 would-be orphan 綁回列首色樣(d=-2.0 哨兵)。
  記帳:code_block_bound 新欄(v7+)、review=n_codes-aligned-blk、名鍵頁閘用
  aligned+blk、塊綁到 icon_sus 色樣照 M5-2 降級。驗收合約第一條:非列版型頁
  v6→v7 零 diff(逐位)。
E-1(v9=v8+場景照搶綁降級;設計=output/e1_design_v9.md,判定式 v3.1 核可
  2026-07-12):photo_sus(b)=S1(色樣面積 ≥ V9_G×頁面積)∧ ¬((S2a 同列尺寸 ∧
  該色樣唯一對齊碼)∨ S2b 帶內唯一碼),逐綁定評估、只作用 ok_x 路(塊綁不
  經此);中=降級進佇列(M5-2 同哲學,code_photo_demoted 新欄 v9+)。多碼
  共享使 S2a 失效(dev 分離量測:A02G 77 筆偽 S2a/FMG 29 筆真 S2a);
  T6 翻面=降級(原審預授權第二分支)。合成案例全表 T1-T9+T5b=selftest 案(10)。
版本號非線性註記(2026-07-12 裁決④;2026-07-13 M5-2b 更新):**v9=E-1 懸空側枝
  (閘=version==9,親驗未過不入主幹);主幹=…v8→v10(S2-2 延伸 L1)→v12(S2-1
  延伸③,m2_scan)→v13(M5-2b);v11=v10+E-1 預留**——E-1 親驗過後以 v11 合成並
  重跑 E-1 全套驗收,屆時閘改 ==9 or >=11;**E-1 票補註(2026-07-13 裁決):v11
  併軌時 E-1 須於 med_ex 世界重跑全套驗收(路線 (a) 已知後續成本)**。
S2-2 延伸 L1(v10=v8+量表碼歸隊;m2_scan.band_regroup,設計=
  output/s22ext_design.md):偵測層 kept→routed band,scan 本檔無新路徑
  (綁定/佇列邏輯零改動,變的只是 codes_doc 集合)。
M5-2b(v13=v12+B 訊號中位穩健化;設計=output/m52b_design.md,2026-07-13 裁決
  路線 (a) 真分叉雙中位):doc_icon_stats 依版本分叉——v13 中位=med_ex(排除
  ≥M52_BIG×頁大圖後小簇中位)、v≤12 含 v9 側枝=原樣舊全體中位(逐位不變=第一
  硬條件)。icon_sus 兩臂判定式不動、A' 皮帶/既有降級鏈不動,僅所餵中位換基準;
  med_ex≤med 單調=構造性零新增真色樣誤殺。
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import median

import fitz

from census import SIZE_RE
from m1_scan import norm
from m2_scan import build_vocabs, code_candidates
from spike_geom import assign_words, extract_swatches


_NUM = r"\d{1,4}(?:[.,]\d{1,2})?"
COMP_RE = re.compile(  # 複合尺寸(≥3 段):頭段=WxH,尾段=厚度/馬賽克粒(33x120x3,2x3,2)
    rf'\b({_NUM}\s*[x×]\s*{_NUM})(?:\s*[x×]\s*{_NUM})+\s*(?:cm|mm)?(?=\b|")', re.I)


def page_sizes(words, version=3):
    out = []
    for t in words:
        m = (COMP_RE.search(t[4]) if version >= 4 else None) or SIZE_RE.search(t[4])
        if m:
            out.append(((t[1] + t[3]) / 2, t[0], t[2], m.group(1 if m.re is COMP_RE else 0)))
    return out


def fold_x(page):
    """spread 頁(左右兩物理頁排一版)→ 折縫 x;單頁 → None。"""
    return page.rect.width / 2 if page.rect.width > 1.2 * page.rect.height else None


def is_name(raw, alpha_vocab):
    """色名候選:字母 token、非泛用詞、且非全小寫(型錄色名=大寫/首大寫;
    全小寫=行銷/技術散文,dev 實測 FMG 'alta capacità' 型誤綁來源)。"""
    t = norm(raw)
    return t.isalpha() and len(t) >= 3 and t not in alpha_vocab and not raw.islower()


def doc_name_index(spec, codes_doc, alpha_vocab, version):
    """M4-ID doc 級預掃,回傳 (name_idx, aligned_codes):
    name_idx = 無碼色樣的圖說色名 → {name: {(page_no, sw_idx)}}(token 層)。
      只收「圖說無偵測碼」的色樣:有碼色樣已有碼層身分,不當色名靶(dev 實證:
      Marazzi 情境照圖說含 MP99,若入索引會把同色異紋理的 MP9D 錯綁過去)。
    aligned_codes = 全 doc 曾 x 對齊的碼 token:這些碼已有幾何的家,其它頁的重複
      實例走 Stage 5 碼身分合併,不吃色名救援(dev 實證:MOSA 5102V 在網格頁已
      對齊,p45 規格表實例若救援會經區段標題詞錯綁到配件照)。
    # ponytail: 單 token 匹配;多詞色名(STEEL WHITE)靠交集守門,n-gram 是升級路
    """
    idx, aligned = {}, set()
    for page in spec:
        sws = extract_swatches(page, version=3 if version >= 3 else 1)
        fold = fold_x(page)
        cap = {i: [] for i in range(len(sws))}
        # 索引釘 v3 幾何(使用者裁決 2026-07-09):M4-2 的 5 道守門在 v3 幾何下逐筆
        # 驗證定案;若隨 M4-3 orphan 化,sec 誤掛碼消失會讓包裝表頁色樣「變無碼」、
        # 表頭詞(FMG CRATE/PESO)以偽色名進索引,多救的全是 junk 數字(S2-2 桶)。
        # 釘住=M4-2/M4-3 解耦,已驗證資料不隨後票漂移。
        for w, i, d in assign_words(page, sws, min(version, 3)):
            t = norm(w[4])
            if (t in codes_doc and i is not None
                    and sws[i].x0 - 2 <= (w[0] + w[2]) / 2 <= sws[i].x1 + 2):
                aligned.add(t)
            # 只收圖說帶(規則1/2 範圍);規則3 遠端散文詞不算圖說,會稀釋唯一性
            if i is None or d > max(1.5 * sws[i].height, 40):
                continue
            if fold and (((w[0] + w[2]) / 2 < fold)      # 圖說不跨折縫(視覺列 d=0
                         != ((sws[i].x0 + sws[i].x1) / 2 < fold)):  # 的跨頁指派要擋)
                continue
            cap[i].append(w)
        for i, ws in cap.items():
            r = sws[i]  # 色名靶=色塊;極端長寬比=表格欄底條/邊飾(MOSA p44 可用性
            if r.height >= 6 * r.width or r.width >= 6 * r.height:  # 矩陣,dev 實證)
                continue
            if any(norm(w[4]) in codes_doc for w in ws):
                continue
            for w in ws:
                if is_name(w[4], alpha_vocab):
                    idx.setdefault(norm(w[4]), set()).add((page.number, i))
    return idx, aligned


def _same_row_side(u, cyw, h, fold, side):
    if abs((u[1] + u[3]) / 2 - cyw) > 1.5 * h:
        return False
    return not (fold and ((u[0] + u[2]) / 2 < fold) != side)


def page_good_names(words, codes_doc, alpha_vocab, fold):
    """可區分色名(per-page 統計):與該詞同列的碼數 ≤ max(3, 頁碼數/3)。
    系列/材質詞(Lume×21 列、Rake×10 列)同列碼過多 → 排除,防整頁錯綁到單一色樣。"""
    codes = [u for u in words if norm(u[4]) in codes_doc]
    co = {}
    for u in words:
        if not is_name(u[4], alpha_vocab):
            continue
        h = max(u[3] - u[1], 1)
        cyu = (u[1] + u[3]) / 2
        side = (u[0] + u[2]) / 2 < fold if fold else None
        co.setdefault(norm(u[4]), set()).update(
            id(c) for c in codes if _same_row_side(c, cyu, h, fold, side))
    lim = max(3, len(codes) / 3)
    return {t for t, s in co.items() if s and len(s) <= lim}


def name_bind(w, words, name_idx, alpha_vocab, fold, good_names=None):
    """非 x 對齊碼的色名救援:同列可區分色名 → 色樣(變體層唯一性)。
    回傳 (page_no, sw) | None。同名多實體=同一 ColorVariant(dev 實證:twin_s
    PLASTER 總覽色塊+p30 色樣皆合法),故實體數 ≤3 即可用;跨系列常用色名
    (總目錄 WHITE)實體數遠大於 3 → 自然擋下。多色名取實體交集(STEEL WHITE
    兩 token 交出同一色塊)。
    # ponytail: K=3 經驗天花板;正解=系列範圍鍵(SCH-3),等總覽型錄切分後升級
    """
    h = max(w[3] - w[1], 1)
    cyw = (w[1] + w[3]) / 2
    side = (w[0] + w[2]) / 2 < fold if fold else None
    sets = []
    for u in words:
        t = norm(u[4])
        if not is_name(u[4], alpha_vocab) or (good_names is not None and t not in good_names):
            continue
        if not _same_row_side(u, cyw, h, fold, side):
            continue
        hit = name_idx.get(t, ())
        if 0 < len(hit) <= 3:
            sets.append(hit)
    if not sets:
        return None
    inter = set.intersection(*sets)
    return min(inter) if inter else None  # 交集空=列上色名互相矛盾,不綁


def row_size(sizes, w, version=3, fold=None):
    """code word → 尺寸 token(M3-R1b;v4=M4-R1b2)。回傳 (token | None)。"""
    if version >= 4 and fold:  # v4 折縫過濾:尺寸不跨物理頁關聯
        side = (w[0] + w[2]) / 2 < fold
        sizes = [s for s in sizes if (s[1] < fold) == side]
    h = max(w[3] - w[1], 1)
    cyw = (w[1] + w[3]) / 2
    same = [(abs(cy - cyw), abs(x0 - w[0]), tok) for cy, x0, x1, tok in sizes
            if abs(cy - cyw) <= 1.5 * h]
    if same:
        return min(same)[2]
    above = [(cyw - cy, abs(x0 - w[0]), tok, x0, x1) for cy, x0, x1, tok in sizes
             if 0 < cyw - cy <= 4 * h and x0 <= w[2]]
    if version >= 4:  # v4 欄親和:x 重疊(同欄標頭/同格上一行)優先於左側列標籤
        xover = [a for a in above if min(w[2], a[4]) - max(w[0], a[3]) > 0]
        above = xover or above
    if above:
        return min(above)[2]
    return None


_K20 = lambda r: (round(r.x0 / 20), round(r.y0 / 20), round(r.x1 / 20), round(r.y1 / 20))


M52_BIG = 0.10  # M5-2b(v13):doc 中位穩健化——排除面積 ≥ M52_BIG×頁的大圖(情境照)
#   後重算小簇中位(med_ex)。校準(m52b_design.md §2.3,dev 量測=dev/b_signal_probe.py):
#   帶碼色樣面積比雙峰——真色樣常態簇 ≤5%(格狀檔 med% 觀測 0.5–3%)、情境照簇 ≥~18%
#   (Uniche 13.7 / Vivo 30.7 / A02G 27.2 / select 44.8);取谷帶下緣 0.10,對 [0.05,0.18]
#   不敏感(病例全修、健康檔零動皆穩定)。⚠ 獨立校準:數值與 V9_G(0.10)同,但為本用途
#   (中位排大圖)重新校準之判定常數,不 import V9_G、不與 v9 側枝耦合。凍結後不動。


def doc_icon_stats(spec, version=12):
    """M5-2(v6)doc 級統計:回傳 (rep_keys, med_area) 供 icon_sus 判定。
    rep_keys=同位(20pt 圓整)出現 ≥max(5, 0.5×spec 頁數) 頁的色樣 bbox(返回鈕/
    頁角 logo 型版面家具;Level 矩陣頁同版位真色樣只佔少數頁,50% 門檻天然排除)。
    M5-2b(v13,2026-07-13 裁決路線 (a) 真分叉雙中位):version≥13 的中位改 med_ex
    =排除面積 ≥M52_BIG×頁的大圖(情境照)後之小簇中位(小簇空→退回全體中位=保存
    原行為);version≤12 含 v9 側枝=原樣全體中位(第一硬條件=逐位不變,預設值即舊
    路)。med_ex≤med 單調⇒icon_sus 兩臂門檻只降⇒降級只減不增=構造性零新增真色樣
    誤殺;rep_keys 照全體母體計算不動(A' 同位判定沿用)。"""
    per = [extract_swatches(p, version=3) for p in spec]
    areas = [abs(r) for sws in per for r in sws]
    if not areas:
        return set(), 0.0
    keyc = Counter(_K20(r) for sws in per for r in sws)
    need = max(5, 0.5 * len(spec))
    rep = {k for k, n in keyc.items() if n >= need}
    if version >= 13:
        small = [abs(r) for p, sws in zip(spec, per) for r in sws
                 if abs(r) < M52_BIG * abs(p.rect)]
        if small:
            return rep, median(small)
    return rep, median(areas)


V9_G = 0.10  # E-1(v9)S1 照片級前置閘:色樣面積 ≥ V9_G×頁面積(dev 校準 2026-07-12,
#              e1_design_v9.md 校準報告):帶碼色樣面積比雙峰——常態簇 ≤5%(Level 真
#              網格上緣 2.8%=3.6× 邊際)、照片簇 ≥25%,5-21% 空帶僅 Topcer 真大塊
#              3 例(交 S2 正面證據);取谷帶下緣=S1 重召回、精確交 S2,與 audit
#              分檔線同值(此處為判定常數,經獨立校準非沿用)。中位臂 K 經 dev 否決
#              (per-doc 中位 0.09%-35% 跨 400 倍:任何 K 不是誤傷 Level 就是永不
#              觸發);折縫感知基底同否決(照片簇原始基底全 ≥25%,不需要)。


def icon_sus(r, icon_ctx):
    """M5-2(v6):疑似版面小圖形?A'=同位跨頁重複 ∧ 面積<0.5×中位;B=面積<0.05×中位。
    dev 校準(2026-07-09,零誤傷=硬約束):B 門檻 0.05=dev 零誤傷上限(0.08 即誤傷
    Emil p24 收邊條縮圖 32 碼);A' 50% 頁數門檻排除 Level 矩陣同版位真色樣(120 碼)。
    處置=降級進佇列(demote),不刪色樣——錯殺成本=人工複查,絕非資料毀損。"""
    rep, med = icon_ctx
    if not med:
        return False
    a = abs(r)
    return a < 0.05 * med or (_K20(r) in rep and a < 0.5 * med)


def scan_page(page, codes_doc, alpha_vocab, version, name_ctx=None, icon_ctx=None):
    name_idx, aligned_doc = name_ctx if name_ctx else (None, set())
    sws = extract_swatches(page, version=3 if version >= 3 else 1)
    sus = {i for i, r in enumerate(sws)
           if version >= 6 and icon_ctx and icon_sus(r, icon_ctx)}
    n_raster = sum(1 for i in page.get_image_info()
                   if 60 < abs(fitz.Rect(i["bbox"])) < 0.55 * abs(page.rect))
    ph = page.rect.height
    words = page.get_text("words")
    sizes = page_sizes(words, version)
    fold = fold_x(page)
    sw_words = {i: [] for i in range(len(sws))}
    n_codes = orphan = far = aligned = with_size = named = demoted = blk = photo_dm = 0
    code_words, band_codes = [], {}
    for w, i, d in assign_words(page, sws, version):
        if i is not None:
            sw_words[i].append(w)
        t = norm(w[4])
        if t not in codes_doc:
            continue
        n_codes += 1
        cx = (w[0] + w[2]) / 2
        if (version == 9 and i is not None                 # E-1 S2b 圖說帶碼收集
                and 0 <= d <= max(1.5 * sws[i].height, 40)  # (==9:懸空側枝,
                and not (fold and (cx < fold) != ((sws[i].x0 + sws[i].x1) / 2 < fold))):  # v11 併主幹後改 >=)
            band_codes.setdefault(i, set()).add(t)          # (幾何=doc_name_index 圖說帶)
        ok_x = i is not None and sws[i].x0 - 2 <= cx <= sws[i].x1 + 2
        if ok_x and i in sus:  # M5-2:疑似小圖形上的 x 對齊 → 降級進佇列(不離隊)
            ok_x = False
            demoted += 1
        ok_blk = version >= 7 and i is not None and d == -2.0  # M5-3 塊綁(哨兵)
        if ok_blk and i in sus:  # 塊綁到疑似小圖形 → 照 M5-2 降級(雙軌皮帶)
            ok_blk = False
            demoted += 1
        code_words.append((w, ok_x, ok_blk, i))
        aligned += ok_x
        blk += ok_blk
        orphan += i is None
        far += i is not None and d > max(2 * sws[i].height, 0.15 * ph)
        with_size += row_size(sizes, w, version, fold) is not None
    if version == 9:  # E-1(v9=懸空側枝,閘==9;判定式 v3.1,T6 翻面=原審預授權
        # 第二分支):photo_sus = S1 ∧ ¬((S2a ∧ 唯一對齊碼) ∨ S2b),逐綁定;
        # 降級不刪除(M5-2 同哲學);塊綁路不經此(T9 結構保證)。
        # S2a 限唯一對齊碼:dev 分離量測(e1_design_v9.md v3.1)——場景照圖說列
        # 同帶尺寸使裸 S2a 無判別力(A02G 病檔 77 筆多碼全偽 S2a、FMG 特寫 29 筆
        # 全單碼真 S2a);多碼共享=場景列表徵,使 S2a 失效而非推翻之。
        pa = abs(page.rect)
        sw_codes = {}
        for w, ok_x, ok_blk, i in code_words:  # 快照=photo 降級前的對齊碼集
            if ok_x:                           # (防降級順序耦合:後降者不得使前者「變唯一」)
                sw_codes.setdefault(i, set()).add(norm(w[4]))
        for k, (w, ok_x, ok_blk, i) in enumerate(code_words):
            if not ok_x or abs(sws[i]) < V9_G * pa:
                continue                              # S1 前置閘:非照片級零觸碰
            h = max(w[3] - w[1], 1)
            cyw = (w[1] + w[3]) / 2
            side = (w[0] + w[2]) / 2 < fold if fold else None
            s2a = len(sw_codes[i]) == 1 and any(      # S2a 同列尺寸 ∧ 唯一對齊碼
                (None if fold is None else ((x0 + x1) / 2 < fold)) == side
                and abs(cy - cyw) <= 1.5 * h
                for cy, x0, x1, _tok in sizes)
            s2b = band_codes.get(i, set()) == {norm(w[4])}  # S2b 帶內唯一碼
            if s2a or s2b:
                continue                              # 有效正面證據不被推翻
            code_words[k] = (w, False, ok_blk, i)     # 降級進佇列
            aligned -= 1
            photo_dm += 1
    # M4-ID 頁級閘門:色名救援僅限「色名鍵值頁」(碼數≥5 且 x 對齊率≤20%,
    # 與 heldout4 硬條件 2 同訊號)。稀疏情境頁(2-3 碼)是 Stage 3B product_page
    # 的範疇,dev 實證會經系列詞錯綁(Marazzi MQ7X→White 照片)。
    if (version >= 4 and name_idx is not None
            and n_codes >= 5 and aligned + blk <= 0.2 * n_codes):  # v7:塊綁計入閘
        good = page_good_names(words, codes_doc, alpha_vocab, fold)
        named = sum(1 for w, ok_x, ok_blk, *_ in code_words
                    if not ok_x and not ok_blk and norm(w[4]) not in aligned_doc
                    and name_bind(w, words, name_idx, alpha_vocab, fold, good) is not None)
    review = n_codes - aligned - blk  # M3-M1 佇列=非 x 對齊碼;M5-1 不離隊;v7 塊綁離隊
    sw_no_code = sum(1 for i in sw_words
                     if not ({norm(w[4]) for w in sw_words[i]} & codes_doc))
    if len(sws) == 0:
        ptype = "text_only" if n_codes else "no_swatch_no_code"
    elif n_raster == 0:
        ptype = "vector"
    elif len(sws) > 15:
        ptype = "dense_grid"
    elif len(sws) <= 4 and sorted(abs(r) for r in sws)[len(sws) // 2] > 0.05 * abs(page.rect):
        ptype = "lifestyle_caption"
    else:
        ptype = "standard"
    return dict(n_sw=len(sws), n_codes=n_codes, code_orphan=orphan, code_far=far,
                code_x_aligned=aligned, code_name_bound=named, code_needs_review=review,
                code_with_size=with_size, sw_no_code=sw_no_code, ptype=ptype,
                **({"code_icon_demoted": demoted} if version >= 6 else {}),
                **({"code_block_bound": blk} if version >= 7 else {}),
                **({"code_photo_demoted": photo_dm} if version == 9 else {}))


def main(corpus, ver, out_csv):
    version = int(ver.lstrip("v"))
    code_vocab, alpha_vocab = build_vocabs()
    rows = []
    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        vendor = pdf.relative_to(corpus).parts[0]
        doc = fitz.open(pdf)
        spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
        routed = {}
        if version >= 5:
            codes_doc, routed = code_candidates(doc, code_vocab, len(spec), version,
                                                alpha_vocab)  # v8:停用詞補充(v≤7 不用)
        else:
            codes_doc = code_candidates(doc, code_vocab, len(spec))
        name_ctx = (doc_name_index(spec, codes_doc, alpha_vocab, version)
                    if version >= 4 else None)
        icon_ctx = doc_icon_stats(spec, version) if version >= 6 else None
        for page in spec:
            r = scan_page(page, codes_doc, alpha_vocab, version, name_ctx, icon_ctx)
            rows.append({"vendor": vendor, "page": page.number + 1,
                         "doc": pdf.name, **r})
        rj = {k: len(v) for k, v in routed.items() if v}
        print(vendor, pdf.name, "done", f"routed={rj}" if rj else "", flush=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    tc = sum(r["n_codes"] for r in rows) or 1
    orph = sum(r["code_orphan"] for r in rows)
    far = sum(r["code_far"] for r in rows)
    al = sum(r["code_x_aligned"] for r in rows)
    nb = sum(r["code_name_bound"] for r in rows)
    rv = sum(r["code_needs_review"] for r in rows)
    ws = sum(r["code_with_size"] for r in rows)
    print(f"\n[{corpus} {ver}] pages={len(rows)} codes={tc}")
    print(f"  x_aligned={al} ({al/tc:.1%})  needs_review={rv} ({rv/tc:.1%})  <- 仲裁佇列(內含色名假說 name_hyp={nb} ({nb/tc:.1%}),M5-1 不離隊)")
    print(f"  (輔助,高估勿當正確率) bound-ok={tc-orph-far} ({(tc-orph-far)/tc:.1%}) orphan={orph} ({orph/tc:.1%}) far={far} ({far/tc:.1%})")
    print(f"  size 關聯覆蓋={ws} ({ws/tc:.1%})")
    if version >= 6:
        dm = sum(r["code_icon_demoted"] for r in rows)
        print(f"  M5-2 小圖形降級={dm} ({dm/tc:.1%},含在 needs_review)")
    if version >= 7:
        bb = sum(r["code_block_bound"] for r in rows)
        print(f"  M5-3 列版型塊綁={bb} ({bb/tc:.1%},已離隊)")
    if version == 9:
        pdm = sum(r["code_photo_demoted"] for r in rows)
        print(f"  E-1 場景照降級={pdm} ({pdm/tc:.1%},含在 needs_review)")
    print("  ptype:", dict(Counter(r["ptype"] for r in rows)))


def selftest():
    """M4-R1b2 三機制的最小可跑檢查(合成資料,不碰 corpus)。"""
    W = lambda x0, y0, x1, y1, t: (x0, y0, x1, y1, t)  # noqa: E731
    # (1) 複合尺寸整 token:v3 抓碎片/漏,v4 取頭段
    ws = [W(0, 0, 60, 10, "33x120x3,2x3,2"), W(0, 20, 40, 30, "93x93x8mm"),
          W(0, 40, 40, 50, "60x120"), W(0, 60, 60, 70, "137x292x29h")]
    assert [s[3] for s in page_sizes(ws, 3)] == ["2x3,2", "60x120"]
    assert [s[3] for s in page_sizes(ws, 4)] == ["33x120", "93x93", "60x120"]
    # (2) 折縫過濾:左頁同列尺寸不得跨到右頁的 code
    sizes = [(105.0, 50, 90, "60x120")]           # 左頁 y=105
    code = W(700, 100, 740, 110, "EK6M")          # 右頁同列
    assert row_size(sizes, code, 3, None) == "60x120"      # v3:跨頁污染
    assert row_size(sizes, code, 4, 595.0) is None         # v4:折縫擋掉
    assert row_size(sizes, W(80, 100, 120, 110, "ELL9"), 4, 595.0) == "60x120"  # 同側保留
    # (3) above 欄親和:x 重疊的同欄標頭優先於更近的左側別欄標籤
    sizes = [(80.0, 10, 60, "100x100"), (70.0, 300, 350, "60x30")]
    code = W(300, 100, 340, 110, "P36631")        # 自家欄頭 60x30 較遠但 x 重疊
    assert row_size(sizes, code, 3, None) == "100x100"     # v3:跨列串位
    assert row_size(sizes, code, 4, None) == "60x30"       # v4:欄親和
    # 無 x 重疊時回退左側列標籤(多行儲存格,Emil p24 型)
    assert row_size([(80.0, 10, 60, "33x120")], code, 4, None) == "33x120"
    # (4) M4-ID 色名綁:同列色名 → 色樣(變體層唯一);>3 實體(跨系列常用色)不綁;
    #     多色名取交集;跨折縫色名不採;全小寫散文詞不算色名
    vocab = {"RETT"}
    idx = {"PLASTER": {(3, 0)}, "WHITE": {(3, 1), (5, 2)},
           "STEEL": {(5, 2), (7, 1)}, "GREY": {(1, 0), (2, 0), (3, 0), (4, 0)}}
    row = [W(10, 100, 60, 110, "PLASTER"), W(70, 100, 100, 110, "Rett."),
           W(400, 100, 460, 110, "P100697")]
    assert name_bind(row[2], row, idx, vocab, None) == (3, 0)
    assert name_bind(row[2], [W(10, 100, 60, 110, "WHITE"), row[2]], idx, vocab, None) == (3, 1)
    assert name_bind(row[2], [W(10, 100, 40, 110, "STEEL"), W(45, 100, 90, 110, "WHITE"),
                              row[2]], idx, vocab, None) == (5, 2)      # 交集
    assert name_bind(row[2], [W(10, 100, 60, 110, "GREY"), row[2]], idx, vocab, None) is None
    assert name_bind(row[2], [W(10, 100, 60, 110, "PLASTER"), row[2]], idx, vocab, 300.0) is None
    assert name_bind(row[2], [W(10, 100, 60, 110, "plaster"), row[2]], idx, vocab, None) is None
    # (5) 可區分守門:系列詞與全頁碼同列(Lume 型)→ 排除;單列色名 → 保留
    codes = {"C%02d" % k for k in range(12)}
    ws = [W(10, 100, 50, 110, "PLASTER")]
    for k in range(12):  # 12 列,每列都有 LUME + 一個碼;PLASTER 只在第一列
        ws += [W(60, 100 + 20 * k, 90, 110 + 20 * k, "LUME"),
               W(200, 100 + 20 * k, 240, 110 + 20 * k, "C%02d" % k)]
    good = page_good_names(ws, codes, vocab, None)
    assert "PLASTER" in good and "LUME" not in good, good
    idx2 = {"PLASTER": {(3, 0)}, "LUME": {(9, 5)}}
    assert name_bind(ws[2], ws, idx2, vocab, None, good) == (3, 0)   # C00:靠 PLASTER
    assert name_bind(ws[4], ws, idx2, vocab, None, good) is None     # C01:只剩 LUME,擋下
    # (6) M4-3 x 對齊全無 → orphan:真 fitz 頁(先取實際 word bbox 再擺色樣,免字型度量)
    from spike_geom import assign_words
    pg = fitz.open().new_page(width=600, height=800)
    pg.insert_text((400, 100), "EK6M", fontsize=10)
    w = pg.get_text("words")[0]
    cy = (w[1] + w[3]) / 2
    swA = fitz.Rect(50, cy - 20, 150, cy + 20)   # 同 y 帶、x 不涵蓋、sec 非空(路徑A)
    assert assign_words(pg, [swA], 3)[0][1] == 0        # v3:鬆散同列硬綁
    assert assign_words(pg, [swA], 4)[0][1] is None     # v4:orphan
    swB = fitz.Rect(50, cy + 1, 150, cy + 40)    # 同 y 帶邊緣、sec 空(路徑B)
    assert assign_words(pg, [swB], 3)[0][1] == 0
    assert assign_words(pg, [swB], 4)[0][1] is None
    swC = fitz.Rect(50, cy - 100, 150, cy - 60)  # 上方遠端、無 x 重疊 → 無 xin 的 sec
    assert assign_words(pg, [swC], 3)[0][1] == 0        # v3:遠端 sec 硬綁(Emil p13 型)
    assert assign_words(pg, [swC], 4)[0][1] is None     # v4:orphan
    swX = fitz.Rect(w[0] - 5, cy - 20, w[2] + 5, cy + 20)  # x 涵蓋 → v3/v4 同綁(1x 不動)
    assert assign_words(pg, [swX], 3)[0][1:] == (0, 0.0)
    assert assign_words(pg, [swX], 4)[0][1:] == (0, 0.0)
    # (7) S2-2 route_junk:價格帶家族(同字母 ≥3)分流、孤立量記(H10)保留;
    #     單位/厚度/尺寸洩漏分流;真 SKU 不動
    from m2_scan import route_junk
    kept, routed = route_junk({"A11", "A28", "A96", "T14", "CM2", "MM3", "12MM",
                               "33X120X5", "7X60X60", "EK6M", "H10", "P36631"})
    assert routed["band"] == {"A11", "A28", "A96"}, routed          # A 家族=3 → 分流
    assert routed["unit"] == {"CM2", "MM3"}
    assert routed["thickness"] == {"12MM"}
    assert routed["size"] == {"33X120X5", "7X60X60"}
    assert kept == {"T14", "EK6M", "H10", "P36631"}, kept           # T 孤立(<3)保留
    # (8) M5-2 icon_sus:B 極小(<0.05×中位)/A' 同位重複∧小(<0.5×中位)→ 疑似;
    #     中型非重複(Emil 收邊條縮圖型)與重複但大(整版網格)→ 不疑
    med = 10000.0
    tiny = fitz.Rect(0, 0, 10, 40)            # 400 = 4% med
    trim = fitz.Rect(0, 0, 60, 60)            # 3600 = 36% med,非重複
    repsm = fitz.Rect(100, 100, 140, 150)     # 2000 = 20% med,同位重複
    repbig = fitz.Rect(200, 200, 400, 300)    # 20000 = 200% med,同位重複
    rep = {_K20(repsm), _K20(repbig)}
    assert icon_sus(tiny, (rep, med)) and icon_sus(repsm, (rep, med))
    assert not icon_sus(trim, (rep, med)) and not icon_sus(repbig, (rep, med))
    assert not icon_sus(tiny, (set(), 0.0))   # 無色樣 doc → 不判
    # (8b) M5-2b(v13)版本閘=真分叉雙中位(dev/m52b_selftest_draft 精華):
    #      情境照撐高檔——v≤12 含 v9 舊全體中位(病灶=B 誤殺真小色樣,逐位保持);
    #      v13=med_ex 排 ≥M52_BIG×頁大圖後小簇中位(真小色樣救回、極小 icon 續死
    #      =非全面救援);無大圖檔 med_ex==med(正確殺 icon 母體零鬆動=閘惰性)。
    def _pg8b(rects):
        pg = fitz.open().new_page(width=600, height=800)
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 4, 4), False)
        pix.set_rect(pix.irect, (180, 90, 60))
        for r in rects:
            pg.insert_image(fitz.Rect(*r), pixmap=pix)
        return pg
    sw8b = fitz.Rect(450, 100, 500, 150)                    # 真小色樣 0.52% 頁
    spec8b = [_pg8b([(30, 30, 430, 470), (450, 100, 500, 150)]),   # 情境照 ~33% 頁
              _pg8b([(30, 30, 430, 470), (450, 300, 500, 350)])]
    ctx_o, ctx_9, ctx_n = (doc_icon_stats(spec8b), doc_icon_stats(spec8b, 9),
                           doc_icon_stats(spec8b, 13))
    assert ctx_o[1] > 20 * abs(sw8b) and icon_sus(sw8b, ctx_o)   # 舊路病灶保持
    assert ctx_9 == ctx_o                                        # v9 側枝=舊路(第一硬條件)
    assert ctx_n[1] <= ctx_o[1] and not icon_sus(sw8b, ctx_n)    # v13 單調+救回
    assert icon_sus(fitz.Rect(450, 500, 462, 509), ctx_n)        # 極小 icon(108)續死
    g8b = [_pg8b([(20 + 100 * k, 100, 118 + 100 * k, 198) for k in range(5)]
                 + [(40, 60, 60, 75)])]                          # 格狀+極小 icon、無大圖
    assert doc_icon_stats(g8b, 13) == doc_icon_stats(g8b)        # med_ex==med(零鬆動)
    assert icon_sus(fitz.Rect(40, 60, 60, 75), doc_icon_stats(g8b, 13))  # icon 續殺
    # (9) M5-3(v7)列首色樣版型救援:塊綁回/末塊下界/欄左不綁/既有路徑不動/
    #     圖標欄與矩陣頁閘 OFF(完整 12 案=scratchpad m53_selftest_draft,此為精華)
    pg9 = fitz.open().new_page(width=600, height=800)
    for x, y, t in [(300, 130, "MLNM"), (300, 200, "MAQ4"), (300, 330, "MH05"),
                    (300, 775, "PGFT"), (55, 115, "M8FX"), (10, 250, "MMDA")]:
        pg9.insert_text((x, y), t, fontsize=10)
    col = [fitz.Rect(40, 100, 100, 150), fitz.Rect(40, 300, 100, 350)]
    a7 = {w[4]: (i, d) for w, i, d in assign_words(pg9, col, 7)}
    a6 = {w[4]: i for w, i, _ in assign_words(pg9, col, 6)}
    assert a6["MLNM"] is None and a6["MAQ4"] is None and a6["MH05"] is None
    assert a7["MLNM"] == (0, -2.0) and a7["MAQ4"] == (0, -2.0)  # 塊1 首列+下方列
    assert a7["MH05"] == (1, -2.0)                              # 塊2
    assert a7["PGFT"][0] is None   # 頁腳:末塊下界=min(0.92×800, 300+1.5×200)=600
    assert a7["MMDA"][0] is None   # 欄左側碼不綁(碼須在欄右)
    assert a7["M8FX"] == (0, 0.0)  # xrow 既有路徑逐位不動
    icons = [fitz.Rect(40, 100, 60, 114), fitz.Rect(40, 160, 60, 174)]
    assert all(i is None for w, i, _ in assign_words(pg9, icons, 7))   # 圖標欄:色樣性擋
    mx = [fitz.Rect(50, 100, 110, 150), fitz.Rect(150, 100, 210, 150)]
    assert ([(w[4], i, d) for w, i, d in assign_words(pg9, mx, 7)]
            == [(w[4], i, d) for w, i, d in assign_words(pg9, mx, 6)])  # 矩陣 v7==v6
    het = [fitz.Rect(40, 100, 100, 150), fitz.Rect(40, 300, 100, 390)]  # T8c 高 50/90
    assert all(i is None for w, i, d in assign_words(pg9, het, 7)
               if w[4] == "MAQ4")                 # 異質成員(1.8>1.5)→ 閘 OFF
    pgb = fitz.open().new_page(width=600, height=800)                   # T8b 欄帶 6 詞
    for x, y, t in [(300, 200, "M0V1")] + [(42, 180 + 12 * k, f"CAP{k}") for k in range(6)]:
        pgb.insert_text((x, y), t, fontsize=10)
    assert all(i is None for w, i, _ in assign_words(pgb, col, 7)
               if w[4] == "M0V1")                 # 帶內詞 6>2×2 → 閘 OFF

    # (10) E-1(v9)場景照搶綁——合成案例全表 T1-T9+T5b(e1_design_v9.md v3,
    #      2026-07-12 審核核可)。紀律:基線斷言(=v8 行為)先綠=基線凍結,
    #      才准動 v9 實作;v9 期望斷言隨實作補於各案。
    def _pg(imgs, texts, w=600, h=800):
        pg = fitz.open().new_page(width=w, height=h)
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8))
        for r in imgs:
            pg.insert_image(fitz.Rect(r), pixmap=pix)
        for x, y, t in texts:
            pg.insert_text((x, y), t, fontsize=10)
        return pg

    def _scan(pg, codes, ver):
        return scan_page(pg, codes, frozenset(), ver, None, None)

    def _both(pg, codes):
        """回傳 (v8, v9);並斷言 v9 恆等式 review=n_codes-aligned-blk。"""
        r8, r9 = _scan(pg, codes, 8), _scan(pg, codes, 9)
        assert r9["code_needs_review"] == r9["n_codes"] - r9["code_x_aligned"] - r9["code_block_bound"]
        return r8, r9

    BIG = (100, 100, 500, 420)                    # 128000=26.7% 頁(照片級)
    assert abs(fitz.Rect(BIG)) >= V9_G * 480000   # S1 常數關係(T8 門檻斷言)
    assert 40 * 40 < V9_G * 480000                # 小色樣必不觸發 S1
    # T1 場景照+5碼、無尺寸、帶內多碼 → 基線 aligned=5;v9 全降級
    t1 = _pg([BIG], [(250, 500 + 20 * k, f"MQA{k}") for k in range(5)])
    r8, r9 = _both(t1, {f"MQA{k}" for k in range(5)})
    assert (r8["n_codes"], r8["code_x_aligned"], r8["code_needs_review"]) == (5, 5, 0), r8
    assert (r9["code_x_aligned"], r9["code_photo_demoted"], r9["code_needs_review"]) == (0, 5, 5), r9
    # T2 寬幅照片+帶外碼+同列尺寸(FMG 特寫規格列型)→ v9 保留(S2a);
    # T2d 對偶=移除尺寸 → v9 降級(隔離 S2a;v3 構造修正:帶內單碼型對偶會被
    # S2b 接住=T5b 設計意圖,故 T2 用帶外碼構造)
    WIDE = (100, 80, 580, 230)                    # 72000=15% 頁,帶=max(1.5×150,40)=225
    t2 = _pg([WIDE], [(250, 600, "MQB1"), (380, 600, "60x120")])
    t2d = _pg([WIDE], [(250, 600, "MQB1")])
    r8, r9 = _both(t2, {"MQB1"})
    assert r8["code_x_aligned"] == 1 and (r9["code_x_aligned"], r9["code_photo_demoted"]) == (1, 0), (r8, r9)
    r8, r9 = _both(t2d, {"MQB1"})
    assert r8["code_x_aligned"] == 1 and (r9["code_x_aligned"], r9["code_photo_demoted"]) == (0, 1), (r8, r9)
    # T3 大圖+帶內唯一碼、尺寸不同列 → v9 保留(S2b);T3d 對偶=帶內第二碼 → 全降級
    t3 = _pg([BIG], [(250, 500, "MQC1"), (380, 700, "60x120")])
    t3d = _pg([BIG], [(250, 500, "MQC1"), (250, 520, "MQC2"), (380, 700, "60x120")])
    r8, r9 = _both(t3, {"MQC1"})
    assert r8["code_x_aligned"] == 1 and (r9["code_x_aligned"], r9["code_photo_demoted"]) == (1, 0), (r8, r9)
    r8, r9 = _both(t3d, {"MQC1", "MQC2"})
    assert r8["code_x_aligned"] == 2 and (r9["code_x_aligned"], r9["code_photo_demoted"]) == (0, 2), (r8, r9)
    # T4 15 小色樣網格(Level 型)→ v9 與 v8 共同欄逐位一致
    imgs4 = [(60 + 100 * c, 60 + 150 * rw, 100 + 100 * c, 100 + 150 * rw)
             for rw in range(3) for c in range(5)]
    txt4 = [(62 + 100 * c, 112 + 150 * rw, f"MT{rw * 5 + c:02d}")
            for rw in range(3) for c in range(5)]
    t4 = _pg(imgs4, txt4)
    r8, r9 = _both(t4, {f"MT{k:02d}" for k in range(15)})
    assert (r8["n_sw"], r8["code_x_aligned"], r8["code_needs_review"]) == (15, 15, 0), r8
    assert {k: v for k, v in r9.items() if k in r8} == r8 and r9["code_photo_demoted"] == 0, r9
    # T5 寬幅照片+碼帶外(d≈370>225,sec-xin 路)無尺寸 → v9 降級
    t5 = _pg([WIDE], [(250, 600, "MQD1")])
    r8, r9 = _both(t5, {"MQD1"})
    assert (r8["code_x_aligned"], r8["code_far"]) == (1, 1), r8
    assert (r9["code_x_aligned"], r9["code_photo_demoted"], r9["code_needs_review"]) == (0, 1, 1), r9
    # T5b 同幅照片+碼帶內(d≈70,帶內唯一碼)→ v9 保留=設計意圖(確認行)
    t5b = _pg([WIDE], [(250, 300, "MQD2")])
    r8, r9 = _both(t5b, {"MQD2"})
    assert (r8["code_x_aligned"], r8["code_far"]) == (1, 0), r8
    assert (r9["code_x_aligned"], r9["code_photo_demoted"]) == (1, 0), r9
    # T6 大圖+3碼共享+逐碼同列尺寸+無圖說 → v9 全降級(v3.1 翻面=原審預授權
    # 第二分支:多碼共享使 S2a 失效);T6d=移除尺寸 → 同降級
    txt6 = [(250, 500 + 20 * k, f"MQE{k}") for k in range(3)]
    t6 = _pg([BIG], txt6 + [(380, 500 + 20 * k, "60x120") for k in range(3)])
    t6d = _pg([BIG], txt6)
    c6 = {f"MQE{k}" for k in range(3)}
    for pg9 in (t6, t6d):
        r8, r9 = _both(pg9, c6)
        assert r8["code_x_aligned"] == 3 and (r9["code_x_aligned"], r9["code_photo_demoted"]) == (0, 3), (r8, r9)
    # T6u 唯一性對偶(v3.1):T2 構造+第二碼(各有同列尺寸、皆帶外)→ 全降級;
    # 與 T2(單碼同構造=保留)對照,隔離「唯一對齊碼」條件本身
    t6u = _pg([WIDE], [(250, 600, "MQH1"), (380, 600, "60x120"),
                       (250, 640, "MQH2"), (380, 640, "60x120")])
    r8, r9 = _both(t6u, {"MQH1", "MQH2"})
    assert r8["code_x_aligned"] == 2 and (r9["code_x_aligned"], r9["code_photo_demoted"]) == (0, 2), (r8, r9)
    # T7 照片主導 doc 內的正常小色樣頁 → v9 逐位不變(S1 對小色樣零觸碰)
    imgs7 = [(60 + 90 * c, 60, 100 + 90 * c, 100) for c in range(6)]
    t7 = _pg(imgs7, [(62 + 90 * c, 112, f"MU{c:02d}") for c in range(6)])
    r8, r9 = _both(t7, {f"MU{c:02d}" for c in range(6)})
    assert r8["code_x_aligned"] == 6, r8
    assert {k: v for k, v in r9.items() if k in r8} == r8 and r9["code_photo_demoted"] == 0, r9
    # T8 照片主導檔大圖+3碼無尺寸(G 臂=唯一臂,門檻斷言在 BIG 常數關係)→ 全降級
    t8 = _pg([BIG], [(250, 500 + 20 * k, f"MQF{k}") for k in range(3)])
    r8, r9 = _both(t8, {f"MQF{k}" for k in range(3)})
    assert r8["code_x_aligned"] == 3, r8
    assert (r9["code_x_aligned"], r9["code_photo_demoted"], r9["code_needs_review"]) == (0, 3, 3), r9
    # T8b 同型檔:大圖+單碼+同列尺寸 → v9 保留(G 臂不誤殺 S2 有證者)
    t8b = _pg([BIG], [(250, 500, "MQG1"), (380, 500, "60x120")])
    r8, r9 = _both(t8b, {"MQG1"})
    assert r8["code_x_aligned"] == 1 and (r9["code_x_aligned"], r9["code_photo_demoted"]) == (1, 0), (r8, r9)
    # T9 塊綁頁(向量色樣欄+大向量塊,無 raster)→ v9 塊綁逐位不變、demoted∩塊綁=∅
    t9 = fitz.open().new_page(width=600, height=800)
    for rct in (fitz.Rect(40, 100, 100, 150), fitz.Rect(40, 300, 100, 350),
                fitz.Rect(320, 480, 520, 710)):  # 第三塊=大向量(46000<0.1×頁)無碼
        t9.draw_rect(rct, fill=(0.5, 0.5, 0.5), color=None)
    for x, y, t in [(300, 130, "MLNM"), (300, 200, "MAQ4"), (300, 330, "MH05")]:
        t9.insert_text((x, y), t, fontsize=10)
    r8, r9 = _both(t9, {"MLNM", "MAQ4", "MH05"})
    assert (r8["code_block_bound"], r8["code_x_aligned"], r8["code_needs_review"]) == (3, 0, 0), r8
    assert {k: v for k, v in r9.items() if k in r8} == r8 and r9["code_photo_demoted"] == 0, r9

    # (11) S2-2 延伸 L1(v10)SL-1~SL-4(s22ext_design.md;SL-2=修正②對抗構造:
    #      P 必須成立,真碼靠 B/A' 雙偽倖免,禁止靠 P 不成立通過)
    def _doc11(texts):
        d11 = fitz.open()
        p11 = d11.new_page(width=600, height=800)
        for x, y, t in texts:
            p11.insert_text((x, y), t, fontsize=10)
        return d11

    d1 = _doc11([(500, 100, "A11"), (500, 130, "A28"), (500, 160, "A86"),
                 (500, 190, "A102"), (100, 100, "MQ1X"),
                 (100, 300, "A512"), (100, 330, "E220")])
    k8_, rb8 = code_candidates(d1, set(), 5, 8, frozenset())
    k10, rb10 = code_candidates(d1, set(), 5, 10, frozenset())
    assert rb8["band"] == {"A11", "A28", "A86"} and {"A102", "A512", "E220", "MQ1X"} <= k8_
    assert "A102" in rb10["band"] and "A102" not in k10           # SL-1:B 臂歸隊
    assert k10 == k8_ - {"A102"}                                  # SL-2:A512(P成立)
    #                                                               /E220/MQ1X 全倖免
    d2 = _doc11([(500, 100, "T14"), (500, 130, "T31"), (500, 160, "T59")]
                + [(100 + 60 * k, 400, "T204") for k in range(4)])
    k8b, _ = code_candidates(d2, set(), 5, 8, frozenset())
    k10b, rb10b = code_candidates(d2, set(), 5, 10, frozenset())
    assert "T204" in k8b and "T204" in rb10b["band"] and "T204" not in k10b  # SL-3:A' 臂
    d2b = _doc11([(100 + 60 * k, 400, "T204") for k in range(4)])
    k10c, rb10c = code_candidates(d2b, set(), 5, 10, frozenset())
    assert "T204" in k10c and not rb10c["band"]                   # SL-3 對偶:P 破不歸隊
    digs = ([(100, 100 + 20 * k, f"{10 + k}") for k in range(8)]
            + [(150, 100 + 20 * k, f"{10 + k}") for k in range(8)])
    d3 = _doc11([(500, 100, "A11"), (500, 130, "A28"), (500, 160, "A86")]
                + digs + [(100 + 60 * k, 600, "58") for k in range(4)])
    k8d, _ = code_candidates(d3, set(), 8, 8, frozenset())
    k10d, _rb = code_candidates(d3, set(), 8, 10, frozenset())
    assert "58" in k8d and k10d == k8d                            # SL-4:junk 控制零觸碰

    # (12) S2-1 延伸 ③型「塊內尺寸繼承」合成案 SM-1~SM-6(設計=output/
    #      s21ext_design.md;工作包#1 落基線、工作包#2 落 v12 期望斷言)
    dm = _doc11([(100, 100, "MZ10"), (200, 100, "60x60"),
                 (100, 130, "MZ20"), (200, 130, "30x60"),
                 (100, 160, "MZ30"), (200, 160, "90x90"),
                 (100, 190, "MZAB"), (100, 220, "MZAC"),   # SM-1 塊內無尺寸列
                 (100, 500, "MZAD"),                        # SM-2 斷裂孤兒(gap≫2×欄距)
                 (400, 190, "MZAE")])                       # SM-3 欄外碼形詞
    kbm, _rm = code_candidates(dm, set(), 5, 10, frozenset())
    assert {"MZ10", "MZ20", "MZ30"} <= kbm                        # 錨列照收
    assert not ({"MZAB", "MZAC", "MZAD", "MZAE"} & kbm), kbm      # v10 基線:③型全漏
    k12m, _r12 = code_candidates(dm, set(), 5, 12, frozenset())
    assert {"MZ10", "MZ20", "MZ30", "MZAB", "MZAC"} <= k12m, k12m  # SM-1+SM-4 收
    assert not ({"MZAD", "MZAE"} & k12m), k12m   # SM-2 斷裂不收/SM-3 ②親自擋(紅線)
    # SM-6:非 4 字真碼(3/5 字各一)塊內繼承必須收——防隱形字長假設(分離量測
    #   「新收全是 4 字碼形」=觀察,不得暗變字長篩選)。④閘=錨長眾數照舊,
    #   故錨取同長構造使字長閘中立,單純隔離繼承機制
    dm3 = _doc11([(100, 100, "MA1"), (200, 100, "60x60"),
                  (100, 130, "MB2"), (200, 130, "30x60"),
                  (100, 160, "MC3"), (200, 160, "90x90"),
                  (100, 190, "MZB")])
    dm5 = _doc11([(100, 100, "MAB12"), (200, 100, "60x60"),
                  (100, 130, "MCD34"), (200, 130, "30x60"),
                  (100, 160, "MEF56"), (200, 160, "90x90"),
                  (100, 190, "MZABC")])
    for d6, c6t in ((dm3, "MZB"), (dm5, "MZABC")):
        k10_6, _ = code_candidates(d6, set(), 5, 10, frozenset())
        assert c6t not in k10_6, (c6t, k10_6)     # v10 基線:③漏(先綠)
        k12_6, _ = code_candidates(d6, set(), 5, 12, frozenset())
        assert c6t in k12_6, (c6t, k12_6)         # SM-6 v12 期望:繼承收、字長中立

    # (13) S2-5 偽碼旗標 pseudo_suspects 單元(工作包#3 線③;出但標記,
    #      絕不影響 kept)。SP-1 檔名軸、SP-2 cap 撞線軸、SP-3 DOM 邊際檔軸、
    #      SP-4★ 反例:健康真碼三軸全不中
    from m2_scan import pseudo_suspects
    dp = _doc11([(100, 100, "MZ10"), (200, 100, "60x60"),
                 (100, 130, "MZ20"), (200, 130, "30x60"),
                 (100, 160, "MZ30"), (200, 160, "90x90"),
                 (100, 190, "MZSE"), (200, 190, "45x45")])
    kp, _rp = code_candidates(dp, set(), 5, 12, frozenset())
    assert "MZSE" in kp
    s1 = pseudo_suspects(dp, kp, "Brand_MZSE_Catalogue", frozenset())
    assert s1 == {"MZSE"}, s1                     # SP-1 檔名軸(SP-4:MZ10 等不中)
    # SP-2 cap 撞線:單頁檔 thr=max(2×med(=1)=2, 0.6×1)=2;MZAB occ=2=thr 撞線,
    #     MZAC occ=1<thr 餘裕 → 不中(OPUS/MLNL 已知病例對之合成鏡像)
    dc = _doc11([(100, 100, "MZ10"), (200, 100, "60x60"),
                 (100, 130, "MZAB"), (200, 130, "30x60"), (400, 300, "MZAB"),
                 (100, 160, "MZAC"), (200, 160, "90x90")])
    kc, _rc = code_candidates(dc, set(), 5, 12, frozenset())
    assert {"MZAB", "MZAC"} <= kc
    s2 = pseudo_suspects(dc, kc, "x", frozenset())
    assert s2 == {"MZAB"}, s2                     # SP-2(SP-4:MZAC/MZ10 不中)
    # SP-3 DOM 邊際檔:eff={MZ10,MZ20,MZA10} 長度眾數 2/3=0.67∈[0.6,0.7)
    #     → ⑦照舊放行、字母碼全標(OCT 型);alnum 錨不標
    dd = _doc11([(100, 100, "MZ10"), (200, 100, "60x60"),
                 (100, 130, "MZ20"), (200, 130, "30x60"),
                 (100, 160, "MZA10"), (200, 160, "90x90"),
                 (100, 190, "MZAB"), (200, 190, "45x45")])
    kd, _rd = code_candidates(dd, set(), 5, 12, frozenset())
    assert "MZAB" in kd
    s3 = pseudo_suspects(dd, kd, "x", frozenset())
    assert "MZAB" in s3 and not s3 & {"MZ10", "MZ20", "MZA10"}, s3  # SP-3
    print("selftest OK")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        selftest()
    elif len(sys.argv) != 4:
        sys.exit(__doc__)
    else:
        main(*sys.argv[1:4])
