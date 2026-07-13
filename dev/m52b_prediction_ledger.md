# M5-2b 預測帳原件(工作包#5 步3;先押後開存證,押於任何 v13 語料開帳之前)

押帳時點:2026-07-13,core v13 版本閘已落地、selftest/draft/smoke(V=12)全綠,
**尚未跑任何 v13 語料掃描**。預測來源=設計案 §1b(dev/b_signal_probe.py codes 模式,
v12 鏈餵 med_ex=v13 語意等價)+凍結 output/s21ext_dev_v12.csv 現側;兌現紀律=
開帳逐筆對兌,偏離=逐筆解釋、禁調(通案一)。

## 一、dev 全量 diff(catalogs/ 289 頁,v13 重掃 vs 凍結 s21ext_dev_v12.csv)

**變動檔=恰 1 檔:Marazzi catalog_A02G-04_en.pdf**(凍結現側 dm=46=dev 唯一非零檔):
- `code_icon_demoted`:46 → **0**(救回 46,§1b「情境照撐高同構」)。
- 守恆式(逐頁):Δaligned+Δblk = −Δdemoted;Δreview = Δdemoted(只降)。
- 其餘全部檔、全部頁、全部欄位=**逐位零 diff**。

白名單(鐵律 8,方向鎖死;白名單外零容忍):
1. `code_icon_demoted`:只准減(A02G 諸頁)。
2. `code_x_aligned`/`code_block_bound`:只准增,增量和=該頁 demoted 減量。
3. `code_needs_review`:只准減,減量=該頁 demoted 減量(佇列消失=全數升級為綁定,
   非無故蒸發;此即「佇列非預期消失」停止線的預期豁免條款)。
4. `code_name_bound`:條件性只准減(M4-ID 頁閘 aligned+blk≤0.2×n_codes 因救回而
   翻面→該頁 named 歸零);押=A02G 現側 name_bound 若非零之頁逐頁對兌,無翻面則零變。
5. 永不變:n_sw/n_codes/code_orphan/code_far/code_with_size/sw_no_code/ptype。

## 二、夾具語料逐檔押帳(§1b 全表照抄=v13 預測;m3_scan v12 vs v13 對照跑)

| corpus | doc | dm v12 | dm v13 押 | 類 |
|---|---|--:|--:|---|
| catalogs6 | **Uniche** ★ | 50 | **0** | 病例 |
| catalogs6 | **Vivo** ★ | 18 | **0** | 病例 |
| catalogs6 | 其餘(D_Segni/Stream/Hello/Room…) | 0 | 0 | 對照 |
| catalogs5 | **Re-Play** ★ | 60 | **0** | 病例 |
| catalogs5 | teknostone | 12 | **6** | 部分(混合) |
| catalogs7 | **Ego** ★(c7 用途 (i)) | 20 | **0** | 病例=修復率 20/20 |
| catalogs7 | Rice | 26 | **0** | 同構 |
| catalogs7 | Frammento | 18 | **0** | 同構 |
| catalogs7 | Limestone Wall | 2 | **0** | 同構 |
| catalogs3 | Salt Stone | 34 | **0** | 同構 |
| catalogs4 | 0general | 89 | **0** | 同構 |
| **catalogs3** | **Stonetalk** | **90** | **90** | 正確殺母體=零鬆動 |
| **catalogs2** | **Woodtouch** | **28** | **28** | 正確殺母體=零鬆動 |
| **catalogs3** | **next-4099** | **18** | **18** | 正確殺母體=零鬆動 |
| **catalogs4** | **PIPO** | **9** | **9** | 正確殺母體=零鬆動 |

合計押:dm 520 → **151**(救回 369;病例 148 全救、母體 145 逐碼零鬆動)。
夾具白名單=§一同五條(逐檔套用);「既有正確子集」(塊綁/對齊現值)只增不減。

## 三、五版本逐位押帳(步 4)

v8/v9 側枝/v10/v12 dev 重掃 vs 各自凍結 CSV(s21_dev_v8/e1_dev_v9/s22_dev_v10/
s21ext_dev_v12)=**逐位 bit-identical、零 diff**(v9=第一硬條件;photo_dm 之 S2a
快照耦合由 v9 逐位一併覆蓋=設計案 §5「不得免驗證」條款兌現)。
