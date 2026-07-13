# 工作包#2 步4 預測帳(先押後開;依 output/s21ext_design.md 分離量測)

## dev(catalogs/,27 檔中僅 2 檔有 ③型真碼病例)

| 檔 | 預測新收(v12 kept − v10 kept) |
|---|---|
| Provenza/Unique Travertine | +43 種(EJMA/EJND… 規格列族) |
| Viva/Metallica | +5 種(EJDD/EJKC-F=EJDJ-L 歷史族) |
| 其餘 25 檔 | 0 |
| **合計** | **48 種;新收全數=繼承機制、散文 0** |

## c7(catalogs7/)

| 檔 | 預測新收 |
|---|---|
| PietraEssenza | +14(p19 塊頭行族)→ GT ③型修復 |
| PortlandStone | +15(p21 E 族 trim/battiscopa;EMHD 型 2 筆=②殘留不收)|
| TdM | +24(夾具反例件) |
| Ego | +17(夾具反例件) |
| Alter | +7(夾具反例件) |
| 其餘檔 | 0 |
| **合計** | **77 種;GT ③型修復=29/31** |

## catalogs6:設計案無預期數字=同步計分觀察(偏離逐筆解釋)

## 鐵律8 白名單(dev CSV diff)
- 允許:UT/Metallica 頁 n_codes↑、x_aligned/needs_review/code_with_size↑、
  code_orphan/far↑(新碼落點)、sw_no_code↓(新碼上色樣);
  name_bound 變動若因新碼改 doc_name_index=逐筆歸因後准。
- 禁止:任何頁 n_codes↓、佇列項非歸因消失、非 UT/Metallica 檔任何變動。
- v8/v9/v10 重掃(改動後代碼)逐位=s21_dev_v8.csv / e1_dev_v9.csv / s22_dev_v10.csv。
