#!/usr/bin/env python3
"""工作包#2 步4/5:kept 差集帳(v12 vs v10)——逐檔列新收/消失 token。
用法:python3 kept_diff.py <corpus_dir>(CWD=專案根)"""
import sys
from pathlib import Path

import fitz

sys.path.insert(0, "core")
from census import SIZE_RE                      # noqa: E402
from m2_scan import build_vocabs, code_candidates  # noqa: E402

corpus = sys.argv[1]
code_vocab, alpha_vocab = build_vocabs()
tot_add = tot_del = 0
for pdf in sorted(Path(corpus).rglob("*.pdf")):
    if pdf.name.startswith("._"):
        continue
    doc = fitz.open(pdf)
    n_spec = sum(len(SIZE_RE.findall(p.get_text())) >= 3 for p in doc)
    k10, r10 = code_candidates(doc, code_vocab, n_spec, 10, alpha_vocab)
    k12, r12 = code_candidates(doc, code_vocab, n_spec, 12, alpha_vocab)
    add, gone = sorted(k12 - k10), sorted(k10 - k12)
    rb = sorted(r12["band"] - r10["band"])
    if add or gone or rb:
        print(f"== {pdf.relative_to(corpus)}  +{len(add)} -{len(gone)}"
              + (f" band+{len(rb)}" if rb else ""))
        if add:
            print("  ADD:", " ".join(add))
        if gone:
            print("  GONE:", " ".join(gone))
        if rb:
            print("  BAND:", " ".join(rb))
    tot_add += len(add)
    tot_del += len(gone)
print(f"[{corpus}] total ADD={tot_add} GONE={tot_del}")
