#!/usr/bin/env python3
"""案3|欄位級 provenance 掃描器(純儀器、只讀、不修只曝光;通案三入庫)。

掃描產線輸出(product 形制目錄)的五類欄位級風險,每筆回指 token/頁/bbox/
正規化前字串(F4 經 PDF 重讀 prov bbox 取 raw):

  F1  產品碼↔價格碼互換候選(A102 型):code 角色 token 形=[A-Z]\\d{3} 且同檔
      priceBand 值有同字母 1-2 位家族(≥3)=high 逐筆;無家族=info 頻率表(T104 型)。
  F1b 偽碼(S2-5 型):Variant 帶 pseudoCodeSuspect 旗,或 code(≥6 位)=檔名子串。
  F2  混欄(shape 稽核):size 非尺寸形/surface 含數字或單位・包裝詞/priceBand 非
      帶形/packing 值非數。
  F3  系列標題跨頁錯誤延續(啟發式 info):同檔 ≥2 個字首碼家族(各 ≥3 碼)且
      頁域不相交=多系列一檔候選(SCH-3 未做=檔名級標題錯誤延續整檔)。
  F4  單位正規化碰撞:同 normalized size 鍵 ← ≥2 種 raw 字串(同鍵碰撞);
      跨鍵 scale 別名(WxH vs 10Wx10Hmm / WxHcm)=同物異鍵候選。
  F5  一 token 多欄位角色:code 角色 ∧ (priceBand|size|surface|packing) 角色並存。

    /opt/homebrew/bin/python3 dev/field_prov_scan.py <outdir>=<corpus> [...] \\
        [--max N]                                             (CWD=專案根)
    /opt/homebrew/bin/python3 dev/field_prov_scan.py --selftest

停止線(規格):掃出災難級既存欄位錯誤(比照 L2 塌縮量級,如大量碼/價互換入庫)
=立即凍結回報。本工具不改任何產線行為、不裁決白名單。
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402  正規化用產線同款 norm_size,不重製

BANDISH = re.compile(r"^[A-Z]\d{3}$")        # A102 型(字母+3 位=量表碼形)
BAND_MEM = re.compile(r"^([A-Z])\d{1,2}$")   # 帶家族成員形(route_junk band 同款)
SIZE_OK = re.compile(r"^\d+(?:[.,]\d+)?x\d+(?:[.,]\d+)?(?:x\d+(?:[.,]\d+)?)?(?:mm|cm)?$")
UNIT_WORD = re.compile(r"(?:\d|\b(?:MM|CM|M2|MQ|SQM|KG|BOX|PALLET|PCS|PZ|PIECES|SCATOLA)\b)", re.I)
SIZE_IN_RAW = re.compile(r"\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?(?:\s*[x×]\s*\d+(?:[.,]\d+)?)?\s*(?:MM|CM)?", re.I)
KEY_SCALE = re.compile(r"^(\d+)x(\d+)(mm|cm)?$")


def _code_roles(doc):
    """(token, 'code', prov) 三元組:variant.code/specByCode.code/orderCode。"""
    out = []
    for s in doc.get("series", []):
        for v in s.get("variants", []):
            if v.get("code"):
                out.append((v["code"], "variant.code", v.get("prov")))
            for vs in v.get("variantSizes", []):
                if vs.get("orderCode"):
                    out.append((vs["orderCode"], "orderCode", vs.get("prov")))
        for r in s.get("specByCode", []):
            if r.get("code"):
                out.append((r["code"], "spec.code", r.get("prov")))
    return out


def _band_families(doc):
    """priceBand 值的同字母 1-2 位家族(≥3 distinct)→ 家族字母集合。"""
    mem = defaultdict(set)
    for s in doc.get("series", []):
        for r in s.get("specByCode", []):
            m = BAND_MEM.match(r.get("priceBand") or "")
            if m:
                mem[m.group(1)].add(r["priceBand"])
        for v in s.get("variants", []):
            for vs in v.get("variantSizes", []):
                m = BAND_MEM.match(vs.get("priceBand") or "")
                if m:
                    mem[m.group(1)].add(vs["priceBand"])
    return {c for c, s in mem.items() if len(s) >= 3}


def _pp(prov):
    return (prov or {}).get("page"), tuple((prov or {}).get("bbox") or ())


def _f(cls, rel, field, token, prov, raw, note):
    pg, bb = _pp(prov)
    return {"cls": cls, "doc": rel, "field": field, "token": token,
            "page": pg, "bbox": bb, "raw": raw, "note": note}


NUMISH = re.compile(r"^\d+(?:[.,]\d+)?$")


def _pack_bad(pk):
    """packing 值非數(dict 則任一值非數;scalar 直接判)。None/空=不旗。"""
    if not pk:
        return False
    vals = list(pk.values()) if isinstance(pk, dict) else [pk]
    return any(v not in (None, "") and not NUMISH.match(str(v).strip()) for v in vals)


def _prefix(code):
    m = re.match(r"^([A-Za-z]+)", code or "")
    return m.group(1).upper() if m else None


def scan_doc(rel, doc, rawf):
    """單檔五類掃描 → findings=[{cls,doc,field,token,page,bbox,raw,note}]。
    rawf(prov)→prov bbox 下的原始字串(None=無 PDF 可回讀)。純曝光、不裁決。"""
    finds = []
    code_roles = _code_roles(doc)
    code_tokens = {t for t, _, _ in code_roles}
    fams = _band_families(doc)
    stem = Path(rel).stem.lower()

    # F1|碼↔價互換(A102 型):碼形 [A-Z]d3 ∧ 同檔存在同字母帶家族(≥3)→ high 逐筆。
    for tok, role, prov in code_roles:
        if tok and BANDISH.match(tok) and tok[0] in fams:
            finds.append(_f("F1_code_price_swap", rel, role, tok, prov, rawf(prov),
                            f"碼形[A-Z]d3 ∧ 同檔 {tok[0]} 帶家族≥3=碼/價互換候選(high)"))

    # F1b|偽碼(S2-5 型):pseudoCodeSuspect 旗,或 code(≥6)=檔名子串。
    for s in doc.get("series", []):
        for v in s.get("variants", []):
            ps = v.get("pseudoCodeSuspect")
            if ps:
                for t in (ps if isinstance(ps, list) else [v.get("code")]):
                    finds.append(_f("F1b_pseudo_code", rel, "variant.code", t, v.get("prov"),
                                    rawf(v.get("prov")), "pseudoCodeSuspect 旗"))
            c = v.get("code") or ""
            if not ps and len(c) >= 6 and c.lower() in stem:
                finds.append(_f("F1b_pseudo_code", rel, "variant.code", c, v.get("prov"),
                                rawf(v.get("prov")), "code(≥6)=檔名子串=偽碼候選"))

    # F2|混欄(shape 稽核 specByCode):size 非尺寸/surface 含數字單位包裝詞/band 非帶形/packing 非數。
    for s in doc.get("series", []):
        for r in s.get("specByCode", []):
            prov, note = r.get("prov"), f"code={r.get('code')}"
            size, surf, band, pk = r.get("size"), r.get("surface"), r.get("priceBand"), r.get("packing")
            if size and not SIZE_OK.match(size):
                finds.append(_f("F2_field_mixing", rel, "size", size, prov, rawf(prov), note + " size 非尺寸形"))
            if surf and UNIT_WORD.search(surf):
                finds.append(_f("F2_field_mixing", rel, "surface", surf, prov, rawf(prov), note + " surface 含數字/單位/包裝詞"))
            if band and not BAND_MEM.match(band):
                finds.append(_f("F2_field_mixing", rel, "priceBand", band, prov, rawf(prov), note + " priceBand 非帶形"))
            if _pack_bad(pk):
                finds.append(_f("F2_field_mixing", rel, "packing", pk, prov, rawf(prov), note + " packing 非數"))

    # 收集 size 鍵→provs(F4 用);other 值→角色(F5 用)。
    bykey = defaultdict(list)
    other = defaultdict(set)
    for s in doc.get("series", []):
        for r in s.get("specByCode", []):
            if r.get("size"):
                bykey[r["size"]].append(r.get("prov"))
            for fld in ("priceBand", "size", "surface"):
                if r.get(fld):
                    other[r[fld]].add(fld)
        for v in s.get("variants", []):
            for vs in v.get("variantSizes", []):
                if vs.get("size"):
                    bykey[vs["size"]].append(vs.get("prov"))
                for fld in ("priceBand", "size", "surface"):
                    if vs.get(fld):
                        other[vs[fld]].add(fld)

    # F4|同正規化鍵 ← ≥2 種 raw(去空白大寫後仍異)=單位碰撞。
    # ★raw 須為「尺寸形」子串(SIZE_IN_RAW):specByCode 列 prov 常指碼位置,rawf 會讀回
    #   碼 token 而非尺寸原字串(鐵律2:非尺寸=None 不計,寧不旗也不誤旗)。
    for key, provs in bykey.items():
        norms = {}
        for prov in provs:
            raw = rawf(prov)
            m = SIZE_IN_RAW.search(raw) if raw else None
            if m:
                norms[re.sub(r"\s", "", m.group(0)).upper()] = prov
        if len(norms) >= 2:
            finds.append(_f("F4_unit_collision", rel, "size", key, next(iter(norms.values())),
                            " | ".join(sorted(norms)),
                            f"同正規化鍵 {key} ← {len(norms)} 種尺寸形 raw"))

    # F4|跨鍵 scale 別名(WxH 與 10^k×WxH 並存)=同物異鍵。
    skeys = [k for k in bykey if KEY_SCALE.match(k)]

    def _wh(k):
        m = KEY_SCALE.match(k)
        return int(m.group(1)), int(m.group(2))
    seen = set()
    for i in range(len(skeys)):
        for j in range(i + 1, len(skeys)):
            (w1, h1), (w2, h2) = _wh(skeys[i]), _wh(skeys[j])
            for rt in (10, 100, 1000):
                if (w2 == w1 * rt and h2 == h1 * rt) or (w1 == w2 * rt and h1 == h2 * rt):
                    pair = tuple(sorted((skeys[i], skeys[j])))
                    if pair not in seen:
                        seen.add(pair)
                        finds.append(_f("F4_unit_alias", rel, "size", "×".join(pair), None, None,
                                        f"scale 別名(×{rt})=同物異鍵候選"))
                    break

    # F5|一 token 多欄位角色:code 角色 ∧ (priceBand|size|surface) 值角色並存。
    for tok in sorted(code_tokens):
        roles = other.get(tok)
        if roles:
            prov = next((p for t, _, p in code_roles if t == tok), None)
            finds.append(_f("F5_multi_role", rel, "code+" + "|".join(sorted(roles)), tok, prov,
                            rawf(prov), f"token {tok} 同時 code 與 {sorted(roles)} 角色"))

    # F3|系列標題跨頁錯續(info 啟發):≥2 個字首碼家族(各≥3)且頁域不相交=多系列一檔候選。
    fam_pages = defaultdict(set)
    fam_codes = defaultdict(set)
    for tok, role, prov in code_roles:
        pf = _prefix(tok)
        if pf:
            fam_codes[pf].add(tok)
            pg = (prov or {}).get("page")
            if pg:
                fam_pages[pf].add(pg)
    big = [pf for pf in fam_codes if len(fam_codes[pf]) >= 3 and fam_pages[pf]]
    for a in range(len(big)):
        for b in range(a + 1, len(big)):
            pa, pb = fam_pages[big[a]], fam_pages[big[b]]
            if pa and pb and (max(pa) < min(pb) or max(pb) < min(pa)):
                finds.append(_f("F3_series_split", rel, "seriesTitle",
                                f"{big[a]}|{big[b]}", None, None,
                                f"字首家族 {big[a]}(p{min(pa)}-{max(pa)}) 與 {big[b]}"
                                f"(p{min(pb)}-{max(pb)}) 頁域不相交=多系列一檔候選"))

    return finds


def scan_pool(pairs, max_items=20):
    tot = Counter()
    per_doc = defaultdict(Counter)
    for outdir, corpus in pairs:
        root = Path(outdir)
        for p in sorted(root.rglob("*.json")):
            if p.name.endswith((".review.json", ".capcodes.json")) or p.name.startswith("._"):
                continue
            rel = p.relative_to(root).as_posix()
            doc = json.loads(p.read_text())
            rawf = _make_rawf(corpus, p) if corpus else (lambda prov: None)
            finds = scan_doc(rel, doc, rawf)
            for f in finds:
                tot[f["cls"]] += 1
                per_doc[(outdir, rel)][f["cls"]] += 1
            for cls in sorted({f["cls"] for f in finds}):
                sub = [f for f in finds if f["cls"] == cls]
                print(f"\n## {outdir}/{rel} [{cls}] ×{len(sub)}")
                for f in sub[:max_items]:
                    print(f"   {f['field']}={f['token']!r} p{f['page']} bbox={f['bbox']} "
                          f"raw={f['raw']!r} {f['note']}")
                if len(sub) > max_items:
                    print(f"   …(+{len(sub) - max_items})")
    print("\n# 頻率表(全池)")
    for cls, n in sorted(tot.items()):
        docs = [k for k, c in per_doc.items() if c[cls]]
        print(f"  {cls}: {n} 筆 / {len(docs)} 檔")
    return tot, per_doc


def _make_rawf(corpus, json_path):
    """prov→raw 字串:開 <corpus>/<brand>/<pdf> 讀 bbox 交疊詞(cache 頁級)。"""
    cache = {}

    def rawf(prov):
        if not prov or not prov.get("bbox") or not prov.get("pdf"):
            return None
        pdf = Path(corpus) / json_path.parent.name / prov["pdf"]
        if not pdf.is_file():
            return None
        key = (prov["pdf"], prov["page"])
        if key not in cache:
            try:
                d = pipeline.fitz.open(pdf)
                cache[key] = d[prov["page"] - 1].get_text("words")
            except Exception:
                cache[key] = []
        x0, y0, x1, y1 = prov["bbox"]
        hit = [w for w in cache[key]
               if x0 - 1 <= (w[0] + w[2]) / 2 <= x1 + 1 and y0 - 1 <= (w[1] + w[3]) / 2 <= y1 + 1]
        return " ".join(w[4] for w in hit) or None

    return rawf


# ---------------- selftest(合成紅燈;鐵律7 實作前 RED)----------------

def _prov(page=1, bbox=(0, 0, 10, 10)):
    return {"pdf": "x.pdf", "page": page, "bbox": list(bbox), "method": "t"}


def selftest():
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(("PASS " if cond else "★RED ") + name)
        ok = ok and cond

    def doc_of(variants=(), rows=()):
        return {"series": [{"variants": list(variants), "specByCode": list(rows)}]}

    def row(code, size=None, surface=None, band=None, packing=None, page=1):
        return {"id": f"s:{page}:{code}", "code": code, "size": size, "surface": surface,
                "priceBand": band, "packing": packing, "prov": _prov(page)}

    def var(code, page=1, **kw):
        return {"code": code, "color": {"en": "GREY"}, "prov": _prov(page),
                "variantSizes": [], "mergedFrom": [], **kw}

    # AC-1|F1 A102 型:code=A102 形 ∧ 同檔 A 帶家族 ≥3 → high 逐筆
    d = doc_of([var("A102")], [row("M1", band="A11"), row("M2", band="A56"), row("M3", band="A86")])
    f = scan_doc("Emil/x.json", d, lambda p: None)
    chk("AC-1 F1 A102 型 high", any(x["cls"] == "F1_code_price_swap" and x["token"] == "A102" for x in f))
    # AC-1b|F1 對照:同形但無帶家族(Rice M961 真碼型)→ 不入 high(info 桶)
    d = doc_of([var("M961"), var("M962")], [row("M961"), row("M962")])
    f = scan_doc("Rice/x.json", d, lambda p: None)
    chk("AC-1b F1 無家族不誤旗", not any(x["cls"] == "F1_code_price_swap" for x in f))
    # AC-2|F1b 偽碼:pseudoCodeSuspect 旗 或 code=檔名子串
    d = doc_of([var("MILANO70", pseudoCodeSuspect=["MILANO70"])], [])
    f = scan_doc("41Zero42/MILANO70 Catalogo.json", d, lambda p: None)
    chk("AC-2 F1b 偽碼旗", any(x["cls"] == "F1b_pseudo_code" and x["token"] == "MILANO70" for x in f))
    # AC-3|F2 混欄:surface 帶包裝詞/數字、priceBand 非帶形、size 非尺寸形
    d = doc_of([], [row("C1", size="Right Box", surface="Tile Right Box 12", band="CARTON"),
                    row("C2", size="60x120", surface="Naturale", band="A11")])
    f = scan_doc("Emil/y.json", d, lambda p: None)
    chk("AC-3 F2 三欄形狀", {x["field"] for x in f if x["cls"] == "F2_field_mixing"}
        >= {"size", "surface", "priceBand"})
    chk("AC-3b F2 乾淨列不旗", not any(x["cls"] == "F2_field_mixing" and "C2" in x["note"] for x in f))
    # AC-4|F4 同鍵碰撞:同 normalized size ← 兩種 raw
    d = doc_of([], [row("C1", size="60x120", page=1), row("C2", size="60x120", page=2)])
    raws = {1: "60 X 120", 2: "600X1200 MM"}
    f = scan_doc("FMG/z.json", d, lambda p: raws.get(p["page"]))
    chk("AC-4 F4 同鍵多 raw", any(x["cls"] == "F4_unit_collision" for x in f))
    # AC-4b|F4 跨鍵 scale 別名:60x120 與 600x1200mm 並存
    d = doc_of([], [row("C1", size="60x120"), row("C2", size="600x1200mm")])
    f = scan_doc("FMG/w.json", d, lambda p: None)
    chk("AC-4b F4 scale 別名", any(x["cls"] == "F4_unit_alias" for x in f))
    # AC-5|F5 一 token 多角色:X100 同時為 code 與 priceBand
    d = doc_of([var("X100")], [row("M1", band="X100"), row("X100", size="60x120")])
    f = scan_doc("Prov/v.json", d, lambda p: None)
    chk("AC-5 F5 多角色", any(x["cls"] == "F5_multi_role" and x["token"] == "X100" for x in f))
    # AC-F3|系列標題跨頁錯續:兩字首家族(各≥3)頁域不相交 → F3_series_split
    d = doc_of([var("AAA1", page=1), var("AAA2", page=2), var("AAA3", page=3),
                var("BBB1", page=5), var("BBB2", page=6), var("BBB3", page=7)], [])
    f = scan_doc("Emil/multi.json", d, lambda p: None)
    chk("AC-F3 多系列一檔", any(x["cls"] == "F3_series_split" for x in f))
    # AC-6|非干涉:全乾淨檔 0 findings(單家族=不觸 F3)
    d = doc_of([var("MFFE")], [row("MFFE", size="60x120", surface="Naturale", band="A11",
                                   packing={"pcsBox": "6"})])
    f = scan_doc("Marazzi/clean.json", d, lambda p: "60X120")
    chk("AC-6 乾淨檔零旗", not f)
    print("field_prov_scan selftest " + ("OK" if ok else "=RED(未實作/失敗)"))
    return ok


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    args = [a for a in sys.argv[1:] if not a.startswith("--max")]
    mx = 20
    for a in sys.argv[1:]:
        if a.startswith("--max"):
            mx = int(a.split("=")[1])
    pairs = []
    for a in args:
        od, _, cp = a.partition("=")
        pairs.append((od, cp or None))
    if not pairs:
        sys.exit(__doc__)
    scan_pool(pairs, mx)
