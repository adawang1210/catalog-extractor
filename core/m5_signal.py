#!/usr/bin/env python3
"""heldout5 硬條件自動訊號(不看頁面):

    python3 m5_signal.py <corpus_dir>

訊號 1|M5-1 驗收對象:色名鍵頁——每 doc 報 name_bound 頁與筆數,並把色名索引拆
  「唯一 token(1 實體)vs 撞名 token(2-3 實體,過 K 守門但有錯綁風險)」;
  撞名 token 存在且 name_bound>0 = M5-1 撞名驗收頁候選。
訊號 2|M5-2 預備驗收對象:小型填色圖形搶綁——
  (a) 面積 < 0.15×per-doc 色樣面積中位數、且有碼 x 對齊到它的色樣(表頭小圖型);
  (b) 跨頁近同位 bbox(圓整 20pt)重複 ≥3 頁的小色樣(返回鈕/版面家具型)。
# ponytail: 只做選件訊號,不改任何綁定行為;閾值僅供建批宣告,非規則
"""
import sys
from collections import Counter
from pathlib import Path
from statistics import median

import fitz

from census import SIZE_RE
from m1_scan import norm
from m2_scan import build_vocabs, code_candidates
from m3_scan import doc_name_index, scan_page
from spike_geom import assign_words, extract_swatches


def main(corpus):
    code_vocab, alpha_vocab = build_vocabs()
    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        vendor = pdf.relative_to(corpus).parts[0]
        doc = fitz.open(pdf)
        spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
        codes_doc = code_candidates(doc, code_vocab, len(spec))
        name_ctx = doc_name_index(spec, codes_doc, alpha_vocab, 4)
        name_idx = name_ctx[0]
        uniq = sum(1 for s in name_idx.values() if len(s) == 1)
        multi = {t: len(s) for t, s in name_idx.items() if 2 <= len(s) <= 3}
        # 逐頁:name_bound、小圖形訊號
        areas, sw_pages, nb_pages, small_hit = [], Counter(), [], []
        page_rows = []
        for page in spec:
            sws = extract_swatches(page, version=3)
            areas += [abs(r) for r in sws]
            for r in sws:
                sw_pages[(round(r.x0 / 20), round(r.y0 / 20),
                          round(r.x1 / 20), round(r.y1 / 20))] += 1
            r = scan_page(page, codes_doc, alpha_vocab, 4, name_ctx)
            if r["code_name_bound"]:
                nb_pages.append((page.number + 1, r["code_name_bound"]))
            page_rows.append((page, sws))
        med = median(areas) if areas else 0
        rep_boxes = {k for k, c in sw_pages.items() if c >= 3}
        for page, sws in page_rows:
            small = [i for i, r in enumerate(sws) if med and abs(r) < 0.15 * med]
            rep = [i for i, r in enumerate(sws)
                   if (round(r.x0 / 20), round(r.y0 / 20),
                       round(r.x1 / 20), round(r.y1 / 20)) in rep_boxes
                   and med and abs(r) < med]
            if not (small or rep):
                continue
            hit = sum(1 for w, i, d in assign_words(page, sws, 4)
                      if i in set(small) | set(rep) and norm(w[4]) in codes_doc
                      and sws[i].x0 - 2 <= (w[0] + w[2]) / 2 <= sws[i].x1 + 2)
            if hit:
                small_hit.append((page.number + 1, len(small), len(rep), hit))
        print(f"\n{vendor}/{pdf.name}: spec={len(spec)} codes_doc={len(codes_doc)}")
        print(f"  訊號1 色名索引: uniq_token={uniq} 撞名token(2-3實體)={len(multi)}"
              f" {dict(sorted(multi.items())[:8])}")
        print(f"  訊號1 name_bound 頁: {nb_pages or '無'}")
        print(f"  訊號2 小圖形搶對齊頁 (page,n_small,n_repeat,x對齊碼): {small_hit or '無'}")
        doc.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
