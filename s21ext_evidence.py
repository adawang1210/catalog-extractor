#!/usr/bin/env python3
"""S2-1 延伸③ v12 證據頁產生器(機械疊框、無人為篩選;切版親驗用,只讀不改規則)。

    /opt/homebrew/bin/python3 s21ext_evidence.py <corpus_dir> <pdf_stem> <頁,頁,...>

例:/opt/homebrew/bin/python3 s21ext_evidence.py catalogs7 "PietraEssenza Catalogo 2025.10 Web" 19

紅框=v12 新收碼實例(塊內尺寸繼承)、綠框=v10 既收碼實例、藍底線=尺寸 token。
判讀問題:紅框編號是否真產品編號?有無散文詞混入?輸出 viewer/s21ext_v12/。
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "core"))

import fitz  # noqa: E402

from census import SIZE_RE  # noqa: E402
from m1_scan import norm  # noqa: E402
from m2_scan import build_vocabs, code_candidates  # noqa: E402

DPI = 150


def main(corpus, stem, pages):
    code_vocab, alpha_vocab = build_vocabs()
    pdf = next(p for p in (ROOT / corpus).rglob("*.pdf")
               if p.stem == stem and not p.name.startswith("._"))
    doc = fitz.open(pdf)
    n_spec = sum(len(SIZE_RE.findall(p.get_text())) >= 3 for p in doc)
    k10, _ = code_candidates(doc, code_vocab, n_spec, 10, alpha_vocab)
    k12, _ = code_candidates(doc, code_vocab, n_spec, 12, alpha_vocab)
    new = k12 - k10
    out = ROOT / "viewer" / "s21ext_v12"
    out.mkdir(parents=True, exist_ok=True)
    slug = stem.replace(" ", "_")[:24]
    body = ["<meta charset='utf-8'><body style='font-family:sans-serif'>",
            f"<h1>{html.escape(stem)} — S2-1 延伸③ v12 切版親驗證據頁</h1>",
            "<p><b>紅框=v12 新收碼實例(塊內尺寸繼承)</b>、綠框=v10 既收碼實例、"
            "藍底線=尺寸 token。機械疊框無篩選。判讀:紅框編號是否真產品編號?"
            "有無散文詞混入?</p>",
            f"<p>本檔 v12 新收 {len(new)} 種:{html.escape(' '.join(sorted(new)))}</p>"]
    for pno in pages:
        page = doc[pno - 1]
        n_new = n_old = 0
        for w in page.get_text("words"):
            t, r = norm(w[4]), fitz.Rect(w[:4])
            if t in new:
                page.draw_rect(r + (-1, -1, 1, 1), color=(1, 0, 0), width=1.2)
                n_new += 1
            elif t in k10:
                page.draw_rect(r + (-1, -1, 1, 1), color=(0, 0.6, 0), width=0.8)
                n_old += 1
            elif SIZE_RE.search(w[4]):
                page.draw_line(r.bl, r.br, color=(0, 0, 1), width=0.8)
        png = f"{slug}_p{pno}.png"
        page.get_pixmap(dpi=DPI).save(out / png)
        body.append(f"<h2>p{pno} — 紅框(新收)實例 {n_new}、綠框(既收)實例 "
                    f"{n_old}</h2><img src='{png}' style='max-width:100%;"
                    f"border:1px solid #999'>")
        print(f"p{pno}: new_inst={n_new} old_inst={n_old} -> {png}", flush=True)
    idx = out / f"{slug}.html"
    idx.write_text("\n".join(body), encoding="utf-8")
    print("index:", idx)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")])
