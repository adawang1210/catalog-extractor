#!/usr/bin/env python3
"""S2-5 偽碼旗標分離量測探針(通案三:入庫;設計案 output/s25_design.md 數字來源)。

    python3 dev/s25_probe.py <corpus_dir> [occ下限]   (CWD=專案根)

對每檔每個 kept 碼量四軸(全 per-doc 統計、零詞表):
  occ=全 doc 實例數;spread=出現頁數/全 doc 頁數;fn=norm token ∈ 檔名(去非
  字數字後);hdr=實例落頁首尾 10% 高度帶之比例。
已知偽碼病例:MILANO70/41ZERO42(catalogs6 檔名系列/品牌名)、OPUS(Provenza
occ=5 與真碼 MLNL 同值)、OCT(Topcer 形狀詞)。輸出=occ ≥ 下限或 spread ≥0.3
或 fn 命中者+標的病例,人判材料。純量測,不改規則。"""
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, "core")
from census import SIZE_RE                                    # noqa: E402
from m1_scan import norm                                      # noqa: E402
from m2_scan import build_vocabs, code_candidates             # noqa: E402

TARGETS = {"MILANO70", "41ZERO42", "OPUS", "OCT", "MLNL", "MLNM"}  # 病例+真碼對照
corpus, occ_min = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 6
mode = sys.argv[3] if len(sys.argv) > 3 else "axes"
code_vocab, alpha_vocab = build_vocabs()
for pdf in sorted(Path(corpus).rglob("*.pdf")):
    if pdf.name.startswith("._"):
        continue
    doc = fitz.open(pdf)
    n_spec = sum(len(SIZE_RE.findall(p.get_text())) >= 3 for p in doc)
    kept, _r = code_candidates(doc, code_vocab, n_spec, 12, alpha_vocab)
    fn = re.sub(r"[^A-Z0-9]", "", pdf.stem.upper())
    occ, pages, hdr = {}, {}, {}
    for page in doc:
        ph = page.rect.height
        for w in page.get_text("words"):
            t = norm(w[4])
            if t not in kept:
                continue
            occ[t] = occ.get(t, 0) + 1
            pages.setdefault(t, set()).add(page.number)
            yc = (w[1] + w[3]) / 2
            hdr[t] = hdr.get(t, 0) + (yc < 0.1 * ph or yc > 0.9 * ph)
    if mode == "flags":
        # 入場邊界軸:重演 alpha_codes ⑤⑦統計(eff/DOM/thr)
        from m1_scan import CODE_RE
        from m2_scan import (V8_DOM, V8_OCC, V8_OCC_CAP, V8_OCC_PG, V8_ROW_H,
                             V8_X_TOL, route_junk)
        c = {}
        for page in doc:
            for w in page.get_text("words"):
                t = norm(w[4])
                if (CODE_RE.match(t) and any(ch.isdigit() for ch in t)
                        and any(ch.isalpha() for ch in t) and not SIZE_RE.search(t)):
                    c[t] = c.get(t, 0) + 1
        anchors, _ = route_junk(set(c) - code_vocab)
        eff, aocc = set(), {}
        for page in doc:
            pw = page.rect.width
            fold = pw / 2 if pw > 1.2 * page.rect.height else None
            words = page.get_text("words")
            sz = [(((w[0] + w[2]) / 2 < fold) if fold else None, (w[1] + w[3]) / 2)
                  for w in words if SIZE_RE.search(w[4])]
            for w in words:
                t = norm(w[4])
                if t.isalpha() and CODE_RE.match(t) and t not in alpha_vocab:
                    aocc[t] = aocc.get(t, 0) + 1
                if t in anchors:
                    side = ((w[0] + w[2]) / 2 < fold) if fold else None
                    cy, h = (w[1] + w[3]) / 2, max(w[3] - w[1], 1)
                    if any(s == side and abs(y - cy) <= V8_ROW_H * h for s, y in sz):
                        eff.add(t)
        dom = (max(__import__("collections").Counter(len(a) for a in eff).values())
               / len(eff)) if eff else None
        med = sorted(c.get(a, 0) for a in eff)[len(eff) // 2] if eff else 0
        thr = max(V8_OCC * med, min(V8_OCC_PG * doc.page_count, V8_OCC_CAP))
        out = []
        for t in sorted(kept):
            pf = t in fn
            alpha = t.isalpha()
            pcap = alpha and aocc.get(t, occ.get(t, 0)) >= V8_OCC_CAP
            pdom = alpha and dom is not None and dom < 0.7
            if pf or pcap or pdom or t in TARGETS:
                out.append(f"  {t:<10} fn={'Y' if pf else 'n'} cap={'Y' if pcap else 'n'}"
                           f"(occ={aocc.get(t, occ.get(t, 0))},thr={thr:.1f})"
                           f" domY={'Y' if pdom else 'n'}(DOM={dom if dom is None else round(dom, 2)})"
                           + (" ★病例" if t in ("MILANO70", "41ZERO42", "OPUS", "OCT")
                              else (" ○真碼對照" if t in ("MLNL", "MLNM") else "")))
        if out:
            print(f"== {pdf.relative_to(corpus)}  kept={len(kept)} 旗標/標的:")
            print("\n".join(out))
        continue
    rows = []
    for t, n in occ.items():
        sp = len(pages[t]) / max(doc.page_count, 1)
        f = t in fn
        h = hdr[t] / n
        if n >= occ_min or sp >= 0.3 or f or t in TARGETS:
            rows.append((sp, n, f, h, t))
    if rows:
        print(f"== {pdf.relative_to(corpus)}  pages={doc.page_count} spec={n_spec} kept={len(kept)}")
        for sp, n, f, h, t in sorted(rows, reverse=True)[:14]:
            tag = " ★病例" if t in ("MILANO70", "41ZERO42", "OPUS", "OCT") else (
                  " ○真碼對照" if t in ("MLNL", "MLNM") else "")
            print(f"  {t:<10} occ={n:<3} spread={sp:.2f} fn={'Y' if f else 'n'} hdr={h:.2f}{tag}")
