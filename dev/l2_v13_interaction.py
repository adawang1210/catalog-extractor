#!/usr/bin/env python3
"""段2 L2 正規修法|v13 交互驗:med_ex(M5-2b)救回批進綁定池後,塌縮守衛是否接住 v13
誘發塌縮(通案三入庫、只讀不改規則)。直接用 pipeline.extract_pdf 回傳的真實 stats+
最終 variants(非鏡射=權威),對每檔 v12 vs v13 對帳:

  merged      = merged_bindings(出 Variant 的綁定)
  xpDemote    = assembly_collapse_demoted(跨頁塌縮守衛降級)
  spDemote    = singlepage_overmerge_demoted(段1 單頁過併守衛降級)
  escGE20     = ★通案四硬閘=色名=None ∧ 跨頁≥2 ∧ mergedFrom≥N 之已出貨 Variant(須=0)
  noneSub20   = 色名=None ∧ 跨頁≥2 ∧ mergedFrom<N 之已出貨 Variant(工作包#7 <N 容忍帶,
                帶 code_color_conflict 旗;報告不硬閘,監看零邊際)
  救回分流    = Δ(merged+demote) v12→v13(med_ex 淨增綁定)拆:→輸出(Δmerged)/→塌縮佇列(Δdemote)

    /opt/homebrew/bin/python3 dev/l2_v13_interaction.py <pdf-or-corpus>...   (CWD=專案根)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402


def _variant_escapes(json_doc, N):
    """對最終 variants 數色名=None ∧ 跨頁≥2 之 ≥N / <N Variant。"""
    ge, sub, mx = 0, 0, 0
    for v in json_doc["series"][0]["variants"]:
        xp = len({m["swatch"]["page"] for m in v["mergedFrom"]})
        if v["color"]["en"] is None and xp >= 2:
            m = len(v["mergedFrom"])
            mx = max(mx, m)
            if m >= N:
                ge += 1
            elif m >= 2:
                sub += 1
    return ge, sub, mx


def _measure(pdf, vocabs, ver, N):
    pipeline.V = ver
    json_doc, review, _, stats = pipeline.extract_pdf(pdf, vocabs)
    ge, sub, mx = _variant_escapes(json_doc, N)
    return {"merged": stats["merged_bindings"],
            "xp": stats["assembly_collapse_demoted"],
            "sp": stats["singlepage_overmerge_demoted"],
            "dd": stats["d_demoted"],  # SL-6~8 merge_key_suspect(779 監看)
            "nv": stats["n_variants"], "escGE20": ge, "noneSub20": sub,
            "maxNone": mx, "spEsc": stats["singlepage_escaped"]}


def main(paths):
    vocabs = pipeline.build_vocabs()
    N = pipeline.L2_COLLAPSE_MIN
    pdfs = []
    for p in paths:
        pp = Path(p)
        pdfs += [pp] if pp.suffix == ".pdf" else sorted(pp.rglob("*.pdf"))
    tot = {"escGE20": 0, "noneSub20": 0, "spEsc": 0}
    dd = {12: 0, 13: 0}
    print(f"# 段2 v13 交互驗(N={N})  merged/xpDemote/spDemote/Variant | escGE20 noneSub20 maxNone")
    for pdf in pdfs:
        if pdf.name.startswith("._"):
            continue
        a = _measure(pdf, vocabs, 12, N)
        b = _measure(pdf, vocabs, 13, N)
        dd[12] += a["dd"]
        dd[13] += b["dd"]
        if a == b:
            continue  # v13 無交互=略
        name = (pdf.parent.name + "/" + pdf.stem)[:34]
        d_merge, d_dem = b["merged"] - a["merged"], (b["xp"] + b["sp"]) - (a["xp"] + a["sp"])
        rescue = d_merge + d_dem
        print(f"  {name:<34}")
        print(f"    v12: {a['merged']:>4}/{a['xp']:>3}/{a['sp']:>3}/{a['nv']:>3}"
              f" | escGE20={a['escGE20']} noneSub20={a['noneSub20']} maxNone={a['maxNone']}")
        print(f"    v13: {b['merged']:>4}/{b['xp']:>3}/{b['sp']:>3}/{b['nv']:>3}"
              f" | escGE20={b['escGE20']} noneSub20={b['noneSub20']} maxNone={b['maxNone']}")
        print(f"    救回分流 Δ={rescue:+d}:→輸出 {d_merge:+d} / →塌縮佇列 {d_dem:+d}")
        for k in tot:
            tot[k] += b[k]
    print(f"\n# ★通案四硬閘(v13 全檔加總):escGE20={tot['escGE20']}(須=0)"
          f"  spEsc={tot['spEsc']}(須=0)  {'✓' if tot['escGE20'] == 0 and tot['spEsc'] == 0 else '✗逃逸'}")
    print(f"# 監看:noneSub20(色名=None∧跨頁∧<N 已出貨,<N 容忍帶)={tot['noneSub20']}"
          f"  ——零邊際觀察(v13 Uniche 19 型)")
    print(f"# SL-6~8(779):merge_key_suspect 全池降級 v12={dd[12]} v13={dd[13]}"
          f"  ——P(band 字母)排除 779 C0 型;守衛非干涉(收編否決)")


def dump(stem, ver):
    """--dump:印指定檔(依 stem)於 v{ver} 之近門檻(12≤size≤28)跨頁色名衝突 cluster 的
    逐綁定(code/colorRaw/page)——供 blocker 票定性 19 團=合法大合併 vs 真塌縮(同病理)。"""
    from pkgB_hub_sep import _clusters, _cap  # noqa: E402(帶 monkeypatch 捕獲 bindings)
    vocabs = pipeline.build_vocabs()
    pipeline.V = ver
    for c in ["catalogs"] + [f"catalogs{i}" for i in range(2, 8)]:
        for pdf in sorted(Path(c).rglob("*.pdf")):
            if pdf.stem != stem or pdf.name.startswith("._"):
                continue
            _cap.clear()
            pipeline.extract_pdf(pdf, vocabs)
            clusters, _ = _clusters(_cap["bindings"], _cap["band_letters"])
            for cl in sorted(clusters, key=len):
                pages = {b["swatch"]["page"] for b in cl}
                raws = {b.get("colorRaw", b["color"]) for b in cl if b.get("colorRaw", b["color"])}
                if len(pages) >= 2 and len(raws) > 1 and 12 <= len(cl) <= 28:
                    print(f"\n=== {c}/{stem} v{ver}  cluster size={len(cl)} 跨頁={sorted(pages)} "
                          f"raw色名={len(raws)} ===")
                    for b in sorted(cl, key=lambda x: (x["swatch"]["page"], x["code"])):
                        print(f"  p{b['swatch']['page']:>3} code={b['code']:<10} "
                              f"colorRaw={b.get('colorRaw', b['color'])!r}")
            return


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--dump":
        dump(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 13)
    else:
        main(sys.argv[1:])
