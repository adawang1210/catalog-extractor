# v10 凍結說明(2026-07-12 定案切版;裁決②=三頁 diff 證據頁存檔放行,不需親驗)

定案依據:S2-2 延伸 L1 全套驗收(設計=output/s22ext_design.md):dev 分離
量測(病例 6/7、真碼淨誤中 0、同形真碼雙控制組零觸碰)、SL-1~SL-4 合成
全過(SL-2=P 成立對抗構造)、dev v10 diff=恰 3 頁全歸隊 token、夾具
PortlandStone+TdM(第三 Emil 檔泛化)+catalogs6 零 diff。
證據頁=viewer/s22_l1_v10/(dev 3 頁+c7 4 頁,機械疊框)。

## ★版本號非線性(裁決④註記義務)

- **主幹:…→ v6 → v7 → v8 → v10(本版)**。
- **v9=E-1 場景照懸空側枝**(閘=`version==9`,親驗未過不入主幹;側枝凍結
  =output/e1_dev_v9.csv,逐位回歸義務照掛)。
- **v11=v10+E-1 預留**:E-1 親驗過後合成,屆時重跑 E-1 全套驗收、閘改
  `==9 or >=11`。

## v10 內容(v8 之上唯一新增)

m2_scan.band_regroup:kept token 歸隊 routed["band"] ⟺
`P(首字母∈routed band 家族字母)∧(B:同頁與 band 實例 x 欄對齊 ±V8_X_TOL
∨ A':同列同 token ≥S22_ROW_N)`。分流保留(過濾≠刪除),C 階段 priceBand
受益(dev 抽到率 9.8%→10.7%)。綁定/佇列/塊綁邏輯零改動。

## 凍結常數

- **S22_ROW_N=3(新,唯一)**:校準=病例 A102 同列 5/A107 同列 4、dev 真碼
  同列 max ≥3=0 筆(s22ext_design 修正①)。
- 沿用:V8_X_TOL、1.5×中位字高同列、fold 1.2、fam≥3(route_junk v5)。
- **凍結基準 CSV=output/s22_dev_v10.csv**(dev 290 行;pipeline --smoke 標的)。
- C 層 priceBand 格式驗證上限隨 band 宇宙擴至 `[A-Z]\d{1,3}`(輸出 sanity
  檢查,非偵測規則)。

## 凍結時已知殘留

- **T104 型(B/A' 雙漏、單色樣多實例)**:dev 1 例仍綁 4 筆;
  「band 家族字母=真碼字首」重合檔=dev 零病例(未量測殘留)——兩者皆
  **GT 監看清單**項。
- P=L1/L2 共模單點(裁決①已知限制):殘餘暴露=無家族字母毒碼型。
- 其餘 v8_FREEZE.md known-gaps 照掛(③同列無尺寸/純 B 碼頁/E-1 懸空等)。
