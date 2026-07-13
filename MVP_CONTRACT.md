# MVP 契約(產線第一版 A→C→D→E+K;2026-07-09 定稿待核)

**一句話:一份 PDF 進 → 一份 SCHEMA JSON(Brand→Series→Variant→VariantSize,
每個有值欄位帶 prov 溯源)+ 每個綁定色樣的裁圖 PNG + 一份 needs_review 佇列檔。**
本契約定義 MVP「交付什麼/不交付什麼/怎麼驗」,避免做完才發現期待落差。

## 一、會填的欄位(體感填充率;⚠ 全部是偏置批數字,真實水準以 I 為準)

| 欄位 | 來源 | 體感 |
|---|---|---|
| brand | 資料夾結構 | 100% |
| seriesName.en | 檔名(頁首抽取不在 MVP) | 高;**總目錄一檔多系列(SCH-3 未做)只給檔名級,標 `multiSeries:true` 旗標** |
| Series.allSizes | SIZE_RE 聯集+粗正規化(x/×統一) | 高 |
| Series.specByCode | **C 新做**:code+size(已驗:(色,尺寸) 二元組 91.2%)+ surface/priceBand/packing 列欄解析(新) | code+size 高;其餘欄=C 首做,填充率未知,I 給數 |
| Variant.code / color.en | v8 綁定(2026-07-12 切版),收 x_aligned+塊綁(佇列外抽驗**雙口徑**:原始 379/4 錯/≈2.4% 現行有效、剔除後 375/0/≈0.8% 並列,見「統計口徑」節) | dev 61%、catalogs5 33%(偏置);真實=I |
| Variant.variantSizes | 列向尺寸關聯+D 按色推導;體制 A/B 判定(SCHEMA 規則)=D 實作 | 矩陣頁列向 91.2%;整體=I |
| VariantSize.orderCode | 體制 A 時填(D) | 隨上 |
| Variant.priceBand | S2-2 分流 band token + C 列對應 | 嘗試;未知 |
| Variant.swatchCrop | E:fitz clip 裁圖+prov | aligned Variant 100% |
| needs_review 佇列檔 | K:孤兒/名鍵假說(含目標)/M5-2 降級,逐筆帶頁+bbox+原因 | 每份 PDF 100% 產出 |
| prov {pdf,page,bbox,method} | 所有有值欄位強制附 | 100%(構造保證) |

## 二、MVP 一定是空的(明確不含)

| 欄位 | 原因 | 何時有 |
|---|---|---|
| appearanceDesc / features / applicableSpaces / applicationScenes | F 未做,需文字 LLM key(**請先去 aistudio.google.com 開免費 key,等待不佔工期**) | F |
| 所有 .zh 欄位 | 翻譯階段 | G |
| origin / isClassic / platformCategory | 外部資料,非型錄可抽(**早問資料方**) | H |
| specType | 定義未與需求方對齊 | 對齊後 |
| shadeVariation / slipRating / unit | 文字層 regex 有訊號但未接管線(便宜後補件,刻意不進 MVP 防 scope creep) | MVP 後小票 |
| Variant.price 實價 | 型錄只有價格帶 token | 資料方價格表 |
| **無碼廠(Sodai 型)的 Variant** | 替代身分鍵靠色名(名鍵假說品質 87.6%,不配直接入庫)→ MVP 只出 Series 骨架+色樣裁圖進佇列 | 名鍵升級票+SCH-3 |

## 三、★已知靜默缺口(紅字:MVP 的產品清單不完整)

偵測缺口使部分產品**整個從 JSON 缺席、任何欄位都不會報警**:
S2-1 B 類全字母 SKU(Emil 型頁漏 74%)、S2-3 一次性長碼(0general 單檔 273 筆)、
C 類低重複純數字(Iris/41Zero42)。**修復=B(S2 系列),照裁決排在 I 之後**,
由 I 的隨機批給出「真實產品缺席率」再定優先序。MVP 產出的 JSON 標頭將帶
`knownGaps` 聲明欄,防下游誤當完整清單。
**跨文件實體解析未實作(2026-07-11 外審行動③追加)**:同一系列出現在總目錄
+單系列型錄、或 2024/2025 年版並存時,D 階段只做文件內合併——下游會收到
**重複且可能互相衝突的系列/Variant 記錄,不得假設已去重**。修不修、何時修
=全池普查後由使用者排。

## 三之二、統計口徑(2026-07-11 外審行動②;「零錯」一詞退役)

- 佇列外(自信輸出)品質的正確表述:**「抽樣 n 筆零發現」→ 錯誤率 95% 信賴
  上界 ≈ 3/n(rule of three;發現 ≥1 筆時改用 Clopper-Pearson)**。
  當前狀態(2026-07-12 c7 GT 收卷;裁決①=**雙數字口徑並列**):
  - **原始口徑(現行有效)**:n=379、發現 4 筆(A102 量表碼值錯誤,GT_REPORT
    §六 C)→ Clopper-Pearson 95% 上界 **≈2.4%**。**有效至 S2-2 延伸修復落地。**
  - **剔除口徑(並列展示)**:A102 機制已窮舉定位(全主批 [A-Z]\d{3} 逃逸
    掃描,有綁定僅此一例)→ 剔除 4 筆後 n=375、零發現 → 上界 **≈0.8%**;
    S2-2 延伸修復落地後升為現行口徑。
  不得表述為「零錯」;歷程=output/c7_gt/GT_REPORT.md §二/§五。
- **累積機制**:此後每輪人工 GT,順帶抽驗該批「佇列外輸出」並併入累積樣本
  (n 單調增、上界單調收緊),每輪把「n 與當前上界」記進對應票。

## 三之三、審查紀律(通案;2026-07-12 裁決③)

- **定案依據的前提中途被否證 → 後續 Phase 自動凍結等重審,預先核可失效。**
  預核只覆蓋「前提成立」的世界線;前提破,核可不順延。
- 本輪案例:V=8 切版於 A102 判定(值錯誤,傷及「主批 GT 零錯綁」前提)之後
  執行,經**事後追認**成立——理由:A102=v5 期缺口、v6 同病(與 v7/v8 無關),
  v7/v8 專屬驗收(反例誤觸發 4/4=0、塊綁 152 筆全對、T1 零失守)全數獨立
  成立。**不回退**;追認為個案,不得引為先例。
- **通案二(2026-07-12 裁決,E-1 v3.1 併裁;範圍擴充=同日二裁)**:任何
  新判別訊號(正面證據/豁免/閘控條件)之送審件**必附「dev 已知病例分離
  量測」**——該訊號在已知病灶與已知正例上的實測分布;**合成案例不能替代**。
  無已知病例可量者,明文標「未量測假設」並列為實作後第一優先驗證。
  **範圍擴充:適用於任何有綁定效果的產線層條件,不限偵測/綁定訊號**
  ——溯源:S2-2 L2 C0 紅燈實彈(D 階段合併鍵條件未量 dev 全量觸發率,
  dev smoke 誤降 739/1070=審查與設計雙方共同漏量,由 SL-10 白名單紅燈
  接住)。正例溯源:M5-3 band/unif 先量後落地;反例:S2-1 occ、E-1 裸
  S2a=設計期陣亡、L2 C0=實彈陣亡(×3)。
- **通案三(2026-07-12 裁決,S2-1 延伸 v12 案)**:設計期的一切量測工具
  (模擬器、探針、分離量測腳本)**一律入庫 commit、與設計案同綁;設計案
  引用的每個數字必須可由庫內腳本重跑復現**。溯源:工作包#1 全鏈模擬器
  =session 級產物、換窗即失傳,工作包#2 只能依設計文字重建,「同欄上方
  實例」成員母體語意毫釐之差使分離地圖整張重畫(批准時的 RUN_GAP 平台期
  消失、UT−2/TdM+6)。本案分離結論倖存(129 種全真碼零散文)**屬運氣
  非制度**——故立此規,不准再發生。

- **通案四(2026-07-13 裁決核定生效,L2 塌縮案;組裝層守恆=切版硬閘)**:
  smoke／押帳除頁級 9 欄守恆(驗綁定總數自洽)外,**必附「組裝層守恆」正式欄**
  ——驗「綁定如何聚合成 Variant」:①任一 Variant 的 mergedFrom 跨頁數(報告);
  ②單一色樣實例吞併綁定數(報告 hub);③**塌縮逃逸偵測=跨頁 ∧ color=None ∧
  mergedFrom≥L2_COLLAPSE_MIN 之已出貨 Variant 數(硬閘=0)**。
  **溯源:A102 嵌合體(合併鍵無條件信任身分,v5/v6)與 L2 塌縮(同鍵、非 band
  橋接碼,A02G/Topcer/Provenza)=同一組裝層兩度漏網;頁級 9 欄守恆只驗綁定
  總數自洽,結構性照不到「綁定如何聚合」——故 V=12 現行產線曾有 4 檔 color=None
  跨頁塌縮(Topcer 1021/30p、FMG 115/17p、Stream 32/6p、Provenza 30/2p=在
  dev smoke 內)在守恆全綠下出貨。**
  **已落地(工作包#7 緊急補丁,2026-07-13)**:此欄已在 pipeline.smoke()
  (`★通案四 組裝層守恆:…塌縮逃逸=0`)+塌縮守衛(assemble 降級
  assembly_collapse_suspect);儀器=dev/assembly_probe.py(--sig/--whitelist/
  --fanout,通案三)。**硬紀律:此欄綠燈(塌縮逃逸=0)為任何未來切版(含
  M5-2b v13/E-1 v9)之放行前提。** 設計案=output/l2_collapse_design.md。
  **段1 擴充(單頁過併,2026-07-13)**:塌縮簽名不只跨頁——單頁 hub 版塊(純碼
  索引頁/情境照)同色名吞併整頁不同碼,跨頁守衛(需 pages≥2∧衝突)照不到,以
  **主色樣 area%**(cluster 內最大色樣 bbox 佔頁面積%)承重:單頁 ∧ mergedFrom≥
  L2_COLLAPSE_MIN ∧ area%≥AREA_T(=5.0,凍結;隙中[2.36,7.02])→ 降級 reason
  **singlepage_overmerge_suspect**。smoke 新增「單頁過併團 N 團/M 綁定」+**第二硬閘
  單頁過併逃逸=0**(單頁∧≥門檻∧area%≥AREA_T 之已出貨 Variant 數);儀器=
  dev/pkgB_hub_sep.py(--floor/--whitelist)+**常態監看** dev/anomaly_probe.py
  (灰帶=單頁衝突 hub area%∈[2.36,5.0],若增長至≥門檻會兩守衛皆逃逸;現況 Emil
  p23 size8 唯一)。鐵律8 全量 diff=全 7 語料恰移除 Ariostea 0general 兩 Variant、
  白名單外 0。無版本閘 V=12 即生效、V=13 同守衛承接。報告=output/pkgA_anomaly_report.md。
  **案1 擴充(零邊際合併權限,2026-07-13 外審修正案)**:sub-20 真塌縮(A02G-18/
  Topcer General-19/Uniche-19(v13),段2 GT 定性 colorRaw 全 junk)與合法團在
  size 軸零邊際(非塌縮上界 19=真塌縮 19 同值)→ 裁決=**取消自動決策權限、不換
  訊號軸**(在會把 23 頁黏成一筆的系統裡,拒絕合併是功能非失敗)。①**不確定帶**
  [L2_BORDERLINE_MIN(=18,凍結;合法衝突上界 16=Level 型、空隙 17 淨空),
  L2_COLLAPSE_MIN):跨頁∧色名衝突 → 降級 reason **borderline_merge_suspect**
  (不硬判塌縮/合法);②**爆炸半徑**:跨頁 cluster 頁數>L2_AUTO_MERGE_MAX_PAGES
  (=5,凍結;合法上界 5=MILANO70/Ariostea 3general、空隙[6,7])∨ mergedFrom>
  L2_AUTO_MERGED_FROM_MAX(=24,凍結;合法上界 24=Level、空隙[25,41])→ 降級
  reason **assembly_merge_radius_suspect**(病理側下界=Topcer VICTORIAN DESIGNS
  11/8p、19/12p、42/16p=dev 1021 塌縮姊妹檔之次臨界變體);單頁域歸段1守衛、
  半徑不碰(合法單頁 25 綁定存在=Ariostea 0general v13)。smoke 新增「次臨界帶
  N 團/M 綁定+超半徑 N 團/M 綁定」+**第三/四硬閘:次臨界逃逸=0、超半徑逃逸=0**;
  D 守恆式擴充=Σ mergedFrom+L2 降級+塌縮+單頁過併+次臨界+超半徑=綁定總數。
  儀器=dev/assembly_probe.py(--borderline/--whitelist-case1)。校準+白名單總帳=
  output/l2_borderline_merge_ledger.md。
- **通案五(2026-07-13 外審審定;停止規則)**:同一病灶已試過**兩條獨立訊號軸**
  仍無真實分離度(通案二口徑之分離量測皆重疊/零邊際)=**停止規則開發**,病例
  移交 VLM/人工 lane(D 板定位=感測器非綁定器,KPI=省人工分鐘)。溯源=sub-20
  塌縮(size 軸零邊際(段2)+fan-out 軸重疊(工作包#6)→案1 裁決=撤權非判別)
  與 S2-4 頁碼污染(段4 證明不可分)——不再為不可分病例造判別器。
- **通案六(2026-07-13 裁決;結論落 git)**:每工作包的**結論性文檔**(裁決、
  定性、放棄理由、VLM 洞歸檔)必須落 git 追蹤,不得只存交接稿——通案三管
  量測工具與數字,本條管**結論本身**的可溯源。溯源=段4 S2-4「不可分」結論
  原始文檔未落 git(僅存交接稿),補立=output/s24_pagefoot_conclusion.md
  (依 dev/s24_pagefoot_probe.py 重跑復現)。
- **工作包收工併版紀律(2026-07-13 裁決②制度化)**:每工作包收工必併回
  main、禁止長期停旁支;接手第一步=git log --all+worktree list 清點旁支。
  溯源=「換窗遺失」根因不是沒 commit,是成果散在未併 main 的 claude/*
  旁支(案1 完整成果曾停在 vibrant 旁支、main 落後兩個工作包)。

## 四、產線正確性怎麼驗(哪步吃 held-out)

- **A/D/E/K(搬運+組裝,不吃 held-out)**:
  1. **v8 綁定輸出逐位凍結**(2026-07-12 切版)——m3_scan v8 dev 重掃 vs output/s21_dev_v8.csv 逐位一致,每步必跑(v6 基準 m52_dev_v6.csv 沿革保留);
  2. 組裝規則單元測試(體制 A/B 判定、按色推導、跨頁碼合併,合成案例);
  3. dev corpus 端到端 smoke:JSON schema 合法性 + **守恆對帳**(JSON 的 Variant/aligned/佇列筆數 = 掃描 CSV 各欄總數,一筆不多不少)+ prov 完整性;
  4. 裁圖抽樣目檢(dev 允許)。
- **C(specByCode 列欄解析=新抽取規則)**:dev 開發自測;**正確率數字由 I 一併給**(與 I 共用一批,省考卷;I 之前不做任何成品宣稱)。
- **I(第一個需要 held-out 的步驟)**:隨機非偏置批(池=Drive 全集扣已燒五批),給第一個真實填充率/正確率;**成品宣稱閘門**。

## 五、產線鐵律(沿用)

產線只 `import` 調用 core/(m3_scan/spike_geom/m2_scan),**不改綁定**;版本釘 v8(凍結說明=output/v8_FREEZE.md);
發現需要動綁定邏輯 → 先停下回報;held-out 只能燒一次;每欄位帶 prov;
不確定的進佇列,絕不自信輸出。
