#!/usr/bin/env python3
"""M2 掃描:身分鍵(代碼∪色名+尺寸)+ 規則版本切換。

    python3 m2_scan.py <corpus_dir> <v1|v2> <out.csv>

詞彙表一律建自 catalogs/(13 家 dev corpus),不從 held-out 學任何統計。
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

from census import SIZE_RE
from m1_scan import CODE_RE, norm
from spike_geom import assign_words, extract_swatches


def doc_token_sets(pdf):
    codes, alphas = set(), set()
    for page in fitz.open(pdf):
        for w in page.get_text("words"):
            t = norm(w[4])
            if CODE_RE.match(t) and any(c.isdigit() for c in t) and any(c.isalpha() for c in t):
                codes.add(t)
            elif t.isalpha() and len(t) >= 3:
                alphas.add(t)
    return codes, alphas


def build_vocabs():
    code_df, alpha_df = Counter(), Counter()
    for pdf in sorted(Path("catalogs").rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        codes, alphas = doc_token_sets(pdf)
        code_df.update(codes)
        alpha_df.update(alphas)
    return ({t for t, n in code_df.items() if n >= 4},      # 產業規格詞彙
            {t for t, n in alpha_df.items() if n >= 8})     # 泛用詞(Naturale/Floor…);門檻高留住常見色名


BAND_RE = re.compile(r"^[A-Z]\d{1,2}$")     # 量表 token:價格帶 A11/T02、防滑 R10…
UNIT_RE = re.compile(r"^(?:CM|MM|M)[23]$")   # 面積/體積單位(CM2=cm²)
THICK_RE = re.compile(r"^\d{1,2}(?:[.,]\d)?MM$")                       # 12MM 厚度
SIZE_LEAK_RE = re.compile(                   # 複合尺寸洩漏成 alnum token(33X120X5)
    r"^\d{1,4}(?:[.,]\d{1,2})?(?:X\d{1,4}(?:[.,]\d{1,2})?)+(?:CM|MM|H)?$")


def route_junk(cands):
    """S2-2(v5):junk 出綁定候選、分流保留(SCHEMA §7 過濾≠刪除;band/unit/
    thickness/size 是欄位原料,字母→欄位語意留 Stage 5 映射,不在此寫死)。
    band=單字母+1-2 位數且同字母家族 ≥3(dev 實測:Emilgroup A##/T## 價格帶成家族,
    FMG H10/L75/R12 孤立量記——家族性=量表的 per-doc 結構訊號,非字母表寫死)。"""
    routed = {"band": set(), "unit": set(), "thickness": set(), "size": set()}
    fam = Counter(t[0] for t in cands if BAND_RE.match(t))
    for t in cands:
        if BAND_RE.match(t) and fam[t[0]] >= 3:
            routed["band"].add(t)
        elif UNIT_RE.match(t):
            routed["unit"].add(t)
        elif THICK_RE.match(t):
            routed["thickness"].add(t)
        elif SIZE_LEAK_RE.match(t):
            routed["size"].add(t)
    kept = cands - set().union(*routed.values())
    return kept, routed


V8_X_TOL = 0.005   # ②錨欄 x0 對齊容差(×頁寬)。凍結 2026-07-11:真 B 碼表格
                   #   對齊 0.0–0.5pt;0.02 會收進 CREA 7.8/FRICTION 6.8 流版偶合
V8_ROW_H = 1.5     # ③同列 y 容差(×字高;同 m3_scan._same_row_side/row_size)
V8_OCC = 2         # ⑤occ 錨中位臂(凍結)
V8_OCC_PG = 0.6    # ⑤occ 頁數臂(凍結):單頁檔門檻退回 2×med(T9/T4 必不收)
V8_OCC_CAP = 5     # ⑤occ 絕對上蓋(凍結):真 B 碼 occ 自然上界(圖說+索引+表格;
                   #   dev/夾具實測 Level 全 2、MFFE 4、MLNL 5=上蓋),系列詞
                   #   occ∝頁數(LOOK 20/VEIN 51)。OPUS occ=5=MLNL 同值不可分
                   #   =已知自信誤收,S2-5 旗標接手、c7 GT 量頻率
V8_R_MIN = 3       # ⑥檔內含尺寸列下限(凍結):小表 occ 訊號鈍化,分支不啟動
V8_DOM = 0.6       # ⑦錨形優勢比下限(凍結):有效錨長度眾數佔比 <0.6=錨品質
                   #   不足,分支不啟動(Iris 50%/Topcer 全錨 50%;Topcer 有效錨
                   #   0.67 放行 OCT=已知自信誤收,不調 0.7=單檔擬合,裁決維持)
S21_RUN_GAP = 2.0  # ③塊內尺寸繼承(v12)塊邊界:相鄰欄成員列距 ≤ S21_RUN_GAP×
                   #   該欄列距中位(凍結 2026-07-12,s21ext_design.md:敏感度
                   #   1.5 與 2.0 收錄完全相同=平台期、3.0 起外擴(UT+2/TdM+6/
                   #   Level+1)→取平台中點;塊間距實測 6.3×列距(PE p19)遠離
                   #   門檻)。動=完整儀式。


def alpha_codes(doc, occ_alnum, anchors, alpha_vocab, version=8):
    """S2-1(v8):全字母 B 類碼(MFFF/EKDM/MLNM 型)錨定升格,全 per-doc/per-page
    統計、無詞典寫死(alpha_vocab=dev 泛用詞停用補充)。校準定案+凍結(2026-07-11
    裁決:m1-m4+m6 全採;m5「同列已有錨碼不收」否決存查——Level 矩陣/Provenza
    收邊條=一列多碼,會殺 100+ 筆真碼)。往嚴偏:零誤收第一,救回量第二。閘序:
    ①形=CODE_RE 全字母、非停用詞、原文非全小寫(is_name 慣例:全小寫=散文,
      擋 vedi/more/thermal 型);
    ②錨 per-page=同頁 kept alnum(含數字碼)實例 x0 對齊(±V8_X_TOL×頁寬);
      無錨頁誠實不收(純 B 碼頁=已知殘口,per-doc 錨=另開票);
    ③同列有尺寸(折縫同側)∧④長度=有效錨長度眾數(③④=AND 凍結;平手全收=
      確定性)。有效錨=至少一實例同列有尺寸(EN14411/DIN51130 型認證雜訊錨
      不參與④⑤統計——Treverkmood 0/4 教訓);
    ⑤occ ≤ max(V8_OCC×有效錨 occ 中位, min(V8_OCC_PG×頁數, V8_OCC_CAP)):
      真 B 碼 occ 有自然上界、系列詞/縮寫 occ∝頁數(T9 NAT occ=3 必不收 ↔
      MLNM occ=3 必須收的機制衝突之解);
    ⑥含尺寸列 ≥ V8_R_MIN ∧ ⑦有效錨優勢比 ≥ V8_DOM,否則分支不啟動。
    已知自信誤收 2(OPUS/OCT,x 對齊):S2-5 偽 Variant 旗標接手。已知誠實漏:
    Viva EJJL/EJJP(欄距 12.8pt)、A02G 索引頁交叉引用 9 筆(MQAF 型)、
    EJJR-EJJU/EJDJ-L(③該列無尺寸)、Emil p15 名鍵頁(尺寸在表頭不在列)。
    S2-1 延伸③(v12,s21ext_design.md 送審核可):③尺寸列定義擴充=塊內繼承
    rowsz'(w)=rowsz(w)∨∃同欄(x0±V8_X_TOL×頁寬)上方實例 u 於同一連續塊內
    (沿欄上溯,相鄰欄成員列距 ≤S21_RUN_GAP×該欄列距中位)∧rowsz(u);
    欄成員=錨實例∪①形字母候選實例(=ax 同族群統計)。②④⑤⑥⑦ 逐位不動、
    ③④=AND 不動;繼承不跨斷裂、不出欄=失敗方向漏救。分離量測(通案二):
    dev+c7 27 檔新收 125 種全真碼、散文 0;v≤11 逐位不變(v11 預留 E-1)。"""
    if not anchors:
        return set()                                     # T5 無錨檔歸 C 類/S2-3
    occ, eff, inst, n_rows = Counter(), set(), [], 0
    for page in doc:
        pw = page.rect.width
        fold = pw / 2 if pw > 1.2 * page.rect.height else None  # 同 m3_scan.fold_x
        words = page.get_text("words")
        ax = [w[0] for w in words if norm(w[4]) in anchors]
        sz = [(((w[0] + w[2]) / 2 < fold) if fold else None, (w[1] + w[3]) / 2)
              for w in words if SIZE_RE.search(w[4])]
        hs = sorted(w[3] - w[1] for w in words)
        hm = hs[len(hs) // 2] if hs else 1
        prev = None
        for side, yc in sorted(sz):                      # ⑥含尺寸列計數(同側聚類)
            n_rows += prev is None or side != prev[0] or yc - prev[1] > V8_ROW_H * hm
            prev = (side, yc)

        def rowsz(w):
            side = ((w[0] + w[2]) / 2 < fold) if fold else None
            cy, h = (w[1] + w[3]) / 2, max(w[3] - w[1], 1)
            return any(s == side and abs(y - cy) <= V8_ROW_H * h for s, y in sz)

        mem, pend = [], []   # v12 欄成員快取 (x0,yc,rowsz) / 過①②但③無尺寸待繼承
        for w in words:
            t = norm(w[4])
            if t in anchors and rowsz(w):
                eff.add(t)                               # 有效錨
            is_alpha = t.isalpha() and CODE_RE.match(t) and t not in alpha_vocab
            if version >= 12 and (t in anchors or (is_alpha and not w[4].islower())):
                mem.append((w[0], (w[1] + w[3]) / 2, rowsz(w)))  # 欄成員(=ax 族群)
            if not is_alpha:
                continue                                 # ①形(occ 含大小寫全實例)
            occ[t] += 1
            if w[4].islower():
                continue                                 # ①原文全小寫=散文
            if not any(abs(a - w[0]) <= V8_X_TOL * pw for a in ax):
                continue                                 # ②同頁錨欄
            if rowsz(w):
                inst.append(t)                           # ③同列有尺寸
            elif version >= 12:
                pend.append((t, w[0], (w[1] + w[3]) / 2))
        for t, x0, yc in pend:                           # ③'塊內尺寸繼承(第三掃)
            col = sorted((m[1], m[2]) for m in mem if abs(m[0] - x0) <= V8_X_TOL * pw)
            gaps = [b[0] - a[0] for a, b in zip(col, col[1:]) if b[0] > a[0]]
            if not gaps:
                continue                                 # 欄無列距統計=不繼承(漏救向)
            lim = S21_RUN_GAP * sorted(gaps)[len(gaps) // 2]
            prev = yc
            for my, mrs in sorted((c for c in col if c[0] < yc - 1e-6), reverse=True):
                if prev - my > lim:
                    break                                # 塊斷裂=繼承終止
                if mrs:
                    inst.append(t)                       # 塊內上方有尺寸列=繼承
                    break
                prev = my
    if n_rows < V8_R_MIN or not eff:
        return set()                                     # ⑥小表/無有效錨不啟動
    lens = Counter(len(a) for a in eff)
    if max(lens.values()) < V8_DOM * len(eff):
        return set()                                     # ⑦錨形優勢比
    len_ok = {L for L, n in lens.items() if n == max(lens.values())}
    med = sorted(occ_alnum[a] for a in eff)[len(eff) // 2]
    thr = max(V8_OCC * med, min(V8_OCC_PG * doc.page_count, V8_OCC_CAP))
    return {t for t in set(inst) if len(t) in len_ok and occ[t] <= thr}  # ④⑤


S25_DOM_MARGIN = 0.7  # S2-5 P_dom(僅旗標層,不影響任何收錄/綁定):⑦有效錨
#   優勢比邊際檔(<0.7)之字母碼全標 pseudoCodeSuspect。校準 2026-07-12
#   (output/s25_design.md):已知病例 OCT 檔 DOM=0.67、dev 其他 alpha 活躍檔
#   DOM=1.0——0.7 取邊際帶與健康帶之間;V8_DOM=0.6 凍結不動。動=完整儀式。


def pseudo_suspects(doc, kept, fname, alpha_vocab, code_vocab=frozenset()):
    """S2-5 偽碼旗標(2026-07-12 工作包#3 線③;設計+分離量測=output/s25_design.md,
    工具=dev/s25_probe.py)。出但標記:回傳 kept 中三軸任一命中之嫌疑碼集,
    絕不影響 kept/綁定/佇列(裁決=接受存在但禁止無聲入庫);失敗方向=多標旗。
    P_fn 檔名軸:token 為檔名(去非字數字、大寫)子字串——系列/品牌名入檔名
      之產業慣例(MILANO70/41ZERO42 型;dev 27 檔誤中 0;子字串式=多標旗向,
      已知過標=ARDESIA2/O20 型截斷系列名=正中偽碼、年份片段=理論殘險)。
    P_cap 撞線軸:字母碼 occ ≥ ⑤閘 thr=零餘裕入場(OPUS occ=5=thr 撞線 vs
      票面命名真碼對照 MLNL occ=5<thr=8 餘裕入場——已知病例對分離;⑤公式
      常數全重用,無新常數)。
    P_dom 邊際檔軸:⑦有效錨優勢比 < S25_DOM_MARGIN 之檔,字母碼全標
      (OCT 檔 DOM=0.67;已知過標=Slow20 型同檔真碼 4 筆,多標旗向代價)。
    ⑤⑦統計為鏡射重演(alpha_codes=凍結路徑不動);漂移風險=送審已註記。"""
    fn = re.sub(r"[^A-Za-z0-9]", "", fname).upper()
    sus = {t for t in kept if t and t in fn}
    c, occ = Counter(), Counter()
    for page in doc:
        for w in page.get_text("words"):
            t = norm(w[4])
            if not CODE_RE.match(t) or SIZE_RE.search(t):
                continue
            if any(ch.isdigit() for ch in t) and any(ch.isalpha() for ch in t):
                c[t] += 1
            elif t.isalpha() and t not in alpha_vocab:
                occ[t] += 1
    anchors, _ = route_junk({t for t in c if t not in code_vocab})
    eff = set()
    for page in doc:
        pw = page.rect.width
        fold = pw / 2 if pw > 1.2 * page.rect.height else None
        words = page.get_text("words")
        sz = [(((w[0] + w[2]) / 2 < fold) if fold else None, (w[1] + w[3]) / 2)
              for w in words if SIZE_RE.search(w[4])]
        for w in words:
            if norm(w[4]) in anchors:
                side = ((w[0] + w[2]) / 2 < fold) if fold else None
                cy, h = (w[1] + w[3]) / 2, max(w[3] - w[1], 1)
                if any(s == side and abs(y - cy) <= V8_ROW_H * h for s, y in sz):
                    eff.add(norm(w[4]))
    if eff:
        alpha_kept = {t for t in kept if t.isalpha()}
        med = sorted(c[a] for a in eff)[len(eff) // 2]
        thr = max(V8_OCC * med, min(V8_OCC_PG * doc.page_count, V8_OCC_CAP))
        sus |= {t for t in alpha_kept if occ[t] >= thr}          # P_cap
        lens = Counter(len(a) for a in eff)
        if max(lens.values()) / len(eff) < S25_DOM_MARGIN:
            sus |= alpha_kept                                    # P_dom
    return sus


S22_ROW_N = 3  # S2-2 延伸 L1 A' 同列計數門檻(凍結 2026-07-12,s22ext_design 修正①):
#                校準=病例 A102 同列 5/A107 同列 4;dev 真碼同列 max ≥3=0 筆
#                (名義 26 種全為已知 junk/標準號且被 P 前提排除)。動=完整儀式。


def band_regroup(doc, kept, band):
    """S2-2 延伸 L1(v10):量表碼歸隊 routed band(分流保留=S2-2 哲學,過濾≠刪除;
    C 階段 priceBand 受益)。歸隊 ⟺ P(同字母 routed band 家族存在)∧
    (B 同頁與 band 實例 x 欄對齊 ±V8_X_TOL×頁寬 ∨ A' 同列同 token ≥S22_ROW_N)。
    全 per-doc 脈絡、零形狀條件(dev 分離量測+同形真碼紅燈控制=
    output/s22ext_design.md §二/SL-2);已宣告殘留=T104 型(B/A' 雙漏)。"""
    letters = {t[0] for t in band}
    cand = {t for t in kept if t and t[0] in letters}
    if not cand:
        return set()
    hitB, maxA = set(), Counter()
    for page in doc:
        words = page.get_text("words")
        pw = page.rect.width
        fold = pw / 2 if pw > 1.2 * page.rect.height else None  # 同 m3_scan.fold_x
        bx = [w[0] for w in words if norm(w[4]) in band]
        hs = sorted(w[3] - w[1] for w in words)
        hm = (hs[len(hs) // 2] if hs else 10) or 10
        rows = Counter()
        for w in words:
            t = norm(w[4])
            if t not in cand:
                continue
            if bx and min(abs(w[0] - b) for b in bx) <= V8_X_TOL * pw:
                hitB.add(t)                                    # B:band 欄對齊
            side = ((w[0] + w[2]) / 2 < fold) if fold else None
            rows[(t, side, round(((w[1] + w[3]) / 2) / (1.5 * hm)))] += 1
        for (t, _s, _y), n in rows.items():
            maxA[t] = max(maxA[t], n)                          # A':同列多實例
    return {t for t in cand if t in hitB or maxA[t] >= S22_ROW_N}


def code_candidates(doc, code_vocab, n_spec, version=4, alpha_vocab=frozenset()):
    """字母+數字混合候選;稀疏時啟動純數字碼自適應(Topcer/41Zero42 型)。
    v5(S2-2):alnum 候選 route_junk 分流(kept=綁定候選,routed=分流保留)。
    sparsity 判定沿用「未清洗」集合、digits 分支完全不動——junk 清洗不得翻轉偵測
    分支(dev 實證:Sodai 清 3 個 junk 後翻進 digits 分支,憑空多 72 個件數型純數字
    junk;件數/頁碼型純數字的根治=偵測分支的結構訊號重建,屬 S2-1/S2-3,非本票)。
    v8(S2-1):全字母 B 類分支 alpha_codes——只新增 kept,alnum/digits/routed
    既有路徑逐位不動(v≤7 bit-identical);alpha_vocab 僅 v8 分支用。
    v12(S2-1 延伸③):alpha_codes 塊內尺寸繼承(v≤11 逐位不動,v11 預留 E-1)。
    version<5 回傳 cands(舊行為);>=5 回傳 (kept, routed)。"""
    c, digits = Counter(), Counter()
    for page in doc:
        for w in page.get_text("words"):
            t = norm(w[4])
            if (CODE_RE.match(t) and any(ch.isdigit() for ch in t) and any(ch.isalpha() for ch in t)
                    and not SIZE_RE.search(t)):
                c[t] += 1
            elif t.isdigit() and len(t) in (2, 3, 5, 6, 7, 8):
                digits[t] += 1
    cands = {t for t in c if t not in code_vocab}
    kept, routed = route_junk(cands) if version >= 5 else (cands, {})
    anchors = set(kept) if version >= 8 else None  # 錨快照=digits 併入前的 alnum 候選
    if len(cands) < 0.5 * max(n_spec, 1):  # per-doc 統計判定「無字母數字 SKU」
        by_len = Counter()
        for t, n in digits.items():
            if n >= 2:
                by_len[len(t)] += 1
        if by_len and max(by_len.values()) >= 8:
            L = max(by_len, key=lambda k: by_len[k])
            kept |= {t for t, n in digits.items() if len(t) == L and n >= 2}
    if version >= 8:
        kept |= alpha_codes(doc, c, anchors, alpha_vocab, version)
    if version >= 10:  # S2-2 延伸 L1:量表碼歸隊(kept→band;v≤9 逐位不動)
        moved = band_regroup(doc, kept, routed["band"])
        kept -= moved
        routed["band"] |= moved
    return (kept, routed) if version >= 5 else kept


def scan_page(page, codes_doc, alpha_vocab, version):
    sws = extract_swatches(page)
    n_raster = sum(1 for i in page.get_image_info()
                   if 60 < abs(fitz.Rect(i["bbox"])) < 0.55 * abs(page.rect))
    ph = page.rect.height
    sw_words = {i: [] for i in range(len(sws))}
    code_stats = []
    for w, i, d in assign_words(page, sws, version):
        if i is not None:
            sw_words[i].append(w)
        if norm(w[4]) in codes_doc:
            code_stats.append((i, d))
    n_codes = len(code_stats)
    orphan = sum(1 for i, _ in code_stats if i is None)
    far = sum(1 for i, d in code_stats
              if i is not None and d > max(2 * sws[i].height, 0.15 * ph))
    sw_no_code = sw_no_id = 0
    for i in sw_words:
        toks = {norm(w[4]) for w in sw_words[i]}
        has_code = bool(toks & codes_doc)
        has_name = any(t.isalpha() and len(t) >= 3 and t not in alpha_vocab for t in toks)
        has_size = any(SIZE_RE.search(w[4]) for w in sw_words[i])
        sw_no_code += not has_code
        sw_no_id += not (has_code or (has_name and has_size))
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
    flagged = ((n_codes >= 3 and (orphan + far) / n_codes > 0.2)
               or (len(sws) > 0 and n_codes >= 3 and sw_no_code / len(sws) > 0.5)
               or (len(sws) == 0 and n_codes >= 3))
    return dict(n_sw=len(sws), n_codes=n_codes, code_orphan=orphan, code_far=far,
                sw_no_code=sw_no_code, sw_no_identity=sw_no_id, ptype=ptype, flagged=flagged)


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
        codes_doc = code_candidates(doc, code_vocab, len(spec))
        for page in spec:
            r = scan_page(page, codes_doc, alpha_vocab, version)
            rows.append({"vendor": vendor, "page": page.number + 1, **r})
        print(vendor, "done", flush=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    tc = sum(r["n_codes"] for r in rows)
    ts = sum(r["n_sw"] for r in rows)
    orph, far = sum(r["code_orphan"] for r in rows), sum(r["code_far"] for r in rows)
    print(f"\n[{corpus} {ver}] pages={len(rows)} codes={tc} swatches={ts}")
    print(f"  code bound-ok={tc-orph-far} ({(tc-orph-far)/max(tc,1):.1%})  orphan={orph} ({orph/max(tc,1):.1%})  far={far} ({far/max(tc,1):.1%})")
    print(f"  sw_no_code={sum(r['sw_no_code'] for r in rows)/max(ts,1):.1%}  sw_no_identity={sum(r['sw_no_identity'] for r in rows)/max(ts,1):.1%}")
    fl = [r for r in rows if r["flagged"]]
    print(f"  flagged={len(fl)} ({len(fl)/max(len(rows),1):.1%}) by type:", dict(Counter(r["ptype"] for r in fl)))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
