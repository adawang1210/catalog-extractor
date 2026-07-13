# 輸出品質自動稽核(audit.md)

日期:2026-07-10。對象:`product/` 下全部 13 份 dev 輸出(v6 綁定、A~E+K 產線)。
本輪**純讀 product/**,未動任何綁定/產線;唯一改動=viewer.py 加網址跳頁(`#p33`、`#p33/v8`),已重生 viewer/。

## ⚠ 硬界線(先讀)

**這份稽核只能發現「輸出內部的問題」,無法發現「型錄裡真實存在但整個沒被抓到的產品」(knownGaps 靜默漏抓:S2-1 全字母/長碼、S2-3 一次性碼、C 類純數字廠)。**那只有 I 的人工 GT 對照真實型錄才驗得出。所以這份稽核的用途是**縮小你的目檢範圍**,不是驗收;不得據此宣稱任何真實正確率或完整率。

分工:第一部分=我能判的技術可疑/矛盾項,逐份標記給你跳查;第二部分=我判不了、需要你肉眼拍板的產品價值題,我只挑實例、不下結論。

連結用法:先在專案根啟動 viewer 伺服器(`/opt/homebrew/bin/python3 -m http.server 8642`),點連結即開該檔並跳頁;`/v8`、`/q0` 會閃對應框並捲到卡片。

---

## 第一部分:技術問題逐份標記

總覽(13 份;v=variants、spec=specByCode 列):

| 檔 | v | spec | ①色名異常 | ②junk混入 | ③體制矛盾 | ④照片級裁圖 | ⑤內部不一致 |
|---|--:|--:|--:|--:|--:|--:|--:|
| 41Zero42 SOLO | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ariostea twin_s | 1 | 32 | 0 | 0 | 0 | 0 | 0 |
| Emil Millelegni | 15 | 70 | 10 | 53 | 0 | 0 | 0 |
| Ergon CornerstoneAlpen | 14 | 32 | 11 | 0 | 0 | 0 | 0 |
| FMG WALK | 33 | 256 | 1 | **518** | 0 | 29 | 0 |
| Iris pietra_di_bilbao | 0 | 7 | 0 | 0 | 0 | 0 | 0 |
| Level CG Light | 68 | 373 | 19 | 9 | 0 | 0 | 0 |
| MOSA Solids | 0 | 70 | 0 | 0 | 0 | 0 | 0 |
| Marazzi A02G-04 | 20 | 143 | 14 | 0 | 0 | 20 | 0 |
| Provenza Unique Travertine | 23 | 148 | 17 | 25 | 0 | 0 | 0 |
| Sodai Limerence | 0 | 5 | 0 | 8 | 0 | 0 | 0 |
| Topcer 2026 General | 1 | 15 | 0 | 2 | 0 | 1 | 0 |
| Viva Metallica | 18 | 30 | 4 | 0 | 0 | 0 | 0 |
| **Σ** | **193** | **1181** | **76** | **615** | **0** | **50** | **0** |

### ① 色名異常(color.en 溢收/多語/非色名)

**76 / 101 有色名的 Variant(75.2%)觸發至少一項訊號**;其中**嚴重 56 筆(55.4%)**=多 token 串接/超長/含非拉丁字母(EJ8L 型圖說溢收),輕度 20 筆=色名混入表面處理詞(Nat./Rett. 型)。分佈:Level 19(全嚴重)、Provenza 17、Marazzi 14、Ergon 11、Emil 10、Viva 4、FMG 1。**色名是身分鍵候選,這條直接影響可售性與後續 G 翻譯。**

最該先看 3 筆:
1. Level v8(157 字元、20 tokens,還混入他色的碼 EMYP/EMYR):`CALACATTA BOOKMATCH CALACATTA GOLD Rettificato Lappato Lappato EMYP Lappato EMYR …` → [Level p27/v8](http://localhost:8642/viewer/Level%20CG%20Light%202026.01%20Web.html#p27/v8)
2. Marazzi v2(21 tokens,整頁圖說收進一個色名,含他碼 MJWZ):`CROGIOLO Grande Look Pietra Sicilia Bianco Riga Ink Lume Dew Emerald …` → [Marazzi p9/v2](http://localhost:8642/viewer/catalog_A02G-04_en.html#p9/v2)
3. Ergon v10(含西里爾 ДЕКОРЫ、德文 Glasfasernetz,五語圖說串):`DEKORE DECORADOS ДЕКОРЫ LISTELLI SFALSATI* Valser Glasfasernetz Sobre` → [Ergon p15/v10](http://localhost:8642/viewer/CornerstoneAlpen%20Catalogo%202025.01%20Web.html#p15/v10)

### ② junk 混入(code 非真 SKU)

**共 615 個實例;其中 388 筆在正式輸出側**(specByCode 311 / orderCode 74 / Variant.code 3),227 筆在佇列(佇列本是待複查場,列供參考)。specByCode junk 佔比 = **311/1181 = 26.3%**。

型態拆解(依證據強度分;**FMG 定性已於 2026-07-10 二輪探查修正**,原「512 筆全是頁碼」不準確):
- **確定 junk——FMG 純數字 512 實例,實為兩族**:①**頁腳頁碼族 100 筆**(spec 65/佇列 35):印刷頁=PDF 頁−2、同位兩簇(x≈40/580、y≈83% 頁高)、邊帶命中 100/100,跨 65+ 頁;3 筆升 B 型 Variant(code=16/27/89)。②**包裝表數字族 361 筆**(spec 190/佇列 171):集中 p274–277 僅 4 頁,值域 10–90 高度重複(40/72/18/54 型=件數/箱、m² 包裝數值)。餘 51 筆=orderCode 54+variant.code 3,由上述 spec 列被合併認領傳染。**FMG spec 表 255/256=99.6% 為此二族,整檔 specByCode 仍屬報廢**。歸 S2-1/S2-3 殘餘;票=BACKLOG S2-4。
- **確定 junk——價格帶/等級逃逸**:Provenza T104/A107 共 25 筆(T/A 家族已知價格帶,該頁家族<3 未被 S2-2 分流)、Emil T23 共 51 筆(specByCode 27+orderCode 13+佇列若干)、Topcer R12 共 2 筆(**R12=DIN 51130 防滑等級**,且 Topcer 全檔唯一一個 Variant 的 orderCode 就是它)。
- **疑似、我判不了**:Level E046/E048/E079 共 9 筆(E+3位數,不像 Level 慣用 4 字母碼,疑價格帶但無詞表證據)、Emil E220 1 筆、Sodai C482/C372 共 8 筆(骨架檔的 spec 列)——列入第二部分請你拍板。

最該先看 3 筆:
1. FMG v0:頁碼 16 當 SKU 且判成 B 型 Variant(共 3 筆同型)→ [FMG p18/v0](http://localhost:8642/viewer/WALK1general_fmg_maxfine.html#p18/v0)
2. Topcer v0:防滑等級 R12 當 orderCode(全檔唯一 Variant)→ [Topcer p9/v0](http://localhost:8642/viewer/Eonian%20x%20Topcer%20_%202026%20General.html#p9/v0)(該列 prov 在 p22,viewer 未渲染 spec-only 頁,先看卡片)
3. Provenza q0:價格帶 A107 進佇列、T104×18 進 specByCode → [Provenza p34/q0](http://localhost:8642/viewer/Unique%20Travertine%20Catalogo%202025.04%20Web.html#p34/q0)

### ③ 體制判定與證據矛盾

**0 筆。**檢了兩個方向:判 B(code≠null)但該碼<2 已知尺寸=0;判 A 但單一碼跨 ≥2 尺寸(應為 B)=0。D 的體制規則在 13 份輸出裡與自身證據一致。注意:FMG 那 3 筆 B 型「規則上」也一致(頁碼恰好跨多尺寸列),它們的病是②的 junk code,不是體制邏輯。

### ④ swatchCrop 照片級(bbox ≥10% 頁面積)

**50 / 193 crops(25.9%)**:FMG 29、Marazzi 20、Topcer 1。自動分類(4×4 宮格亮度均勻度 inter_std;<14=材質特寫、>23=場景照、14–23=待人工):特寫 28 / 場景 16 / 待人工 6。**中間帶 6 張我已逐張目檢補判**(這是內容型態的技術分類,不是可用性判斷):Marazzi v9/v12/v14/v17=場景照、FMG v17=大理石紋理特寫、Topcer v0=拼磚版面產品圖(兩者皆非)。

最終型態:**場景照 20(全 Marazzi)、材質特寫 29(全 FMG)、拼磚版面 1(Topcer)**。可不可以用=第二部分你定。提醒一件事實:Marazzi 佔剩餘池 155/244=63.5%,此型比重在真產線只會放大。

最該先看 3 筆:
1. 場景照:[Marazzi p24/v17](http://localhost:8642/viewer/catalog_A02G-04_en.html#p24/v17)(廚房全景,磚只是背景牆)
2. 材質特寫:[FMG p67/v17](http://localhost:8642/viewer/WALK1general_fmg_maxfine.html#p67/v17)(滿版石紋,frac=0.35)
3. 拼磚版面:[Topcer p9/v0](http://localhost:8642/viewer/Eonian%20x%20Topcer%20_%202026%20General.html#p9/v0)

### ⑤ 內部不一致

**0 筆。**逐份驗過:mergedFrom 認領無重複、無 null id;derivedFrom 互斥且 100% 指到存在的 specByCode 列;prov 四欄完整率 100%(filename 法允許 page/bbox=null);needsReviewCount=佇列筆數 13/13;裁圖 PNG 檔案存在 193/193。(A/D/E 的 smoke 守恆本就斷言其中大半,本稽核用獨立腳本重驗,結論一致。)

---

## 第二部分:我判不了、要你肉眼拍板的(8 筆)

以下每筆都是「產品價值判斷」——能不能用、夠不夠好、算不算對,由你看完決定;我不下結論。

1. **場景照當 swatchCrop 可否接受**(影響 20/20 Marazzi crops,且 Marazzi=剩餘池 63.5%):[Marazzi p19/v12 臥室](http://localhost:8642/viewer/catalog_A02G-04_en.html#p19/v12)、[p24/v17 廚房](http://localhost:8642/viewer/catalog_A02G-04_en.html#p24/v17)
2. **滿版材質近拍當色樣可否接受**(29/33 FMG):[FMG p67/v17](http://localhost:8642/viewer/WALK1general_fmg_maxfine.html#p67/v17)
3. **拼磚版面產品圖**(多尺寸拼貼、非單一色樣):[Topcer p9/v0](http://localhost:8642/viewer/Eonian%20x%20Topcer%20_%202026%20General.html#p9/v0)
4. **圖說溢收型 Variant 該出貨還是該修**:綁圖可能對、但 color.en 毀且混入他色碼——這種 Variant 上線是資產還是負債:[Level p27/v8](http://localhost:8642/viewer/Level%20CG%20Light%202026.01%20Web.html#p27/v8)
5. **特殊件(Left/收邊條)綁定算不算對**:`EJUY Left Minimal Chocolate` 這類 Angolare 件被綁進主色系列:[Provenza p35/v15](http://localhost:8642/viewer/Unique%20Travertine%20Catalogo%202025.04%20Web.html#p35/v15)
6. **表面處理詞當色名的 Variant 身分**:`Nat. Rett.` 不是色、是 finish——這個 Variant 的身分還成立嗎:[Emil p23/v0](http://localhost:8642/viewer/Millelegni%20Catalogo%202023.03b%20Web.html#p23/v0)
7. **頁碼身分 B 型 Variant 的處置**(刪?降佇列?):[FMG p18/v0](http://localhost:8642/viewer/WALK1general_fmg_maxfine.html#p18/v0)
8. **疑似碼真偽**:Sodai C482/C372([p61/q1](http://localhost:8642/viewer/Sodai_Limerence_season_2026.html#p61/q1))與 Level E046/E048/E079([p25/v5](http://localhost:8642/viewer/Level%20CG%20Light%202026.01%20Web.html#p25/v5))——真 SKU 還是價格帶/貨架號,我無詞表證據可判。

---

---

## 補充:決策材料(2026-07-10 二輪探查;純讀,未實作)

### D1|color.en 溢收病因集中度

機制(讀碼確認):圖說收集帶=`assign_words` 距離 ≤ max(1.5×色樣高, 40pt) 且同折縫側;`caption_name` 只做 is_name 過濾(字母≥3、非泛用詞、非全小寫),**無帶距絕對上限、無語言過濾、無碼排除**。

76 筆逐 token/逐筆分解(一筆可多因):
| 病因 | 命中 | 集中處 | 修法量級 |
|---|--:|---|---|
| ①帶距無上限(色樣高→帶>35%頁高) | **42/76=55%** | Level 19/19、Marazzi 14/14 全中 | pipeline.py 1 行(帶距絕對上限) |
| ②多語圖說同義串 | dup-token 25 筆、非拉丁 8 筆 | Ergon/Viva 表頭型 | 非拉丁濾=1 行;同義行選擇=大票(併 SCH-2 詞彙表) |
| ③finish 詞混入(Rett./Nat./Lappato) | 21 筆 | Emil/Ergon/Viva | 複用 C 的 finish_vocab 過濾(數行;Marazzi「Lux」兼色名成分,須目檢) |
| ④B類漏抓真 SKU 洩入(EMYP/EJUY 型) | Provenza 11 筆主體 | **交叉證據:這些「碼」全不在 specByCode=S2-1 漏抓的真 SKU 浮出** | 根治=S2-1;防禦=cap 排除 codes_doc 1 行 |

**結論:病因集中——嚴重 56 筆的大宗(42 筆)由單一幾何病因①貢獻**;①+②非拉丁+④防禦合計約 3 行 label 層改動(只動 cap→color.en 標籤,不碰綁定/佇列/name_index(釘 v3)/v6 凍結),回歸=色名長度分佈對比+抽樣目檢,不吃 held-out。③與②同義行是另兩張小票。插隊考量(事實供判,不下結論):此修與 knownGaps 漏抓修復(偵測層)機制完全獨立可並行;若 I 要報「color.en 溢收率」,先修則 I 只驗一次修後狀態。

**▶ 落地結果(2026-07-10,使用者拍板插隊後實作,D5 色名標籤 v2)**:實測推翻原「d 帶距上限」提案——照片級色樣的溢收詞 d=0(assign_words 規則1 xrow),改為「貼緣窄帶」幾何:色樣高 >150pt 時圖說只收距上緣 ≤35pt/下緣 ≤16pt 的詞(dev 全集掃描選值,平台期 30–35/16–20 非刀口;真圖說貼緣、帶外=頁面文字),加排已偵測碼+非拉丁濾。**雙軌守門**:衝突偵測用 v1 全帶圖說(colorRaw)——防「窄帶使一側證人變 null→殘存 junk 名補位離隊」(dev 實測抓到 6 筆:Level EDEP/EGGC、Marazzi×3、Topcer 技術頁文字,全數擋回佇列)。成績:溢收率 56/101=55%→28/85=33%(Level 19→1、Emil 2→0、Marazzi 13→8);gain 0/lost 16(全為 finish 詞與 junk 串→null 誠實);守恆全綠=佇列 519 精確(color 55/regime 4 不動)、Σ mergedFrom=721、Variant 193、八欄 289 頁零不一致、selftest 21/21(新增 T20 非拉丁/T21 雙軌守門)。副產品=capcodes.json 線索檔(S2-1 票已補指標)。殘餘 28 筆 severe=多語圖說同義串(Ergon 8/Provenza 9,小色樣幾何治不了)+Marazzi 底部多產品圖說塊(8,SCH-2/圖說切分層)。

### D2|頁腳頁碼通用過濾探路(不實作)

- 候選訊號(全結構、不寫死廠商):純數字 ∧ 跨頁同位聚類(20pt 圓整、≥5 頁)∧ 邊帶(y 中心 <8% 或 >92% 頁高)∧ 值−頁=常數族。
- dev 實測:FMG 頁腳族 **100/100 全中、其餘 12 份 0 誤抓**(但其餘 12 份純數字候選=0,考驗未至)。
- 對帳舊教訓:S2-2 曾試「頁碼過濾 all() 判準」dev 0 命中而移除——舊判準疑未含 offset 族(值≠頁,FMG 差 −2)。實作前先考古舊判準為何失手。
- 風險:41Zero42/Iris 純數字真 SKU 廠在 S2-1 落地後才是真考驗(真 SKU 理論上不會跨頁同位+值=頁±c,須 held-out 驗證);Sodai 稀疏判定翻轉案例須重驗(本訊號不碰稀疏判定,但 S2-2 有「digits 分支不動」定案在先)。
- **包裝表族(361 筆)不適用此過濾**——非頁碼,是包裝欄數值;歸 S2-1/S2-3 結構重建或 C packing 語境,S2-4 票僅記量。

附註(方法與可重跑):稽核腳本在 scratchpad(`audit_scan.py`,facts 落 `audit_facts.json`),純讀 product/+catalogs/ 頁面積;junk 判型=頁碼對齊/價格帶正則/單位正則;色名訊號=token 數/長度/非拉丁/Titlecase 混排;裁圖分類=64×64 灰階 4×4 宮格亮度標準差。②的「疑似」三組與⑤的 smoke 重疊部分已如實標註。
