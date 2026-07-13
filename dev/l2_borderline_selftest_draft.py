#!/usr/bin/env python3
"""案1 零邊際合併權限合成紅燈(外審修正案;鐵律7 紅燈先行→實作→轉綠)。

    /opt/homebrew/bin/python3 dev/l2_borderline_selftest_draft.py   (CWD=專案根)

外審裁決:sub-20 真塌縮(A02G-18/Topcer General-19/Uniche-19)與合法團在 size 軸
零邊際([19,20] 相鄰)→ 正解=撤銷自動合併權限,非找新判別器。三段防線(assemble):
  ①既有 跨頁∧衝突∧≥L2_COLLAPSE_MIN(20) → assembly_collapse_suspect(不動)
  ②新 跨頁∧衝突∧[L2_BORDERLINE_MIN,20) → borderline_merge_suspect(不硬判塌縮/合法)
  ③新 跨頁∧(pages>L2_AUTO_MERGE_MAX_PAGES ∨ mergedFrom>L2_AUTO_MERGED_FROM_MAX)
     → assembly_merge_radius_suspect(爆炸半徑;單頁域歸段1守衛不碰)
常數校準=dev/assembly_probe.py --borderline 全7語料×v12/v13(l2_borderline_merge_ledger.md)。
基線(實作前)RED:AC-1/1b/3/4(現行出 Variant);AC-2/5/6 恆綠(合法側+非干涉)。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))
import pipeline  # noqa: E402

P = {"pdf": "t.pdf", "page": 1, "bbox": [0, 0, 1, 1], "method": "t"}


def B(k, code, sw, color=None, page=1):
    return {"id": f"b:{page}:{k}", "code": code,
            "swatch": {"page": page, "bbox": sw}, "color": color, "prov": P}


def hub_bindings(n_codes, color_p1="RED", color_p2="BLUE"):
    """hub 色樣(p1 掛 n_codes 碼)+各碼再現 p2 → 2*n_codes 綁定跨 2 頁單一 cluster。"""
    swH = [0, 0, 100, 100]
    return ([B(k, f"X{k}", swH, color_p1, page=1) for k in range(n_codes)]
            + [B(n_codes + k, f"X{k}", [10 * k, 0, 10 * k + 9, 9], color_p2, page=2)
               for k in range(n_codes)])


def chain_bindings(n_pages, color="RED"):
    """同色鏈:每頁一色樣 S_i,碼 Ci 綁 S_i 與 S_{i+1}(共享實例→union 連通)
    → 2*(n_pages-1) 綁定跨 n_pages 頁單一 cluster。"""
    bs, k = [], 0
    for i in range(1, n_pages):
        bs.append(B(k, f"C{i}", [0, 0, 9, 9], color, page=i)); k += 1
        bs.append(B(k, f"C{i}", [0, 0, 9, 9], color, page=i + 1)); k += 1
    return bs


def run():
    N = getattr(pipeline, "L2_COLLAPSE_MIN", 20)
    LO = getattr(pipeline, "L2_BORDERLINE_MIN", 18)
    MXP = getattr(pipeline, "L2_AUTO_MERGE_MAX_PAGES", 5)
    MXM = getattr(pipeline, "L2_AUTO_MERGED_FROM_MAX", 24)
    fails = []

    def check(tag, ok):
        print(f"{tag} -> {'PASS' if ok else 'RED'}")
        if not ok:
            fails.append(tag.split("|")[0].strip())

    # AC-1|19 綁定跨頁∧衝突(Topcer/Uniche-19 型)→ 整團 borderline_merge_suspect、0 Variant
    bs = hub_bindings(10)[:-1]  # 19 綁定(掉 1 個 p2 綁定,hub 連通不變)
    vs, rv, st = pipeline.assemble(bs, [], [])
    dem = [r for r in rv if r["reason"] == "borderline_merge_suspect"]
    conserved = sum(len(v["mergedFrom"]) for v in vs) + sum(
        1 for r in rv if r["reason"].endswith("_suspect")) == len(bs)
    check(f"AC-1 |19 綁定次臨界降級: demoted={len(dem)}/19 Variant={len(vs)} 守恆={conserved}",
          len(dem) == 19 and not vs and conserved
          and st.get("assembly_borderline_demoted") == 19
          and all(r["swatch"] and r["prov"] for r in dem))

    # AC-1b|18 綁定(A02G-18 型;=T27 AC-3 原案例,語意翻轉)→ 降級
    vs, rv, st = pipeline.assemble(hub_bindings(9), [], [])
    dem = [r for r in rv if r["reason"] == "borderline_merge_suspect"]
    check(f"AC-1b|18 綁定次臨界降級: demoted={len(dem)}/18 Variant={len(vs)}",
          len(dem) == 18 and not vs)

    # AC-2|下緣外合法衝突團(16 綁定=Level CG Light 型)→ 不動、仍走 code_color_conflict
    vs, rv, st = pipeline.assemble(hub_bindings(8), [], [])
    check(f"AC-2 |16 綁定合法衝突不動: borderline={st.get('assembly_borderline_demoted', 0)}(期望0) "
          f"code_color_conflict={sum(r['reason'] == 'code_color_conflict' for r in rv)}(期望≥1)",
          st.get("assembly_borderline_demoted", 0) == 0
          and any(r["reason"] == "code_color_conflict" for r in rv))

    # AC-3|同色鏈跨 MXP+1 頁(無衝突→band/塌縮皆照不到)→ assembly_merge_radius_suspect
    bs = chain_bindings(MXP + 1)
    vs, rv, st = pipeline.assemble(bs, [], [])
    dem = [r for r in rv if r["reason"] == "assembly_merge_radius_suspect"]
    check(f"AC-3 |跨 {MXP + 1} 頁超半徑降級: demoted={len(dem)}/{len(bs)} Variant={len(vs)}",
          len(dem) == len(bs) and not vs
          and st.get("assembly_merge_radius_demoted") == len(bs))

    # AC-4|同色 2 頁 MXM+2 綁定(hub 過併但無衝突)→ 超半徑降級
    bs = hub_bindings((MXM + 2) // 2, "RED", "RED")
    vs, rv, st = pipeline.assemble(bs, [], [])
    dem = [r for r in rv if r["reason"] == "assembly_merge_radius_suspect"]
    check(f"AC-4 |{len(bs)} 綁定超半徑降級: demoted={len(dem)}/{len(bs)} Variant={len(vs)}",
          len(dem) == len(bs) and not vs)

    # AC-5|校準上界本身=合法(同色 2 頁 MXM 綁定;同色 MXP 頁鏈)→ 皆不動
    _, rv5a, st5a = pipeline.assemble(hub_bindings(MXM // 2, "RED", "RED"), [], [])
    _, rv5b, st5b = pipeline.assemble(chain_bindings(MXP), [], [])
    check(f"AC-5 |上界合法不動: {MXM} 綁定/2頁 radius={st5a.get('assembly_merge_radius_demoted', 0)}"
          f" {MXP} 頁鏈 radius={st5b.get('assembly_merge_radius_demoted', 0)}(皆期望0)",
          st5a.get("assembly_merge_radius_demoted", 0) == 0
          and st5b.get("assembly_merge_radius_demoted", 0) == 0)

    # AC-6|非干涉:≥N 跨頁衝突仍 assembly_collapse_suspect(band 不搶);單頁域 radius 不碰
    _, rv6, st6 = pipeline.assemble(hub_bindings(10), [], [])
    sp = [B(k, f"S{k}", [0, 0, 50, 50], "RED", page=1) for k in range(MXM + 2)]  # 單頁 hub
    _, rv6b, st6b = pipeline.assemble(sp, [], [])  # 單頁 MXM+2 綁定、無 page_dims
    check(f"AC-6 |非干涉: ≥{N} 仍塌縮守衛={st6.get('assembly_collapse_demoted', 0)}/20 "
          f"單頁 radius={st6b.get('assembly_merge_radius_demoted', 0)}(期望0)",
          st6.get("assembly_collapse_demoted", 0) == 20
          and st6.get("assembly_borderline_demoted", 0) == 0
          and st6b.get("assembly_merge_radius_demoted", 0) == 0)

    print("=" * 40)
    print(f"案1 紅燈: {'全綠(落地後)' if not fails else 'RED 待實作: ' + ','.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
