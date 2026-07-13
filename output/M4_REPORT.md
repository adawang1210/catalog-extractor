# M4 驗收報告(catalogs4,2026-07-09)

範圍:M4-1(R1b2 尺寸修正)、M4-2(色名身分鍵)、M4-3(x 對齊全無→orphan)。
唯一一次接觸:v3/v4 各掃一次(output/m4_heldout_v3.csv / _v4.csv)+ 13 頁抽樣人工 GT。
**catalogs4 已燒毀(2026-07-09,GT 目檢後)。永不再用於規則調整或驗收。**

⚠ 本批分布刻意偏置(0general+PIPO=190/293 頁、Topcer/Sodai/Level/Viva 缺席、PIPO 60%
漏抓失真),**絕對值不代表全 corpus 水準,禁止跨批比較**;有效訊號=同批 v3 vs v4 差。

## 0. 抽樣宣告(憑 CSV 統計與自動訊號,未看頁選頁)

宣告驗收對象(Emil p15、Ergon p22/23)+ 每 doc n_codes 最大頁 + name_bound>0 頁全收
+ 2b 訊號頁最小/中位(p35/p90)= 13 頁 569 碼(51% of 1113)。
逐筆:output/m4_gt/GT_NAME_BOUND_VERDICTS.csv;overlay/JSON 在 output/m4_gt/。

## 1. Ablation 總表(輔助,系統性高估,勿當正確率)

| | v3 | v4 |
|---|---|---|
| x_aligned | 471(42.3%) | 471(同,綁定規則未動的印證) |
| name_bound | — | 60(5.4%) |
| needs_review | 642(57.7%) | 582(52.3%) |
| orphan / far | 13 / 332 | 632 / 66 |
| 尺寸關聯覆蓋 | 499(44.8%) | 482(43.3%,折縫過濾誠實化) |

## 2. 綁定真實正確率(GT 抽樣,真 SKU,junk 另計)

- **v3 67/495=13.5% → v4 84/495=17.0%(+3.5pt)**。低絕對值=偏置批(代碼表巨頁
  p151 佔 287/495)。junk 佔偵測碼 70/569=12.3%(T##/A## 價格帶、CM2、BODY3、TR3ND)。
- **v4 錯值輸出崩量:v3 ~481 筆錯綁 → v4 58 筆**(其餘全部誠實 orphan 進佇列)。

## 3. orphan 拆解(131→632;新增中 sampled 474 筆逐筆歸因)

- **97.9%=「v3 錯值→誠實 None」,計正確**(Emil p15 54、Ergon kv 86、p151 217、
  MOSA 13、Provenza 15…)。
- **真退步 10 筆(2.1%)**:
  (a) **Treverkhome p11 七筆(結構性)**:表格列首圖版型(列首產品圖+同列規格列),
  MLF3/6/4→Acero、MJW9→Betulla、MLF0/5/1→Frassino,v3 鬆散同列全綁對、v4 全誤
  orphan。這是 M4-3 的已知代價頁型,開修正票(見 §8)。
  (b) Emil p15 三筆(碰運氣):ECX5/ECX9/EEM3 按 y 帶巧合落對色,v4 誠實化;不視為
  結構性損失。

## 4. 四個決定性指標

### 4a. (色,尺寸) 二元組(可驗矩陣列,aligned 真 SKU 57 筆逐筆)

- **v3 21/57=36.8% → v4 52/57=91.2%**。修復實錘:Ergon p26 v3 25/41 筆尺寸=碎片
  「2x3,2」→ v4 全取正確(33x33/33x60/33x120);Provenza ELJ1-9 6/6 同修
  (33x120x3,2x3,2→33x120);FMG p136 5 對全對(5 筆 None=誠實缺,列上無尺寸)。
- 新殘口:**帶空格尺寸「15 x 15」SIZE_RE 不收**(MOSA 全檔 sizes=None)。

### 4b. needs_review 接住率 —— ⚠ 基線破了(結構性,立即回報項)

- **v4 佇列外錯綁 58 筆 vs v3 同頁 25 筆**:p151 尺寸圖示錯對齊 16(v3=v4 同錯)、
  MOSA 返回鈕錯對齊 9(v3=v4 同錯)、**name_bound 錯綁 33(v4 獨有)**。
- 病理:M4-2 名鍵把錯綁「洗白」出佇列——dev 60 筆全對看不到這風險,held-out 45%
  正確率使 33 筆錯值以「已救」身分逃逸。**這與 v3 的 98% 接住率不可直比**(v3 定義
  下 sampled 接住率≈456/481≈94.8%,低於 catalogs3 的 98% 是 icon 型逃逸多);v4 把
  「佇列抓得到的錯」全 orphan 化,剩下的錯全是佇列構造上抓不到的(aligned/nb)。
- 誤 flag:v4=0(佇列只剩 orphan,不再 flag 正確綁定;v3 基線 14.4% 的問題消失)。
- **處置建議(待裁決)**:name_bound 不離開 needs_review(降級為「佇列內附色名假說」),
  或守門加嚴至跨系列碰撞可擋(§4c),二選一後 name_bound 才有資格離隊。

### 4c. 色名身分鍵 held-out 成績(60 筆逐筆,GT_NAME_BOUND_VERDICTS.csv)

- **27/60=45.0% vs dev 31/31 目檢 100%**——dev 不踩單 token 碰撞,held-out 總目錄踩滿:
  - 0general p151:23/54。錯因全部=**單 token 色名跨系列/跨色碰撞**:GRIGIO→
    FRAGMENTA 四色 21 筆全倒進 LUXURY GRIGIO 頁;BIANCO CALACATTA 3 筆→COVELANO 頁;
    STATUARIO 2→Arabescato 色樣;PULPIS GREY 3→Pulpis Bronze;BALANCE IVORY 2→
    ONICE IVORY;p153 ASTRA 2→BIANCO/NERO UNI 頁。
  - 對的一半有系統性:**色名 token 全域唯一時全對**(THASSOS、LINCOLN、COVELANO、
    MACCHIA VECCHIA、VIOLA、FIOR DI BOSCO、ST. DENIS、GREY MARBLE、MARQUINIA、
    ALASKA WHITE)。
  - **Treverkhome 4/4 全對**(Rovere/Castagno/Quercia/Olmo→逐色正確)=第二家救回
    廠商,且其目標色樣的圖說帶含未偵測 B 類碼(MJWA/MJWC/MJWM),證明「漏抓→假無碼
    →色名鍵補位」鏈條真實存在。
  - **Ergon Tr3nd 0 筆=守門正確拒絕**(色名全是泛用材質詞組合 WOOD×8/CONCRETE×19/
    TAUPE×6 實體,K=3 擋下)——該救沒救的原因不是守門錯,是色名本身不可區分,
    需系列範圍鍵(SCH-3)。
  - **Emil p15 0 筆=junk 污染索引**:左半四張真色樣(IVORY/SAND/CONCRETE/BLACK)
    圖說帶被 T## 價格帶碼污染→「有碼不入索引」誤擋。**S2-2 清 junk 即可解鎖此頁
    整頁救援**(42 真 SKU 逐色標名,是名鍵理想頁型)。
- 救回廠商數:2(Ariostea 0general 部分、Treverkhome 乾淨);升級路徑明確=
  n-gram/系列範圍鍵 + junk 清洗,非機制推翻。

### 4d. 2b 圖說在上(逐筆,不稀釋)

- 宣告樣本 p35/p90:**標題級 4/4**(THASSOS ULTRA/MICHELANGELO ALTISSIMO、
  SABULA/PLUVIA 各自掛對板)。加計 Emil p15 左頁四色名標籤上圖說 4/4 → **8/8**。
- 與 M3 4/4 合計 12/12,無反例;建議 2b 由「已驗證(初步)」轉正(樣本仍偏標題級,
  轉正註記此限定)。

## 5. M4-GT1 立體圖判定:**A(無害)+ 發現同族真害「小圖形搶綁」**

- 立體圖本身=A:配件剖面線圖(MOSA p3 整頁)、尺寸空心方框(Emil p15)、battiscopa
  剖面小圖(FMG p136)、厚度 icon——全部未被收為色樣(無填色向量線稿,extract_swatches
  正確忽略),無代碼搶綁。
- **同畫面抓到的真害(B 族,但源頭不是立體圖)**:小型「有填色/raster 圖形」被收為
  色樣且**贏走 x 對齊**——p151 表頭尺寸小圖示吃 16 碼、MOSA p3 左上「<」返回鈕吃 9 碼,
  25 筆錯綁全部逃逸佇列(v3=v4 同錯,非本輪退步)。
- 擋除方案(開票,見 §8):per-doc 統計「跨頁重複小圖形」(同位置/近同 bbox 重複出現
  =版面家具,pHash 或 bbox 聚類)+ 色樣面積下限用 per-doc 中位數比例;僅動候選收集,
  與路由器相容、不丟頁、不寫死廠商。

## 6. S2 系列量測(GT 階段交付)

- **S2-1 B 類精確化(全字母 SKU)**:Emil p15 單頁 42 真 SKU 只偵測 11(**漏 31 筆
  =74%**,EKDM/ECXU/EDPF 型);Provenza ELJF/ELJG 同病。B 類是 Emil/Ergon/Viva 型
  廠商的主漏抓源,catalogs3 結論再確認。
- **S2-3 一次性碼下界(首個真實數字)**:0general 單檔 **273 筆 distinct 9-14 字元
  長碼(BL60400AN 型 battiscopa 碼),全部整檔只出現 1 次,s2gap ≥2 門檻 0 筆可見、
  codes_doc 0 筆收錄**——「連量測工具都看不見」正式坐實,規模遠超 A 類已知 54 筆。
- junk(S2-2)佔偵測碼 12.3%(sampled);新實例:T##(Emil 價格帶)、BODY3、TR3ND。

## 7. 折縫 >1.2 門檻泛化(GT 必辦)

- 9 檔開本:真 spread 1.37-1.56(Ariostea/Emil/Ergon/Marazzi/Provenza)✓ 全判對;
  單頁 0.73-0.74(FMG/Iris)✓;**MOSA 1.78=單頁寬幅數位開本被誤判 spread(風險實錘)**。
  本批傷害≈0(MOSA 尺寸帶空格本就未匹配),但寬幅開本上折縫過濾會誤擋跨中線關聯+
  name_bind 同側檢查誤裁。修正方向:spread 判定加內容訊號(左右半各自獨立頁碼/鏡像
  邊距),不能只看比例。

## 8. 本輪衍生票(進 BACKLOG)

1. **name_bound 佇列地位/守門加嚴**(4b/4c,v4 定案的前置裁決)。
2. **小圖形搶綁過濾**(§5,25 筆逃逸錯綁的來源)。
3. **表格列首圖版型救援**(§3a,Treverkhome p11 型 7 筆真退步)。
4. **帶空格尺寸 SIZE_RE**(§4a,MOSA 全檔)。
5. **spread 判定內容訊號**(§7)。
6. S2-1 B 類 / S2-3 一次性碼偵測(既有票,GT 數字已補)。
