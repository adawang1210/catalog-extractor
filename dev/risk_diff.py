#!/usr/bin/env python3
"""鐵律 8 全量 diff 的五類風險摘要（只讀輸出，不改產線）。

    python3 dev/risk_diff.py <before_outdir> <after_outdir>
    python3 dev/risk_diff.py --selftest

只列：新自動放行、佇列項消失、跨頁 Variant、新來源扇出、欄位 provenance／角色變動。
其餘差異折疊為計數。白名單判定仍應由呼叫端對五類清單逐項核對；本工具不放寬鐵律 8。
"""
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


def _docs(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*.json")
            if not p.name.endswith((".review.json", ".capcodes.json")) and not p.name.startswith("._")}


def _load(path):
    return json.loads(path.read_text()) if path else {"series": [], "specByCode": []}


def _variants(doc):
    return [v for s in doc.get("series", []) for v in s.get("variants", [])]


def _key(v):
    return tuple(sorted(m["id"] for m in v.get("mergedFrom", [])))


def _pages(v):
    return sorted({m["swatch"]["page"] for m in v.get("mergedFrom", [])})


def _prov(x):
    if not x:
        return None
    return (x.get("pdf"), x.get("page"), tuple(x.get("bbox") or ()), x.get("method"))


def _field_prov(doc):
    out = {}
    for v in _variants(doc):
        k = _key(v)
        out[("variant", k, "variant")] = _prov(v.get("prov"))
        out[("variant", k, "color")] = _prov(v.get("color", {}).get("prov"))
        for i, s in enumerate(v.get("variantSizes", [])):
            for field in ("size", "finish", "orderCode", "priceBand"):
                out[("variantSize", k, i, field)] = (_prov(s.get("prov")), s.get(field))
    for s in doc.get("series", []):
        for r in s.get("specByCode", []):
            for field in ("size", "surface", "priceBand", "packing"):
                out[("specByCode", r.get("id"), field)] = (_prov(r.get("prov")), r.get(field))
    return out


def _review(doc):
    return {(r.get("reason"), r.get("code"), _prov(r.get("prov")),
             r.get("swatch", {}).get("page"), tuple(r.get("swatch", {}).get("bbox") or ()) )
            for r in doc.get("items", [])}


def _fanout(doc):
    out = Counter()
    for v in _variants(doc):
        for m in v.get("mergedFrom", []):
            sw = ("swatch", m["swatch"]["page"], tuple(m["swatch"]["bbox"]))
            src = ("token",) + _prov(m.get("prov"))
            out[sw] += 1
            out[src] += 1
    return out


def compare(before_root, after_root):
    before, after = _docs(before_root), _docs(after_root)
    rows = defaultdict(list)
    folded = Counter()
    for rel in sorted(set(before) | set(after)):
        b, a = _load(before.get(rel)), _load(after.get(rel))
        bv, av = {_key(v): v for v in _variants(b)}, {_key(v): v for v in _variants(a)}
        # ① 新 direct-output Variant，與同身分 Variant 的 None→有值欄位。
        for k in av.keys() - bv.keys():
            rows["new_release"].append((rel, "new Variant", len(k), _pages(av[k])))
        for k in av.keys() & bv.keys():
            for field, old, new in (("color", bv[k].get("color", {}).get("en"), av[k].get("color", {}).get("en")),
                                    ("code", bv[k].get("code"), av[k].get("code"))):
                if old is None and new is not None:
                    rows["new_release"].append((rel, f"{field}:None→{new}", len(k), _pages(av[k])))
        # ② K 佇列項消失。
        br = _review(_load(Path(before_root) / rel.replace(".json", ".review.json")))
        ar = _review(_load(Path(after_root) / rel.replace(".json", ".review.json")))
        for item in br - ar:
            rows["review_disappeared"].append((rel, item[0], item[1], item[3]))
        # ③ 新增或由單頁變跨頁的 Variant;跨頁 Variant 消失(撤權/降級)以摘要現身
        #    (案2:撤權=安全方向但屬高風險「形狀變化」,不得摺疊消音;佇列側增量歸②之外
        #    的正常呈現,此處只給 cluster 級摘要=筆數+頁)。
        for k, v in av.items():
            if len(_pages(v)) < 2:
                continue
            if k not in bv or len(_pages(bv[k])) < 2:
                rows["cross_page"].append((rel, "new_crosspage", len(k), _pages(v)))
        for k, v in bv.items():
            if len(_pages(v)) >= 2 and k not in av:
                rows["cross_page"].append((rel, "removed_crosspage", len(k), _pages(v)))
        # ④ 單一色樣／token 的扇出上升(n≥2 才是「扇出」;0→1 單次綁定歸①③呈現)。
        bf, af = _fanout(b), _fanout(a)
        for source, n in af.items():
            if n >= 2 and n > bf[source]:
                rows["fanout"].append((rel, source, bf[source], n))
        # ⑤ 可回指欄位的來源或角色（值）改變。
        bp, ap = _field_prov(b), _field_prov(a)
        for field in bp.keys() & ap.keys():
            if bp[field] != ap[field]:
                rows["field_provenance"].append((rel, field, bp[field], ap[field]))
        folded["unchanged_variants"] += len(bv.keys() & av.keys())
        folded["other_variant_removed"] += sum(  # 跨頁移除已入③摘要,只摺疊單頁移除
            1 for k in bv.keys() - av.keys() if len(_pages(bv[k])) < 2)
    labels = [("new_release", "①新自動放行"), ("review_disappeared", "②佇列項消失"),
              ("cross_page", "③跨頁合併/撤權"), ("fanout", "④單一來源扇出"),
              ("field_provenance", "⑤欄位來源／角色變動")]
    for key, label in labels:
        print(f"{label}: {len(rows[key])}")
        for row in rows[key]:
            print("  ", row)
    print(f"其餘摺疊: unchanged_variants={folded['unchanged_variants']} "
          f"other_variant_removed={folded['other_variant_removed']}")
    return rows


def _write(root, rel, doc, review):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc))
    p.with_name(p.stem + ".review.json").write_text(json.dumps({"items": review}))


def selftest():
    def m(i, page=1):
        return {"id": f"b:{i}", "swatch": {"page": page, "bbox": [i, 0, i + 1, 1]},
                "prov": {"pdf": "x.pdf", "page": page, "bbox": [i, 0, i + 1, 1], "method": "x"}}
    def v(ms, color=None):
        return {"mergedFrom": ms, "color": {"en": color}, "variantSizes": [], "prov": ms[0]["prov"]}
    with tempfile.TemporaryDirectory() as d:
        before, after = Path(d) / "before", Path(d) / "after"
        old = {"series": [{"variants": [v([m(0)], None)],
                             "specByCode": [{"id": "s:1", "priceBand": None, "prov": m(0)["prov"]}]}]}
        # A02G-119 類跨頁、新放行；S2-2 毒碼歸隊=priceBand 角色／來源變；單來源扇出 1→3。
        newm = [m(0, 1), m(1, 2), m(2, 3)]
        for item in newm:
            item["prov"] = newm[0]["prov"]  # 同一來源 token 的扇出 1→3。
        new = {"series": [{"variants": [v(newm, "A02G")],
                             "specByCode": [{"id": "s:1", "priceBand": "A02", "prov": m(1, 2)["prov"]}]}]}
        _write(before, "Marazzi/A02G.json", old, [{"reason": "needs_review", "code": "A02", "prov": m(0)["prov"]}])
        _write(after, "Marazzi/A02G.json", new, [])
        # 案2|撤權對偶:before 有跨頁 Variant,after 整團降級佇列(案1 撤權 37 筆型)
        # → 不得摺疊消音,須以 類③摘要(removed_crosspage)現身。
        rvk = [m(0, 1), m(1, 2), m(2, 2)]
        _write(before, "Topcer/G.json",
               {"series": [{"variants": [v(rvk, "OCT")], "specByCode": []}]}, [])
        _write(after, "Topcer/G.json", {"series": [{"variants": [], "specByCode": []}]},
               [{"reason": "borderline_merge_suspect", "code": "OCT", "prov": rvk[0]["prov"]}])
        rows = compare(before, after)
        assert all(rows[k] for k in ("new_release", "review_disappeared", "cross_page", "fanout", "field_provenance"))
        rem = [r for r in rows["cross_page"] if r[0] == "Topcer/G.json" and r[1] == "removed_crosspage"]
        assert rem and rem[0][2] == 3 and rem[0][3] == [1, 2], f"撤權未現身類③摘要: {rem}"
        # 撤權=佇列淨增方向,不得誤入 ①(新自動放行)
        assert not [r for r in rows["new_release"] if r[0] == "Topcer/G.json"]
    print("risk_diff selftest OK (A02G跨頁／S2-2毒碼角色／單來源扇出／撤權③摘要 皆命中)")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    elif len(sys.argv) == 3:
        compare(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
