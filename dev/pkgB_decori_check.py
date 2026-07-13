#!/usr/bin/env python3
"""包 B｜附帶查證:指定頁半邊的碼偵測/綁定逐筆下場(只讀,不改規則)。

    /opt/homebrew/bin/python3 dev/pkgB_decori_check.py <corpus> <stem子字串> <頁> [left|right|all]

用途(使用者親驗發現):UniqueMarble p16 左頁 Decori(MOSAICO 3X3/ARROWS 馬賽克樣,
EL63/EL65/EL66… 每款一色樣+EL 編號)偵測層下場逐筆——(a) 碼有偵測+綁定 vs (b) 漏抓。
判「拼磚/馬賽克頁型 VLM 洞」還是「幾何可救漏抓」的材料。鏡射 extract_pdf(V=12)真值:
codes_doc(含哪些碼進候選)、bindings(綁定=偵測到色樣+x對齊/塊綁)、review(漏/降級原因)。
逐筆印該半邊每個 code_candidate 實例:狀態=bound/orphan/not_x_aligned/icon_demoted/
未進候選(codes_doc 外);另印該半邊偵測到的色樣數。
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import fitz                                          # noqa: E402
import pipeline                                      # noqa: E402
from census import SIZE_RE                           # noqa: E402
from m1_scan import CODE_RE, norm                    # noqa: E402
from m2_scan import code_candidates                  # noqa: E402
from spike_geom import extract_swatches              # noqa: E402


def main(corpus, sub, pno, half):
    pipeline.V = 12
    cv, av = pipeline.build_vocabs()
    pdf = next(p for p in sorted(Path(corpus).rglob("*.pdf"))
               if not p.name.startswith("._") and sub.lower() in p.stem.lower())
    doc = fitz.open(pdf)
    spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
    cd = code_candidates(doc, cv, len(spec), 12, av)
    codes_doc = cd[0] if isinstance(cd, tuple) else cd
    json_doc, review, _, _ = pipeline.extract_pdf(pdf, (cv, av))
    # 綁定碼詞位置(prov.bbox 左上角)、佇列碼詞位置+原因
    bound = {(round(m["prov"]["bbox"][0], 1), round(m["prov"]["bbox"][1], 1))
             for v in json_doc["series"][0]["variants"] for m in v["mergedFrom"]
             if m["prov"]["page"] == pno and m["prov"]["bbox"]}
    rv = {(round(it["prov"]["bbox"][0], 1), round(it["prov"]["bbox"][1], 1)): it["reason"]
          for it in review if it.get("prov", {}).get("page") == pno and it["prov"].get("bbox")}

    page = doc[pno - 1]
    mid = page.rect.width / 2
    in_half = lambda x0: half == "all" or (x0 < mid) == (half == "left")  # noqa: E731
    sws = [r for r in extract_swatches(page, version=3) if in_half(r.x0)]
    print(f"# {pdf.stem} p{pno} {half} 半邊(mid_x={mid:.0f}):偵測色樣={len(sws)}")
    print(f"# {'code':<10} x0    狀態")
    stat, seen = Counter(), set()
    for w in page.get_text("words"):
        t = norm(w[4])
        if not in_half(w[0]) or (round(w[0], 1), round(w[1], 1)) in seen:
            continue
        if not (CODE_RE.match(t) and any(c.isdigit() for c in t)
                and any(c.isalpha() for c in t) and not SIZE_RE.search(t)):
            continue
        key = (round(w[0], 1), round(w[1], 1))
        seen.add(key)
        if t not in codes_doc:
            st = "未進候選(codes_doc外=偵測層漏)"
        elif key in bound:
            st = "bound(偵測色樣+綁定)"
        elif key in rv:
            st = f"佇列:{rv[key]}"
        else:
            st = "?候選但無綁定/佇列紀錄"
        stat[st.split("(")[0].split(":")[0].rstrip("佇列")] += 1
        print(f"  {t:<10} {w[0]:>5.0f}  {st}")
    print(f"# 統計:{dict(stat)}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]),
         sys.argv[4] if len(sys.argv) > 4 else "left")
