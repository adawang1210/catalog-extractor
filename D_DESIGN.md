# D|Stage 5 組裝——設計(2026-07-09 交審;核可後才實作)

D 的性質:第一個「合併+推導」步驟,輸出筆數≠輸入筆數,A/C 的筆數守恆失效。
本設計三支柱:①單元測試每規則 正例+反例+邊界;②守恆替代品=mergedFrom 可追溯
守恆(原始紀錄零遺失);③合併 key 只用身分證據(code),絕不用幾何/距離,
寧可不合(留兩筆)不誤合(資料毀損)。

## 一、核心設計決策(供否決)

### D1|合併 key 定義

- **同一產品的唯一合併鍵 = (doc, series, code)**(SCHEMA 複合 PK)。同 code 跨頁
  出現 → 合併為一個 Variant/其 VariantSize 來源。
- **色名(color.en)永遠不當合併鍵**,只當標籤與一致性檢查——SCH-3 未做,
  series=檔名級,總目錄一檔多系列時色名跨系列撞名(GRIGIO×2 系列),用色名合併
  = 誤合毀損。代價:同色跨頁無共同碼時留多個 Variant(不合≠毀損),記 knownGaps,
  SCH-3 完成後升級。
- **頁內分組**:同一色樣實例(page,bbox)的 x_aligned 碼 = 同一色的碼集(這是
  綁定引擎已驗證的輸出,非新判定)。
- **跨折縫(spread)**:合併只認 code 身分、不含任何幾何鍵,折縫不參與合併判定,
  結構上不存在「幾何誤合」路徑。折縫的防污染已在 v6 綁定層(row_size/圖說側檢查)
  處理完畢,D 不再碰幾何。
- **同碼異色名衝突**(p3 圖說 WHITE、p5 圖說 BLACK):PK 要求同碼=同產品 → 合併
  為一個 Variant,但 **color.en=null(不挑邊、不猜)**+ 佇列項 `code_color_conflict`
  (附兩個候選與 prov)——這同時是上游錯綁的偵測器。

### D2|體制 A/B 判定(每個 Variant 色組獨立判,不做 doc 級投票)

判定材料 = 該色組的 {distinct code → distinct 已知尺寸集}(來自 specByCode 認領列):

- **B 的正面證據**:色組恰 1 個 distinct code 且該碼 ≥2 個已知尺寸
  → `Variant.code=該碼`,VariantSize.orderCode=null。
- **其餘一律 A 形式**(SCHEMA 定版:「Variant.code 僅在色層級唯一可下單碼存在時
  填值」;A 形式無損——每個碼都保留在 VariantSize.orderCode):
  - 多碼各一尺寸(標準 A)→ code=null,每 (碼,尺寸) 一筆 VariantSize。
  - **1 碼 1 尺寸(臨界)→ A 形式**(B 需正面證據;A 形式碼仍在 orderCode,
    放錯體制≠丟資料)。# ponytail: doc 級體制投票=升級路,等 I 看錯置率再決定
  - **混合訊號(某碼 ≥2 尺寸 且 有兄弟碼)→ A 形式 + 佇列項 `regime_conflict`**
    (不猜語意,無損展開,人工裁)。
  - 尺寸=None 不算 B 證據(≥2「已知」尺寸才算);全 None 碼 → 一筆
    VariantSize{size:null, orderCode:碼}(碼不得丟)。

### D3|mergedFrom 可追溯守恆(守恆的替代品)

A/C 產物先發身分證:綁定紀錄 id=`b:{page}:{序}`、specByCode 列 id=`s:{page}:{序}`
(確定性編號,重跑不變)。D 輸出掛雙向帳:

- 每個 Variant 帶 `mergedFrom:[綁定紀錄 id…]`;
- 每個 VariantSize 帶 `derivedFrom:[spec 列 id…]`(≥1,同碼列才可認領);
- **零遺失三檢(dev smoke 硬性)**:
  1. 全部綁定紀錄 id 被恰好一個 Variant 認領(覆蓋∧互斥;
     Σlen(mergedFrom)=aligned 總數=dev 721);
  2. aligned 碼的 specByCode 列全數被該碼的 VariantSize 認領;非 aligned 碼的列
     留在 specByCode 原始表(本來就整表保留,不存在消失路徑);
  3. 佇列只增不減:A/C 佇列項全數原樣傳遞,D 只新增
     `regime_conflict`/`code_color_conflict` 兩類。
- 同 (碼,已知尺寸) 多列 → 去重為一筆 VariantSize、derivedFrom 認領全部來源列;
  同 (碼,尺寸) 的 priceBand/surface 等值衝突 → 該欄 null(原始值都在 specByCode,
  不猜不丟)。

### D4|無碼廠(Sodai 型)骨架路徑

- 結構性成立:Variant **只能**由 x_aligned 綁定紀錄構成——name_bound 是佇列內
  假說(M5-1 定案),D 讀不到它作為 Variant 來源,「硬推色名入庫」無程式路徑。
  整檔 0 aligned → variants=[] 自動成骨架;色樣+nameHint 全在佇列檔。
- JSON 加 doc 級旗標 `seriesSkeleton:true`(variants 空∧spec 頁有色樣),
  下游一眼識別「這檔只有骨架」。
- 反例守門進單元測試:佇列項即使 nameHint 唯一也不得晉升(Medley 15 筆教訓)。

### D5|color.en 標籤抽取(非鍵,首做,正確率=I)

x_aligned 色樣的圖說詞(沿用 doc_name_index 同一套圖說幾何:d≤max(1.5h,40)、
同折縫側)中過 is_name 的 token,依 x 序連接(STEEL WHITE 型);無 → null。
只做標籤,不參與合併。

## 二、單元測試案例清單(合成資料;每規則 正例+反例+邊界)

| # | 規則 | 案例 | 期望 |
|---|---|---|---|
| T1 | 體制A 正例 | 色組 {C1→60x60, C2→60x120, C3→30x60} | code=null;3 筆 VS 各帶 orderCode |
| T2 | 體制B 正例 | 色組 {C1→{60x60,60x120,30x60}} | code=C1;3 筆 VS,orderCode 全 null |
| T3 | 體制臨界 | 色組 {C1→60x60}(1碼1尺寸) | A 形式:code=null、VS(60x60,C1);無佇列項 |
| T4 | 體制反例(混合) | {C1→{60x60,60x120}, C2→30x60} | A 形式無損展開 3 筆 VS + 佇列 regime_conflict |
| T5 | None 尺寸邊界 | {C1→{None,60x60}} | 1 筆 VS(60x60,C1)認領兩列;不算 B 證據、無 null-size 重複列 |
| T6 | 全 None 邊界 | {C1→{None}} | 1 筆 VS{size:null,orderCode:C1}(碼不丟) |
| T7 | 跨頁合併正例 | C1 綁定於 p3 與 p5(兩紀錄) | 1 個 Variant,mergedFrom=[b:3:*, b:5:*] |
| T8 | 合併反例(異色名) | C1@p3 圖說 WHITE、C1@p5 圖說 BLACK | 合併為 1 Variant、color=null + 佇列 code_color_conflict |
| T9 | 合併邊界(折縫) | C1 左半頁+C1 右半頁(同 spread 頁) | 照樣以 code 合併(幾何不參與);同頁異碼同色名相鄰 → 不合 |
| T10 | 色名非鍵 | p3 WHITE(C1)、p9 WHITE(C2),無共同碼 | 2 個 Variant(寧可不合);色名不觸發合併 |
| T11 | (碼,尺寸) 去重 | C1→60x60 ×3 列 | 1 筆 VS,derivedFrom 認領 3 列 |
| T12 | 欄值衝突 | 同 (C1,60x60) 兩列 priceBand=T31/T14 | VS.priceBand=null(不猜);原始兩列仍在 specByCode |
| T13 | 無碼廠正例 | 0 aligned、30 色樣帶色名 | variants=[]、seriesSkeleton=true、佇列含全部 nameHint |
| T14 | 無碼廠反例守門 | 佇列項 nameHint 全 doc 唯一 | 仍不晉升 Variant(Medley 教訓) |
| T15 | 混合檔邊界 | 2 aligned 碼+30 無碼色樣 | 恰 2 個 Variant;skeleton 旗標=false |
| T16 | color.en 正例 | 圖說「PLASTER Rett. 60x60」 | color.en="PLASTER" |
| T17 | color.en 反例 | 圖說全小寫/全泛用詞 | color.en=null |
| T18 | color.en 邊界 | 圖說「STEEL WHITE」 | color.en="STEEL WHITE"(x 序連接) |
| T19 | 可追溯守恆 | 任意合成 doc | mergedFrom 覆蓋∧互斥;Σ=aligned;佇列只增不減 |

單元測試跑合成資料(不碰 corpus);dev smoke 另跑真 corpus 的 T19 全域版
(721/460/1181 對帳)+ A 三道回歸照舊。

## 二之二、I 後必辦回報(延後決定的正式追蹤;使用者指定,不得遺忘)

I(隨機非偏置驗收)跑完後,**專門回報以下兩個數字**,再共同決定是否開票:

- **(a) 體制 A/B 錯置率**:1碼1尺寸臨界一律 A 形式(doc 級投票未做)。I 的 GT 中
  「真 B 體制被放成 A 形式」的比例;高則補 doc 級體制投票票。
- **(b) 同色未合併比例**:色名不當合併鍵(SCH-3 未做)。I 的 GT 中「同色因無共同碼
  分列多個 Variant」的比例;高則提升 SCH-3(系列切分→系列範圍色名鍵)優先級。

兩條同時掛在 pipeline KNOWN_GAPS(JSON 隨檔聲明,下游可見)。dev smoke 起先印
`same_color_unmerged`(同 doc 同色名多 Variant 計數)當 (b) 的先行觀測值。

## 三、驗證(哪步吃什麼)

- 單元測試(上表,合成)+ dev smoke(可追溯守恆全域版+A 三道回歸)= D 的過關條件。
- 體制判定/合併「判得準不準」的正確率數字 = I(隨機批),D 不做宣稱。
- dev 目檢(允許):抽 Topcer(B 型)、Emil/Provenza(A 型)、Sodai(骨架)各一份
  的組裝結果看結構合理性。
