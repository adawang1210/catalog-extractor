#!/usr/bin/env python3
"""繼承路徑探針:對單一 PDF 重演 alpha_codes v12 邏輯,逐筆列出
(a) 繼承成功者:所需最大 gap/中位 比值、來源尺寸列距離
(b) 繼承失敗的 pend:斷點 gap/中位 比值
用法:python3 probe_inherit.py <pdf> (CWD=專案根)"""
import sys
from collections import Counter
from pathlib import Path

import fitz

sys.path.insert(0, "core")
from census import SIZE_RE                                   # noqa: E402
from m1_scan import CODE_RE, norm                            # noqa: E402
from m2_scan import (S21_RUN_GAP, V8_ROW_H, V8_X_TOL,        # noqa: E402
                     build_vocabs, code_candidates, route_junk)

pdf = Path(sys.argv[1])
code_vocab, alpha_vocab = build_vocabs()
doc = fitz.open(pdf)
n_spec = sum(len(SIZE_RE.findall(p.get_text())) >= 3 for p in doc)
k10, _ = code_candidates(doc, code_vocab, n_spec, 10, alpha_vocab)
k12, _ = code_candidates(doc, code_vocab, n_spec, 12, alpha_vocab)
new = k12 - k10

# anchors 快照=digits 併入前 alnum kept(鏡射 code_candidates v>=8)
c = Counter()
for page in doc:
    for w in page.get_text("words"):
        t = norm(w[4])
        if (CODE_RE.match(t) and any(ch.isdigit() for ch in t)
                and any(ch.isalpha() for ch in t) and not SIZE_RE.search(t)):
            c[t] += 1
anchors, _r = route_junk({t for t in c if t not in code_vocab})

hits, misses = {}, {}
for pno, page in enumerate(doc, 1):
    pw = page.rect.width
    fold = pw / 2 if pw > 1.2 * page.rect.height else None
    words = page.get_text("words")
    ax = [w[0] for w in words if norm(w[4]) in anchors]
    sz = [(((w[0] + w[2]) / 2 < fold) if fold else None, (w[1] + w[3]) / 2)
          for w in words if SIZE_RE.search(w[4])]

    def rowsz(w):
        side = ((w[0] + w[2]) / 2 < fold) if fold else None
        cy, h = (w[1] + w[3]) / 2, max(w[3] - w[1], 1)
        return any(s == side and abs(y - cy) <= V8_ROW_H * h for s, y in sz)

    mem, pend = [], []
    for w in words:
        t = norm(w[4])
        is_alpha = t.isalpha() and CODE_RE.match(t) and t not in alpha_vocab
        if t in anchors or (is_alpha and not w[4].islower()):
            mem.append((w[0], (w[1] + w[3]) / 2, rowsz(w), t))
        if not (is_alpha and not w[4].islower()):
            continue
        if not any(abs(a - w[0]) <= V8_X_TOL * pw for a in ax):
            continue
        if not rowsz(w):
            pend.append((t, w[0], (w[1] + w[3]) / 2))
    for t, x0, yc in pend:
        col = sorted((m[1], m[2], m[3]) for m in mem if abs(m[0] - x0) <= V8_X_TOL * pw)
        gaps = [b[0] - a[0] for a, b in zip(col, col[1:]) if b[0] > a[0]]
        if not gaps:
            continue
        med = sorted(gaps)[len(gaps) // 2]
        lim = S21_RUN_GAP * med
        prev, ratio_max, got, brk = yc, 0.0, None, None
        for my, mrs, mt in sorted((cc for cc in col if cc[0] < yc - 1e-6), reverse=True):
            g = prev - my
            if g > lim:
                brk = g / med
                break
            ratio_max = max(ratio_max, g / med)
            if mrs:
                got = (mt, ratio_max)
                break
            prev = my
        if got:
            cur = hits.get(t)
            if cur is None or got[1] < cur[2]:
                hits[t] = (pno, got[0], got[1], med)
        elif t not in hits:
            m0 = misses.get(t)
            r = brk if brk is not None else float("inf")
            if m0 is None or r < m0[1]:
                misses[t] = (pno, r, med)

print(f"== {pdf.name}  new={len(new)}")
print("-- 繼承成功(token, 頁, 尺寸源, 所需最大 gap/中位, 欄中位距):")
for t in sorted(new):
    h = hits.get(t)
    print(f"  {t}: p{h[0]} via {h[1]} ratio={h[2]:.2f} med={h[3]:.1f}" if h
          else f"  {t}: ―(不在探針 hits?)")
print("-- pend 失敗(過①②、③與繼承皆未過;斷點比值=至尺寸列所需):")
for t, (pno, r, med) in sorted(misses.items()):
    if t not in k12:
        print(f"  {t}: p{pno} break_ratio={r:.2f} med={med:.1f}")
