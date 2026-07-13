#!/usr/bin/env python3
"""c7 GT 證據頁產生器(機械疊框,無人為篩選;判讀表=output/c7_gt/GT_PROTOCOL.md)。

    /opt/homebrew/bin/python3 c7_evidence.py <product_c7 內 json 路徑> [method 過濾]

例:/opt/homebrew/bin/python3 c7_evidence.py product_c7/FMG/roads-465.json geom_v7_block

每個含目標綁定的頁 → viewer/c7_gt/<stem>/pXX.png(藍框=色樣、綠框=碼詞、
標碼字)+ index.html(頁清單+判讀問題)。PDF 原檔不動(疊框在記憶體頁上,
只輸出 PNG)。
"""
import html
import json
import sys
from collections import defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).parent
DPI = 150


def main(json_path, method=None):
    jd = json.loads(Path(json_path).read_text())
    stem = Path(json_path).stem
    pdf = next(p for p in (ROOT / "catalogs7").rglob("*.pdf") if p.stem == stem)
    out = ROOT / "viewer" / "c7_gt" / stem.replace(" ", "_")
    out.mkdir(parents=True, exist_ok=True)
    by_page = defaultdict(list)
    for v in jd["series"][0]["variants"]:
        for m in v.get("mergedFrom", []):
            if method and m["prov"]["method"] != method:
                continue
            by_page[m["prov"]["page"]].append(
                (v["code"], m["prov"]["bbox"], m["swatch"]["bbox"], m["prov"]["method"]))
    doc = fitz.open(pdf)
    rows = []
    for pno in sorted(by_page):
        page = doc[pno - 1]
        sh = page.new_shape()
        for k, (code, cb, sb, meth) in enumerate(by_page[pno]):
            sh.draw_rect(fitz.Rect(sb))                     # 色樣=藍
            sh.finish(color=(0, 0, 1), width=1.2)
            sh.draw_rect(fitz.Rect(cb))                     # 碼詞=綠
            sh.finish(color=(0, 0.55, 0), width=1.2)
            sh.draw_line(fitz.Point(cb[0], (cb[1] + cb[3]) / 2),
                         fitz.Point(sb[2], (sb[1] + sb[3]) / 2))
            sh.finish(color=(0.85, 0, 0), width=0.6)
            sh.insert_text(fitz.Point(cb[0], cb[1] - 2), f"{k}:{code}",
                           color=(0.85, 0, 0), fontsize=6)
        sh.commit()
        fn = f"p{pno:03d}.png"
        page.get_pixmap(dpi=DPI).save(out / fn)
        rows.append((pno, len(by_page[pno]), fn))
    total = sum(n for _, n, _ in rows)
    q = "判讀依 output/c7_gt/GT_PROTOCOL.md(已鎖死);綁定=系統自信輸出,逐筆對原始 PDF。"
    body = [f"<h1>{html.escape(stem)} — GT 證據頁</h1>",
            f"<p><b>{html.escape(q)}</b></p>",
            ("<p><b>本檔零綁定</b>(全佇列或零偵測)——靜默漏抓與佇列項判讀請直接對原始 PDF。</p>"
             if not rows else ""),
            f"<p>綁定筆數合計 {total}(method={html.escape(method or '全部')});"
            f"藍框=色樣、綠框=碼詞、紅線=綁定。</p>"]
    for pno, n, fn in rows:
        body.append(f"<h2 id='p{pno}'>p{pno}({n} 筆)</h2><img src='{fn}' style='max-width:100%'>")
    (out / "index.html").write_text(
        "<meta charset='utf-8'><body style='font-family:sans-serif'>" + "\n".join(body))
    print(f"{stem}: 頁數={len(rows)} 綁定={total} → {out}/index.html")
    for pno, n, _ in rows:
        print(f"  p{pno}: {n}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
