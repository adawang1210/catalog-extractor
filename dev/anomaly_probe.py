#!/usr/bin/env python3
"""全池組裝層異常掃描器(包 A;通案三入庫、只讀不改規則)。標準職責=巡檢全語料,
確認無「第二個 L2 塌縮量級災難」——即除已知守衛涵蓋者外,無未攔的跨頁塌縮/單頁過併巨團。

    /opt/homebrew/bin/python3 dev/anomaly_probe.py <corpus...> [ver]   (CWD=專案根;ver 預設 12)

塌縮簽名(overmerge 病灶,非=同色合法合併)=色名衝突 或 單頁大 area% hub。三類:
  跨頁塌縮  = 跨頁(≥2)∧色名衝突 ∧ mergedFrom≥COLLAPSE_MIN → 工作包#7 跨頁守衛涵蓋。
  單頁過併  = 單頁 ∧ mergedFrom≥COLLAPSE_MIN ∧ 主色樣 area%≥AREA_T → 段1 單頁守衛涵蓋。
  ★灰帶監看 = 單頁 hub(≥HUB_MIN 綁定)∧色名衝突 ∧ area%∈[GREY_LO, AREA_T)——邊界:
              area% 未達門檻的單頁衝突 hub,若增長至 ≥COLLAPSE_MIN 會兩守衛皆逃逸,故監看
              (單頁過併母體現況 Ariostea 唯一,此為薄弱補償;校準隙 [2.36,7.02])。

★未攔=有塌縮簽名(衝突 或 單頁高 area%)之 ≥COLLAPSE_MIN cluster 卻不落任一守衛(斷言=0;
非零即第二災難候選,停止線回報)。同色大合併(即使跨 16 頁)=T7 設計內合法,不算災難、
只列 sanity sweep。100% 鏡射 assemble(借 pkgB_hub_sep 之 _clusters/_area_pct)。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))   # dev/(借 pkgB_hub_sep 助手)
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402
from pkgB_hub_sep import _clusters, _page_areas, _area_pct, _cap  # noqa: E402

COLLAPSE_MIN = 20     # =pipeline.L2_COLLAPSE_MIN(mergedFrom 塌縮門檻)
AREA_T = 5.0          # =pipeline 單頁過併 area% 門檻(段1,隙中 [2.36, 7.02])
GREY_LO = 2.36        # 灰帶下界=合法單頁 hub area% 上界(pkgB_hub_sep 校準:Ergon Woodtouch)
HUB_MIN = 5           # 灰帶只看 hub 形(≥5 綁定),濾掉零星小 cluster


def _cluster_kind(cl, page_areas):
    """回傳 (kind, size, xpages, maxpct, conflict)。kind∈{跨頁塌縮,單頁過併,灰帶,-}。"""
    pages = {b["swatch"]["page"] for b in cl}
    cols = {b["color"] for b in cl if b["color"]}
    raws = {b.get("colorRaw", b["color"]) for b in cl if b.get("colorRaw", b["color"])}
    conflict = len(cols) > 1 or len(raws) > 1
    sws = {(b["swatch"]["page"], tuple(b["swatch"]["bbox"])): b["swatch"] for b in cl}
    maxpct = max(_area_pct(sw, page_areas) for sw in sws.values())
    size, xp = len(cl), len(pages)
    if xp >= 2 and conflict and size >= COLLAPSE_MIN:
        return "跨頁塌縮", size, xp, maxpct, conflict
    if xp == 1 and size >= COLLAPSE_MIN and maxpct >= AREA_T:
        return "單頁過併", size, xp, maxpct, conflict
    # 塌縮簽名(衝突 或 單頁高area)但不落守衛 → 未攔候選
    if size >= COLLAPSE_MIN and (conflict or (xp == 1 and maxpct >= AREA_T)):
        return "未攔", size, xp, maxpct, conflict
    if xp == 1 and size >= HUB_MIN and conflict and GREY_LO <= maxpct < AREA_T:
        return "灰帶", size, xp, maxpct, conflict
    return "-", size, xp, maxpct, conflict


def main(corpora, ver):
    vocabs = pipeline.build_vocabs()
    pipeline.V = ver
    guarded, grey, unguarded, big = [], [], [], []
    pdfs = sorted(p for c in corpora for p in Path(c).rglob("*.pdf"))
    for pdf in pdfs:
        if pdf.name.startswith("._"):
            continue
        _cap.clear()
        pipeline.extract_pdf(pdf, vocabs)
        binds = _cap.get("bindings", [])
        bl = _cap.get("band_letters", set())
        if not binds:
            continue
        page_areas = _page_areas(pdf)
        for cl in _clusters(binds, bl)[0]:
            kind, size, xp, pct, conf = _cluster_kind(cl, page_areas)
            pg = sorted({b["swatch"]["page"] for b in cl})[0]
            name = (pdf.parent.name + "/" + pdf.stem)[:38]
            rec = (name, pg, size, xp, pct, conf, kind)
            if size >= COLLAPSE_MIN:
                big.append(rec)
                if kind in ("跨頁塌縮", "單頁過併"):
                    guarded.append(rec)
                elif kind == "未攔":       # 有塌縮簽名卻逃逸=第二災難候選(斷言=0)
                    unguarded.append(rec)
            if kind == "灰帶":
                grey.append(rec)
    print(f"# corpora={corpora} v{ver}  全池組裝層異常巡檢"
          f"(COLLAPSE_MIN={COLLAPSE_MIN} AREA_T={AREA_T} 灰帶[{GREY_LO},{AREA_T}) hub≥{HUB_MIN})")
    print(f"\n## 守衛涵蓋之 ≥{COLLAPSE_MIN} 塌縮/過併 cluster({len(guarded)}):")
    for name, pg, size, xp, pct, conf, kind in sorted(guarded, key=lambda r: -r[2]):
        print(f"  [{kind}] {name:<38} p{pg} 綁定={size} 跨頁={xp} area%={pct:.3f} {'★衝突' if conf else '同色'}")
    print(f"\n## ★灰帶監看 單頁 hub area%∈[{GREY_LO},{AREA_T})({len(grey)}):")
    for name, pg, size, xp, pct, conf, kind in sorted(grey, key=lambda r: -r[4]):
        print(f"  {name:<38} p{pg} 綁定={size} area%={pct:.3f} {'★衝突' if conf else '同色'}")
    print(f"\n## ★未攔 ≥{COLLAPSE_MIN} 巨團(守衛外=第二災難候選,斷言=0):{len(unguarded)}")
    for rec in sorted(unguarded, key=lambda r: -r[2]):
        print(f"  ✗ {rec[0]:<38} p{rec[1]} 綁定={rec[2]} 跨頁={rec[3]} area%={rec[4]:.3f}")
    top = sorted(big, key=lambda r: -r[2])[:8]
    print(f"\n## 最大吞併前列(sanity sweep,{len(big)} 個 ≥{COLLAPSE_MIN} 團):")
    for name, pg, size, xp, pct, conf, kind in top:
        print(f"  {name:<38} p{pg} 綁定={size} 跨頁={xp} [{kind}]")
    verdict = "✓無第二個 L2 塌縮量級災難(所有 ≥門檻巨團皆落守衛)" if not unguarded \
        else f"✗{len(unguarded)} 個守衛外巨團=停止線"
    print(f"\n# 結論:{verdict}  灰帶邊界 {len(grey)} 例(常態監看)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = sys.argv[1:]
    ver = 12
    if args and args[-1].isdigit():
        ver = int(args[-1])
        args = args[:-1]
    main(args, ver)
