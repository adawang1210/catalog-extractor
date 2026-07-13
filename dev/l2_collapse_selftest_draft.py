#!/usr/bin/env python3
"""L2 塌縮守衛合成紅燈(工作包#7 緊急補丁;鐵律7 紅燈先行→實作→轉綠)。

    /opt/homebrew/bin/python3 dev/l2_collapse_selftest_draft.py   (CWD=專案根)

守衛=cluster 層後驗塌縮簽名:跨頁(≥2)∧色名衝突(len(colors)>1 or len(raws)>1)
∧ mergedFrom≥L2_COLLAPSE_MIN(=20,校準見 l2_collapse_design.md/emergency 節)
→ 整團降級佇列 assembly_collapse_suspect、不出 Variant(失敗方向=寧不合併)。
基線=守衛 OFF(RED:塌縮團出成 1 color=None Variant、0 降級);落地=GREEN。
AC-1 塌縮降級 / AC-2 無衝突大合併不動 / AC-3 未達 N 不動 / AC-4 SL-6 併行不重複。
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


def collapse_bindings(n_codes=10, color_p1="RED", color_p2="BLUE"):
    """hub 色樣(p1 掛 n_codes 碼)+ 各碼再現於 p2 自有色樣(橋接)→ 單一連通 cluster。
    2*n_codes 綁定、跨 2 頁;color_p1≠color_p2 → 色名衝突。"""
    swH = [0, 0, 100, 100]
    bs, k = [], 0
    for i in range(n_codes):
        bs.append(B(k, f"X{i}", swH, color_p1, page=1)); k += 1
    for i in range(n_codes):
        bs.append(B(k, f"X{i}", [10 * i, 0, 10 * i + 9, 9], color_p2, page=2)); k += 1
    return bs


def is_collapse_variant(v, n):
    pages = {m["swatch"]["page"] for m in v["mergedFrom"]}
    return len(pages) >= 2 and v["color"]["en"] is None and len(v["mergedFrom"]) >= n


def run():
    N = getattr(pipeline, "L2_COLLAPSE_MIN", 20)
    fails = []

    # AC-1|注入救回塌縮(20 綁定跨 2 頁∧衝突)→ 整團降級、0 塌縮 Variant
    bs = collapse_bindings(10)  # 20 綁定
    vs, rv, st = pipeline.assemble(bs, [], [])
    dem = [r for r in rv if r["reason"] == "assembly_collapse_suspect"]
    ac1 = (len(dem) == 20 and all(r["swatch"] and r["prov"] for r in dem)
           and not any(is_collapse_variant(v, N) for v in vs)
           and st.get("assembly_collapse_demoted") == 20)
    # 守恆:進 Variant 綁定 + 降級 = 原始總數
    conserved = sum(len(v["mergedFrom"]) for v in vs) + len(dem) == len(bs)
    print(f"AC-1 塌縮降級: demoted={len(dem)}/20 塌縮Variant={sum(is_collapse_variant(v,N) for v in vs)} 守恆={conserved} -> {'PASS' if ac1 and conserved else 'RED'}")
    if not (ac1 and conserved):
        fails.append("AC-1")

    # AC-2|無色名衝突之大跨頁合併(20 綁定同色)→ 不動(守衛需正面衝突證據)
    bs = collapse_bindings(10, "RED", "RED")  # 20 綁定、同色→無衝突
    vs, rv, st = pipeline.assemble(bs, [], [])
    dem = [r for r in rv if r["reason"] == "assembly_collapse_suspect"]
    ac2 = len(dem) == 0 and st.get("assembly_collapse_demoted", 0) == 0
    print(f"AC-2 無衝突大合併不動: demoted={len(dem)}(期望0) -> {'PASS' if ac2 else 'RED'}")
    if not ac2:
        fails.append("AC-2")

    # AC-3|未達下緣之跨頁衝突團(16 綁定=Level CG Light 型保護)→ 不動
    #     (原 18 綁定案例經案1 語意翻轉=帶內降級,移 dev/l2_borderline_selftest_draft)
    bs = collapse_bindings(8)  # 16 綁定<L2_BORDERLINE_MIN(18)
    vs, rv, st = pipeline.assemble(bs, [], [])
    dem = [r for r in rv if r["reason"] in ("assembly_collapse_suspect",
                                            "borderline_merge_suspect")]
    conf = [r for r in rv if r["reason"] == "code_color_conflict"]
    ac3 = len(dem) == 0 and len(conf) >= 1  # 未降級、仍走既有 code_color_conflict
    print(f"AC-3 未達下緣不動: demoted={len(dem)}(期望0) code_color_conflict={len(conf)}(期望≥1) -> {'PASS' if ac3 else 'RED'}")
    if not ac3:
        fails.append("AC-3")

    # AC-4|SL-6(A102)併行:單頁列向嵌合→SL-6 降級 2、新守衛不重複觸發(單頁→非塌縮)
    sw1, sw2 = [0, 0, 10, 10], [20, 0, 30, 10]
    bs = [B(0, "A991", sw1), B(1, "MX1A", sw1),
          B(2, "A991", sw2), B(3, "MX2B", sw2)]
    vs, rv, st = pipeline.assemble(bs, [], [], {"A"})
    mks = [r for r in rv if r["reason"] == "merge_key_suspect"]
    acd = [r for r in rv if r["reason"] == "assembly_collapse_suspect"]
    ac4 = len(mks) == 2 and len(acd) == 0 and st.get("d_demoted") == 2
    print(f"AC-4 SL-6併行不重複: merge_key_suspect={len(mks)}(期望2) assembly={len(acd)}(期望0) -> {'PASS' if ac4 else 'RED'}")
    if not ac4:
        fails.append("AC-4")

    print("=" * 40)
    print(f"L2 塌縮守衛紅燈: {'全綠(落地後)' if not fails else 'RED 待實作: ' + ','.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
