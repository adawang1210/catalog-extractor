#!/usr/bin/env python3
"""M5-2b v13 救回證據頁(機械疊框、無人為篩選;切版親驗用,只讀不改規則)。

    /opt/homebrew/bin/python3 m52b_evidence.py <corpus> <pdf_stem> [--list | <頁號...>]

救回筆=v12(舊全體中位)icon 降級、v13(med_ex 排大圖後中位)存活 的碼。
逐頁重演 doc_icon_stats(spec,12) vs (spec,13);每頁救回數與 scan_page 頁級
code_icon_demoted 差(v12−v13)交叉驗證(assert),確保疊框=真實救回筆。

疊框:紅框=救回碼詞、藍框=其綁定色樣、標救回類型(x對齊/塊綁)+色樣佔頁面積%。
判讀問句:紅框救回的碼,是否配對到該列真色樣(而非小圖標/雜圖)?
--list 印全 spec 頁救回數(挑代表頁用)。輸出 viewer/m52b_v13/。
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
from m3_scan import doc_icon_stats, doc_name_index, icon_sus, scan_page  # noqa: E402
from spike_geom import assign_words, extract_swatches  # noqa: E402

DPI = 150


def rescued(page, sws, kept, ic_old, ic_new):
    """回傳 [(w, i, kind)]:v12 icon 降級、v13 存活的碼(kind=x對齊|塊綁)。"""
    resc_sw = {i for i, r in enumerate(sws)
               if icon_sus(r, ic_old) and not icon_sus(r, ic_new)}
    out = []
    for w, i, d in assign_words(page, sws, 12):
        if i is None or i not in resc_sw or norm(w[4]) not in kept:
            continue
        cx = (w[0] + w[2]) / 2
        if sws[i].x0 - 2 <= cx <= sws[i].x1 + 2:
            out.append((w, i, "x對齊"))
        elif d == -2.0:                       # M5-3 塊綁哨兵
            out.append((w, i, "塊綁"))
    return out


def main(corpus, stem, pages):
    cv, av = build_vocabs()
    pdf = next(p for p in (ROOT / corpus).rglob("*.pdf")
               if p.stem == stem and not p.name.startswith("._"))
    doc = fitz.open(pdf)
    spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
    cd, _ = code_candidates(doc, cv, len(spec), 12, av)
    nc = doc_name_index(spec, cd, av, 12)
    ic_old, ic_new = doc_icon_stats(spec, 12), doc_icon_stats(spec, 13)

    if pages == ["--list"]:
        print(f"# {stem}: 逐 spec 頁救回數(med={ic_old[1]:.0f} → med_ex={ic_new[1]:.0f})")
        for p in spec:
            sws = extract_swatches(p, version=3)
            rc = rescued(p, sws, cd, ic_old, ic_new)
            dm_o = scan_page(p, cd, av, 12, nc, ic_old)["code_icon_demoted"]
            dm_n = scan_page(p, cd, av, 12, nc, ic_new)["code_icon_demoted"]
            assert len(rc) == dm_o - dm_n, (p.number + 1, len(rc), dm_o, dm_n)
            if rc:
                print(f"  p{p.number + 1}: 救回 {len(rc)}(dm {dm_o}→{dm_n})")
        return

    out = ROOT / "viewer" / "m52b_v13"
    out.mkdir(parents=True, exist_ok=True)
    slug = stem.replace(" ", "_")[:24]
    body = ["<meta charset='utf-8'><body style='font-family:sans-serif'>",
            f"<h1>{html.escape(stem)} — M5-2b v13 救回親驗證據頁</h1>",
            "<p><b>紅框=v13 救回的碼詞</b>(v12 被 icon 降級進佇列、v13 存活)、"
            "<b>藍框=其綁定色樣</b>;標救回類型與色樣佔頁面積%。機械疊框無篩選。<br>"
            "<b>判讀問句:紅框救回的碼,是否配對到該列真色樣(磁磚色片),"
            "而非小圖標/雜圖?</b></p>"]
    for pno in pages:
        page = doc[int(pno) - 1]
        sws = extract_swatches(page, version=3)
        pa = abs(page.rect)
        rc = rescued(page, sws, cd, ic_old, ic_new)
        dm_o = scan_page(page, cd, av, 12, nc, ic_old)["code_icon_demoted"]
        dm_n = scan_page(page, cd, av, 12, nc, ic_new)["code_icon_demoted"]
        assert len(rc) == dm_o - dm_n, (pno, len(rc), dm_o, dm_n)
        sh = page.new_shape()
        seen_sw = {}
        for w, i, kind in rc:
            sh.draw_rect(fitz.Rect(w[:4]) + (-1, -1, 1, 1))
            sh.finish(color=(0.85, 0, 0), width=1.4)
            sh.insert_text(fitz.Point(w[0], w[1] - 2),
                           f"{norm(w[4])}:{kind}", color=(0.85, 0, 0), fontsize=6)
            seen_sw[i] = sws[i]
        for i, r in seen_sw.items():
            sh.draw_rect(fitz.Rect(r))
            sh.finish(color=(0, 0, 1), width=1.2)
            sh.insert_text(fitz.Point(r.x0, r.y1 + 7),
                           f"色樣 {abs(r) / pa * 100:.1f}%頁", color=(0, 0, 1), fontsize=6)
        sh.commit()
        png = f"{slug}_p{pno}.png"
        page.get_pixmap(dpi=DPI).save(out / png)
        body.append(f"<h2>p{pno} — 救回 {len(rc)} 碼(dm {dm_o}→{dm_n}),"
                    f"涉 {len(seen_sw)} 色樣</h2>"
                    f"<img src='{png}' style='max-width:100%;border:1px solid #999'>")
        print(f"p{pno}: 救回 {len(rc)} 涉色樣 {len(seen_sw)} -> {png}", flush=True)
    idx = out / f"{slug}.html"
    idx.write_text("\n".join(body), encoding="utf-8")
    print("index:", idx)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
