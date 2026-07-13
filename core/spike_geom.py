#!/usr/bin/env python3
"""§0.2 綁定 spike — 純幾何基線(不用任何模型)。

    python3 spike_geom.py <pdf> <page_1based> <tag> [gt.json]

對每個色樣捕捉:row(同 y 帶、全寬)→ 空則 below(下方圖說帶)。
GT 格式:[{"code": "...", "name": "..."}, ...];正確 = 該色樣捕捉文字
同時含 code token 與 name 首詞,且該 code 只被一個色樣命中。
輸出 overlay PNG + JSON 到 output/spike/。
"""
import json
import sys
from pathlib import Path

import fitz


def extract_swatches(page, version=1):
    pa = abs(page.rect)
    cands = [fitz.Rect(i["bbox"]) for i in page.get_image_info()]
    cands = [r for r in cands if 60 < abs(r) < 0.55 * pa and r.width > 6 and r.height > 6]
    if not cands:  # 向量色樣(Topcer 型)fallback:PDF 繪圖指令,非 raster CV
        cands = [d["rect"] for d in page.get_drawings()
                 if d.get("fill") and 60 < abs(d["rect"]) < 0.1 * pa]
        if version >= 3:  # v3 家具過濾:縱向細長條(側欄/表格分隔線)。僅限向量
            ph = page.rect.height  # fallback——raster 產品照可為合法長條(Millelegni
            cands = [r for r in cands  # 直立木板 h/w 6-8,dev 自測實證,不得誤殺)
                     if not (r.height >= 6 * r.width and r.height >= 0.25 * ph)]
    out = []
    for r in sorted(cands, key=lambda r: (r.y0, r.x0)):
        if not any(abs(r & o) > 0.5 * min(abs(r), abs(o)) for o in out if r.intersects(o)):
            out.append(r)
    return out


# M5-3(v7)列首色樣版型閘控常數——全部相對量(頁內統計/頁尺寸比例),無絕對尺寸:
M53_MIN_COL = 2     # 欄成員數下限(單色樣不成欄)
M53_H_MED = 3       # 色樣性下限:高度 ≥ 3×頁中位詞高(pictogram≈1-2 行字高,擋圖標欄)
M53_AREA = 0.03     # 色樣性上限:面積 ≤ 3% 頁(擋照片級大圖假欄)
M53_X0_TOL = 0.02   # 欄 x0 對齊容差(×頁寬;矩陣頂列/錯位欄不成欄)
M53_LEFT = 0.45     # 欄右緣須在所屬半頁左側帶(×半頁寬)
M53_BOT = 0.92      # 末塊絕對下界(×頁高=邊帶,頁腳不入塊)
M53_PITCH = 1.5     # 末塊相對下界(×中位欄距;不默認開到頁底)
# 兩道假欄閘(2026-07-11 dev 凍結,catalogs7 前不准再調;蓋不同型態、無頁同時中,
# 歸因可分離——dev 實測:FMG p274-276 只死 band、p277 只死 unif,真列版型頁
# band 全 0-19 詞/unif 全 1.00):
M53_BAND_W = 2      # 欄帶淨空:帶內詞 ≤ 2×成員數(包裝箱表型=帶內說明文字 50-84 詞)
#                     ⚠ 已知弱點:成員數小時閾值鬆(2 成員=容 4 詞),p277 型靠 unif 補
M53_H_UNIF = 1.5    # 成員高度一致:max/min ≤ 1.5(貨架照+小圖塊異質堆疊=1.73;
#                     列首色樣=同模板產物,真列版型頁實測全 1.00)
# 「列 y 均勻」(原票語)不實作:真列版型欄距本就不均(Uniche p13=3.22,色塊列數
# 不同),做了會殺真陽性;殘餘暴露=同尺寸圖不等距堆疊+帶內少詞型假欄(catalogs7 監看)


def m53_blocks(page, sws, words):
    """M5-3(v7)列首色樣版型偵測:{fold側: [(y0, y_end, sw_idx, col_x1)]};
    非列版型頁回傳 {}(閘 OFF)。中塊下界=下一色樣 y0;末塊下界=
    min(M53_BOT×頁高, y0+M53_PITCH×中位欄距)——切太緊的方向=漏救進佇列(安全側)。"""
    hs = sorted(w[3] - w[1] for w in words)
    if not hs:
        return {}
    h_med = hs[len(hs) // 2]
    pa, pw, ph = abs(page.rect), page.rect.width, page.rect.height
    fold = pw / 2 if pw > 1.2 * ph else None    # 同 m3_scan.fold_x(不可反向 import)
    sides = {}
    for i, r in enumerate(sws):
        if r.height < M53_H_MED * h_med or abs(r) > M53_AREA * pa:
            continue                             # 非色樣性(icon/照片級)不入欄
        side = (r.x0 + r.x1) / 2 < fold if fold else None
        sides.setdefault(side, []).append((i, r))
    blocks = {}
    for side, col in sides.items():
        if len(col) < M53_MIN_COL:
            continue
        col.sort(key=lambda t: t[1].y0)
        if max(r.x0 for _, r in col) - min(r.x0 for _, r in col) > M53_X0_TOL * pw:
            continue                             # 欄 x0 不對齊
        x_org = fold if (fold and side is False) else 0.0
        half = (pw - fold) if (fold and side is False) else (fold or pw)
        if max(r.x1 for _, r in col) > x_org + M53_LEFT * half:
            continue                             # 欄不在左側帶
        hs = [r.height for _, r in col]
        if max(hs) > M53_H_UNIF * min(hs):
            continue                             # 成員高度異質(T8c 貨架照堆疊型假欄)
        pit = sorted(col[k + 1][1].y0 - col[k][1].y0 for k in range(len(col) - 1))
        mp = pit[len(pit) // 2]
        cx1 = max(r.x1 for _, r in col)
        y_bot = min(M53_BOT * ph, col[-1][1].y0 + M53_PITCH * mp)
        n_in = sum(1 for w in words              # 欄帶淨空(T8b 包裝箱表型假欄):
                   if min(r.x0 for _, r in col) - 2 <= (w[0] + w[2]) / 2 <= cx1 + 2
                   and col[0][1].y0 <= (w[1] + w[3]) / 2 <= y_bot)
        if n_in > M53_BAND_W * len(col):
            continue
        blocks[side] = [(r.y0, col[k + 1][1].y0 if k + 1 < len(col)
                         else y_bot, i, cx1)
                        for k, (i, r) in enumerate(col)]
    return blocks


def assign_words(page, sws, version=1):
    """反向指派:每個 word → (sw_idx | None, gap)。皆內容推導,無版型假設。
    v1(M1 凍結版):1 同列 → 2 圖說在圖下方 → 3 垂直區段(最近上方色樣起點)。
    v2(M2 擴充):v1 + 2b 圖說在圖上方;規則 3 有 x 重疊者優先(欄親和,修交叉矩陣)。
    v3(M3):規則 1 加 x 約束——同列僅在 x 涵蓋時立即綁;x 不涵蓋的「鬆散同列」
    降級到 2a/2b/規則3-x親和 之後(修 M2 GT 實證的 30.1% d=0 越頁/家具搶綁)。
    v4(M4-3):詞級 x 對齊全無(xrow/2a/2b/3x 皆空)→ orphan——鬆散同列與無 xin 的
    遠端 sec(純 y 距離)兩種硬綁一律放棄(M3 GT:v3 殘錯 88% 集中無色樣代碼表頁,
    正是這兩條路徑;orphan=誠實放棄,needs_review 接手)。
    v7(M5-3):列首色樣版型救援——m53_blocks 閘 ON 時,would-be orphan 落在
    區塊內且在欄右側(cx>col_x1+2)→ 綁列首色樣,d=-2.0 哨兵(scan 層以此記帳/
    排除圖說收集)。只接手 v4 的兩條 orphan 路;xrow/2a/2b/sec-xin 逐位不動
    (驗收合約第一條:非列版型頁 v6→v7 零 diff)。
    """
    words = page.get_text("words")
    blocks = m53_blocks(page, sws, words) if version >= 7 else None
    if blocks is not None:
        pw, ph = page.rect.width, page.rect.height
        m53_fold = pw / 2 if pw > 1.2 * ph else None

    def m53(w, cx, cy):
        """would-be orphan 的 M5-3 救援;不中回 None(維持 orphan)。"""
        if not blocks:
            return None
        side = cx < m53_fold if m53_fold else None
        for y0, y1, i, cx1 in blocks.get(side, ()):
            if y0 <= cy < y1 and cx > cx1 + 2:
                return (w, i, -2.0)
        return None

    out = []
    for w in words:
        cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
        row = [(abs((r.x0 + r.x1) / 2 - cx), i) for i, r in enumerate(sws)
               if r.y0 - 2 <= cy <= r.y1 + 2]
        if row:
            if version < 3:
                out.append((w, min(row)[1], 0.0))
                continue
            xrow = [(d, i) for d, i in row if sws[i].x0 - 2 <= cx <= sws[i].x1 + 2]
            if xrow:
                out.append((w, min(xrow)[1], 0.0))
                continue
            # v3:x 不涵蓋 → 不立即綁,先讓 x 對齊規則(2a/2b/3x)嘗試
        above = [(cy - r.y1, i) for i, r in enumerate(sws)
                 if r.y1 - 2 <= cy and min(w[2], r.x1) - max(w[0], r.x0) > 0.3 * (w[2] - w[0])]
        above = [(d, i) for d, i in above if d < max(1.5 * sws[i].height, 40)]
        if above:
            d, i = min(above)
            out.append((w, i, d))
            continue
        if version >= 2:
            below = [(r.y0 - cy, i) for i, r in enumerate(sws)
                     if r.y0 + 2 >= cy and min(w[2], r.x1) - max(w[0], r.x0) > 0.3 * (w[2] - w[0])]
            below = [(d, i) for d, i in below if d < max(1.5 * sws[i].height, 40)]
            if below:
                d, i = min(below)
                out.append((w, i, d))
                continue
        sec = [(cy - r.y0, i) for i, r in enumerate(sws) if r.y0 <= cy]
        if version >= 2 and sec:
            xin = [(d, i) for d, i in sec if sws[i].x0 - 2 <= cx <= sws[i].x1 + 2]
            if xin:
                sec = xin
            elif version >= 4:  # M4-3:x 對齊全無(xrow/2a/2b/3x 皆空)→ orphan,
                out.append(m53(w, cx, cy) or (w, None, -1.0))  # v7:M5-3 救援先試
                continue        # 不落鬆散同列、也不落遠端 sec(同屬非 x 對齊)
            elif version >= 3 and row:  # v3:無任何 x 對齊 → 視覺列優先於遠端 above
                out.append((w, min(row)[1], 0.0))
                continue
        if sec:
            d, i = min(sec)
            out.append((w, i, max(0.0, cy - sws[i].y1)))
        elif version >= 3 and row:
            out.append((w, min(row)[1], 0.0) if version < 4
                       else (m53(w, cx, cy) or (w, None, -1.0)))
        else:
            out.append(m53(w, cx, cy) or (w, None, -1.0))
    return out


def bind(page, sws, version=1):
    assigned = {i: [] for i in range(len(sws))}
    for w, i, _ in assign_words(page, sws, version):
        if i is not None:
            assigned[i].append(w)
    res = []
    for i, r in enumerate(sws):
        ws = sorted(assigned[i], key=lambda w: (round(w[1]), w[0]))
        res.append({"id": i, "bbox": [round(v, 1) for v in r],
                    "text": " ".join(w[4] for w in ws)[:2000]})
    return res


def score(bindings, gt):
    def tokens(s):
        return {t.strip("*,;:()").upper() for t in s.split()}
    code_hits, full_hits = 0, 0
    for g in gt:
        code, name1 = g["code"].upper(), g["name"].split()[0].upper()
        matched = [b for b in bindings if code in tokens(b["text"])]
        if len(matched) == 1:
            code_hits += 1
            if name1 in tokens(matched[0]["text"]):
                full_hits += 1
    return code_hits, full_hits


def main(pdf, pageno, tag, gt_path=None):
    page = fitz.open(pdf)[int(pageno) - 1]
    sws = extract_swatches(page)
    bindings = bind(page, sws)
    shape = page.new_shape()
    for b in bindings:
        r = fitz.Rect(b["bbox"])
        shape.draw_rect(r)
        shape.finish(color=(1, 0, 0), width=1.2)
        shape.insert_text(fitz.Point(r.x0 + 1, r.y0 + 9), str(b["id"]), color=(1, 0, 0), fontsize=8)
    shape.commit()
    page.get_pixmap(dpi=110).save(f"output/spike/{tag}_overlay.png")
    Path(f"output/spike/{tag}_bind.json").write_text(json.dumps(bindings, indent=1, ensure_ascii=False))
    print(f"{tag}: {len(sws)} swatches")
    if gt_path:
        gt = json.loads(Path(gt_path).read_text())
        c, f = score(bindings, gt)
        print(f"  GT={len(gt)}  code_acc={c}/{len(gt)}={c/len(gt):.0%}  code+name_acc={f}/{len(gt)}={f/len(gt):.0%}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:5])
