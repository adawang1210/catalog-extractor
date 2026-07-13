#!/usr/bin/env python3
"""M5-2b B 訊號誤 icon 修理:合成案例(工作包#4 紅燈 draft → 工作包#5 轉綠=常備回歸)。

    python3 dev/m52b_selftest_draft.py            (CWD=專案根)

歷程:工作包#4 止於紅燈(A 段綠/B 段 3/3 紅,對「實作後目標行為」下斷言);
工作包#5(2026-07-13 裁決路線 (a) 真分叉雙中位)core 落地 v13 版本閘後轉綠——
B 段斷言內容一位元不動,僅呼叫閘由「無版本(當時=目標語意)」改「顯式 version=13」。
  A 段 V=12 基線(舊全體中位路;v≤12 含 v9 側枝=doc_icon_stats 預設)須全 PASS
    ——鎖定病灶「保持」於舊路(=v9 側枝逐位不變的合成見證)與正確殺 icon 母體。
  B 段 v13 目標(med_ex 排大圖中位;core 已實作)須全 PASS。
精華已併 core selftest(8b);本檔=完整版常備回歸。純合成、零語料。"""
import sys
from statistics import median

import fitz

sys.path.insert(0, "core")
from spike_geom import extract_swatches                       # noqa: E402
from m3_scan import _K20, M52_BIG, doc_icon_stats, icon_sus   # noqa: E402


def make_page(specs, w=600, h=800):
    """specs=[(x0,y0,x1,y1)...] 各插一張 raster 圖(受控面積);回傳 page。"""
    pg = fitz.open().new_page(width=w, height=h)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 4, 4), False)
    pix.set_rect(pix.irect, (180, 90, 60))
    for r in specs:
        pg.insert_image(fitz.Rect(*r), pixmap=pix)
    return pg


def med_ex(spec):
    """對照組(獨立重演設計式):排除 ≥M52_BIG×頁的大圖後,小簇中位;
    小簇空→退回全體(保存原行為)。core as-built 須與此逐位一致(B1)。"""
    small = [abs(r) for p in spec for r in extract_swatches(p, version=3)
             if abs(r) < M52_BIG * abs(p.rect)]
    if not small:
        alla = [abs(r) for p in spec for r in extract_swatches(p, version=3)]
        return median(alla) if alla else 0.0
    return median(small)


A, B = [], []


def check(seg, cond, label):
    seg.append((bool(cond), label))


# ── A 段:V=12 基線(舊路=doc_icon_stats 預設;全 PASS)────────────────────────
# A1 病灶複現:單系列型檔=每 spec 頁 1 情境照(~30%頁)+ 1 真小色樣(~0.5%頁)。
#    pooled 2 大 2 小 → statistics.median 取中間兩者平均 = 被大圖撐高。
#    v13 落地後此病灶必須「保持」於 v≤12 路=真分叉雙中位的舊半邊見證。
scene = [(30, 30, 430, 470)]           # 大圖 ~33% 頁
swat = (450, 100, 500, 150)            # 真小色樣 0.52% 頁
p1 = make_page(scene + [swat])
p2 = make_page(scene + [(450, 300, 500, 350)])
spec_scene = [p1, p2]
rep, med = doc_icon_stats(spec_scene)
real_sw = fitz.Rect(*swat)
# A1a 舊路中位被撐高(> 真小色樣面積的 20× → 觸發 B 誤殺)
check(A, med > 20 * abs(real_sw), "A1a 舊路 doc 中位被情境照撐高(病灶保持於 v≤12)")
# A1b 舊路 icon_sus 誤殺真小色樣(B 臂 a<0.05×med)
check(A, icon_sus(real_sw, (rep, med)), "A1b 舊路 B 訊號誤殺真小色樣(病灶保持)")
# A1c v9 側枝顯式對照:doc_icon_stats(spec, 9) 與預設(≤12)逐位同(第一硬條件見證)
check(A, doc_icon_stats(spec_scene, 9) == (rep, med),
      "A1c v9 側枝=舊路逐位(真分叉雙中位之舊半邊)")

# A2 正確殺 icon 母體:格狀型檔=多真小色樣(~2%頁,area 9604)+ 極小 icon(area 300)、
#    無情境照。中位落小色樣簇(9604),icon 遠小於 0.05×med → B 正確殺;此類無大圖、
#    med_ex==med(小簇=全體)須完全保全(對應語料 Woodtouch/Stonetalk/next/PIPO)。
grid = [(20 + 100 * k, 100, 118 + 100 * k, 198) for k in range(5)]  # 5 真小色樣 area 9604
icon = (40, 60, 60, 75)                                             # 極小 icon area 300
pg_grid = make_page(grid + [icon])
rep_g, med_g = doc_icon_stats([pg_grid])
real_icon = fitz.Rect(*icon)
check(A, icon_sus(real_icon, (rep_g, med_g)), "A2a 舊路 B 正確殺極小 icon")
check(A, not icon_sus(fitz.Rect(*grid[0]), (rep_g, med_g)),
      "A2b 舊路 B 不殺格狀真小色樣")

# A3 selftest(8) 逐位重演(V=12 icon_sus 基線鎖定;判定式不動=兩臂式零改動見證)
med8 = 10000.0
tiny = fitz.Rect(0, 0, 10, 40); trim = fitz.Rect(0, 0, 60, 60)
repsm = fitz.Rect(100, 100, 140, 150); repbig = fitz.Rect(200, 200, 400, 300)
rep8 = {_K20(repsm), _K20(repbig)}
check(A, icon_sus(tiny, (rep8, med8)) and icon_sus(repsm, (rep8, med8))
      and not icon_sus(trim, (rep8, med8)) and not icon_sus(repbig, (rep8, med8))
      and not icon_sus(tiny, (set(), 0.0)), "A3 selftest(8) V=12 基線逐位")

# ── B 段:v13 目標行為(med_ex;core 版本閘已實作 → 全 PASS)──────────────────
# B1 正例:情境照撐高型檔,core v13 回傳中位=獨立重演之 med_ex(排大圖後小簇中位)。
mex = med_ex(spec_scene)
rep13, med13 = doc_icon_stats(spec_scene, 13)
check(B, abs(med13 - mex) < 1.0,
      "B1 v13:doc_icon_stats 排大圖→回傳小簇中位(as-built≡設計式)")
check(B, not icon_sus(real_sw, (rep13, med13)),
      "B2 v13:情境照撐高型檔真小色樣存活")

# B3 對抗反例:正確殺 icon 母體在 v13 下仍須殺(保全,不得漏殺)。
#    格狀檔無大圖 → med_ex==med → icon 仍被殺 = med_ex 不會「連 icon 一起救」。
check(B, doc_icon_stats([pg_grid], 13) == (rep_g, med_g)
      and icon_sus(real_icon, doc_icon_stats([pg_grid], 13)),
      "B3 對抗:無大圖檔 v13≡舊路、極小 icon 仍被殺(正確殺母體保全)")

# B4 混合語意:同一撐高檔,舊路(med)/v13(med_ex)並存——真小色樣舊殺新救、
#    極小 icon 兩路皆死。real_sw area 2500;tiny_icon area 108(<0.05×mex=125)。
tiny_icon = fitz.Rect(450, 500, 462, 509)   # area 12×9=108
check(B, icon_sus(real_sw, (rep, med)) and not icon_sus(real_sw, (rep13, med13)),
      "B4a v13:撐高檔真小色樣舊路被殺→v13 救回")
check(B, not icon_sus(real_sw, (rep13, mex)),
      "B4b v13:med_ex 下真小色樣存活")
check(B, icon_sus(tiny_icon, (rep13, med13)),
      "B4c 對抗:v13 下極小 icon(area108<0.05×2500)仍死")

# ── 報表 ──────────────────────────────────────────────────────────────────
ok_all = True
print("== A 段 V=12/v9 舊路基線(須全 PASS)==")
for ok, lbl in A:
    print(f"  [{'PASS' if ok else 'FAIL'}] {lbl}")
    ok_all &= ok
print("== B 段 v13 目標(工作包#5 轉綠;須全 PASS)==")
for ok, lbl in B:
    print(f"  [{'PASS' if ok else 'FAIL'}] {lbl}")
    ok_all &= ok
print(f"\n{'全綠 ✓(紅燈 3/3 已轉綠+基線鎖定)' if ok_all else '有 FAIL ✗(停止線)'}")
sys.exit(0 if ok_all else 1)
