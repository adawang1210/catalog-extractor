#!/usr/bin/env python3
"""案4|裁圖真實性掃描器(純儀器、只讀、不修只曝光;通案三入庫)。

補「場景照非唯一影像」盲區。掃產線裁圖(product/<brand>/<stem>_crops/*.png)四類:

  C1  一圖多用/近似重複(dhash 漢明距):同/近裁圖跨 ≥2 不同 Variant → 場景照或
      同圖被多產品共用候選(ham=0 high、ham≤HAM medium)。
  C2  退化裁圖:低解析(min 邊 < LOWRES)、近均勻(灰階 std < UNIFORM=遮罩/空白)、
      透明層(alpha 有實際透明)→ 裁到縮圖/遮罩/透明/低解析預覽。
  C3  裁到碼文字:swatchCrop 裁框 bbox 顯著涵蓋同頁某碼 token bbox(涵蓋率≥COVER)
      → 裁到文字冒充色樣(失敗方向危險=送人工)。
  C4  同色樣多產品:≥2 不同碼 Variant 共用同頁近同 swatch bbox(IoU≥IOU)→ 一色樣
      被不同裁框產生多產品候選。

技術:PIL+numpy 自算 dhash(零新依賴)。不改任何產線行為、不裁決白名單。

    /opt/homebrew/bin/python3 dev/crop_authenticity_scan.py product=. [--max N] [--sheet OUT.html]
        (CWD=專案根;'product=.' 之 '.'=裁圖 root 前綴,裁圖在 product/<brand>/ 下)
    /opt/homebrew/bin/python3 dev/crop_authenticity_scan.py --selftest

停止線(規格):掃出大量「一圖多用」或「裁到文字冒充色樣」災難級=立即凍結回報。
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent

# 常數(儀器判別;非產線凍結常數,可校準)
# ★校準紅字(鐵律2 寧不旗也不誤旗):HAM 曾試 6=8x8 dhash 對小色樣條太粗,誤判
#   不同深色為近似(實測 Viva Steel/Dark 107x35 ham=5)→收緊為 0=僅完全相同=真一圖多用。
#   UNIFORM 曾試 4.0=誤殺合法純色磁磚(std 2-4 屬正常)→收緊 1.0=僅近全白空裁。
HAM = 0          # C1 一圖多用:只認完全相同 dhash(ham=0);near-dup 對小色樣噪音大不採
LOWRES = 16      # C2 低解析:min(w,h) 像素下界
UNIFORM = 1.0    # C2 近全白空裁:灰階 std 下界(純色磁磚 std 2-5 不誤殺)
COVER = 0.6      # C3 裁框涵蓋 token bbox 面積比
IOU = 0.85       # C4 同 swatch bbox IoU 下界


def dhash(im, size=8):
    """列差分 dhash → 64-bit int(PIL+numpy,零新依賴)。"""
    g = im.convert("L").resize((size + 1, size), Image.LANCZOS)
    a = np.asarray(g, dtype=np.int16)
    diff = (a[:, 1:] > a[:, :-1]).flatten()
    bits = 0
    for b in diff:
        bits = (bits << 1) | int(b)
    return bits


def _ham(a, b):
    return bin(a ^ b).count("1")


def _img_stats(path):
    """(w, h, gray_std, has_alpha, dhash) — 讀不到回 None。"""
    try:
        im = Image.open(path)
        im.load()
    except Exception:
        return None
    w, h = im.size
    alpha = im.mode in ("RGBA", "LA") and np.asarray(im.getchannel("A")).min() < 250
    std = float(np.asarray(im.convert("L")).std())
    return w, h, std, alpha, dhash(im)


def _iou(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    ua = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / ua if ua > 0 else 0.0


def _cover(inner, outer):
    """inner bbox 被 outer 涵蓋的面積比(inner∩outer / inner)。"""
    ix0, iy0, ix1, iy1 = max(inner[0], outer[0]), max(inner[1], outer[1]), \
        min(inner[2], outer[2]), min(inner[3], outer[3])
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    ia = (inner[2] - inner[0]) * (inner[3] - inner[1])
    return (iw * ih) / ia if ia > 0 else 0.0


def _f(cls, rel, vkey, page, note, crop=None):
    return {"cls": cls, "doc": rel, "variant": vkey, "page": page, "note": note, "crop": crop}


def crops_of(rel, doc):
    """回 [(vkey, page, crop_bbox, crop_png, [token_bbox...], [swatch_bbox...])]。"""
    out = []
    for s in doc.get("series", []):
        for v in s.get("variants", []):
            vkey = v.get("code") or (v.get("color") or {}).get("en") or "?"
            sc = v.get("swatchCrop") or {}
            cb = ((sc.get("prov") or {}).get("bbox"))
            pg = ((sc.get("prov") or {}).get("page"))
            toks = [m["prov"]["bbox"] for m in v.get("mergedFrom", [])
                    if m.get("prov", {}).get("bbox") and m["prov"].get("page") == pg]
            sws = [(m["swatch"]["page"], tuple(m["swatch"]["bbox"]))
                   for m in v.get("mergedFrom", []) if m.get("swatch", {}).get("bbox")]
            out.append((vkey, pg, cb, sc.get("png"), toks, sws))
    return out


def scan_doc(rel, doc, brand_dir, hashes):
    """單檔 C2/C3/C4 + 蒐集 dhash 供 C1(跨檔)。hashes: list 累積 (dhash,rel,vkey,crop)。"""
    finds = []
    sw_index = defaultdict(list)     # (page, bbox) 群組 → [vkey]  for C4
    for vkey, pg, cb, png, toks, sws in crops_of(rel, doc):
        # C3 裁到碼文字:裁框 bbox 涵蓋同頁 token bbox
        if cb:
            for tb in toks:
                if _cover(tb, cb) >= COVER:
                    finds.append(_f("C3_crop_text", rel, vkey, pg,
                                    f"裁框涵蓋碼 token bbox {_cover(tb, cb):.0%}=裁到文字冒充色樣", png))
                    break
        # C2 退化裁圖(讀圖)
        if png and brand_dir is not None:
            st = _img_stats(Path(brand_dir) / png)
            if st:
                w, h, std, alpha, dh = st
                hashes.append((dh, rel, vkey, png))
                if min(w, h) < LOWRES:
                    finds.append(_f("C2_degenerate", rel, vkey, pg, f"低解析 {w}x{h}=縮圖/預覽", png))
                elif std < UNIFORM:
                    finds.append(_f("C2_degenerate", rel, vkey, pg, f"近均勻 std={std:.1f}=遮罩/空白", png))
                elif alpha:
                    finds.append(_f("C2_degenerate", rel, vkey, pg, "含透明層 alpha", png))
        # C4 蒐 swatch bbox
        for (spg, sb) in sws:
            sw_index[spg].append((sb, vkey))
    # C4 同色樣多產品:同頁近同 swatch bbox 跨 ≥2 不同 vkey
    for spg, items in sw_index.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                (b1, k1), (b2, k2) = items[i], items[j]
                if k1 != k2 and _iou(b1, b2) >= IOU:
                    finds.append(_f("C4_shared_swatch", rel, f"{k1}|{k2}", spg,
                                    f"同頁近同 swatch bbox(IoU {_iou(b1, b2):.0%})→ 一色樣多產品"))
    return finds


def scan_pool(pairs, max_items=20, sheet=None):
    tot = Counter()
    all_finds = []
    hashes = []          # (dhash, rel, vkey, crop_png)
    for outdir, prefix in pairs:
        root = Path(outdir)
        brand_root = Path(prefix) if prefix and prefix != "." else root
        for p in sorted(root.rglob("*.json")):
            if p.name.endswith((".review.json", ".capcodes.json")) or p.name.startswith("._"):
                continue
            rel = p.relative_to(root).as_posix()
            doc = json.loads(p.read_text())
            brand_dir = p.parent  # 裁圖在 JSON 同目錄下 <stem>_crops/
            finds = scan_doc(rel, doc, brand_dir, hashes)
            all_finds += finds
    # C1 一圖多用(全池 dhash 近似分群;union by ham≤HAM)
    reuse = _dup_groups(hashes)
    all_finds += reuse
    for f in all_finds:
        tot[f["cls"]] += 1
    for cls in sorted({f["cls"] for f in all_finds}):
        sub = [f for f in all_finds if f["cls"] == cls]
        print(f"\n## [{cls}] ×{len(sub)}")
        for f in sub[:max_items]:
            print(f"   {f['doc']} :: {f['variant']} p{f['page']}  {f['note']}")
        if len(sub) > max_items:
            print(f"   …(+{len(sub) - max_items})")
    print("\n# 頻率表(全池)")
    for cls, n in sorted(tot.items()):
        print(f"  {cls}: {n} 筆")
    if sheet:
        _contact_sheet(all_finds, sheet)
        print(f"\n[contact-sheet] {sheet}")
    return tot, all_finds


def _dup_groups(hashes):
    """跨 Variant 近似重複分群(ham≤HAM)→ C1 findings(群跨 ≥2 不同 (rel,vkey))。"""
    finds, n = [], len(hashes)
    seen = [False] * n
    for i in range(n):
        if seen[i]:
            continue
        grp = [i]
        for j in range(i + 1, n):
            if not seen[j] and _ham(hashes[i][0], hashes[j][0]) <= HAM:
                grp.append(j)
                seen[j] = True
        seen[i] = True
        ids = {(hashes[k][1], hashes[k][2]) for k in grp}
        if len(ids) >= 2:                       # 跨 ≥2 不同 Variant 才算一圖多用
            exact = all(hashes[k][0] == hashes[grp[0]][0] for k in grp)
            members = ", ".join(f"{hashes[k][1]}::{hashes[k][2]}" for k in grp[:6])
            for k in grp:
                finds.append(_f("C1_crop_reuse", hashes[k][1], hashes[k][2], None,
                                f"{'exact' if exact else 'near'} dup ×{len(grp)}群 [{members}]",
                                hashes[k][3]))
    return finds


def _contact_sheet(all_finds, out):
    """findings contact-sheet(輕量 HTML,<img> 引裁圖供人工複核;不做影像合成)。
    sheet 與 product/ 同層,故 img src=product/<brand>/<crop>。"""
    groups = defaultdict(list)
    for f in all_finds:
        if f.get("crop"):
            groups[f["cls"]].append(f)
    rows = []
    for cls, fs in sorted(groups.items()):
        imgs = "".join(f'<figure><img src="product/{Path(f["doc"]).parent.name}/{f["crop"]}" '
                       f'width="150" loading="lazy">'
                       f'<figcaption>{Path(f["doc"]).parent.name}::{str(f["variant"])[:24]}<br>{f["note"][:50]}</figcaption></figure>'
                       for f in fs)
        rows.append(f'<section><h3>{cls} ×{len(fs)}</h3><div class="g">{imgs}</div></section>')
    Path(out).write_text(
        "<!doctype html><meta charset=utf-8><style>body{font-family:sans-serif}"
        ".g{display:flex;flex-wrap:wrap;gap:8px}figure{margin:0;font-size:11px;max-width:160px}"
        "img{border:1px solid #ccc;object-fit:contain;background:#f4f4f4}</style>"
        "<h2>案4 裁圖真實性 contact-sheet</h2>" + "".join(rows))


# ---------------- selftest(合成紅燈;鐵律7 實作前 RED)----------------

def selftest():
    import tempfile
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(("PASS " if cond else "★RED ") + name)
        ok = ok and cond

    tmp = Path(tempfile.mkdtemp())
    cdir = tmp / "X_crops"
    cdir.mkdir()
    # 合成裁圖:兩張相同(dup)、一張低解析、一張近均勻
    import numpy as _np
    scene = Image.fromarray((_np.random.RandomState(0).rand(80, 120, 3) * 255).astype("uint8"))
    scene.save(cdir / "reuseA.png")
    scene.save(cdir / "reuseB.png")                       # 與 A 完全相同=一圖多用
    Image.fromarray((_np.random.RandomState(1).rand(60, 90, 3) * 255).astype("uint8")).save(cdir / "distinct.png")
    Image.new("RGB", (8, 8), (128, 128, 128)).save(cdir / "tiny.png")       # 低解析
    Image.new("RGB", (60, 60), (200, 200, 200)).save(cdir / "flat.png")     # 近均勻

    def var(code, png, cbbox, tok_bbox=None, sw_bbox=None, page=1):
        mf = [{"id": "b", "swatch": {"page": page, "bbox": sw_bbox or [0, 0, 10, 10]},
               "prov": {"pdf": "x.pdf", "page": page, "bbox": tok_bbox or [500, 500, 510, 510]}}]
        return {"code": code, "color": {"en": None}, "mergedFrom": mf,
                "swatchCrop": {"png": f"X_crops/{png}", "prov": {"pdf": "x.pdf", "page": page, "bbox": cbbox}}}

    # AC-1 C1 一圖多用:reuseA/reuseB 同圖跨兩 Variant
    doc = {"series": [{"variants": [var("A1", "reuseA.png", [0, 0, 100, 50]),
                                    var("A2", "reuseB.png", [0, 60, 100, 110])]}]}
    f = scan_doc("D/x.json", doc, tmp, [])
    # C1 是跨檔全池計算,單檔 scan_doc 只蒐 hash;用 scan_pool 級模擬
    hs = []
    scan_doc("D/x.json", doc, tmp, hs)
    c1 = _dup_groups(hs)
    chk("AC-1 C1 一圖多用", any(x["cls"] == "C1_crop_reuse" for x in c1))
    # AC-2 C2 退化:tiny(低解析)+ flat(近均勻)
    doc = {"series": [{"variants": [var("B1", "tiny.png", [0, 0, 8, 8]),
                                    var("B2", "flat.png", [0, 0, 60, 60])]}]}
    f = scan_doc("D/y.json", doc, tmp, [])
    chk("AC-2 C2 低解析", any(x["cls"] == "C2_degenerate" and "低解析" in x["note"] for x in f))
    chk("AC-2b C2 近均勻", any(x["cls"] == "C2_degenerate" and "均勻" in x["note"] for x in f))
    # AC-3 C3 裁到碼文字:裁框涵蓋 token bbox
    doc = {"series": [{"variants": [var("C1c", "distinct.png", [0, 0, 100, 100],
                                        tok_bbox=[10, 10, 30, 25])]}]}   # token 在裁框內
    f = scan_doc("D/z.json", doc, tmp, [])
    chk("AC-3 C3 裁到碼文字", any(x["cls"] == "C3_crop_text" for x in f))
    # AC-3b 對照:token 在裁框外 → 不旗
    doc = {"series": [{"variants": [var("C2c", "distinct.png", [0, 0, 100, 100],
                                        tok_bbox=[500, 500, 520, 520])]}]}
    f = scan_doc("D/z2.json", doc, tmp, [])
    chk("AC-3b C3 框外不旗", not any(x["cls"] == "C3_crop_text" for x in f))
    # AC-4 C4 同色樣多產品:兩碼共用同 swatch bbox
    doc = {"series": [{"variants": [var("D1", "distinct.png", [0, 0, 50, 50], sw_bbox=[10, 10, 60, 60]),
                                    var("D2", "reuseA.png", [0, 0, 50, 50], sw_bbox=[10, 10, 60, 61])]}]}
    f = scan_doc("D/w.json", doc, tmp, [])
    chk("AC-4 C4 同色樣多產品", any(x["cls"] == "C4_shared_swatch" for x in f))
    # AC-5 非干涉:distinct 單獨乾淨裁圖 → 零旗
    doc = {"series": [{"variants": [var("E1", "distinct.png", [0, 0, 60, 90], sw_bbox=[10, 10, 20, 20])]}]}
    f = scan_doc("D/clean.json", doc, tmp, [])
    chk("AC-5 乾淨裁圖零旗", not f)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("crop_authenticity_scan selftest " + ("OK" if ok else "=RED(未實作/失敗)"))
    return ok


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    mx, sheet, args = 20, None, []
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a.startswith("--max"):
            mx = int(a.split("=")[1])
        elif a == "--sheet":
            sheet = sys.argv[i + 1]
            i += 1
        else:
            args.append(a)
        i += 1
    pairs = []
    for a in args:
        od, _, cp = a.partition("=")
        pairs.append((od, cp or None))
    if not pairs:
        sys.exit(__doc__)
    scan_pool(pairs, mx, sheet)
