# 案3|欄位級 provenance 掃描器 總帳(dev/field_prov_scan.py)

純儀器、只讀、不修只曝光(通案三入庫)。掃產線輸出(product 形制目錄)五類欄位級風險,
每筆回指 token/頁/bbox/raw。**不改任何產線行為、不裁決白名單。**

跑法:`/opt/homebrew/bin/python3 dev/field_prov_scan.py product=catalogs [--max N]`(CWD=專案根)
      `… --selftest`

## 紅燈先行(鐵律7)
F1/F1b/F2/F4碰撞/F4別名/F5 六 AC 實作前 RED(接手時骨架偵測器空轉,selftest=RED 確認)→
實作後全綠。F3(啟發 info)同輪補 AC-F3(非嚴格紅燈先行,誠實註記)。selftest 10/10 全 PASS。

## 全池頻率表(product=catalogs,現行 V=12 輸出)
| 類 | 筆 | 檔 | 說明 |
|---|---|---|---|
| F1_code_price_swap | 5 | 1 | 碼形 [A-Z]d3 ∧ 同檔同字母帶家族≥3=碼/價互換候選(high) |
| F1b_pseudo_code | 1 | 1 | pseudoCodeSuspect 旗 或 code(≥6)=檔名子串 |
| F2_field_mixing | 136 | 4 | size 非尺寸/surface 含數字單位包裝詞/band 非帶形/packing 非數 |
| F3_series_split | 10 | 2 | ≥2 字首碼家族(各≥3)頁域不相交=多系列一檔候選(info) |
| F4_unit_alias | 1 | 1 | 跨鍵 ×10^k scale=同物異鍵候選(info) |
| F4_unit_collision | 2 | 1 | 同正規化鍵 ← ≥2 種尺寸形 raw |
| F5_multi_role | 0 | 0 | code 角色 ∧ 值角色並存(本池零) |

## 驗證錨(已知病例須被正確標)
- **A102 型(碼↔價互換)→ F1 命中**:Provenza `T104`(產品碼)與同檔 T 帶家族
  {T14,T17,T31,T49,T59}=5 成員 並存 → 正確標 high。核實=真家族非誤報。
- **S2-5 型(偽碼)→ F1b 命中**:Provenza `OPUS`(pseudoCodeSuspect 旗)。selftest AC-2
  另以 MILANO70 合成錨覆蓋。

## 停止線判定:**未觸發**(非災難級)
規格停止線=掃出災難級既存欄位錯誤(比照 L2 塌縮量級=誤綁出貨)。本池最大訊號
F2=136 筆為 **surface 欄混入包裝/trim 詞**(Emil/Ergon/Provenza/Viva 規格表,如
`surface='Box'`/`'Battiscopa Box'`),屬**欄級曝光噪音、非誤綁**;F1=5/F4=3 皆零星、
可人工核。無 L2 量級災難 → 不凍結,findings 交 VLM/人工 lane(通案五)。

## 已知邊界(誠實紅字)
- **F4_unit_collision 首版誤報→已修**:specByCode 列 prov 常指「碼」位置,rawf 回讀
  碼 token 而非尺寸原字串→初跑 54 筆/8 檔全為碼污染假碰撞。修法=rawf 結果須經
  SIZE_IN_RAW 濾出尺寸形子串(非尺寸=None 不計,鐵律2 寧不旗)→降至 2 筆/1 檔真碰撞
  (Topcer 拼磚頁 96x296←29X29X8 型 mosaic chip 尺寸,已知 VICTORIAN 姊妹檔髒區)。
- **F4_unit_alias 軟誤報**:`100x100cm×10x10cm`(A02G)同單位 ×10=兩個不同真尺寸、
  非單位別名,呈現為 info 候選(需人工排除)。detector 以 ×10^k 判別,無法自辨
  「真別名 vs 真兩尺寸」=info 級侷限、非 high。
- F2 surface 判別以 UNIT_WORD(含數字/單位/包裝詞);合法帶數字表面極罕、本池未見誤殺,
  但屬啟發式,計數供人眼複核非硬判。

儀器不裁決;findings=人工/VLM 材料。pipeline/core/凍結常數零改動,V 仍 12。
