#!/usr/bin/env python3
"""孤兒磁磚圖召回 分離量測探針(通案三:入庫;設計案 output/orphan_swatch_recall_design.md 數字來源)。

純儀器、只讀、零產線改動。量「被幾何偵測到、但沒配到碼」的色樣圖(orphan swatch)裡,
用「尺寸鄰近 ∧ 非大面積」訊號能篩出多少高機率真磁磚——供「連磁磚都沒標」呈現層改善評估。

    /opt/homebrew/bin/python3 dev/orphan_swatch_probe.py <product_dir> [--corpus DIR ...]   (CWD=主樹專案根)
    /opt/homebrew/bin/python3 dev/orphan_swatch_probe.py --selftest

訊號(使用者 2026-07-14 提案,per-doc 幾何結構、非形狀寫死):
  orphan   = extract_swatches 偵測到、但 bbox 不與任何已綁定色樣重疊(>30%)的圖;
  size_near= 圖底部中心下方 [-0.3h, 1.2h]、水平 ±max(60,寬) 內有 SIZE_RE 尺寸 token;
  is_large = 圖面積 ≥ V9_G(=0.10)×頁面積(E-1 場景照面積閘,疑情境/房間照,排除);
  高機率真磁磚 = orphan ∧ size_near ∧ ¬is_large。
★已知但書:拼磚/馬賽克頁(dense mosaic)每小格=小圖+尺寸,會大量誤篩(Topcer 型);
  正規化須排除塌縮/拼磚頁(沿用 pipeline 既有 assembly_collapse 偵測),本探針只曝光不排除。
"""
import glob
import os
import sys
from pathlib import Path

import fitz
import json

sys.path.insert(0, "core")
from spike_geom import extract_swatches  # noqa: E402
from census import SIZE_RE               # noqa: E402
from m3_scan import V9_G                 # noqa: E402


def find_pdf(name, corpora):
    for cd in corpora:
        for r, _, fs in os.walk(cd):
            for f in fs:
                if f == name and not f.startswith("._"):
                    return os.path.join(r, f)
    return None


def overlap(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy > 0.3 * max(1, (a[2] - a[0]) * (a[3] - a[1]))


def size_near(sw, sizes):
    cx, cyb, h = (sw.x0 + sw.x1) / 2, sw.y1, sw.y1 - sw.y0
    return any(abs(cx - sx) < max(60, sw.x1 - sw.x0) and -0.3 * h <= (sy - cyb) <= 1.2 * h
               for sy, sx in sizes)


def analyze_doc(pdf, bound_by_page):
    """回傳 (orphan, clean_tile, large):孤兒圖數 / 尺寸鄰近∧非大 / 大面積(疑場景)。"""
    doc = fitz.open(pdf)
    orphan = clean = large = 0
    for pg in doc:
        pa = abs(pg.rect)
        sws = extract_swatches(pg)
        if not sws:
            continue
        sizes = [((w[1] + w[3]) / 2, (w[0] + w[2]) / 2)
                 for w in pg.get_text("words") if SIZE_RE.search(w[4])]
        bnd = bound_by_page.get(pg.number + 1, [])
        for s in sws:
            bb = [s.x0, s.y0, s.x1, s.y1]
            if any(overlap(bb, b) for b in bnd):
                continue
            orphan += 1
            if (s.x1 - s.x0) * (s.y1 - s.y0) >= V9_G * pa:
                large += 1
            elif size_near(s, sizes):
                clean += 1
    return orphan, clean, large


def bound_pages(doc_json):
    d = json.loads(Path(doc_json).read_text())
    out = {}
    for s in d.get("series", []):
        for v in s.get("variants", []):
            for inst in v.get("mergedFrom", []):
                out.setdefault(inst["swatch"]["page"], []).append(inst["swatch"]["bbox"])
    return out, (d.get("pdf") or os.path.basename(doc_json)[:-5] + ".pdf")


def scan_pool(product_dir, corpora):
    print(f"{'檔':34} {'孤兒圖':>6} {'尺寸鄰近+非大':>12} {'大面積(疑場景)':>13}")
    to = tc = tl = 0
    for jp in sorted(glob.glob(product_dir + "/*/*.json")):
        if jp.endswith((".review.json", ".capcodes.json")) or os.path.basename(jp).startswith("._"):
            continue
        bnd, pdfn = bound_pages(jp)
        pdf = find_pdf(os.path.basename(jp).replace(".json", ".pdf"), corpora) or find_pdf(pdfn, corpora)
        if not pdf:
            continue
        o, c, l = analyze_doc(pdf, bnd)
        to += o; tc += c; tl += l
        print(f"{os.path.basename(jp)[:-5][:34]:34} {o:>6} {c:>12} {l:>13}")
    print(f"\n{'總計':34} {to:>6} {tc:>12} {tl:>13}")
    print(f"→ 孤兒磁磚圖 {to},其中 {tc} 張『尺寸鄰近∧非大面積』=高機率真磁磚、{tl} 張大面積=疑場景照(該過濾)。")
    print("★但書:拼磚頁(Topcer 型)會使 clean 值暴增(馬賽克小格),正規化須排除塌縮頁——見設計案。")
    return to, tc, tl


class _SW:
    def __init__(s, x0, y0, x1, y1):
        s.x0, s.y0, s.x1, s.y1 = x0, y0, x1, y1


def selftest():
    # 合成:一張小圖底下有尺寸=clean;一張大圖(場景)=large;一張小圖無尺寸=既非 clean 非 large
    tile = _SW(100, 100, 140, 140)          # 40x40 小圖
    sizes = [(150, 120)]                     # 尺寸在圖正下方(y=150 在 [-0.3h,1.2h] 內)
    assert overlap([100, 100, 140, 140], [105, 105, 138, 138]) is True
    assert overlap([100, 100, 140, 140], [300, 300, 340, 340]) is False
    assert size_near(tile, sizes) is True
    assert size_near(tile, [(500, 120)]) is False       # 尺寸太遠
    assert size_near(tile, [(150, 900)]) is False       # 水平太遠
    print("orphan_swatch_probe selftest OK")
    return True


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    args = sys.argv[1:]
    prod = next((a for a in args if not a.startswith("--")), None)
    corpora = [args[i + 1] for i, a in enumerate(args) if a == "--corpus"] \
        or sorted(glob.glob("catalogs*"))
    if not prod:
        sys.exit(__doc__)
    scan_pool(prod, corpora)
