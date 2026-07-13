#!/usr/bin/env python3
"""M1 泛化測試:凍結版幾何綁定器掃全 corpus spec 頁,輸出雙向孤兒率。

    python3 m1_scan.py test      # 測試集(9 家,扣設計集 12 頁)
    python3 m1_scan.py heldout   # held-out(4 家,只跑最後一次)

綁定規則 import 自 spike_geom(凍結,不在此修改);本檔只加量測。
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

from census import SIZE_RE
from spike_geom import extract_swatches

CODE_RE = re.compile(r"^[A-Za-z0-9]{3,8}$")
# 設計集:spike 期間 render/目視過的頁(1-based),不計入泛化分數
DESIGN = {("Marazzi", 3), ("Marazzi", 38), ("Marazzi", 41),
          ("MOSA", 20), ("MOSA", 21), ("MOSA", 26), ("MOSA", 27), ("MOSA", 45), ("MOSA", 46),
          ("Topcer", 5), ("Topcer", 6), ("Topcer", 7)}
# held-out:開跑前宣告,文件級隔離,只在最後跑一次
HELDOUT = {"Ariostea", "Iris", "Sodai", "Viva"}


def norm(t):
    return t.strip("*,;:().").upper()


def code_candidates(doc, vocab):
    """SKU 候選:字母+數字混合短 token,排除跨文件產業詞彙與尺寸。純數字碼(Topcer 型)偵測不到,列為已知限制。"""
    c = Counter()
    for page in doc:
        for w in page.get_text("words"):
            t = norm(w[4])
            if (CODE_RE.match(t) and any(ch.isdigit() for ch in t) and any(ch.isalpha() for ch in t)
                    and not SIZE_RE.search(t)):
                c[t] += 1
    return {t for t in c if t not in vocab}


def build_vocab(pdfs):
    df = Counter()
    for pdf in pdfs:
        doc = fitz.open(pdf)
        toks = set()
        for page in doc:
            for w in page.get_text("words"):
                t = norm(w[4])
                if CODE_RE.match(t) and any(ch.isdigit() for ch in t) and any(ch.isalpha() for ch in t):
                    toks.add(t)
        for t in toks:
            df[t] += 1
    return {t for t, n in df.items() if n >= 4}  # 出現在 ≥4 家 = 產業詞彙非 SKU


def scan_page(page, codes_doc):
    sws = extract_swatches(page)
    n_raster = sum(1 for i in page.get_image_info()
                   if 60 < abs(fitz.Rect(i["bbox"])) < 0.55 * abs(page.rect))
    words = page.get_text("words")
    ph = page.rect.height
    sw_words = {i: [] for i in range(len(sws))}
    code_stats = []  # (assigned_idx or None, gap)
    for w in words:
        cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
        is_code = norm(w[4]) in codes_doc
        row = [(abs((r.x0 + r.x1) / 2 - cx), i) for i, r in enumerate(sws) if r.y0 - 2 <= cy <= r.y1 + 2]
        if row:
            i = min(row)[1]
            sw_words[i].append(w)
            if is_code:
                code_stats.append((i, 0.0))
            continue
        above = [(cy - r.y1, i) for i, r in enumerate(sws)
                 if r.y1 - 2 <= cy and min(w[2], r.x1) - max(w[0], r.x0) > 0.3 * (w[2] - w[0])]
        above = [(d, i) for d, i in above if d < max(1.5 * sws[i].height, 40)]
        if above:
            d, i = min(above)
            sw_words[i].append(w)
            if is_code:
                code_stats.append((i, d))
            continue
        sec = [(cy - r.y0, i) for i, r in enumerate(sws) if r.y0 <= cy]
        if sec:
            d, i = min(sec)
            sw_words[i].append(w)
            if is_code:
                code_stats.append((i, max(0.0, cy - sws[i].y1)))
        elif is_code:
            code_stats.append((None, -1))
    n_codes = len(code_stats)
    orphan = sum(1 for i, _ in code_stats if i is None)
    far = sum(1 for i, d in code_stats
              if i is not None and d > max(2 * sws[i].height, 0.15 * ph))
    sw_no_text = sum(1 for i in sw_words if not sw_words[i])
    sw_no_code = sum(1 for i in sw_words
                     if not any(norm(w[4]) in codes_doc for w in sw_words[i]))
    # 頁型分類
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
                sw_no_text=sw_no_text, sw_no_code=sw_no_code, ptype=ptype, flagged=flagged)


def main(split):
    root = Path("catalogs")
    pdfs = sorted(p for p in root.rglob("*.pdf") if not p.name.startswith("._"))
    vocab = build_vocab(pdfs)
    rows = []
    for pdf in pdfs:
        vendor = pdf.relative_to(root).parts[0]
        in_heldout = vendor in HELDOUT
        if (split == "heldout") != in_heldout:
            continue
        doc = fitz.open(pdf)
        codes_doc = code_candidates(doc, vocab)
        for pno, page in enumerate(doc, 1):
            if len(SIZE_RE.findall(page.get_text())) < 3:  # census 的 spec 訊號門檻
                continue
            if split == "test" and (vendor, pno) in DESIGN:
                continue
            r = scan_page(page, codes_doc)
            rows.append({"vendor": vendor, "page": pno, **r})
        print(f"{vendor}: done", flush=True)
    out = Path(f"output/m1_{split}.csv")
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # 摘要
    tc = sum(r["n_codes"] for r in rows)
    ts = sum(r["n_sw"] for r in rows)
    print(f"\n[{split}] pages={len(rows)}  codes={tc}  swatches={ts}")
    print(f"  code_orphan={sum(r['code_orphan'] for r in rows)} ({sum(r['code_orphan'] for r in rows)/max(tc,1):.1%})"
          f"  code_far={sum(r['code_far'] for r in rows)} ({sum(r['code_far'] for r in rows)/max(tc,1):.1%})")
    print(f"  sw_no_text={sum(r['sw_no_text'] for r in rows)} ({sum(r['sw_no_text'] for r in rows)/max(ts,1):.1%})"
          f"  sw_no_code={sum(r['sw_no_code'] for r in rows)} ({sum(r['sw_no_code'] for r in rows)/max(ts,1):.1%})")
    flag = [r for r in rows if r["flagged"]]
    print(f"  flagged_pages={len(flag)} ({len(flag)/max(len(rows),1):.1%})  by type:",
          dict(Counter(r["ptype"] for r in flag)))
    print("  all pages by type:", dict(Counter(r["ptype"] for r in rows)))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("test", "heldout"):
        sys.exit(__doc__)
    main(sys.argv[1])
