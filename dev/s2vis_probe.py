#!/usr/bin/env python3
"""S2-1 延伸②-vis 分離量測探針(通案三:入庫;設計案 output/s2vis_design.md 數字來源)。

    python3 dev/s2vis_probe.py <corpus_dir> [COL_N] [rowsz|blocksz]   (CWD=專案根)

機制重演:①形全字母 token(CODE_RE∧非停用詞∧原文非全小寫)之 x0 欄
(容差 V8_X_TOL×頁寬)成員數 ≥COL_N 且欄帶內零數字錨實例 → 旗標。
變體:rowsz=另要求 token 同列(折縫同側、V8_ROW_H)有尺寸(③閘重用;
已否決存查——漏 PS 塊頭型)。blocksz=rowsz' 欄級移植(2026-07-12 裁決①
放行量測):rowsz(w)∨沿欄連續塊上溯(欄成員=①形字母∪欄內尺寸 token,
相鄰列距 ≤S21_RUN_GAP×該欄列距中位)遇尺寸 token 或有尺寸列成員=繼承。
環境變數 S2VIS_DETAIL=頁號逗號清單 → 該頁逐 token 列帳(值+擋下條件)。
純量測,不改規則。"""
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

sys.path.insert(0, "core")
from census import SIZE_RE                                    # noqa: E402
from m1_scan import CODE_RE, norm                             # noqa: E402
from m2_scan import (S21_RUN_GAP, V8_ROW_H, V8_X_TOL,        # noqa: E402
                     build_vocabs, code_candidates, route_junk)

corpus, col_n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2
mode = sys.argv[3] if len(sys.argv) > 3 else "base"
detail = {int(x) for x in os.environ.get("S2VIS_DETAIL", "").split(",") if x}
code_vocab, alpha_vocab = build_vocabs()
tot = Counter()
for pdf in sorted(Path(corpus).rglob("*.pdf")):
    if pdf.name.startswith("._"):
        continue
    doc = fitz.open(pdf)
    spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
    n_spec = len(spec)
    kept, _r = code_candidates(doc, code_vocab, n_spec, 12, alpha_vocab)
    # 錨快照=digits 併入前 alnum kept(沿 alpha_codes 慣例)
    c = set()
    for page in doc:
        for w in page.get_text("words"):
            t = norm(w[4])
            if (CODE_RE.match(t) and any(ch.isdigit() for ch in t)
                    and any(ch.isalpha() for ch in t) and not SIZE_RE.search(t)):
                c.add(t)
    anchors, _ = route_junk(c - code_vocab)
    hits = defaultdict(set)
    for page in spec:                       # 佇列=spec 頁(與掃描/佇列同範圍)
        pno = page.number + 1
        pw = page.rect.width
        tol = V8_X_TOL * pw
        fold = pw / 2 if pw > 1.2 * page.rect.height else None
        words = page.get_text("words")
        ax = [w[0] for w in words if norm(w[4]) in anchors]
        sz = [(((w[0] + w[2]) / 2 < fold) if fold else None, (w[1] + w[3]) / 2)
              for w in words if SIZE_RE.search(w[4])]
        szx = [(w[0], (w[1] + w[3]) / 2) for w in words if SIZE_RE.search(w[4])]

        def rowsz(w):
            side = ((w[0] + w[2]) / 2 < fold) if fold else None
            cy, h = (w[1] + w[3]) / 2, max(w[3] - w[1], 1)
            return any(s == side and abs(y - cy) <= V8_ROW_H * h for s, y in sz)

        alp = [(w[0], norm(w[4]), rowsz(w), (w[1] + w[3]) / 2) for w in words
               if (t := norm(w[4])) and t.isalpha() and CODE_RE.match(t)
               and t not in alpha_vocab and not w[4].islower()]

        def blk(x0, yc):
            """rowsz' 欄級:沿欄上溯,回 (裁定, 說明)。欄成員=①形字母∪尺寸 token。"""
            m = sorted({(y, rs) for x2, _t, rs, y in alp if abs(x2 - x0) <= tol}
                       | {(y, "SZ") for x2, y in szx if abs(x2 - x0) <= tol})
            gaps = [b[0] - a[0] for a, b in zip(m, m[1:]) if b[0] > a[0]]
            if not gaps:
                return False, "no-block(欄無列距)"
            med = sorted(gaps)[len(gaps) // 2]
            lim = S21_RUN_GAP * med
            prev = yc
            for my, kind in sorted((e for e in m if e[0] < yc - 1e-6), reverse=True):
                if prev - my > lim:
                    return False, f"break@{(prev - my) / med:.2f}(med={med:.1f})"
                if kind == "SZ" or kind is True:
                    return True, (f"塊內尺寸行@{(prev - my) / med:.2f}" if kind == "SZ"
                                  else f"塊內有尺寸列成員@{(prev - my) / med:.2f}")
                prev = my
            return False, "塊頂無尺寸(上溯盡)"

        for x0, t, rs, yc in alp:
            why = None
            if t in kept:
                why = "∈kept(v12 已收)"
            elif any(abs(a - x0) <= tol for a in ax):
                why = "欄內有錨(②正常路徑)"
            elif sum(1 for x2, _t2, _r2, _y in alp if abs(x2 - x0) <= tol) < col_n:
                why = f"欄成員<{col_n}"
            elif mode == "rowsz" and not rs:
                why = "無同列尺寸(rowsz 變體)"
            elif mode == "blocksz":
                if rs:
                    hits[pno].add(t)
                    why = "★旗標:同列尺寸直中"
                else:
                    ok, ex = blk(x0, yc)
                    if ok:
                        hits[pno].add(t)
                    why = ("★旗標:" if ok else "擋:") + ex
            else:
                hits[pno].add(t)
                why = "★旗標(base)"
            if pno in detail and why and "∈kept" not in why:
                print(f"  [p{pno}] {t:<12} x0={x0:6.1f} rowsz={str(rs):<5} {why}")
    if hits and not detail:
        n = sum(len(v) for v in hits.values())
        tot[pdf.relative_to(corpus).parts[0]] += n
        print(f"== {pdf.relative_to(corpus)}  flagged={n}")
        for pno in sorted(hits):
            print(f"  p{pno}: {' '.join(sorted(hits[pno]))}")
    elif hits:
        tot[pdf.relative_to(corpus).parts[0]] += sum(len(v) for v in hits.values())
print(f"[{corpus} COL_N={col_n} mode={mode}] per-vendor:", dict(tot),
      " TOTAL=", sum(tot.values()))
