#!/usr/bin/env python3
"""S2-1 量測:因 SKU 偵測缺口而「完全漏抓」的產品數(普查階段量化隱形損失)。

    python3 s2gap.py <corpus_dir>

兩類缺口(distinct token ≈ 一個可下單品項):
  A|長 SKU(規則明確,確定值):9-14 字元英數混合含數字與字母、非尺寸、
    同 doc 重複 ≥2——現行 CODE_RE {3,8} 永遠不收(Ariostea P612562S8 型)。
  B|全字母 SKU(啟發式,估計值):4-6 字元全大寫、同 doc 重複 ≥2、非 dev 泛用詞
    (alpha_vocab)、且與已偵測代碼同頁共現(Viva EGUC / Level ELMS 型)。
    B 含色名/系列名噪音,只當上界訊號。

另印:無色樣代碼表頁訊號 = spec 頁中「偵測代碼實例 ≥5 且色樣 ≤2」的頁(heldout4
硬條件 2 的存在性驗證;結構統計,不看頁面、不涉綁定正確性)。
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

from census import SIZE_RE
from m1_scan import norm
from m2_scan import build_vocabs, code_candidates
from spike_geom import extract_swatches

LONG_RE = re.compile(r"^[A-Za-z0-9]{9,14}$")
ALPHA_RE = re.compile(r"^[A-Z]{4,6}$")


def main(corpus):
    code_vocab, alpha_vocab = build_vocabs()
    tot_d = tot_a = tot_b = 0
    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        doc = fitz.open(pdf)
        spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
        detected = code_candidates(doc, code_vocab, len(spec))
        longc, alpha = Counter(), Counter()
        alpha_pg, det_pg = defaultdict(set), set()
        codetable = []
        for p in doc:
            toks = [norm(w[4]) for w in p.get_text("words")]
            n_det = sum(1 for t in toks if t in detected)
            if n_det >= 3:
                det_pg.add(p.number)
            if p in spec and n_det >= 5 and len(extract_swatches(p)) <= 2:
                codetable.append(p.number + 1)
            for t in toks:
                if (LONG_RE.match(t) and any(c.isdigit() for c in t)
                        and any(c.isalpha() for c in t) and not SIZE_RE.search(t)):
                    longc[t] += 1
                elif ALPHA_RE.match(t) and t not in alpha_vocab:
                    alpha[t] += 1
                    alpha_pg[t].add(p.number)
        A = {t for t, n in longc.items() if n >= 2}
        B = {t for t, n in alpha.items() if n >= 2 and alpha_pg[t] & det_pg}
        d = len(detected)
        tot_d, tot_a, tot_b = tot_d + d, tot_a + len(A), tot_b + len(B)
        print(f"{str(pdf.relative_to(corpus)):50s} detected={d:<4d} "
              f"A長SKU漏={len(A):<4d} ex={sorted(A)[:3]} "
              f"B全字母候選={len(B):<3d} ex={sorted(B)[:4]} 代碼表頁={codetable[:8]}")
    print(f"\nTOTAL detected={tot_d}  A(確定漏抓)={tot_a} "
          f"(漏抓率 {tot_a/(tot_d+tot_a):.1%})  B(啟發式上界)={tot_b}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
