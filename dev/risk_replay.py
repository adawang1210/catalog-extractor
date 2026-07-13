#!/usr/bin/env python3
"""案2|已知案例回放世界產生器(只讀產線規則;monkeypatch 版本/守衛常數造歷史世界)。

產生 product 形制輸出目錄供 dev/risk_diff.py 做 before/after 五類風險摘要。
所有世界=歷史已審世界的重演(回放驗收,非新規則;不改 pipeline/core 任何行為)。

    /opt/homebrew/bin/python3 dev/risk_replay.py <outdir> <corpus...> \\
        [--ver N] [--off case1,collapse,seg1] [--only substr]      (CWD=專案根)

--ver N   pipeline.V=N(預設 12;8/10=S2-2 L1 歷史世界、13=med_ex 版本閘)
--off …   守衛常數推至 ∞:case1=帶+半徑(=--whitelist-case1 之 OFF 側)、
          collapse=跨頁塌縮+單頁過併(共用 L2_COLLAPSE_MIN 門檻)、seg1=單頁過併(AREA_T)
--only s  只跑檔名含 s 之 PDF(單病例回放)
--nocrop  裁圖 no-op(JSON/佇列內容逐位不變;供只讀 JSON 的掃描器世界=案3/案4 之外快速生成)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402

INF = 10 ** 9


def main(argv):
    pos, only, ver, off, nocrop = [], None, 12, set(), False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--ver":
            ver, i = int(argv[i + 1]), i + 2
        elif a == "--off":
            off, i = set(argv[i + 1].split(",")), i + 2
        elif a == "--only":
            only, i = argv[i + 1], i + 2
        elif a == "--nocrop":
            nocrop, i = True, i + 1
        else:
            pos.append(a)
            i += 1
    outdir, corpora = pos[0], pos[1:]
    bad = off - {"case1", "collapse", "seg1"}
    assert corpora and not bad, f"用法見 --help;未知 --off={bad}"
    pipeline.V = ver
    if "case1" in off:      # 案1 OFF(既有守衛保持 ON)=鐵律8 --whitelist-case1 同語意
        pipeline.L2_BORDERLINE_MIN = INF
        pipeline.L2_AUTO_MERGE_MAX_PAGES = INF
        pipeline.L2_AUTO_MERGED_FROM_MAX = INF
    if "collapse" in off:   # ≥20 雙守衛 OFF;帶上緣亦失效 → 全關須連 case1 一起 OFF
        pipeline.L2_COLLAPSE_MIN = INF
    if "seg1" in off:
        pipeline.AREA_T = float("inf")
    if nocrop:
        pipeline.crop_png = lambda *a, **k: None
    vocabs = pipeline.build_vocabs()
    n = 0
    for c in corpora:
        for pdf in sorted(Path(c).rglob("*.pdf")):
            if pdf.name.startswith("._") or (only and only not in pdf.stem):
                continue
            pipeline.write_out(pdf, outdir, vocabs)
            n += 1
            print(f"  {pdf.parent.name}/{pdf.stem[:44]} done", flush=True)
    print(f"[risk_replay] V={ver} off={sorted(off) or '無'} only={only or '全'} → {outdir}({n} 檔)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1:])
