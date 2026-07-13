#!/usr/bin/env python3
"""M5-2 B 訊號誤 icon 分離量測探針(工作包#4 步1;通案三:入庫、數字可復現)。

    python3 dev/b_signal_probe.py <corpus_dir> [large_frac] [mode] [ver]   (CWD=專案根)
      mode=sws(預設):色樣級 B/A' 降級 + 候選中位分離
      mode=codes    :code 級 icon_demoted(現行 med vs 候選 med_ex),餵 ctx 純量測
      ver(codes 模式限定,預設 12):scan 鏈版本。ver=9=工作包#4 反查題量測——
        v9 側枝是否實際依賴 doc_icon_stats 中位(dm/photo_dm 於 med vs med_ex 逐檔對照;
        任何差異=依賴成立=版本閘須真分叉雙中位)。

背景:M5-2 B 訊號=色樣面積 < 0.05×doc 中位 → 判 icon 降級。單系列型錄的情境照
被 extract_swatches 抽成大面積色樣,撐高 doc 中位,真小色樣掉到門檻下被誤殺。

本探針對每檔重演 doc_icon_stats/icon_sus(version=3 抽色樣、spec 頁母體),逐檔列:
  spec 頁數 / 色樣總數 / med(現行 B 基準=全色樣面積中位)
  大圖數(面積 ≥ large_frac×頁面積,預設 0.10=V9_G 谷帶下緣)與其面積占比
  B 降級數(a<0.05×med)/ A' 降級數(rep∧a<0.5×med)
  候選穩健中位分離實測:
    med_ex = 排除大圖(≥large_frac×頁)後重算中位 → B_ex 降級數
    med_pg = 各 spec 頁「頁內中位」再取檔級中位 → B_pg 降級數
    med_lo = 只取「小簇」(<large_frac×頁)色樣中位 → 同 med_ex(對照)
  各候選下:B 降級減少量 = 疑似救回的真色樣(失敗方向=寧可少殺 icon)。

純量測、不改規則、不改 core。標的病例會在檔名處標 ★。"""
import sys
from pathlib import Path
from statistics import median

import fitz

sys.path.insert(0, "core")
from census import SIZE_RE                                    # noqa: E402
from spike_geom import extract_swatches                       # noqa: E402
from m3_scan import _K20                                      # noqa: E402

CASES = ("Re-Play", "Vivo", "Uniche", "Ego")  # 標的病例(檔名子字串)
corpus = sys.argv[1]
LARGE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.10
MODE = sys.argv[3] if len(sys.argv) > 3 else "sws"
VER = int(sys.argv[4]) if len(sys.argv) > 4 else 12


def med_ex_of(spec):
    """候選:排除 ≥LARGE×頁 的大圖後,對剩餘小簇色樣面積取檔級中位;
    小簇空(全大圖)→ 退回全體中位(保存原行為)。"""
    small = []
    for p in spec:
        pa = abs(p.rect)
        small += [abs(r) for r in extract_swatches(p, version=3) if abs(r) < LARGE * pa]
    if not small:
        alla = [abs(r) for p in spec for r in extract_swatches(p, version=3)]
        return median(alla) if alla else 0.0
    return median(small)


if MODE == "codes":
    # code 級救回量測:餵 (rep, med_ex) 給 scan_page,對照現行 (rep, med)。純量測不改 core。
    from m2_scan import build_vocabs, code_candidates            # noqa: E402
    from m3_scan import doc_name_index, doc_icon_stats, scan_page  # noqa: E402
    cv, av = build_vocabs()
    v9 = VER == 9  # 反查模式:另列 photo_dm(E-1 照片降級)於雙中位下的對照
    print(f"# corpus={corpus} large_frac={LARGE} ver={VER}  code 級 icon_demoted:現行 vs med_ex")
    hdr = "  pdm_now pdm_ex" if v9 else ""
    print(f"# {'doc':<42}  codes  dm_now  dm_ex  救回{hdr}")
    tot_now = tot_ex = ptot_now = ptot_ex = 0
    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        doc = fitz.open(pdf)
        spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
        if not spec:
            continue
        cd, _ = code_candidates(doc, cv, len(spec), VER, av)
        nc = doc_name_index(spec, cd, av, VER)
        rep, _med = doc_icon_stats(spec)
        ic_now = (rep, _med)
        ic_ex = (rep, med_ex_of(spec))
        dm_now = dm_ex = pdm_now = pdm_ex = ncodes = 0
        for p in spec:
            rn = scan_page(p, cd, av, VER, nc, ic_now)
            re_ = scan_page(p, cd, av, VER, nc, ic_ex)
            ncodes += rn["n_codes"]
            dm_now += rn["code_icon_demoted"]
            dm_ex += re_["code_icon_demoted"]
            if v9:
                pdm_now += rn["code_photo_demoted"]
                pdm_ex += re_["code_photo_demoted"]
        tot_now += dm_now
        tot_ex += dm_ex
        ptot_now += pdm_now
        ptot_ex += pdm_ex
        if dm_now or dm_ex or pdm_now or pdm_ex:
            star = " ★" if any(c in pdf.name for c in CASES) else ""
            name = (pdf.parent.name + "/" + pdf.stem)[:42]
            p9 = f"  {pdm_now:>7} {pdm_ex:>6}" if v9 else ""
            print(f"  {name:<42} {ncodes:>5} {dm_now:>6} {dm_ex:>6} {dm_now - dm_ex:>5}{p9}{star}")
    p9t = f"  photo_dm_now={ptot_now} photo_dm_ex={ptot_ex}" if v9 else ""
    print(f"# 合計:dm_now={tot_now} dm_ex={tot_ex} 救回={tot_now - tot_ex}{p9t}")
    sys.exit(0)

print(f"# corpus={corpus} large_frac={LARGE}  (med=現行B基準; med_ex=排大圖; "
      f"med_pg=頁內中位再檔級中位)")
print(f"# {'doc':<42} spec sws  med%pg  big B  Aq | med_ex%  Bex | med_pg%  Bpg")

for pdf in sorted(Path(corpus).rglob("*.pdf")):
    if pdf.name.startswith("._"):
        continue
    doc = fitz.open(pdf)
    spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
    if not spec:
        continue
    # 每 spec 頁色樣面積(絕對 pt^2)與「占頁面積比」
    per_abs, per_frac, page_area = [], [], []
    for p in spec:
        pa = abs(p.rect)
        sws = extract_swatches(p, version=3)
        per_abs.append([abs(r) for r in sws])
        per_frac.append([abs(r) / pa for r in sws])
        page_area.append(pa)
    all_abs = [a for row in per_abs for a in row]
    all_frac = [f for row in per_frac for f in row]
    if not all_abs:
        continue
    med = median(all_abs)                             # 現行 B 基準
    # rep_keys 重演(A' 判定用)
    from collections import Counter
    keyc = Counter(_K20(r) for p in spec for r in extract_swatches(p, version=3))
    need = max(5, 0.5 * len(spec))
    rep = {k for k, n in keyc.items() if n >= need}
    # 大圖(情境照)統計
    big = sum(1 for f in all_frac if f >= LARGE)
    # 現行 B / A' 降級數(重演 icon_sus 兩臂)
    B = sum(1 for a in all_abs if a < 0.05 * med)
    # A' 需 bbox key,重掃
    Aq = 0
    for p in spec:
        for r in extract_swatches(p, version=3):
            a = abs(r)
            if not (a < 0.05 * med) and (_K20(r) in rep and a < 0.5 * med):
                Aq += 1
    # 候選 1:排除大圖後中位
    small_abs = [a for a, f in zip(all_abs, all_frac) if f < LARGE]
    med_ex = median(small_abs) if small_abs else med
    Bex = sum(1 for a in all_abs if a < 0.05 * med_ex)
    # 候選 2:頁內中位再取檔級中位
    pg_meds = [median(row) for row in per_abs if row]
    med_pg = median(pg_meds) if pg_meds else med
    Bpg = sum(1 for a in all_abs if a < 0.05 * med_pg)

    apa = median(page_area)  # 代表頁面積(換算 %)
    star = " ★" if any(c in pdf.name for c in CASES) else ""
    name = (pdf.parent.name + "/" + pdf.stem)[:42]
    print(f"  {name:<42} {len(spec):>3} {len(all_abs):>4} "
          f"{med/apa*100:>6.2f} {big:>3} {B:>2} {Aq:>3} |"
          f" {med_ex/apa*100:>6.2f} {Bex:>4} |"
          f" {med_pg/apa*100:>6.2f} {Bpg:>4}{star}")
