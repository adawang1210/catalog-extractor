#!/usr/bin/env python3
"""L2 塌縮式跨頁誤合併診斷探針(新票步1坐實+步2曝光;通案三入庫、只讀不改規則)。

    /opt/homebrew/bin/python3 dev/assembly_probe.py <corpus> [ver] [--detail <stem>]
      (CWD=專案根;ver 預設對照 12 vs 13)

背景:pipeline.assemble() 用 union-find,合併鍵=同色樣實例(page,bbox)∪同碼(code)
=傳遞閉包。同碼跨頁 union 會把不同頁色樣鏈式連通→單一 swatch cluster 吞併大量
跨頁綁定(A02G v13:page3 大情境照吞 119 綁定/23 頁/color=None)。SL-6~8 的
merge_key_suspect 只對首字母∈band_letters 的碼生效(P 前提,避免 C0 誤中 779),
非 band 的普通產品碼橋接=條件不涵蓋=漏網。

本探針 monkeypatch 攔截 assemble 收到的真實 bindings+band_letters(100% 鏡射),
重演 union-find(含 SL-6~8 suspect 降級),對每檔量「組裝層守恆」指標:
  v_now/v_ex   = ver_a/ver_b 下 Variant 數(預設 12/13)
  max_merge    = 單一 cluster 吞併綁定數上限(塌縮體量)
  max_pages    = 單一 cluster 跨頁數上限(跨頁塌縮幅度)
  none_big     = 有 color=None 且 merged≥COLLAPSE_MIN 的巨 cluster 數(塌縮簽名)
  bridge       = 巨 cluster 內跨≥2 色樣的橋接碼(標 band?=首字母是否∈band_letters)
--detail <stem>:印該檔最大 cluster 的連通結構逐筆(橋接碼/跨頁/色樣/C3 為何不觸發)。
--borderline <ver>:案1 零邊際分離量測(不確定帶母體+合法側上界;下緣/半徑校準依據)。
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402

COLLAPSE_MIN = 20  # 巨 cluster 綁定數門檻(A02G 塌縮=119;正常單色樣 Variant 個位數)

_cap = {}
_orig_assemble = pipeline.assemble


def _wrap(bindings, spec_rows, review, band_letters=frozenset(), pseudo=frozenset(),
          page_dims=None):
    _cap["bindings"] = list(bindings)
    _cap["band_letters"] = set(band_letters)
    _cap["page_dims"] = page_dims
    return _orig_assemble(bindings, spec_rows, review, band_letters, pseudo, page_dims)


pipeline.assemble = _wrap


def _clusters(bindings, band_letters):
    """鏡射 assemble 前段:SL-6~8 suspect 降級 + union-find。回傳 clusters(list of bl)。"""
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


def _metrics(pdf, vocabs, ver):
    pipeline.V = ver
    _cap.clear()
    json_doc, _, _, _ = pipeline.extract_pdf(pdf, vocabs)
    variants = json_doc["series"][0]["variants"]
    return variants, _cap["bindings"], _cap["band_letters"]


def _variant_stats(variants):
    """對最終 json variants 量塌縮指標(對應真實產出)。
    max_merge=單一 Variant 吞併綁定數;max_pages=其跨頁數;
    collapse=merged≥COLLAPSE_MIN 的巨 Variant 數(塌縮體量簽名);
    none_collapse=其中 color.en=None(色名衝突塌成無名巨團)的數。"""
    if not variants:
        return 0, 0, 0, 0, None
    mm = max(len(v["mergedFrom"]) for v in variants)
    big = max(variants, key=lambda v: len(v["mergedFrom"]))
    mp = len({m["swatch"]["page"] for m in big["mergedFrom"]})
    collapse = sum(1 for v in variants if len(v["mergedFrom"]) >= COLLAPSE_MIN)
    none_collapse = sum(1 for v in variants if len(v["mergedFrom"]) >= COLLAPSE_MIN
                        and not v["color"]["en"])
    return mm, mp, collapse, none_collapse, big


def main(corpus, ver_pair, detail):
    vocabs = pipeline.build_vocabs()
    a, b = ver_pair
    print(f"# corpus={corpus}  組裝層守恆:v{a} vs v{b}  (COLLAPSE_MIN={COLLAPSE_MIN})")
    print(f"# {'doc':<36} vA>vB|v{a}:mrg/none|v{b}:maxMrg pg none  塌縮橋接碼/類別")
    # 塌縮帳分兩類:preexist=v{a}(現行產線)已有的 color=None 巨團(潛在產線缺陷)、
    # induced=v{b} 新誘發或惡化(切版阻擋條件)。none_* 為硬病灶(color=None 塌縮)。
    tot = Counter()
    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        va, _, _ = _metrics(pdf, vocabs, a)
        vb, binds_b, bl = _metrics(pdf, vocabs, b)
        if not vb:
            continue
        mm_a, mp_a, coll_a, none_a, _ = _variant_stats(va)
        mm, mp, collapse, none_c, big = _variant_stats(vb)
        # 橋接碼(重演 union-find 找跨≥2 色樣的碼;塌縮檔才算,對 v{b})
        bridge, nb_band = [], 0
        if collapse:
            cls, _ = _clusters(binds_b, bl)
            bigc = max(cls, key=len)
            sw_of = lambda m: (m["swatch"]["page"], tuple(m["swatch"]["bbox"]))  # noqa
            code_sw = defaultdict(set)
            for m in bigc:
                code_sw[m["code"]].add(sw_of(m))
            bridge = sorted(c for c, s in code_sw.items() if len(s) >= 2)
            nb_band = sum(1 for c in bridge if c and c[0] in bl)
            if detail and pdf.stem == detail:
                _detail(pdf, bigc, code_sw, bridge, bl,
                        {m.get("color") for m in bigc},
                        {m["swatch"]["page"] for m in bigc})
        tot["coll_a"] += coll_a
        tot["coll_b"] += collapse
        tot["none_a"] += none_a
        tot["none_b"] += none_c
        induced = none_c > none_a or collapse > coll_a  # v{b} 新誘發/惡化
        if induced:
            tot["induced_docs"] += 1
        if none_a:  # v{a}=現行產線已塌縮
            tot["preexist_docs"] += 1
        if len(va) != len(vb) or collapse or coll_a:
            kind = "★誘發" if induced else (" 產線既存" if none_a else "")
            bsamp = f"{len(bridge)}碼(band:{nb_band})" if bridge else "-"
            name = (pdf.parent.name + "/" + pdf.stem)[:36]
            print(f"  {name:<36} {len(va):>2}>{len(vb):<2}|{mm_a:>4}/{none_a}"
                  f" |{mm:>4} {mp:>3}p {none_c}none  {bsamp}{kind}")
    print(f"# {corpus}: v{a} color=None 塌縮={tot['none_a']}(產線既存,{tot['preexist_docs']} 檔)"
          f"  v{b} color=None 塌縮={tot['none_b']}(誘發/惡化 {tot['induced_docs']} 檔)")
    print(f"#   merged≥{COLLAPSE_MIN} 巨團:v{a}={tot['coll_a']}  v{b}={tot['coll_b']}")


def _detail(pdf, big, code_sw, bridge, band_letters, colors, pages):
    print(f"\n=== --detail {pdf.stem}:最大 cluster 連通結構 ===")
    print(f"  綁定={len(big)}  跨頁={len(sorted(pages))}: {sorted(pages)}")
    print(f"  color 值集={colors}  (None=塌縮成無名巨團)")
    print(f"  橋接碼(跨≥2 色樣,把不同頁色樣 union 連通)={len(bridge)} 個:")
    for c in bridge[:15]:
        isb = c and c[0] in band_letters
        print(f"    {c:<10} 跨 {len(code_sw[c])} 色樣  band?={isb}"
              f"  {'←SL-6~8 P 成立會攔' if isb else '←P 不成立=C3 不觸發=漏網'}")
    nb = sum(1 for c in bridge if c and c[0] in band_letters)
    print(f"  → 橋接碼 {len(bridge)} 個中 band 開頭 {nb} 個:"
          f"{'C3 應攔部分' if nb else 'C3 全不觸發(P 前提不涵蓋)=條件不涵蓋,非觸發序'}\n")


def whitelist_report(corpus, ver, guards="collapse"):
    """鐵律8 全量 diff:守衛 OFF vs ON 逐檔比 Variant 集合。
    guards="collapse"=工作包#7(L2_COLLAPSE_MIN ∞↔20);"case1"=案1(基線含既有守衛,
    只切 L2_BORDERLINE_MIN/L2_AUTO_MERGE_MAX_PAGES/L2_AUTO_MERGED_FROM_MAX ∞↔凍結值)。
    白名單=僅降級團 Variant 消失(其綁定→佇列),其餘全語料 Variant 逐筆零變化。
    Variant 身分=frozenset(mergedFrom 綁定 id)。守衛只移除不新增 ⇒ ON⊂OFF。"""
    vocabs = pipeline.build_vocabs()
    changed, total_docs = [], 0
    knobs = (("L2_COLLAPSE_MIN",) if guards == "collapse" else
             ("L2_BORDERLINE_MIN", "L2_AUTO_MERGE_MAX_PAGES", "L2_AUTO_MERGED_FROM_MAX"))
    frozen_vals = {k: getattr(pipeline, k) for k in knobs}

    def variant_keys(pdf):
        pipeline.V = ver
        json_doc, _, _, _ = pipeline.extract_pdf(pdf, vocabs)
        return {frozenset(m["id"] for m in v["mergedFrom"]): (
                v["color"]["en"], len(v["mergedFrom"])) for v in json_doc["series"][0]["variants"]}

    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        total_docs += 1
        for k in knobs:
            setattr(pipeline, k, 10 ** 9)   # 守衛 OFF
        off = variant_keys(pdf)
        for k, v_ in frozen_vals.items():
            setattr(pipeline, k, v_)        # 守衛 ON(凍結值)
        on = variant_keys(pdf)
        removed = set(off) - set(on)
        added = set(on) - set(off)
        if removed or added:
            name = (pdf.parent.name + "/" + pdf.stem)[:40]
            for k in removed:
                print(f"  {name:<40} 移除 Variant: {off[k][1]} 綁定 color={off[k][0]}")
            for k in added:
                print(f"  {name:<40} ✗新增 Variant: {on[k][1]} 綁定(白名單外!)")
            changed.append((pdf.stem, len(removed), len(added)))
    for k, v_ in frozen_vals.items():
        setattr(pipeline, k, v_)
    n_added = sum(a for _, _, a in changed)
    print(f"# {corpus}: {total_docs} 檔,{len(changed)} 檔有變動,移除 Variant "
          f"{sum(r for _, r, _ in changed)},新增 {n_added}(白名單外新增須=0)"
          f"  {'✓白名單守住' if n_added == 0 else '✗紅線'}")


def sig_report(corpus, ver):
    """塌縮簽名列舉(N 校準+白名單):列出每 cluster 的(跨頁∧色名衝突)狀態與大小。
    色名衝突=len(colors)>1 or len(raws)>1(鏡射 assemble color_en=None∧code_color_conflict)。
    印所有「跨頁∧衝突」cluster 的大小分布→ N 落在 4 塌縮團(≥N)與合法小衝突團之間。"""
    vocabs = pipeline.build_vocabs()
    sizes_hit, all_confl_xpage = [], []
    print(f"# corpus={corpus} v{ver} 塌縮簽名(跨頁≥2 ∧ 色名衝突)cluster 列舉")
    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        _, binds, bl = _metrics(pdf, vocabs, ver)
        if not binds:
            continue
        clusters, _ = _clusters(binds, bl)
        for cl in clusters:
            pages = {b["swatch"]["page"] for b in cl}
            colors = {b["color"] for b in cl if b["color"]}
            raws = {b.get("colorRaw", b["color"]) for b in cl if b.get("colorRaw", b["color"])}
            conflict = len(raws) > 1 or len(colors) > 1
            if len(pages) >= 2 and conflict:
                all_confl_xpage.append(len(cl))
                name = (pdf.parent.name + "/" + pdf.stem)[:34]
                mark = "★塌縮" if len(cl) >= 20 else ""
                print(f"  {name:<34} mergedFrom={len(cl):>4} 跨頁={len(pages):>2} "
                      f"色名={len(colors)}/raw={len(raws)} {mark}")
    all_confl_xpage.sort()
    print(f"# 跨頁∧衝突 cluster 大小(升序)={all_confl_xpage}")
    print(f"#   ≥20 者={[n for n in all_confl_xpage if n >= 20]}  <20 者={[n for n in all_confl_xpage if n < 20]}")


def fanout_report(corpus, ver):
    """通案二分離證據:每檔 code fan-out(最共享碼跨幾色樣)+sw fan-out(最忙色樣掛
    幾碼)。真產品身分=低 fan-out(1~2);橋接碼/hub 色樣=離群。塌縮檔對照健康檔。"""
    vocabs = pipeline.build_vocabs()
    print(f"# corpus={corpus} v{ver} fan-out 分離(健康 vs 塌縮;塌縮=color=None 巨團)")
    print(f"# {'doc':<40} maxCodeFan maxSwFan  塌縮?")
    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        vb, binds, _ = _metrics(pdf, vocabs, ver)
        if not binds:
            continue
        sw_of = lambda b: (b["swatch"]["page"], tuple(b["swatch"]["bbox"]))  # noqa: E731
        code_sw, sw_code = defaultdict(set), defaultdict(set)
        for b in binds:
            code_sw[b["code"]].add(sw_of(b))
            sw_code[sw_of(b)].add(b["code"])
        mcf = max(len(s) for s in code_sw.values())
        msf = max(len(s) for s in sw_code.values())
        _, _, _, none_c, _ = _variant_stats(vb)
        if mcf >= 3 or msf >= 3 or none_c:
            name = (pdf.parent.name + "/" + pdf.stem)[:40]
            print(f"  {name:<40} {mcf:>9} {msf:>8}  {'★' + str(none_c) + 'none' if none_c else '-'}")


def borderline_report(corpus, ver):
    """案1 零邊際分離量測(通案二):對現行雙守衛(跨頁≥20∧衝突/單頁≥20∧area%≥AREA_T)
    放行的 cluster 三分帳——①band=跨頁∧衝突∧<20(不確定帶母體,含 sub-20 真塌縮)
    ②xpage=其餘跨頁 cluster(半徑上限=合法側上界的反例來源)③單頁只記上界。
    純量測不改規則;下緣/半徑常數校準依據(→ output/l2_borderline_merge_ledger.md)。"""
    vocabs = pipeline.build_vocabs()
    band, xpage, sp_max = [], [], (0, "")
    for pdf in sorted(Path(corpus).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        _, binds, bl = _metrics(pdf, vocabs, ver)
        if not binds:
            continue
        pd_ = _cap.get("page_dims") or {}
        clusters, _ = _clusters(binds, bl)
        for cl in clusters:
            pages = {b["swatch"]["page"] for b in cl}
            cols = {b["color"] for b in cl if b["color"]}
            raws = {b.get("colorRaw", b["color"]) for b in cl if b.get("colorRaw", b["color"])}
            conflict = len(cols) > 1 or len(raws) > 1
            n = len(cl)
            area = max((100.0 * (x1 - x0) * (y1 - y0) / pd_[p]
                        for p, (x0, y0, x1, y1) in {(b["swatch"]["page"],
                                                     tuple(b["swatch"]["bbox"])) for b in cl}
                        if pd_.get(p)), default=0.0)
            if n >= pipeline.L2_COLLAPSE_MIN and (
                    (len(pages) >= 2 and conflict)
                    or (len(pages) == 1 and area >= pipeline.AREA_T)):
                continue  # 現行守衛已接走
            name = (pdf.parent.name + "/" + pdf.stem)[:40]
            row = (n, len(pages), len(cols), len(raws), name)
            if len(pages) >= 2 and conflict:
                band.append(row)
            elif len(pages) >= 2:
                xpage.append(row)
            elif n > sp_max[0]:
                sp_max = (n, name)
    print(f"# corpus={corpus} v{ver} 案1 分離量測(現行守衛放行者)")
    print(f"# ①跨頁∧衝突∧<{pipeline.L2_COLLAPSE_MIN}(不確定帶母體,降序):")
    for n, p, c, r, name in sorted(band, reverse=True):
        print(f"  {name:<40} mergedFrom={n:>3} pages={p} colors/raw={c}/{r}")
    print("# ②其餘跨頁 cluster(合法側;半徑上限反例,取前12大):")
    for n, p, c, r, name in sorted(xpage, key=lambda t: (-t[1], -t[0]))[:12]:
        print(f"  {name:<40} mergedFrom={n:>3} pages={p} colors/raw={c}/{r}")
    mx_p = max((p for _, p, *_ in xpage + band), default=0)
    mx_n = max((n for n, *_ in xpage), default=0)
    print(f"# 摘要:band={len(band)} 團(大小分布={sorted(n for n, *_ in band)});"
          f"放行跨頁最大 pages={mx_p};非衝突跨頁最大 mergedFrom={mx_n};"
          f"單頁放行最大 mergedFrom={sp_max[0]} ({sp_max[1]})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    corpus = sys.argv[1]
    vers = (12, 13)
    detail = None
    args = sys.argv[2:]
    if "--fanout" in args:
        i = args.index("--fanout")
        fanout_report(corpus, int(args[i + 1]) if len(args) > i + 1 else 13)
        sys.exit(0)
    if "--borderline" in args:
        i = args.index("--borderline")
        borderline_report(corpus, int(args[i + 1]) if len(args) > i + 1 else 12)
        sys.exit(0)
    if "--sig" in args:
        i = args.index("--sig")
        sig_report(corpus, int(args[i + 1]) if len(args) > i + 1 else 12)
        sys.exit(0)
    if "--whitelist-case1" in args:
        i = args.index("--whitelist-case1")
        whitelist_report(corpus, int(args[i + 1]) if len(args) > i + 1 else 12, "case1")
        sys.exit(0)
    if "--whitelist" in args:
        i = args.index("--whitelist")
        whitelist_report(corpus, int(args[i + 1]) if len(args) > i + 1 else 12)
        sys.exit(0)
    if "--detail" in args:
        i = args.index("--detail")
        detail = args[i + 1]
        args = args[:i]
    if args:
        vers = (12, int(args[0])) if len(args) == 1 else (int(args[0]), int(args[1]))
    main(corpus, vers, detail)
