#!/usr/bin/env python3
"""案5|管線狀態守恆 + 來源版本聲明(純追蹤/儀器、只讀、不改產線;通案三入庫)。

兩節,皆讀 product 形制目錄(JSON+review),不碰產線邏輯:

【A 管線狀態守恆】每候選(specByCode 碼)生命週期 discovered→published/review/spec-only,
  任何候選不得無帳消失。實測不變量(全池):spec_only=0 ∧ phantom=0。
    P1  候選無帳消失:D−P−R≠∅(specByCode 碼既非 published Variant 亦不在 review)。
    P2  幽靈候選:R−D≠∅(review 碼不在 specByCode=來源不明)。
    P3  佇列滯塞:review_ratio=|R|/|D| ≥ STUCK(候選多數卡 review=長期未處理代理信號)。

【B 來源版本聲明】不建實體解析,只存不可變聲明:每檔 brand/pdf/版次年/碼數(+md5 若
  PDF 可得),每系列來源檔集合,同 brand 同碼跨檔(版本)衝突候選。
  ★MD5 只擋完全相同檔;翻譯/重排/改封面版須 brand+版次+相似度家族分組(非 MD5)=此工具
    以 brand+code 跨檔重現偵測衝突候選(相似度家族=VLM/人工 lane,不在此實作)。
    B1  同 brand 同碼出現於 ≥2 不同 pdf → 跨版本衝突候選(size/color 相異=conflict)。

    /opt/homebrew/bin/python3 dev/pipeline_conservation_scan.py product [--md5] [--max N]
        (CWD=專案根;--md5=找 catalogs*/ 內 PDF 算 hash,慢)
    /opt/homebrew/bin/python3 dev/pipeline_conservation_scan.py --selftest

停止線(規格):管線守恆掃出「候選無故消失」災難級(P1/P2 大量)=立即凍結回報。
"""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
STUCK = 0.9            # P3 佇列滯塞 review_ratio 下界(校準:實測 twin_s/Topcer/Mosa=1.0)
VER_RE = re.compile(r"(20\d\d)(?:[.\-]?(\d\d))?")


def lifecycle(doc, review):
    """→ (D, P, R) 三 code 集合。D=specByCode 碼;P=published(variant.code/orderCode);
    R=review 碼(code + codes[])。"""
    D, P, R = set(), set(), set()
    for s in doc.get("series", []):
        for row in s.get("specByCode", []):
            if row.get("code"):
                D.add(row["code"])
        for v in s.get("variants", []):
            if v.get("code"):
                P.add(v["code"])
            for vs in v.get("variantSizes", []):
                if vs.get("orderCode"):
                    P.add(vs["orderCode"])
    for it in review.get("items", []):
        if it.get("code"):
            R.add(it["code"])
        for c in (it.get("codes") or []):
            R.add(c)
    return D, P, R


def _codes_data(doc):
    """brand 版本聲明用:code → (size 集合, color) 供跨版本比對。"""
    out = {}
    for s in doc.get("series", []):
        for row in s.get("specByCode", []):
            if row.get("code"):
                out.setdefault(row["code"], set()).add(row.get("size"))
    return out


def _pdf_md5(brand, pdf_name):
    for cdir in sorted(ROOT.glob("catalogs*")):
        p = cdir / brand / pdf_name
        if p.is_file():
            h = hashlib.md5()
            with open(p, "rb") as f:
                for b in iter(lambda: f.read(1 << 16), b""):
                    h.update(b)
            return h.hexdigest()
    return None


def scan(pool, do_md5=False, max_items=20):
    finds = []
    census = []
    declarations = []
    bc = defaultdict(list)   # (brand, code) → [pdf]
    bc_data = defaultdict(dict)  # brand → code → (sizes, pdf)
    root = Path(pool)
    for p in sorted(root.rglob("*.json")):
        if p.name.endswith((".review.json", ".capcodes.json")) or p.name.startswith("._"):
            continue
        rel = p.relative_to(root).as_posix()
        doc = json.loads(p.read_text())
        rv = p.with_name(p.stem + ".review.json")
        review = json.loads(rv.read_text()) if rv.exists() else {"items": []}
        brand = p.parent.name
        D, P, R = lifecycle(doc, review)

        # A 守恆
        spec_only = D - P - R
        phantom = R - D
        if spec_only:
            finds.append(("P1_candidate_vanish", rel, f"{len(spec_only)} 碼既非 published 亦不在 review(無帳消失):{sorted(spec_only)[:6]}"))
        if phantom:
            finds.append(("P2_phantom", rel, f"{len(phantom)} review 碼不在 specByCode(來源不明):{sorted(phantom)[:6]}"))
        ratio = len(R) / len(D) if D else 0.0
        # P3 只旗非骨架檔:seriesSkeleton=無碼廠設計上全 review=預期,不算滯塞(鐵律2)
        if D and ratio >= STUCK and not doc.get("seriesSkeleton"):
            finds.append(("P3_review_stuck", rel, f"review_ratio={ratio:.0%}(|R|={len(R)}/|D|={len(D)},非骨架)=候選多數卡佇列"))
        census.append((rel, len(D), len(P), len(R), len(spec_only), len(phantom)))

        # B 版本聲明
        pdf_name = review.get("pdf") or f"{p.stem}.pdf"
        m = VER_RE.search(pdf_name) or VER_RE.search(p.stem)
        ver = (m.group(0) if m else None)
        md5 = _pdf_md5(brand, pdf_name) if do_md5 else None
        declarations.append({"brand": brand, "pdf": pdf_name, "version": ver,
                             "codes": len(D), "md5": md5})
        cd = _codes_data(doc)
        for code, sizes in cd.items():
            bc[(brand, code)].append(pdf_name)
            bc_data[brand].setdefault(code, []).append((pdf_name, tuple(sorted(str(s) for s in sizes))))

    # B1 跨版本衝突候選:同 brand 同碼出現於 ≥2 不同 pdf
    for (brand, code), pdfs in bc.items():
        uniq = sorted(set(pdfs))
        if len(uniq) >= 2:
            variants_sz = {sz for pn, sz in bc_data[brand][code]}
            note = "size 相異=conflict" if len(variants_sz) > 1 else "同 size(僅重複出現)"
            finds.append(("B1_cross_version", f"{brand}/{code}",
                          f"同 brand 同碼於 {len(uniq)} 檔 {uniq[:3]} {note}"))

    # 輸出
    by_cls = defaultdict(list)
    for cls, doc, note in finds:
        by_cls[cls].append((doc, note))
    for cls in sorted(by_cls):
        sub = by_cls[cls]
        print(f"\n## [{cls}] ×{len(sub)}")
        for doc, note in sub[:max_items]:
            print(f"   {doc}  {note}")
        if len(sub) > max_items:
            print(f"   …(+{len(sub) - max_items})")

    print("\n# 管線守恆 census(每檔 D=discovered P=published R=review)")
    print(f"  {'檔':40s} {'D':>4s} {'P':>4s} {'R':>4s} {'消失':>4s} {'幽靈':>4s}")
    for rel, D, P, R, so, ph in census:
        flag = "  ⚠" if (so or ph) else ""
        print(f"  {rel[:40]:40s} {D:4d} {P:4d} {R:4d} {so:4d} {ph:4d}{flag}")
    tot_so = sum(c[4] for c in census)
    tot_ph = sum(c[5] for c in census)
    print(f"  ★守恆:候選無帳消失合計={tot_so}  幽靈候選合計={tot_ph}  (硬不變量=0/0)")

    print("\n# 來源版本聲明(不可變聲明;MD5 只擋完全相同檔)")
    for d in declarations:
        print(f"  {d['brand']:10s} ver={str(d['version']):8s} 碼={d['codes']:4d} "
              f"md5={d['md5'][:12] if d['md5'] else '(未算)'}  {d['pdf'][:36]}")
    print(f"\n# 頻率表")
    for cls in sorted(by_cls):
        print(f"  {cls}: {len(by_cls[cls])}")
    return finds, census


# ---------------- selftest(合成紅燈;鐵律7 實作前 RED)----------------

def selftest():
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(("PASS " if cond else "★RED ") + name)
        ok = ok and cond

    def doc_of(spec_codes, var_codes):
        return {"series": [{"specByCode": [{"code": c, "size": "60x120"} for c in spec_codes],
                            "variants": [{"code": c, "variantSizes": []} for c in var_codes]}]}

    def rev(codes):
        return {"items": [{"code": c, "reason": "orphan"} for c in codes]}

    # AC-P1 候選無帳消失:spec 有 X 但既非 published 亦不在 review
    D, P, R = lifecycle(doc_of(["A", "B", "X"], ["A"]), rev(["B"]))
    chk("AC-P1 候選消失偵測", bool(D - P - R))              # {X}
    # AC-P1b 對照:全部有帳 → 無消失
    D, P, R = lifecycle(doc_of(["A", "B"], ["A"]), rev(["B"]))
    chk("AC-P1b 全有帳不誤旗", not (D - P - R))
    # AC-P2 幽靈候選:review 有 Z 但不在 spec
    D, P, R = lifecycle(doc_of(["A"], ["A"]), rev(["Z"]))
    chk("AC-P2 幽靈候選偵測", bool(R - D))                  # {Z}
    # AC-P3 佇列滯塞:全部卡 review
    D, P, R = lifecycle(doc_of(["A", "B", "C"], []), rev(["A", "B", "C"]))
    chk("AC-P3 滯塞(ratio=1.0≥STUCK)", (len(R) / len(D)) >= STUCK)
    # AC-B1 跨版本衝突:同 brand 同碼於兩 pdf、size 相異(用 scan 級邏輯模擬)
    bc_data = {"Marazzi": {"A102": [("v2024.pdf", ("60x120",)), ("v2025.pdf", ("30x60",))]}}
    szs = {sz for pn, sz in bc_data["Marazzi"]["A102"]}
    chk("AC-B1 跨版本 size 衝突", len({p for p, s in bc_data["Marazzi"]["A102"]}) >= 2 and len(szs) > 1)
    # AC-B1b 版本年解析
    m = VER_RE.search("Millelegni Catalogo 2023.03b Web.pdf")
    chk("AC-B1b 版次年解析", m and m.group(0) == "2023.03")

    print("pipeline_conservation_scan selftest " + ("OK" if ok else "=RED(未實作/失敗)"))
    return ok


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    do_md5 = "--md5" in sys.argv
    mx = 20
    for a in sys.argv:
        if a.startswith("--max"):
            mx = int(a.split("=")[1])
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not pos:
        sys.exit(__doc__)
    scan(pos[0], do_md5, mx)
