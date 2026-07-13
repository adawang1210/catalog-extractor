#!/usr/bin/env python3
"""catalogs7 打包驗收跑批器(M5-3 v7+S2-1 v8;外審行動⑦)。

    /opt/homebrew/bin/python3 c7_run.py

- pipeline 本體釘 V=6 不動;本器 monkeypatch pipeline.V=8 鏡射跑 catalogs7
  → product_c7/(JSON+佇列+裁圖)。
- 頁級守恆對帳:pipeline counts vs m3_scan.scan_page(v8) 同名欄逐頁必一致。
- 產出:output/c7_scan_v8.csv(頁級掃描)+ output/c7_run_summary.md(聚合
  指標:首觸自動可用率曲線第二點、反例 4 件塊綁誤觸發、佇列率)。
- 零讀取紀律:只輸出聚合數字與檔名,不落任何頁內容/token;人工 GT=使用者。
- A 板前不執行任何銷毀(外審行動⑦條款)。
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "core"))

import fitz  # noqa: E402

import pipeline  # noqa: E402
from census import SIZE_RE  # noqa: E402
from m2_scan import build_vocabs, code_candidates  # noqa: E402
from m3_scan import doc_icon_stats, doc_name_index, scan_page  # noqa: E402

pipeline.V = 8  # 鏡射版本(v8 ⊇ v7 綁定行為)

COUNTEREX = {  # 反例 4 件(頁型定向;宣告=catalogs7_DECLARATION.md)
    "Tele Di Marmo Revolution TdM Revolution Catalogo 2025.08 Web.pdf": "矩陣",
    "Alter Catalogo 2024.11 Web.pdf": "InDesign",
    "roads-465.pdf": "堆疊",
    "Ego Catalogo 2025.01 Web.pdf": "M5-2b型",
}
PHOTO_LV = 0.10  # 照片級門檻(audit 實測雙峰:正常色樣 <10% 頁面積)


def main():
    vocabs = build_vocabs()
    code_vocab, alpha_vocab = vocabs
    rows, summary = [], []
    mismatch = 0
    for pdf in sorted(Path("catalogs7").rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        jd, review, page_counts, _ = pipeline.write_out(pdf, "product_c7", vocabs)
        doc = fitz.open(pdf)
        spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
        codes_doc, _ = code_candidates(doc, code_vocab, len(spec), 8, alpha_vocab)
        name_ctx = doc_name_index(spec, codes_doc, alpha_vocab, 8)
        icon_ctx = doc_icon_stats(spec)
        pc = {c["page"]: c for c in page_counts}
        agg = dict(n_codes=0, aligned=0, blk=0, review=0, demoted=0)
        for page in spec:
            r = scan_page(page, codes_doc, alpha_vocab, 8, name_ctx, icon_ctx)
            rows.append({"vendor": pdf.parts[1], "page": page.number + 1,
                         "doc": pdf.name, **r})
            p = pc.get(page.number + 1, {})
            for k, v in r.items():  # 守恆:同名欄逐頁一致
                if k in p and p[k] != v:
                    mismatch += 1
                    print(f"  ✗ 頁級不一致 {pdf.name} p{page.number + 1} {k}: "
                          f"pipeline={p[k]} scan={v}")
            agg["n_codes"] += r["n_codes"]
            agg["aligned"] += r["code_x_aligned"]
            agg["blk"] += r.get("code_block_bound", 0)
            agg["review"] += r["code_needs_review"]
            agg["demoted"] += r.get("code_icon_demoted", 0)
        vs = jd["series"][0]["variants"]
        photo = usable = 0
        for v in vs:
            pg = doc[v["swatch"]["page"] - 1]
            x0, y0, x1, y1 = v["swatch"]["bbox"]
            if (x1 - x0) * (y1 - y0) >= PHOTO_LV * abs(pg.rect):
                photo += 1
            else:
                usable += 1
        summary.append(dict(
            doc=pdf.name, vendor=pdf.parts[1],
            kind=COUNTEREX.get(pdf.name, "主批"),
            pages=doc.page_count, spec=len(spec), **agg,
            variants=len(vs), usable_img=usable, photo_lv=photo,
            queue_items=len(review)))
        print(pdf.parts[1], pdf.name[:44], "done", flush=True)

    with open("output/c7_scan_v8.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    main_b = [s for s in summary if s["kind"] == "主批"]
    ctr = [s for s in summary if s["kind"] != "主批"]
    tc = sum(s["n_codes"] for s in main_b)
    ta = sum(s["aligned"] for s in main_b)
    tb = sum(s["blk"] for s in main_b)
    lines = ["# catalogs7 打包跑批摘要(v7+v8;A 板前不銷毀;GT=人工)", "",
             "## 主批 10(首觸自動可用率曲線第二點;第一點=I 批 18.4% 對齊)", "",
             "| 檔 | 頁 | spec | 碼 | x對齊 | 塊綁 | 佇列 | Variant | 可用圖 | 照片級 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for s in main_b:
        lines.append(f"| {s['doc'][:34]} | {s['pages']} | {s['spec']} | {s['n_codes']} "
                     f"| {s['aligned']} | {s['blk']} | {s['review']} | {s['variants']} "
                     f"| {s['usable_img']} | {s['photo_lv']} |")
    lines += ["",
              f"主批合計:碼 {tc}、x對齊 {ta}({ta / max(tc, 1):.1%})、塊綁 {tb}"
              f"({tb / max(tc, 1):.1%})、**自動綁定率 {(ta + tb) / max(tc, 1):.1%}**、"
              f"佇列 {sum(s['review'] for s in main_b)}"
              f"({sum(s['review'] for s in main_b) / max(tc, 1):.1%})、"
              f"Variant {sum(s['variants'] for s in main_b)}、"
              f"可用圖 {sum(s['usable_img'] for s in main_b)}、"
              f"照片級 {sum(s['photo_lv'] for s in main_b)}",
              "", "## 反例 4(塊綁誤觸發須=0)", "",
              "| 檔 | 頁型 | 碼 | 塊綁 | x對齊 | 佇列 |", "|---|---|---|---|---|---|"]
    for s in ctr:
        lines.append(f"| {s['doc'][:34]} | {s['kind']} | {s['n_codes']} | **{s['blk']}** "
                     f"| {s['aligned']} | {s['review']} |")
    lines += ["", f"頁級守恆不一致={mismatch}(須=0)", ""]
    Path("output/c7_run_summary.md").write_text("\n".join(lines))
    print("\n".join(lines[-14:]))
    print("c7_run done → output/c7_scan_v8.csv + c7_run_summary.md + product_c7/")


if __name__ == "__main__":
    main()
