#!/usr/bin/env python3
"""單頁過併(single-page overmerge)hub 色樣分離量測(包 B 前半;通案三入庫、只讀不改規則)。

    /opt/homebrew/bin/python3 dev/pkgB_hub_sep.py <corpus> [ver]   (CWD=專案根;ver 預設 12)

背景(續 L2 跨頁塌縮=工作包#6/#7):assemble() union-find「同色樣實例∪同碼」在**單頁**
內也會塌縮——一張純碼索引頁(丙:Ariostea p152)有一大塊 hub 色樣被眾多碼 x-align,把
整頁不同色名的碼併成一個巨 cluster(color=None 過併)。但同樣「單頁 cluster mergedFrom≥20」
也有合法型:甲=欄頭矩陣(Provenza/Cornerstone,眾多小色片)、乙=單色表(SistemT,容忍色名
junk)。跨頁守衛(工作包#7)以 len(pages)>=2 為前提,單頁型完全漏網=補位缺口。

分離訊號=**主色樣 area%**(cluster 內最大色樣 bbox 佔頁面積 %)。機制:過併 hub 是一大塊
情境/索引版塊(高 area%);合法矩陣/單色表是小色片(低 area%)。本探針 monkeypatch 攔截
assemble 收到的真實 bindings(100% 鏡射 union-find+SL-6~8),開 PDF 取頁尺寸算 area%,列舉
**所有**單頁 cluster(mergedFrom≥COLLAPSE_MIN)的 area%,印升序分布→ AREA_T 落在合法上界與
過併下界的空隙中。同印 hub 色樣(掛最多碼者)area% 與掛碼數,供判別子定義比對。

判別子(審查方核可待複核):單頁 cluster ∧ mergedFrom≥20 ∧ 主色樣 area%≥AREA_T → 整團降級
佇列 reason=singlepage_overmerge_suspect。本探針=AREA_T 校準依據(通案二分離量測/鐵律4)。
"""
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402

COLLAPSE_MIN = 20  # 複用 L2_COLLAPSE_MIN=20(mergedFrom 門檻);單頁分支同門檻

_cap = {}
_orig_assemble = pipeline.assemble


def _wrap(bindings, spec_rows, review, band_letters=frozenset(), pseudo=frozenset(),
          page_dims=None):
    _cap["bindings"] = list(bindings)
    _cap["band_letters"] = set(band_letters)
    return _orig_assemble(bindings, spec_rows, review, band_letters, pseudo, page_dims)


pipeline.assemble = _wrap


def _clusters(bindings, band_letters):
    """鏡射 assemble 前段:SL-6~8 suspect 降級 + union-find。回傳 (clusters, suspects)。"""
    sw_of = lambda b: (b["swatch"]["page"], tuple(b["swatch"]["bbox"]))  # noqa: E731
    code_sw, sw_codes = {}, {}
    for b in bindings:
        code_sw.setdefault(b["code"], set()).add(sw_of(b))
        sw_codes.setdefault(sw_of(b), set()).add(b["code"])
    suspects = set()
    for c, ss in code_sw.items():
        if not (c and c[0] in band_letters and len(ss) >= 2):
            continue
        if sum(1 for s in ss if sw_codes[s] - {c}) < 2:
            continue
        sl = sorted(ss)
        if any(sw_codes[a] & sw_codes[b2] == {c}
               for i9, a in enumerate(sl) for b2 in sl[i9 + 1:]):
            suspects.add(c)
    bl2 = [b for b in bindings if b["code"] not in suspects]
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for b in bl2:
        union(b["id"], ("sw", b["swatch"]["page"], tuple(b["swatch"]["bbox"])))
        union(b["id"], ("code", b["code"]))
    cl = defaultdict(list)
    for b in bl2:
        cl[find(b["id"])].append(b)
    return list(cl.values()), suspects


def _page_areas(pdf):
    doc = pipeline.fitz.open(pdf)
    areas = {i + 1: (pg.rect.width * pg.rect.height) for i, pg in enumerate(doc)}
    doc.close()
    return areas


def _area_pct(sw, page_areas):
    x0, y0, x1, y1 = sw["bbox"]
    a = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    pa = page_areas.get(sw["page"]) or 1.0
    return 100.0 * a / pa


def main(corpora, ver, floor=COLLAPSE_MIN):
    vocabs = pipeline.build_vocabs()
    pipeline.V = ver
    rows = []  # (name, page, size, ncols, nraws, conflict, max_pct, hub_pct, hub_codes, nsw)
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
        clusters, _ = _clusters(binds, bl)
        for cl in clusters:
            pages = {b["swatch"]["page"] for b in cl}
            if len(pages) != 1 or len(cl) < floor:
                continue
            cols = {b["color"] for b in cl if b["color"]}
            raws = {b.get("colorRaw", b["color"]) for b in cl if b.get("colorRaw", b["color"])}
            conflict = len(cols) > 1 or len(raws) > 1
            sw_key = lambda b: (b["swatch"]["page"], tuple(b["swatch"]["bbox"]))  # noqa: E731
            sws = {sw_key(b): b["swatch"] for b in cl}
            max_pct = max(_area_pct(sw, page_areas) for sw in sws.values())
            sw_codes = defaultdict(set)
            for b in cl:
                sw_codes[sw_key(b)].add(b["code"])
            hub_key = max(sw_codes, key=lambda k: len(sw_codes[k]))
            rows.append(((pdf.parent.name + "/" + pdf.stem)[:38], list(pages)[0],
                         len(cl), len(cols), len(raws), conflict,
                         max_pct, _area_pct(sws[hub_key], page_areas),
                         len(sw_codes[hub_key]), len(sws)))
    print(f"# corpora={corpora} v{ver}  單頁 cluster(mergedFrom≥{COLLAPSE_MIN})主色樣 area% 分離量測")
    print(f"# {'doc':<38} {'pg':>3} {'sz':>4} col/raw confl  maxArea%  hubArea% hubCodes nSw")
    for r in sorted(rows, key=lambda x: x[6]):
        big = "  ≥20" if r[2] >= COLLAPSE_MIN else ""
        print(f"  {r[0]:<38} {r[1]:>3} {r[2]:>4} {r[3]:>3}/{r[4]:<3} "
              f"{'★衝突' if r[5] else '同色 ':<5} {r[6]:8.3f}  {r[7]:8.3f} {r[8]:>7} {r[9]:>4}{big}")
    pcts = sorted(r[6] for r in rows)
    print(f"\n# 單頁 cluster maxArea% 升序({len(pcts)} 團)={[round(p, 3) for p in pcts]}")
    # 空隙偵測:相鄰 area% 最大跳距(合法上界→過併下界)
    if len(pcts) >= 2:
        gaps = [(pcts[i + 1] - pcts[i], pcts[i], pcts[i + 1]) for i in range(len(pcts) - 1)]
        g, lo, hi = max(gaps)
        print(f"# 最大空隙=[{lo:.3f}, {hi:.3f}](跨度 {g:.3f})→ AREA_T 應落隙中")
    confl = sorted(r[6] for r in rows if r[5])
    print(f"# 其中★衝突團 maxArea% 升序={[round(p, 3) for p in confl]}")


def whitelist_report(corpora, ver):
    """鐵律8 全量 diff:單頁守衛 OFF(AREA_T=∞)vs ON(=5.0)逐檔比 Variant 集合。
    只切 AREA_T=隔離單頁守衛(跨頁守衛 L2_COLLAPSE_MIN 不動)。白名單=僅單頁過併 Variant
    消失(其綁定→佇列),其餘全語料 Variant 逐筆零變化;守衛只移除不新增 ⇒ ON⊂OFF。
    Variant 身分=frozenset(mergedFrom id)→(color, 綁定數)。"""
    vocabs = pipeline.build_vocabs()
    pipeline.V = ver
    changed, total = [], 0

    def variant_keys(pdf):
        json_doc, _, _, _ = pipeline.extract_pdf(pdf, vocabs)
        return {frozenset(m["id"] for m in v["mergedFrom"]):
                (v["color"]["en"], len(v["mergedFrom"]))
                for v in json_doc["series"][0]["variants"]}

    for pdf in sorted(p for c in corpora for p in Path(c).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        total += 1
        pipeline.AREA_T = 10 ** 9   # 守衛 OFF
        off = variant_keys(pdf)
        pipeline.AREA_T = 5.0       # 守衛 ON
        on = variant_keys(pdf)
        removed, added = set(off) - set(on), set(on) - set(off)
        if removed or added:
            name = (pdf.parent.name + "/" + pdf.stem)[:40]
            for k in removed:
                print(f"  {name:<40} 移除 Variant: {off[k][1]} 綁定 color={off[k][0]}")
            for k in added:
                print(f"  {name:<40} ✗新增 Variant: {on[k][1]} 綁定(白名單外!)")
            changed.append((pdf.stem, len(removed), len(added)))
    pipeline.AREA_T = 5.0
    n_add = sum(a for _, _, a in changed)
    print(f"# {corpora}: {total} 檔,{len(changed)} 檔有變動,移除 Variant "
          f"{sum(r for _, r, _ in changed)},新增 {n_add}(白名單外新增須=0)"
          f"  {'✓白名單守住' if n_add == 0 else '✗紅線'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = sys.argv[1:]
    floor, mode = COLLAPSE_MIN, "main"
    if "--whitelist" in args:
        mode = "whitelist"
        args.remove("--whitelist")
    if "--floor" in args:
        i = args.index("--floor")
        floor = int(args[i + 1])
        args = args[:i] + args[i + 2:]
    ver = 12
    if args and args[-1].isdigit():
        ver = int(args[-1])
        args = args[:-1]
    if mode == "whitelist":
        whitelist_report(args, ver)
    else:
        main(args, ver, floor)
