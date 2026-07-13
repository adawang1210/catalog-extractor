#!/usr/bin/env python3
"""E-1 v3.1 證據頁產生器(機械疊框、無人為篩選;送審用,只讀不改規則)。

    /opt/homebrew/bin/python3 e1_evidence.py <corpus_dir> <pdf_stem>

對每個 S1 觸發(照片級色樣上的 ok_x 綁定)渲染判定結果:
紅框=photo_sus 降級(碼詞)、綠框=有效證據存活(標 S2a唯一/S2b);
藍框=涉事照片級色樣。輸出 viewer/e1_<stem簡>/。
"""
import html
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "core"))

import fitz  # noqa: E402

from census import SIZE_RE  # noqa: E402
from m1_scan import norm  # noqa: E402
from m2_scan import build_vocabs, code_candidates  # noqa: E402
from m3_scan import V9_G, fold_x, page_sizes  # noqa: E402
from spike_geom import assign_words, extract_swatches  # noqa: E402

DPI = 130


def main(corpus, stem):
    code_vocab, alpha_vocab = build_vocabs()
    pdf = next(p for p in (ROOT / corpus).rglob("*.pdf") if p.stem == stem)
    doc = fitz.open(pdf)
    spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
    kept, _ = code_candidates(doc, code_vocab, len(spec), 8, alpha_vocab)
    out = ROOT / "viewer" / ("e1_" + stem.replace(" ", "_")[:24])
    out.mkdir(parents=True, exist_ok=True)
    body = [f"<meta charset='utf-8'><body style='font-family:sans-serif'>"
            f"<h1>{html.escape(stem)} — E-1 v3.1 判定證據頁</h1>"
            f"<p>紅框=photo_sus 降級、綠框=有效證據存活(S2a唯一/S2b)、"
            f"藍框=照片級色樣(≥{V9_G:.0%} 頁面積)。機械疊框無篩選。</p>"]
    n_demo = n_keep = 0
    for page in spec:
        sws = extract_swatches(page, version=3)
        pa = abs(page.rect)
        fold = fold_x(page)
        words = page.get_text("words")
        sizes = page_sizes(words, 8)
        band, sw_codes = defaultdict(set), defaultdict(set)
        rows = []
        for w, i, d in assign_words(page, sws, 8):
            t = norm(w[4])
            if t not in kept:
                continue
            cx = (w[0] + w[2]) / 2
            if (i is not None and 0 <= d <= max(1.5 * sws[i].height, 40)
                    and not (fold and (cx < fold) != ((sws[i].x0 + sws[i].x1) / 2 < fold))):
                band[i].add(t)
            if i is not None and sws[i].x0 - 2 <= cx <= sws[i].x1 + 2:
                sw_codes[i].add(t)
                rows.append((w, i, t))
        hits = [(w, i, t) for w, i, t in rows if abs(sws[i]) >= V9_G * pa]
        if not hits:
            continue
        sh = page.new_shape()
        stat = []
        for w, i, t in hits:
            h = max(w[3] - w[1], 1)
            cyw = (w[1] + w[3]) / 2
            side = (w[0] + w[2]) / 2 < fold if fold else None
            s2a = len(sw_codes[i]) == 1 and any(
                (None if fold is None else ((x0 + x1) / 2 < fold)) == side
                and abs(cy - cyw) <= 1.5 * h for cy, x0, x1, _ in sizes)
            s2b = band[i] == {t}
            keep = s2a or s2b
            n_keep += keep
            n_demo += not keep
            sh.draw_rect(fitz.Rect(sws[i]))
            sh.finish(color=(0, 0, 1), width=1.0)
            col = (0, 0.55, 0) if keep else (0.85, 0, 0)
            sh.draw_rect(fitz.Rect(w[:4]))
            sh.finish(color=col, width=1.4)
            tag = ("S2a唯一" if s2a else "S2b") if keep else "降級"
            sh.insert_text(fitz.Point(w[0], w[1] - 2), f"{t}:{tag}", color=col, fontsize=6)
            stat.append((t, tag))
        sh.commit()
        fn = f"p{page.number + 1:03d}.png"
        page.get_pixmap(dpi=DPI).save(out / fn)
        body.append(f"<h2>p{page.number + 1}({len(hits)} 筆:"
                    f"{html.escape(', '.join(f'{t}={g}' for t, g in stat))})</h2>"
                    f"<img src='{fn}' style='max-width:100%'>")
    body.insert(1, f"<p><b>合計:降級 {n_demo}、存活 {n_keep}。</b></p>")
    (out / "index.html").write_text("\n".join(body))
    print(f"{stem}: 降級 {n_demo} 存活 {n_keep} → {out}/index.html")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
