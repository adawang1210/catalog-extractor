#!/usr/bin/env python3
"""段1 單頁過併守衛合成紅燈(鐵律7 紅燈先行→實作後轉綠;core 零改動)。

判別子(審查方核可):單頁 cluster ∧ mergedFrom≥L2_COLLAPSE_MIN ∧ 主色樣 area%≥AREA_T(=5.0)
→ 整團降級佇列 reason=singlepage_overmerge_suspect(帶 prov/swatch 無損)。area% 經 page_dims
(頁號→頁面積)算:主色樣=cluster 內最大色樣 bbox 佔頁面積%。

  AC-1 單頁 hub 大 area% ∧ ≥N → 整團降級、0 逃逸、守恆、資料無損
  AC-2 對偶|單頁 ≥N 但 area% < AREA_T(小色片)→ 不動(area% 承重)
  AC-3 對偶|單頁大 area% 但 <N 綁定 → 不動(未達 N)
  AC-4 對偶|跨頁同色大 area% ≥N → 單頁守衛不越界 ∧ 跨頁守衛同色不動(兩守衛皆不誤動)
精華待併 pipeline selftest T28。實作前跑=RED(AREA_T/page_dims 未實作)。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402

P = {"pdf": "t.pdf", "page": 1, "bbox": [0, 0, 1, 1], "method": "t"}
swH = [0, 0, 100, 100]        # area=10000
PAGE_AREA = {1: 100000.0, 2: 100000.0}  # swH area%=10.0(≥AREA_T);小色片見 AC-2


def B(k, code, sw, color=None, page=1):
    return {"id": f"b:{page}:{k}", "code": code,
            "swatch": {"page": page, "bbox": sw}, "color": color, "prov": P}


def sp_hub(n, sw=swH, color="GREY"):
    """單頁 hub:n 碼全掛同一色樣(page1)→ union 成單頁單 cluster。"""
    return [B(k, f"X{k}", sw, color, page=1) for k in range(n)]


def run():
    N = pipeline.L2_COLLAPSE_MIN
    A = pipeline.AREA_T
    assert A == 5.0, f"AREA_T 凍結=5.0,實得 {A}"
    # AC-1 單頁 hub 大 area% ∧ ≥N → 降級
    vs, rv, st = pipeline.assemble(sp_hub(N), [], [], page_dims=PAGE_AREA)
    dem = [r for r in rv if r["reason"] == "singlepage_overmerge_suspect"]
    assert len(dem) == N and st["singlepage_overmerge_demoted"] == N \
        and st["singlepage_overmerge_clusters"] == 1, "AC-1 降級"
    assert st.get("singlepage_escaped", 0) == 0, "AC-1 零逃逸"
    assert sum(len(v["mergedFrom"]) for v in vs) + len(dem) == N, "AC-1 守恆"
    assert all(r["swatch"] and r["prov"] for r in dem), "AC-1 資料無損"
    print("AC-1 PASS 單頁過併降級")
    # AC-2 小 area%(20x20=400 → 0.4%)→ 不動
    _, _, st2 = pipeline.assemble(sp_hub(N, sw=[0, 0, 20, 20]), [], [], page_dims=PAGE_AREA)
    assert st2["singlepage_overmerge_demoted"] == 0, "AC-2 小area%不動"
    print("AC-2 PASS 小area%不動")
    # AC-3 未達 N(N-1 綁定)→ 不動
    _, _, st3 = pipeline.assemble(sp_hub(N - 1), [], [], page_dims=PAGE_AREA)
    assert st3["singlepage_overmerge_demoted"] == 0, "AC-3 未達N不動"
    print("AC-3 PASS 未達N不動")
    # AC-4 跨頁同色大 area% ≥N(page1+page2 各 12,同碼橋接成單一 24 綁定跨頁 cluster;
    #     案1 後自 2N=40 縮 24=半徑上界內,保持「兩守衛皆不誤動」原意)
    cross = sp_hub(12) + [B(12 + k, f"X{k}", swH, "GREY", page=2) for k in range(12)]
    _, _, st4 = pipeline.assemble(cross, [], [], page_dims=PAGE_AREA)
    assert st4["singlepage_overmerge_demoted"] == 0, "AC-4 單頁守衛不越界(跨頁)"
    assert st4["assembly_collapse_demoted"] == 0, "AC-4 跨頁守衛同色不動"
    assert st4.get("assembly_merge_radius_demoted", 0) == 0, "AC-4 半徑上界內不動"
    print("AC-4 PASS 跨頁/同色雙不動")
    print("singlepage_overmerge selftest OK")


if __name__ == "__main__":
    run()
