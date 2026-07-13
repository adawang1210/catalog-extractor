#!/usr/bin/env python3
"""S2-1(v8)合成案例草稿(scratchpad,session 級;票=BACKLOG S2-1,案例清單
v1 經審查方核可 2026-07-11)。紅燈流程:實作前 P 案必紅,實作後全綠;
定案後精華案例進 m3_scan 官方 selftest。

    /opt/homebrew/bin/python3 s21_selftest_draft.py

v8 合約(受測):code_candidates(doc, code_vocab, n_spec, 8, alpha_vocab=…)
全字母 token 升格候選須同時過:①形(CODE_RE∧isalpha∧不在 alpha_vocab 停用詞)
②錨 per-page(同頁 kept 錨詞 x0 欄帶對齊)③同列有尺寸 ④長度=錨碼眾數
+occ 比值擋(含尺寸列數/occ 高頻=finish 縮寫、系列詞→不收)
+小表下限(檔內含尺寸列 < R_MIN=3 → 分支不啟動)。往嚴偏:零誤收第一。
"""
import sys
from pathlib import Path

ROOT = Path("/Volumes/USB DISK/catalog-extractor")
sys.path.insert(0, str(ROOT / "core"))

import fitz

from m2_scan import BAND_RE, SIZE_LEAK_RE, THICK_RE, UNIT_RE, code_candidates


def mkdoc(*pages):
    doc = fitz.open()
    for words in pages:
        pg = doc.new_page(width=600, height=800)
        for x, y, t in words:
            pg.insert_text((x, y), t, fontsize=10)
    return doc


def cc(doc, version=8, av=frozenset()):
    """v8 呼叫(alpha_vocab 停用詞補充);實作前無此參數→退回舊簽名(紅燈期)。"""
    try:
        kept, _ = code_candidates(doc, set(), 1, version, alpha_vocab=av)
    except TypeError:
        kept, _ = code_candidates(doc, set(), 1, version)
    return kept


def rows(*items, x=300, sx=450, y0=100, dy=25):
    """每 item 一列:token@x + 尺寸@sx(None=該列無尺寸)。"""
    out = []
    for k, (t, size) in enumerate(items):
        y = y0 + dy * k
        if t:
            out.append((x, y, t))
        if size:
            out.append((sx, y, size))
    return out


def p1():  # 錨定基本型:2 錨+2 全字母同欄同長同列尺寸 → 全收
    doc = mkdoc(rows(("MMD2", "60x120"), ("MMD4", "60x120"),
                     ("MFFF", "60x120"), ("MFFG", "60x120")))
    k = cc(doc)
    assert {"MFFF", "MFFG"} <= k, k
    assert {"MMD2", "MMD4"} <= k, k


def p2():  # 單錨救多(Treverkmood 型):1 錨+4 全字母
    doc = mkdoc(rows(("MLN2", "20x120"), ("MLNM", "20x120"), ("MLNN", "20x120"),
                     ("MLNP", "20x120"), ("MLNL", "20x120")))
    k = cc(doc)
    assert {"MLNM", "MLNN", "MLNP", "MLNL"} <= k, k


def p3():  # 色名鍵值頁(Emil p15 型):錨欄家族收;他欄同長色名不收
    words = rows(("E1Z2", "60x60"), ("E2Z3", "60x60"),
                 ("EKDM", "60x60"), ("ECXU", "60x60"))
    words += [(100, 100 + 25 * k, c) for k, c in
              enumerate(["AVIO", "MUSK", "PERA", "NOCE"])]   # 左欄色名,列有尺寸
    k = cc(mkdoc(words))
    assert {"EKDM", "ECXU"} <= k, k
    assert not k & {"AVIO", "MUSK", "PERA", "NOCE"}, k


def t1():  # 列首色名:色樣欄 x(遠離錨欄)→ 不收
    words = rows(("MMD2", "60x120"), ("MMD3", "60x120"), ("MFFF", "60x120"))
    words += [(60, 100, "MUSK"), (60, 125, "MOKA")]
    k = cc(mkdoc(words))
    assert not k & {"MUSK", "MOKA"}, k
    assert "MFFF" in k, k


def t2():  # 表頭詞:CODICE 欄頂同 x0(該列無尺寸+長度≠眾數)→ 不收
    words = [(300, 70, "CODICE")] + rows(("MMD2", "60x120"), ("MMD3", "60x120"),
                                         ("MMD5", "60x120"))
    assert "CODICE" not in cc(mkdoc(words))


def t3():  # 泛用詞停用補充:MATT 同欄同長同列尺寸、occ 1 → 只有 alpha_vocab 能擋
    words = rows(("MMD2", "60x120"), ("MMD3", "60x120"),
                 ("MATT", "60x120"), ("MFFF", "60x120"))
    k = cc(mkdoc(words), av=frozenset({"MATT"}))
    assert "MATT" not in k, k
    assert "MFFF" in k, k    # 對照:同構造非停用詞 → 收(證明擋的是詞表)


def t4():  # 系列詞高頻(LUME 型):同欄同長但 5 列全出現 → occ 比值擋
    doc = mkdoc(rows(("MMD2", "60x120"), ("MMD3", "60x120"), ("MFFF", "60x120"),
                     ("LUME", "60x120"), ("LUME", "60x120"), ("LUME", "60x120"),
                     ("LUME", "60x120"), ("LUME", "60x120")))
    k = cc(doc)
    assert "LUME" not in k, k
    assert "MFFF" in k, k


def t5():  # 無錨檔:0 含數字碼 → 分支不啟動,0 收(歸 C 類/S2-3)
    doc = mkdoc(rows(("MFFF", "60x120"), ("MFFG", "60x120"), ("MLNM", "60x120")))
    assert not cc(doc), cc(doc)


def t6():  # 散文頁偶然 x 重合:同欄但該列無尺寸 → 不收
    words = rows(("MMD2", "60x120"), ("MMD3", "60x120"), ("MMD5", "60x120"))
    words += [(300, 500, "CALX")]
    assert "CALX" not in cc(mkdoc(words))


def t7():  # route_junk 不交互:四 RE 皆要求數字,全字母天然不入分流
    for t in ("MFFF", "NAT", "LUME", "RETT"):
        assert not (BAND_RE.match(t) or UNIT_RE.match(t)
                    or THICK_RE.match(t) or SIZE_LEAK_RE.match(t)), t
    doc = mkdoc(rows(("MMD2", "60x120"), ("MMD4", "60x120"), ("MFFF", "60x120"),
                     ("A11", "60x120"), ("A28", None), ("A96", None)))
    kept, routed = code_candidates(doc, set(), 1, 8)
    assert routed["band"] == {"A11", "A28", "A96"}, routed
    assert not any(v & {"MFFF"} for v in routed.values()), routed


def t8():  # 版本閘:v7 呼叫不得含任何全字母候選(全量 bit-identical=回歸電池)
    doc = mkdoc(rows(("MMD2", "60x120"), ("MMD4", "60x120"),
                     ("MFFF", "60x120"), ("MFFG", "60x120")))
    k7 = cc(doc, version=7)
    assert k7 == {"MMD2", "MMD4"}, k7


def t9():  # 表面處理縮寫陷阱(審查方案例):NAT/LAP/RET/LUX 帶內+同列尺寸+
    #        同長(3=錨碼眾數)→ 唯 occ 比值可擋,定案組合下必須不收。
    #        構造=真實高頻(各 ≥3 列);前置斷言鎖住 occ 比值條件防案例退化。
    items = [("M2D", "60x90"), ("M5D", "60x90"),          # 錨(len 3)
             ("MFF", "60x90"), ("MLN", "60x90")]          # 真 B 碼(occ=1)
    items += [(a, "60x90") for a in ("NAT",) * 3 + ("LAP",) * 3
              + ("RET",) * 3 + ("LUX",) * 3]              # 縮寫各 3 列(帶內)
    doc = mkdoc(rows(*items) + [(360, 100 + 25 * k, "SOF") for k in range(3)])
    words = [w[4] for p in doc for w in p.get_text("words")]
    for a in ("NAT", "LAP", "RET", "LUX"):                # 前置斷言:高頻條件成立
        occ = words.count(a)
        assert occ >= 3 and occ > words.count("MFF"), (a, occ)   # occ 比值前提
    k = cc(doc)
    assert not k & {"NAT", "LAP", "RET", "LUX"}, k        # 帶內高頻 → occ 擋
    assert "SOF" not in k, k                              # 欄旁(帶外)→ 錨擋
    assert {"MFF", "MLN"} <= k, k                         # 真 B 碼收
    assert {"M2D", "M5D"} <= k, k


def t10():  # 小表邊界(審查方問題):含尺寸列 2 < R_MIN=3 → 分支不啟動,
    #         全字母一律不收(NAT 與 MFF 皆不收=寧誠實漏不誤收;票有記)
    doc = mkdoc(rows(("M2D", "60x90"), ("MFF", "60x90"))
                + [(330, 100, "NAT"), (330, 125, "NAT")])
    words = [w[4] for p in doc for w in p.get_text("words")]
    assert words.count("60x90") == 2 < 3                  # 前置斷言:小表前提
    k = cc(doc)
    assert not k & {"MFF", "NAT"}, k
    assert "M2D" in k, k                                  # 既有 alnum 分支不受影響


CASES = [p1, p2, p3, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10]

if __name__ == "__main__":
    red = 0
    for fn in CASES:
        try:
            fn()
            print(f"{fn.__name__.upper():>4} PASS  {fn.__doc__.strip().splitlines()[0] if fn.__doc__ else ''}")
        except Exception as e:
            red += 1
            print(f"{fn.__name__.upper():>4} FAIL  {e!r:.80}")
    print(f"\n{len(CASES) - red}/{len(CASES)} green" + (f",{red} red" if red else " — 全綠"))
