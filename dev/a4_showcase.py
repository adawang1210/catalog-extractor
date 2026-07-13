#!/usr/bin/env python3
"""A4|全語料隨機抽樣 demo 批跑存檔(純展示、只讀存檔、零回饋規則;通案三入庫)。

每語料(catalogs, catalogs2..7)固定 seed 抽 2 檔 → 跑現行產線(V=12)→
存 SCHEMA JSON + 裁圖 + 每頁 disposition + viewer HTML 到 DEMO 目錄。
輸出到 repo 外的 USB(demo_showcase),不進 git。catalogs2~7 含已燒考卷/夾具:
展示可跑但★絕不回饋改任何規則/凍結常數(鐵律5/6)。

    /opt/homebrew/bin/python3 dev/a4_showcase.py [DEMO_DIR] [--list]

--list 只印抽樣清單(檔名+md5,可重現核對),不跑產線。
"""
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core"))
import pipeline  # noqa: E402
import viewer    # noqa: E402

SEED = 20260713
CORPORA = ["catalogs"] + [f"catalogs{i}" for i in range(2, 8)]


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def sample():
    random.seed(SEED)
    picks = []
    for c in CORPORA:
        pdfs = sorted(p for p in (ROOT / c).rglob("*.pdf") if not p.name.startswith("._"))
        for p in sorted(random.sample(pdfs, min(2, len(pdfs)))):
            picks.append((c, p))
    return picks


def main(argv):
    demo = Path(argv[0]) if argv and not argv[0].startswith("--") \
        else Path("/Volumes/USB DISK/demo_showcase")
    picks = sample()
    print(f"[A4] seed={SEED}  抽中 {len(picks)} 檔:")
    for c, p in picks:
        print(f"  {c:11s} | {p.parent.name:14s} | {p.name}  md5={md5(p)}")
    if "--list" in argv:
        return 0

    (demo / "product").mkdir(parents=True, exist_ok=True)
    vocabs = pipeline.build_vocabs()
    for c, pdf in picks:
        pipeline.write_out(pdf, str(demo / "product"), vocabs)

    # viewer:ROOT=DEMO(product/viewer 輸出根);find_pdf 仍指主樹語料
    viewer.ROOT = demo
    viewer.OUT = demo / "viewer"
    viewer.OUT.mkdir(parents=True, exist_ok=True)
    viewer.find_pdf = lambda name: next(
        (p for cd in sorted(ROOT.glob("catalogs*")) for p in cd.rglob("*.pdf")
         if p.name == name and not p.name.startswith("._")), None)

    recs, report = [], []
    for c, pdf in picks:
        brand = pdf.parent.name
        jp = demo / "product" / brand / f"{pdf.stem}.json"
        rec = viewer.collect(jp, jp.with_name(jp.stem + ".review.json"), brand)
        viewer.build_doc(rec)
        recs.append(rec)
        report.append({"corpus": c, "brand": brand, "file": pdf.name, "md5": md5(pdf),
                       "pages": rec["totalPages"], "variants": len(rec["variants"]),
                       "queue": len(rec["queue"]), "skeleton": len(rec["skeleton"]),
                       "coverage": rec["coverage"]})
    viewer.build_index(recs)
    (demo / "A4_showcase_manifest.json").write_text(
        json.dumps({"seed": SEED, "picks": report}, ensure_ascii=False, indent=2))

    print("\n[A4] 每檔四態統計(coverage=每頁處置):")
    for r in report:
        cv = r["coverage"]
        assert sum(cv.values()) == r["pages"], f"覆蓋不守恆 {r['file']}"
        print(f"  {r['corpus']:11s} {r['file'][:36]:36s} 頁{r['pages']:3d} "
              f"auto{cv['auto']:3d} rev{cv['review']:3d} noprod{cv['noprod']:3d} "
              f"nonspec{cv['nonspec']:3d} img{cv['image']:3d}  綁定{r['variants']}")
    print(f"\n[A4] 存檔:{demo}  (product/ + viewer/ + A4_showcase_manifest.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
