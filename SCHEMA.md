# 目標資料模型 SCHEMA v1.0(2026-07-09 定版待核;核可後為所有後續步驟的目標契約)

## 0. 實體關係

```
Brand(廠商)
  └─ Series(系列)1:N          ← seriesId = brand + normalize(seriesName_en)
       ├─ specByCode[](規格表原始列)      ← 系列層保存「原始對照表」
       └─ Variant(單品=色號)1:N          ← variantId = seriesId + (code | color_en)
            └─ VariantSize(尺寸)1:N       ← variantSizes 由 specByCode 按色群組**推導**
```

**推導規則(兩種 SKU 體制,corpus 皆有)**
- 體制 A|每(色,尺寸)一碼(Emil/Provenza/Viva/Ergon/Marazzi):色號有 N 個可下單碼
  → `Variant.code = null`,可下單碼放 `VariantSize.orderCode`。
- 體制 B|每色一碼跨尺寸(Topcer 2 位數、MOSA 15thirty):`Variant.code` = 該色碼,
  `VariantSize.orderCode = null`(繼承色碼)。
- ⚠ 定版決策:`Variant.code` 僅在「色層級唯一可下單碼存在」時填值;否則以
  VariantSize.orderCode 為準。審閱時可否決改為「主碼=最小尺寸碼」等替代政策。

**溯源(每個抽取欄位必附)**:`prov = {pdf, page, bbox?, method}`——GT/稽核/回溯裁圖都靠它。

## 1. Series(系列層級,每系列一次)

| 欄位 | 型別 | 雙語 | 說明 |
|---|---|---|---|
| brand | str | – | 廠商(資料夾結構) |
| seriesName | {en, zh} | ✓ | 系列名;en 取型錄,zh 翻譯 |
| origin | str | – | 產地(國別) |
| appearanceDesc | {en, zh} | ✓ | 外觀描述(敘述文字) |
| features | [str] | – | 功能特性(防凍、抗汙、20mm…) |
| isClassic | bool | – | 經典系列標示 |
| applicableSpaces | {en, zh}[] | ✓ | 適用空間(地/壁/室內外…) |
| slipRating | [str] | – | 防滑等級(R9-R13、DCOF、BOT3000…可多值,附表面) |
| specType | str | – | 規格類型(⚠ 定義待與需求方對齊:暫定=材質/成型類,如 porcelain stoneware) |
| allSizes | [SizeToken] | – | 全系列尺寸清單(跨頁彙整聯集,正規化 60x120 型式) |
| applicationScenes | {en, zh}[] | ✓ | 應用場景(商空/住宅/廚衛…) |
| unit | str | – | 計量單位(pcs/box/m²/箱) |
| platformCategory | str | – | 平台分類對應(外部 taxonomy 映射) |
| specByCode | [SpecRow] | – | 規格頁對照表原始列(見下) |

`SpecRow = {code, size, surface/finish, priceBand?, packing?{pcsBox, m2Box, kgBox}, prov}`

## 2. Variant(單品層級,每色號一筆)

| 欄位 | 型別 | 雙語 | 說明 |
|---|---|---|---|
| code | str? | – | 完整可下單 SKU(體制 B)或 null(體制 A,見推導規則) |
| color | {en, zh} | ✓ | 顏色名;en 取圖說,zh 翻譯 |
| colorQuality | enum? | – | 色名品質旗標(2026-07-10 裁決:溢收照出但標記不擋):clean=無溢收訊號(不保證正確,正確率=I)/needs_review=溢收訊號命中(≥4 token/長度>30/非拉丁),下游勿直接信該色名/null=無色名。聲明層推導欄,無獨立 prov(依附 color.prov) |
| shadeVariation | enum V1–V4 | – | 窯變等級 |
| price / priceBand | str? | – | 價格帶(A11/A96…型 token)或實價 |
| variantSizes | [VariantSize] | – | **該色號實際對應尺寸(非系列聯集)**——最高優先欄位 |
| swatchCrop | {png, prov} | – | 色塊裁切圖 + 頁面座標(pdf/page/bbox) |

`VariantSize = {size, finish?, orderCode?, priceBand?, prov}`

## 3. 落差盤點表(欄位 → 來源頁型 → 抽取機制 → 現況)

圖例:✅ 已有|🟡 部分/機制在但未接|❌ 未做|🌐 外部資料,非型錄可抽

### Series

| 欄位 | 來源頁型 | 機制 | 現況 | 備註 |
|---|---|---|---|---|
| brand | 資料夾結構 | 檔案系統 | ✅ | |
| seriesName.en | 封面/頁首/檔名 | 文字層 | 🟡 | 檔名可用;頁首抽取未做。**⚠ 總覽型錄(1general_ultra、Marazzi A02G)一檔多系列→需系列切分,新問題,開票 SCH-3** |
| seriesName.zh | – | 翻譯步驟 | ❌ | 見〔旗標 c〕 |
| origin | 型錄極少載明 | 🌐 vendor 主檔 | 🌐 | 向資料方要 |
| appearanceDesc | **系列介紹頁(前導情境頁)** | 文字層擷取+文字 LLM 選段 | ❌ | **〔旗標 a〕架構翻轉,見 §4** |
| features | 介紹頁文字+技術 icon | 文字 LLM + icon 對照(VLM 或向量 icon 分類) | ❌ | icon 部分需 VLM;文字部分不需 |
| isClassic | 型錄無此概念 | 🌐 業務標記 | 🌐 | |
| applicableSpaces | 技術頁 icon 列+介紹文字 | icon 對照+LLM | ❌ | |
| slipRating | 技術/規格頁 | 文字層 regex(R10/R11 token 已在 census top_codes 出現) | 🟡 | per-doc 聚合易;per-表面歸屬較細 |
| specType | 技術頁 | 文字層+對照表 | ❌ | 定義先對齊 |
| allSizes | spec 頁 | SIZE_RE 聯集(已有)+正規化 | 🟡 | 正規化(×/x、逗號、吋)未做 |
| applicationScenes | 情境照頁+介紹文字 | LLM(+圖說) | ❌ | 〔旗標 a〕同源 |
| unit | 包裝表(IMBALLI E PESI 型) | 表格解析 | ❌ | 包裝表頁型已在 GT 頁出現過(Provenza p16 右下、Ariostea p36 右) |
| platformCategory | – | 🌐 taxonomy 映射規則 | 🌐 | 由 features/specType 推導 |
| specByCode | 規格表頁(Ariostea p36 型)+交叉矩陣頁 | **幾何綁定(欄=色)+同列解析(列=尺寸)** | 🟡 | code↔swatch v2 GT 69.9%;**code→列尺寸關聯機制不存在,開票 M3-R1b**;>8 字元/全字母 SKU 漏抓(S2-1)直接打擊本欄 |

### Variant

| 欄位 | 來源頁型 | 機制 | 現況 | 備註 |
|---|---|---|---|---|
| code | spec/矩陣頁 | 候選偵測(既有) | 🟡 | S2-1 缺口(>8 字元、全字母);junk 17.6%(S2-2) |
| color.en | 色樣圖說 | 幾何綁定擷取文字(既有) | 🟡 | 綁定正確率=瓶頸(同 M3-R1) |
| color.zh | – | 翻譯步驟 | ❌ | 〔旗標 c〕 |
| shadeVariation | 技術頁(Viva p14 實見「SHADE VARIATION V3」) | 文字層 regex | 🟡 | 系列級易;逐色罕見,缺值=繼承系列 |
| price/priceBand | 矩陣「Fascia di prezzo」欄+價格表 | 同列關聯(A\d+ token→列) | ❌ | **⚠ A\d+ 在 M2 GT 被歸 junk——僅指「不做綁定候選」;S2-2 過濾必須改為「分流到價格欄位」而非丟棄** |
| variantSizes | **交叉矩陣頁(欄=色、列=尺寸)+ specByCode** | 欄綁定(v2 已修)+**列尺寸關聯(M3-R1b 新機制)** | 🟡 | **〔旗標 b〕本輪驗收必涵蓋,見 §5** |
| swatchCrop | spec 頁 | extract_swatches bbox(已有)+fitz clip 裁圖 | 🟡 | 家具/icon 混入→M3-R1 家具過濾直接改善純度 |

## 4.〔旗標 a〕架構翻轉:情境頁從「可丟棄」變「唯一來源」

M1 起的立場是「系列介紹/情境頁=分類洩漏,Stage 1 要把它們踢出 spec 集」。新 schema 下,
appearanceDesc / features / applicableSpaces / applicationScenes 的**唯一來源就是這些頁**。
- Stage 1 從「過濾器」翻轉為「**路由器**」:spec 頁→綁定管線;系列介紹頁→敘述欄位桶;
  情境照頁→應用場景證據;規格表頁→specByCode 解析。**不再有「丟棄」,只有「分流」。**
- 機制評估:corpus 文字層覆蓋率高(census has_text_layer),敘述文字**本體用文字層即可取**,
  不需 VLM 讀圖;難點是「哪段是外觀、哪段是行銷廢話」的選段/歸欄 → **文字 LLM 足夠**。
  VLM 僅兩處需要:技術 icon 判讀、無文字層的掃描檔(census 可篩)。
- 本輪不實作(SCH-1 開票),但 M3 的 Stage 1 改動(家具過濾)不得與路由器方向衝突。

## 5.〔旗標 b〕variantSizes 與 M3-R1 的直接耦合

variantSizes 本質 = specByCode 按色拆分。交叉矩陣(欄=色樣、列=尺寸、格=code)正是
「哪個色號有哪些尺寸」的載體:
- **欄向(code→色)**:= code↔swatch 綁定。v2 已修欄親和;規則 1 搶綁(30.1%)是現存
  唯一破壞源 → M3-R1 修的就是它。
- **列向(code→尺寸)**:機制目前**不存在** → 新開 **M3-R1b:code→同列尺寸 token 關聯**
  (幾何同列查找,小機制,與 M3-R1 同批驗收)。
- **驗收升級(定版)**:M3 的 GT 不只判 code→swatch,矩陣頁逐 code 判
  `(code → 色, 尺寸)` 二元組正確性 = variantSizes 的直接正確率。

## 6.〔旗標 c〕雙語盤點

| 語言狀態 | 廠商 | 說明 |
|---|---|---|
| 原生多語(義+英,常加德/法/西/俄) | Emil、Ergon、Provenza、Level、Viva(Emilgroup);Marazzi;Ariostea、FMG、Iris(Iris Group) | en 直接抽;圖說欄位名多語並列(Decors\|Dekore\|Декоры 型),抽取時取 en 欄 |
| 原生英文為主 | MOSA、Topcer、41Zero42(義英) | en 直接抽 |
| 中文 | **全 corpus 皆無** | **所有 zh 欄位=翻譯步驟產出**(seriesName/appearanceDesc/applicableSpaces/applicationScenes/color) |

翻譯定位:獨立批次階段(抽取完成後、入庫前),文字 LLM + 品牌/材質詞彙表保持一致性;
**不進本輪**,開票 SCH-2。

## 7. 對本輪(M3)的影響摘要

1. M3-R1 驗收升級:矩陣頁 GT 判 (code→色,尺寸) 二元組(=variantSizes 正確率),
   不只 code→swatch。
2. 新增 M3-R1b:code→同列尺寸 token 關聯(小幾何機制,同批 ablation+GT)。
3. S2-2 修訂:A\d+ 價格帶/CM2 厚度=「移出綁定候選」但**分流保留**(價格欄位/厚度欄位來源),
   不是刪除。
4. Stage 1 方向約束:任何過濾改動須與「路由器」架構相容(不丟頁,只分流)。
5. 新票:SCH-1(敘述欄位抽取)、SCH-2(翻譯階段)、SCH-3(總覽型錄系列切分)——本輪不做。
