#!/usr/bin/env python3
"""Held-out 選件統計:每份 PDF 的「圖說在上」訊號(驗證 2b 硬條件用)。

    python3 caption_signal.py <corpus_dir_or_pdf>

定義(鏡射 spike_geom 規則 2 的距離幾何,僅作選件統計,不是綁定規則、不看頁面):
  一個色樣計為「圖說在上」= 其上方 cap 帶(cap = max(1.5*高, 40pt))內有 x 重疊文字,
  且下方 cap 帶內沒有 → 2b 是唯一能接住該圖說的規則。
輸出:每份 doc 的 above-only 色樣數、頁分布;供 heldout3 宣告引用。
"""
import sys
from pathlib import Path

import fitz

from census import SIZE_RE
from spike_geom import extract_swatches


def page_signal(page):
    sws = extract_swatches(page)
    if not sws or len(sws) > 50:  # 密集向量頁噪音大,不算訊號
        return 0
    words = page.get_text("words")
    n = 0
    for r in sws:
        cap = max(1.5 * r.height, 40)
        def band(lo, hi):
            return any(lo < (w[1] + w[3]) / 2 < hi
                       and min(w[2], r.x1) - max(w[0], r.x0) > 0.3 * (w[2] - w[0])
                       for w in words)
        if band(r.y0 - cap, r.y0) and not band(r.y1, r.y1 + cap):
            n += 1
    return n


def doc_signal(pdf):
    doc = fitz.open(pdf)
    per_page = {}
    for page in doc:
        if len(SIZE_RE.findall(page.get_text())) < 3:
            continue
        n = page_signal(page)
        if n:
            per_page[page.number + 1] = n
    return per_page


def main(target):
    p = Path(target)
    pdfs = [p] if p.suffix == ".pdf" else [q for q in sorted(p.rglob("*.pdf"))
                                           if not q.name.startswith("._")]
    for pdf in pdfs:
        pp = doc_signal(pdf)
        tot = sum(pp.values())
        strong = [pg for pg, n in pp.items() if n >= 3]
        print(f"{str(pdf):60s} above-only={tot:<4d} pages(>=3)={strong} all={pp}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
