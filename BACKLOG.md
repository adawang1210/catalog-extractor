# Backlog(2026-07-09 建;**M5 打包驗收完成:catalogs5 已燒毀,結果見
# output/M5_REPORT.md——M5-1 零逃逸 153/153+假說 87.6%、S2-2 零誤殺、
# M5-2 抓中 12/12/誤降 18/30(→M5-2b);等使用者定案裁決**)

## ★ I 批診斷後優先序(2026-07-11 使用者核准;詳 output/I_REPORT.md,舊序作廢)

I 實測(catalogs6 主批 10/10 Marazzi):可用產品圖=0、佇列 86%、B 類漏 19%。
新序:**①M5-3 列版型救援(v7)→ ②S2-1 B 類全字母 → ③S2-3/C 類+稀疏閘重建
→ ④E-1 場景照+S2-5 系列名偽碼**。原「色名收尾→S2-4→漏抓」序=dev 錯覺產物,作廢。
catalogs6=已知病例回歸夾具(驗收效力已燒毀,實體保留);泛化=另建 catalogs7
(⚠ USED_DIRS 屆時加 catalogs6)。

## ★★ 外審行動清單(2026-07-11;審查方裁決後,優先於一切修理票)

外審核心:工程紀律全在防已知錯誤復發,三個前視盲區=樣本框(13 家義系≈宇宙
3~4%,「泛化」的誠實表述=在 9 個義大利品牌的未見型錄內)、召回認識論(幾何
規則結構上不知道自己漏了什麼,歷來靜默漏抓 100% 靠人眼)、佇列經濟(量級數萬
筆+召回稽核全頁人眼)。**舊修理排程(M5-2b/C 類/S2-5 等)全部暫停——普查⑥
與經濟表⑤出來後由使用者重排修理組合。**catalogs7 期間 held-out 紀律照舊。

- [x] **①版本控制+備份(2026-07-11 完成)**:git 庫=工作樹在 USB、庫本體在
      內接碟 APFS(~/catalog-extractor.gitdir;FAT32 實測 AppleDouble 污染
      pack 棄用 USB 內置)。不可再生資產全入庫;catalogs*/product*/viewer/
      skills 排除(內接碟僅 1.2G 之空間不可抗力;語料=Drive 依宣告 md5 可
      重抓、產出可重生)。**每輪收工必 commit,message 帶版本/票號。雲端
      異地備份方式待使用者確認(候選:Drive 上傳 git bundle,OAuth 現成);
      內接碟 100% 滿=獨立風險,已回報。**
- [x] **②「零錯」口徑退役(2026-07-11 完成)**:活文件全改「n=103 零發現,
      95% 上界≈2.9%」;M5_REPORT 凍結原文不動+日期化 ERRATA;公式與累積
      機制(每輪 GT 併佇列外抽驗、n 增上界緊)入 MVP_CONTRACT「統計口徑」節。
- [x] **③跨文件實體解析紅字(2026-07-11 完成)**:MVP_CONTRACT §三+
      pipeline.KNOWN_GAPS 新增「下游不得假設已去重」;修復時點=普查後使用者排。
- [ ] **④VLM 召回金絲雀試點(設計案;key 啟用等 D 板)**:定位=差異警報器,
      非真值源非擷取者,輸出永不回饋規則、永不入庫。試點=取已有人工 GT 的頁
      (I 批+夾具),VLM 每頁只答「這頁有幾個產品」,與 (a)人工 GT (b)系統
      偵測數三方對帳——先量 VLM 自己的準確度,再談當警報器。產出=混淆統計
      +(若可用)警報規則草案「偵測數 < VLM 數 − 容差 → 該頁進召回稽核佇列」
      (只設計,啟用另審)。邊界=託管免費層(規劃書允許、非中國模型)。
- [ ] **⑤佇列經濟學試算表 v1(2026-07-11 草案完成,econ_queue_v1.md)**:
      錨點=dev 1.57/I 批 5.50/v7 後 3.00 筆/spec頁、spec 占比 38%(兩批同);
      外推=全 corpus 佇列 9,000~42,000 筆、首輪人工 ≈400~900 hr(中間情境)
      +年度 120~900 hr;單價與損益線 Z 留白=使用者 C 板材料。
- [ ] **⑥全池版型家族普查(設計案先送審,執行等 A 板後)**:目標=量出版型
      家族分布尾巴(前 N 家族蓋多少頁),回答「修規則收斂嗎」。**新亮線
      (取代「碰過即燒」在普查場景)**:防火牆執行=獨立會話跑、每檔只輸出
      「家族標籤+頁級特徵聚類」、逐頁特徵不落 dev 語料目錄、全程不寫不改
      規則→不算燒;超出(規則訊號調試/GT/人工翻閱)=算燒。工具=推廣
      caption_signal.py/m5_signal.py 型「不看頁的訊號」到全池特徵抽取+聚類。
- [ ] **⑦catalogs7 打包驗收(v7+v8)執行條款**:(a)**A 板前不執行任何銷毀**
      (考完燒 vs 凍結計分板待拍);(b)新增必報=**新廠商首觸自動可用率曲線**
      (x 對齊率/可用圖率/佇列率;I 批第一點=18.4% 對齊,c7=第二點,此曲線
      =使用者商業主指標);(c)反例 4 件誤觸發率單獨列、須=0;(d)人工 GT 時
      併佇列外抽驗累積(行動②機制);(e)零讀取/規則不回饋照舊。
      **跑批完成+紅線停下(2026-07-11,c7_run.py;產出 output/c7_scan_v8.csv
      +c7_run_summary.md+product_c7/)**:主批 10=碼 339/x對齊 36.6%/塊綁
      16.5%/**自動綁定率 53.1%(曲線第二點;I 批=18.4%)**/佇列 46.9%/
      Variant 51/可用圖 38/照片級 13;pipeline vs scan 頁級守恆 14 檔零不一致
      (pipeline 已補 V≥7 塊綁鏡射+alpha_vocab 呼叫點,V=6 惰性、smoke 全綠)。
      反例:矩陣(TdM Revolution)/InDesign(Alter)/M5-2b(Ego)塊綁=0 ✓;
      **✗ FMG roads-465(堆疊型)塊綁 96/113、佇列僅 1——違反(c) 條款=紅線**。
      =M5-3 已知限制②預告型(同尺寸不等距堆疊+帶內少詞假欄,band/unif 雙閘
      照不到;反例件本為壓測此型而選)。**是否真誤觸發=人工 GT 裁定;零讀取
      紀律下未做任何頁內容診斷、未動任何規則。若 GT 判誤觸發:96 筆=自信
      錯綁量級,M5-3 需第三閘(另開票、新版本閘),v7/v8 定案與 pipeline
      切版全部凍結待裁。**
      **GT 判定(2026-07-11,使用者親驗,分支二)**:roads-465 p15=**真列
      版型、96 筆綁定全對**→反例誤觸發條款通過 4/4=0;探針落空註記(限制②
      堆疊型假欄仍未量測、照掛)+頁型掃描「堆疊型」定義可靠度存疑(本檔
      誤判,普查⑥設計須計入);96 筆列 v7 跨廠泛化正面證據(FMG,與 dev
      Provenza p36 blk=10 並列=Marazzi/Provenza/FMG 三廠實證);佇列外抽驗
      累積 n=103→199(上界≈1.5%)。**主批 10 檔 GT 進行中**:工作表+證據頁
      =output/c7_gt/GT_REPORT.md+viewer/c7_gt/(綁定 180 筆逐檔疊框);
      全部完成後打包送審=v7/v8 定案裁決,之前不碰切版/凍結/銷毀/④⑤⑥。
      **GT 收卷+定案(2026-07-12)**:主批判定逐字入 GT_REPORT §五(召回總表:
      漏 71 全落既知機制)、歸因 §六;Quarzite p6=版面事實 → 33/33 既知、
      c7 零新型;A102=量表碼值錯誤 4 筆(§六 C)→ 抽驗重算 n=375、上界≈0.8%。
      **v8 已定案切版**(pipeline V=8;凍結=output/s21_dev_v8.csv+
      v8_FREEZE.md;回歸全綠:selftest 22/22、v5-v8 bit-identical、v3/v4 差異
      =既知歷史語意 0 筆未解釋、smoke 289/289 守恆);catalogs7 轉夾具
      (禁調參;銷毀=A 板)。餘留:打包送審文件包=GT_REPORT+v8_FREEZE+
      e1_design_v9;反例 4 件與 I 批曲線已在 c7_run_summary。

## 修理票(v8 後;2026-07-12 建票。硬條款貫穿:c7=夾具禁調參;動凍結=
## 新版本閘+完整儀式;訊號全 per-doc/per-page;禁單檔擬合)

- [x] **L2 塌縮緊急補丁=下架 V=12 產線既存塌縮(工作包#7 已落地,2026-07-13;
      設計=output/l2_collapse_design.md 附錄)**:assemble() union-find「同色樣
      實例∪同碼」無守衛→hub 色樣+橋接碼傳遞連通成跨頁 color=None 巨團。塌縮守衛
      =cluster 層後驗簽名(跨頁∧色名衝突∧mergedFrom≥**L2_COLLAPSE_MIN=20**,凍結)
      →降級佇列 assembly_collapse_suspect(失敗方向=寧不合併、資料無損、無版本閘)。
      **鐵律8 全量 diff(--whitelist 12,84 檔):移除 Variant 恰 4 塊=Provenza 30/
      Topcer VICTORIAN 1021/FMG terrapura 115/Stream 32(全 color=None),白名單外
      新增 0、其餘逐筆零變化**(「7 塊」定案=V=12 恰 4、另 3 為 v13 誘發)。selftest
      27/27(新增 T27)、m3 selftest OK(core 零改動)、smoke 通案四押帳欄塌縮逃逸=0、
      dHardening 2→3、掃描層 byte-identical。制度補洞 MVP_CONTRACT 通案四=核定生效。
- [x] **單頁過併守衛(段1;工作包#9,2026-07-13 已落地)**:塌縮簽名補位——單頁 hub
      版塊(純碼索引頁)同色名吞併整頁不同碼,跨頁守衛(pages≥2∧衝突)照不到。判別子
      =單頁 ∧ mergedFrom≥L2_COLLAPSE_MIN ∧ **主色樣 area%≥AREA_T(=5.0,新常數凍結;
      隙中[2.36,7.02])**→ 降級 **singlepage_overmerge_suspect**。area% 經 extract_pdf 建
      page_dims(頁號→頁面積)傳入 assemble(無 swatch/JSON schema 變更)。**校準(通案二/
      鐵律4)=dev/pkgB_hub_sep.py --floor 2:合法單頁 hub 上界 Ergon Woodtouch p13 2.359
      (對 2.36)、過併下界 Ariostea p152 7.015(對 7.02),5.0 落隙、0 誤旗**。**鐵律8 全量
      diff(--whitelist,84 檔):恰移除 Ariostea 0general 兩 Variant[34-/82-merge]、白名單
      外 0**。selftest 28/28(新增 T28)、m3 OK(core 零改動)、smoke 289/289 逐位守恆+單頁
      過併團 0/單頁逃逸 0(0general 在 catalogs4 非 dev smoke 集)、dHardening 3→4。包 A
      巡檢=無第二災難、灰帶 1 例(Emil p23)掛常態監看。無版本閘 V=12 即生效。
- [~] **L2 塌縮正規修法(完整版;工作包#7 緊急補丁之超集;段2 驗證大半完成,2026-07-13)**:
      與緊急補丁共用判別子。**段2 已辦**:①N v13 世界複校準(dev/assembly_probe.py --sig 13
      全 7 語料)——★真下界=**20**(Marazzi/Uniche_A0BO 有 20 與 27 兩團),非交接稿的 27;
      非塌縮上界=19、空隙 [19,20]=**零邊際**,N=20 為唯一分隔整數(接 20/除 19),不動。②v13
      交互驗(dev/l2_v13_interaction.py 全 7 語料)——塌縮守衛接住全部 v13 誘發塌縮:A02G
      xpDemote 119、Uniche 47(=20+27)、Rice 44;**★通案四硬閘 escGE20=0、spEsc=0 全檔加總
      達成**;救回分流(med_ex 淨增綁定→輸出/→塌縮佇列)=A02G +46(-73/+119)、Uniche +50
      (+3/+47)、Rice +26(-18/+44)、Ego +20(+20/+0=健康救回全進輸出)。**段2 剩餘**:AC-5/AC-6
      完整紅燈套(AC-5 已由段1 T28 對偶覆蓋)+SL-6~8 收編 779 複跑。fan-out 上限修法已否決。
      與 A102 嵌合體同根(見下 S2-2 延伸)。
- [x] **★M5-2b(v13)切版前 blocker=sub-20 真塌縮逃逸——已解(案1 零邊際合併權限,
      工作包#10,2026-07-13 外審修正案)**:外審裁決推翻「需替代訊號」前提=**正解是取消
      自動決策權限,不換訊號軸**(兩軸已測皆不可分=通案五停止規則);落地=①不確定帶
      [L2_BORDERLINE_MIN=18,20) 跨頁∧衝突→borderline_merge_suspect(A02G-18/Topcer
      General-19/Uniche-19(v13) 全落降級側,合法衝突上界 16=Level 型、空隙 17)
      ②爆炸半徑 pages>5 ∨ mergedFrom>24→assembly_merge_radius_suspect(恰接 Topcer
      VICTORIAN DESIGNS 11/8p+19/12p+42/16p=dev 1021 姊妹檔次臨界變體,V=12 產線
      既存出貨、無衝突簽名=帶也照不到的型)。selftest T29+紅燈 dev/
      l2_borderline_selftest_draft AC-1~6+鐵律8 白名單(--whitelist-case1 全 7 語料
      ×v12/v13)+通案四第三/四硬閘。總帳=output/l2_borderline_merge_ledger.md。
      **殘餘已知缺口(不在帶內,通案五 VLM lane)**:<18 之 sub-band color=None 出貨
      (A02G 餘 7 個 ≤13)帶 code_color_conflict 旗=非全靜默;帶外監看=--borderline
      合法側分布(16 上界若增長貼 18 會縮空隙)。原票文案(診斷仍有效)留底:
  <!-- 原票(2026-07-13 段2):
      N 零邊際複校準暴露結構缺口——塌縮守衛以 size≥N 為閘,但**真塌縮存在於 <N 帶、被 <20
      容忍帶掩蓋**(非「貼近可接受的近失」)。定性證據(dev/l2_v13_interaction.py --dump,只讀):
      **Topcer General 19 團=真塌縮**(v12 產線既存+v13 同):跨頁 5/9/21/22,格式碼 OCT/STP/TR
      +尺寸碼 W##X##X8 經共享格式碼橋接,**全 colorRaw=junk**(表頭「CARTON PALLET Measurements」、
      規格段「Data Unglazed DESIGNING COMPONENTS…」、碼片段),非真色名;**Uniche 19 團**(v13 誘發)
      同病理(同檔 20/27 之弟)。→ size 閘無法分離塌縮 vs 合法(19 有真塌縮、亦可能有合法),
      **替代訊號候選=colorRaw junk 偵測(長/表文字 caption)或橋接碼 fan-out**(注:fan-out 上限
      前已否決,但「橋接=colorRaw junk」複合訊號未測);與段4 S2-4 非產品 token 同源。
      現況:V=12 產線即有此類 sub-20 color=None 出貨(A02G 8 個 maxNone=18、Topcer 19=實錘),
      帶 code_color_conflict 旗=非全靜默但仍出錯綁 Variant。**逃逸(≥20)=0 為當前交付(守衛只接
      大塌縮);<20 真塌縮=已知缺口,M5-2b(v13)切版前必解(v13 世界更危險=Uniche 誘發),非再議**。
      量測工具入庫(通案三):dev/l2_v13_interaction.py(--dump 定性/主模式 v12v13 交互+救回分流)。
  -->

- **c7 用途邊界(2026-07-12 裁決⑤(d) 補款,約束本節全部票)**:
  准 **(i)** 修復率(只讀計分);准 **(ii)** 已驗證正確子集零變化斷言
  (152 筆塊綁屬此;E-1 回歸之 c7 斷言即類型 (ii));
  禁 **(iii)** 調參/以 c7 diff 迭代實作。**本次 E-1 核可=類型 (ii),
  不得引為 (iii) 先例。**
- **c7 身分定規(2026-07-12 裁決,定案)**:病例夾具角色(修復率+失敗
  審計)與回歸計分板角色(類型 (ii) 零變化斷言)**並存;兩者皆非泛化
  證據**。E-1 泛化證據=**dev only**;41/47 一律稱**夾具修復率**,不得
  作任何泛化表述。catalogs6 同規。

- [ ] **E-1|場景照搶綁(下一張修理單;方向已核可,v3 全表送審中)**:設計=
      output/e1_design_v9.md(**v3=全表 T1-T9+T5b(逐案場景/v8 基線斷言
      先綠/v9 期望/紅綠語意)+附件 A(T6 覆蓋指名型)/B(紅燈複合斷言)/
      C(常數審計含 S2b 之 40)+T5b 設計意圖確認行;齊件即審即批**)。
      判定式 v3 簡化:**photo_sus=S1∧¬S2 逐綁定;S3 退為診斷訊號**
      (v2 之 S1∧(S3∨¬S2) 有推翻正面證據缺陷,v2 表 T5 矛盾已修正拆
      T5/T5b)。降級不刪除;紅燈=T2/T3/T4/T6/T8/T8b/T9。ROI=13.9pt、
      無偏頻率 4/10 檔、夾具=c7 四檔 47 筆照片級綁定+catalogs6(c7 用途
      =類型 (i)(ii),見上補款)。
      **v3.1 已核可+實作完成(2026-07-12,全綠停下)**:判定式=
      photo_sus=S1∧¬((S2a∧唯一對齊碼)∨S2b)、V9_G=0.10 單全域臂(中位臂
      /折縫基底經 dev 否決);T6 翻面(原審預授權第二分支)+T6u 唯一性
      對偶入表。結果:selftest 全過、v8 逐位不變、dev 三零+降級 79=分離
      量測逐筆吻合(A02G 77+Topcer 2)、**c7 夾具修復率 41/47**(6 筆單碼
      =T5b 類保留)+塊綁 152/152、**catalogs6 夾具修復 58**+塊綁 137/137;
      證據頁=viewer/e1_catalog_A02G-04_en/(+Topcer 代價、FMG 零誤殺);
      dev 紀錄=output/e1_dev_v9.csv(候選凍結)。**V=9 pipeline 切版=等
      使用者親驗,本輪不切;送審包=e1_design_v9.md v3.1 節+三份證據頁。**
      **M5-2b 裁決補註(2026-07-13,路線 (a) 已知後續成本)**:v13 起
      doc_icon_stats=真分叉雙中位(v9 側枝現行走舊全體中位=逐位不變);
      **v11 併軌時 E-1 須於 med_ex 世界重跑全套驗收**(E-1 與 M5-2b=同病
      兩面:V9_G 擋照片搶綁、M52_BIG 剔照片出中位母體,同一雙峰谷帶獨立
      校準)。
- [ ] **S2-1 延伸|③同列無尺寸+②無錨欄/無錨頁(工作包#1 設計完成,
      2026-07-12 送審中=output/s21ext_design.md)**:
      **③型主案「塊內尺寸繼承」**(rowsz' 沿欄連續塊上溯;RUN_GAP=2.0 平台
      期校準;分離量測:dev+c7 新收錄 125 種全真碼零散文,c7 修復 29/31、
      dev 真碼 +48、夾具反例件 +48);SM-1~4 基線已綠(m3 selftest 案 12)。
      **工作包#2 實作落地(2026-07-12,送審中=s21ext_design.md 實作結果節
      +v12_FREEZE.md;pipeline 仍 V=10)**:SM-1~SM-6 全綠(SM-6=3/5 字碼
      防隱形字長假設)、v8/v9/v10 逐位、GT 修復 29/31 準確兌現、佇列零消失、
      c6 零 diff;**偏離二處逐筆歸因**(UT +41 vs 43=邊界殘留 5 筆漏救向、
      TdM +30 vs 24=EHQ 族比值 1.75;根因=模擬器成員母體語意差,新收 129 種
      全真碼零散文,分離結論不變);RUN_GAP=2.0 未動,as-built 校準=分離帶
      (真碼上界 1.75/散文下界 2.22)。
      **四裁決落地(2026-07-12)**:(a)(b)(c) 核備——UT 邊界 5 筆
      (EJSW/EJSY/ELLD/ELLE/ELLL)改歸檔「**此訊號軸已證不可分**(比值帶
      2.0–2.54 與散文下界 2.22 重疊,OPUS/OCT 先例),待其他訊號、禁為此
      動 RUN_GAP」;FREEZE 校準改寫=原平台期依據失效、現依據=事後分離帶
      1.75–2.22、餘裕窄(−12%/+10%)、新文件中間比值=已知脆弱點。
      制度=通案三入 MVP_CONTRACT(設計期量測工具一律入庫;模擬器失傳
      =本案根因);工具已入庫 dev/s21ext_kept_diff.py+s21ext_probe.py+
      預測帳。**(d) 使用者親驗通過(2026-07-12 紅框無異議)→ V=12 已切版**
      (工作包#3 步1:pipeline V=12、smoke 對 s21ext_dev_v12.csv、四版本
      逐位+守恆 1564 全綠)。
      **②-vis 可見化票(工作包#3 步2)=設計期陣亡×2,凍結等裁
      (2026-07-12,output/s2vis_design.md)**:token 級 dev 誤旗標 2303
      (佇列+505%,ANGOLARE/GOLD/UNI 型=b2b 同根:碼形欄零錨軸與散文欄
      不可分)、頁級降級 50–85% 頁亮旗=零資訊量——預授權路徑用罄;
      召回側滿分(PE p21 26/26+PS 親驗病例 14/14 全接住)。rowsz 變體
      否決(漏 PS 塊頭型=親驗發起病例)。**承接候選=rowsz' 塊內繼承
      欄級移植(未量測,需裁決)**/頁型限定(形狀邊緣)/VLM④/手工。
      步3 S2-5 偽碼旗標未啟動(整包凍結紀律)。工具=dev/s2vis_probe.py。
      **裁決①②落地(2026-07-12)**:blocksz(rowsz' 欄級移植)量測完成
      (s2vis_design.md blocksz 節=兇手逐筆帳)——色名條欄/認證欄被塊軸
      擋下 ✓、包裝表欄+碼列同列詞欄穿透 ✗(與真碼欄全幾何軸同構),
      dev 764=佇列+168%、最佳頁 S/N≈1:2=**②型第五次陣亡,預案生效
      歸檔:「②型殘留:現有幾何訊號不可分,待 VLM 金絲雀承接(D 板);
      禁止第六案」**。召回側證據保全(機制族召回 100%=PE 26+PS 14+13,
      VLM 承接時=現成考卷)。步3=S2-5 票已實作送審(線③)。
      **②型兩候選(同列他欄錨/無錨頁回退)實測否決**(色名穿透=誤綁方向;
      守門「碼形欄成員」失效:GOLD 欄 27 vs 真碼 ENUF=1)→ **29 筆殘留宣告
      +GT 監看**;承接方向候選=per-doc 欄格外推(初步不利)/VLM④/S2-5。
      ②錨帶外 10(EMJ 族)不屬本包,照掛。
- [ ] **S2-2 延伸|量表碼逃逸(A102 型;2026-07-12 裁決④釘死,設計送審制、
      不啟動)**:c7 實錘=值錯誤綁定 4 筆+嵌合 variant 1(GT_REPORT §六 C;
      嵌合 variant 已加 knownDefect 註記)。**形狀級修法必錯**——Rice
      M961-M969/Limestone M907 同形([A-Z]\d{3})真碼實證,**禁任何位數/
      前綴形狀條件**。**修法限 per-doc 脈絡訊號**,候選:(a)共享標籤 occ
      簽名——A102 沿整排色樣重複(同列五欄各 1 實例)、與 v8 finish 縮寫
      同族的「一 token 配多實體」結構;(b)價格帶列結構——band 家族
      (A11…A86)所在列/欄位置關聯,3 位數成員按同列同欄結構歸隊。
      **②歸因(D 紅線僅接住 1/4 死因,§六 C 補記)**:L1=assemble 合併鍵
      無條件信任 code,junk 碼毒化鍵鏈併 4 色樣;L2=code_color_conflict
      偵測單位=cluster 級(1 筆/嵌合,非綁定級)且處置=color=null+佇列、
      **無解鏈機制**。**D 階段加固=本票子項(不另立票)**:「跨 ≥2 色樣
      共享、且每色樣另有專屬碼」之碼 → 不作合併鍵+逐綁定降級佇列
      (per-doc 結構訊號,非形狀)。**加固設計必含分離驗證合成案例
      (2026-07-12 裁決②補款):注入值錯誤碼 → 斷言 D 不成嵌合(即便上游
      偵測未修)——上下游兩層獨立成立、歸因可分;band/unif 先例。**
      BAND_RE/合併鍵=凍結,動=新版本閘+完整儀式;設計案送審核可後才動
      code。統計口徑連動:原始口徑(379/4/≈2.4%)有效至本票修復落地
      (MVP_CONTRACT §三之二)。
      **設計核可+L1 實作全綠、L2 紅燈回滾+v2 修正案送審(2026-07-12,
      output/s22ext_design.md 實作結果節)**:
      L1(v10)完成——band_regroup P∧(B∨A')、S22_ROW_N=3 凍結(修正①)、
      SL-2 對抗構造過(修正②)、E-1 閘==9 懸空編碼化(修正④);回歸:v8/
      v9 側枝逐位不變、dev v10 diff=3 頁全歸隊 token(A107 值錯綁定 −9)、
      夾具=PortlandStone A102 −4+**TdM 額外歸隊 5 token(第三 Emil 檔泛化)**
      +catalogs6 零 diff;殘留 T104 照宣告;③重合檔=dev 零病例 → 未量測
      殘留+GT 監看。**L1 切版(V=10)與口徑升級等三條件+使用者核可。**
      **L2 原案(C0)SL-10 白名單紅燈:dev 降級 739/1070 → 已回滾(溯源入
      通案二範圍擴充)。L2 v2(C3)已核可+落地(2026-07-12 裁決①⑤)**:
      assemble band_letters 參數、SL-6 改造=「B/A' 雙偽逃逸+L2 接住」注入
      構造入常備回歸(T23 四部:逃逸證明/接住/P 對偶/橋接對偶);dev 降級
      =0(純備援)、白名單=僅 dHardening 標頭。**已知限制明文:P=L1/L2
      共模單點,殘餘暴露=無家族字母毒碼型(T104 屬此)——GT 監看。**
      **v10 已切版(裁決②,證據頁 viewer/s22_l1_v10/ 七頁存檔免親驗);
      口徑升級證據包三件齊(s22ext_design 末節),待使用者一句核可生效。**
- [ ] **手工車道清單(C 板損益線實例帳;不開規則票)**:
      第 1 筆=Mystone Ardesia20(壞損 PDF;整檔唯一產品 MFJS p4,SIZE_RE
      整檔命中 1<3=spec 閘結構性不可見)→ 建議人工登打 1 筆,單價/損益線
      =C 板材料。後續同型(整檔 ≤N 筆可救量)一律先入此帳再議票。

## M5 驗收衍生(2026-07-09)

- [x] **M5-2b|B 訊號中位數基底修正——dev 完成(2026-07-13 工作包#4+#5,
      v13 版本閘;pipeline 仍 V=12,切版=送審後另裁)**:原票 Re-Play p34
      誤降 18 筆——doc 中位被情境照撐高,<0.05×中位失義。定案(設計=
      output/m52b_design.md,凍結=output/v13_FREEZE.md):**med_ex=排除
      ≥M52_BIG(0.10,凍結)×頁大圖後小簇中位,單調⇒構造性零新增真色樣誤殺**;
      med_pg 整組否決。工作包#4 反查②=v9 實際依賴此中位(V9_G 吸收假說不
      成立,依賴逐筆 10 檔 335 碼);**裁決路線 (a) 真分叉雙中位((b)(c) 否決
      入檔)**:v13=med_ex、v≤12 含 v9 側枝=逐位舊路(第一硬條件)。
      總帳(預測帳先押後開全兌現、白名單外零違規):**dm 520→151=救回 369;
      病例 148 全救(Re-Play 60/Uniche 50/Ego 20=c7 (i) 修復率 20/20/Vivo 18)
      =解鎖 Uniche(B 類最大檔)+Vivo 可用圖**;正確殺 icon 母體 145 碼
      (Stonetalk/Woodtouch/next/PIPO)逐碼零鬆動;五版本(v8/v9/v10/v12)dev
      重掃 byte-identical;selftest 新增 (8b)+draft 紅燈 3/3 轉綠=常備回歸。
      殘留:icon 洩漏帳未開(預授權方向,GT 監看)。原 M5-3 夾具 ROI 帳
      (Uniche 22+Vivo 13=35 筆)=塊綁子集,已由本修理連帶救回。
- [ ] **名鍵升級票補充證據(M5 GT)**:兩個 n-gram 治不了的新失效模式——
      (a) Medley 旋轉直排邊緣色名標籤被圖說帶錯收(索引實體錯,White→Dark Grey
      15 筆);(b) teknostone finish 說明塊偽色名(PEARL→說明塊)、圖說溢收
      (SOFT BLACK→TOBACCO)。索引建構的幾何品質是根,與 SCH-3 一併設計。

## M4 驗收衍生(2026-07-09,GT 實證;優先序待使用者裁決)

- [x] **M5-1|name_bound 降級佇列內假說、不離隊**(v4 定案前置)——**dev 完成
      (2026-07-09,使用者裁決採「不離隊」方案)**:m3_scan.py scan_page 佇列記帳改
      `review = n_codes - aligned`(name_bound 不再扣除);name_bind 演算法/五道守門/
      index 釘 v3 幾何全不動,name_bound 續算續報=掛在佇列項上的建議答案(加速人工
      複查)。dev 回歸全綠:selftest OK;v3 289 頁逐欄位一致(僅多 name_bound=0 欄);
      v4 vs 凍結 m4_dev_v4_m43.csv 僅 code_needs_review 欄逐頁 +name_bound(487→518
      =回到 v3 佇列規模),其餘欄位 0 差異;name_bound 仍 31(twin_s p29 30 筆+FMG
      junk 1 筆),twin_s 30/30 綁定目標不變、僅地位改「佇列內假說」。
      **held-out 驗證待下一批(批內須含撞名色名頁)**;catalogs4 記帳推算:佇列外
      錯綁 58→25(v4 獨有 33 筆歸零,殘 25 筆全為 M5-2 小圖示型、v3 同錯)。
      守門加嚴(n-gram 多詞全匹配/系列範圍鍵 SCH-3)=之後的離隊資格票,另開。
      原始病理存查:held-out 名鍵 27/60=45%(dev 100% 不踩單 token 碰撞;GRIGIO 21 筆
      倒進 LUXURY GRIGIO 頁型);色名 token 全域唯一時 23/23 全對,機制方向正確。
- [x] **M5-2|小圖形搶綁——dev 完成(2026-07-09,v6 版本閘,等 catalogs5 打包驗收)**。
      **設計轉向(dev 目檢實證後)**:原票「過濾/刪色樣」會屠殺真色樣——dev 校準
      發現兩類假陽性陷阱:(a) Level/FMG 網格型錄同版位跨頁重複=真色樣(天真 rep
      訊號誤標 363 個、上面 120 對齊碼);(b) Emil p24/Provenza p35 PEZZI SPECIALI
      收邊條縮圖+矩陣表頭色片=真產品小圖(面積 0.15×中位門檻誤殺 69 對齊碼,目檢
      PNG 確認全是 E297/EJKH 型真訂購碼)。定案=**降級不刪除**:x 對齊到疑似小圖形
      的碼 ok_x→否、落入 needs_review(錯殺=複查成本,與 M5-1 同哲學);色樣不刪、
      指派不動。判定 icon_sus 兩訊號(AND 組合,dev 零誤傷=硬約束):
      A'=同位(20pt 圓整)重複 ≥max(5, 50% spec 頁) ∧ 面積<0.5×doc 中位(返回鈕/
      頁角 logo;50% 頁數門檻排除 Level 矩陣型);B=面積<0.05×doc 中位(0.05=dev
      零誤傷上限,0.08 即誤傷 Emil 收邊條 32 碼)。dev 迴歸:selftest(新增 icon_sus
      案例)、v4 逐位凍結、v5 逐位=S2-2 紀錄、v6 dev 降級=0(=校準零誤傷)、
      twin_s 30/30 不動。凍結紀錄 output/m52_dev_v6.csv(+s22_dev_v5.csv)。
      **已知限制(GT 驗收看點)**:單頁型表頭 icon(p151 型無跨頁重複)只有 B 能抓,
      若 icon 面積 >5% doc 中位會漏(v3=v4=v6 同錯、佇列外);catalogs5 驗收必報
      6 檔 7 頁訊號頁(Ergon Cornerstone p27 78 碼最大宗)的抓中率與誤降級率。
- [ ] **M5-3|表格列首圖(列首色樣)版型救援——★升第一優先(2026-07-11,I 批
      診斷;原僅 Treverkhome p11 的 7 筆,I 證實=Marazzi 主力版型=母體 63.8%)**。
      證據(I_REPORT §2 診斷一):單系列型錄規格表頁=每色一張左欄小色樣+右側
      多列規格表(每列一尺寸一碼);碼在 Codice 欄 x 不涵蓋色樣 → 規則 1 失敗、
      下方列=遠端 sec 無 xin → M4-3 orphan。7/10 主批因此 0 Variant 或全場景照,
      可用產品圖=0。夾具頁:catalogs6 Stream p12-16/Hello p7-8/Treverkmood p15/
      Mystone p5/Uniche p12/Vivo p13(6 頁已目檢)+dev Treverkhome p11。
      **設計初案(2026-07-11,v7 版本閘)**:病灶=spike_geom.assign_words;
      解法=per-page 版型偵測(①色樣 ≥2 成左欄:x0 對齊+集中半頁左側帶;
      ②小圖非滿版;③頁 x 對齊率≈0)成立時,允許垂直區塊綁定(色樣 i 擁有
      [y0, 下一色樣 y0) 同折縫側、碼在色樣欄右側)。反例閘:矩陣頁(色樣成
      頂列)/情境照頁(1-2 大圖)/Emil p13(無左欄色樣)不得觸發。
      **風險主軸=M4-3 部分回退(30% 搶綁的教訓)**:泛化驗收第一指標=誤觸發,
      非救回量;鐵律 8 全量 diff(佇列離隊=設計目的,逐筆對頁目檢)。
      回歸電池:selftest 新增列版型合成案例、v3-v6 bit-identical、twin_s 30/30、
      Emil p13 45/45 orphan、name_bound 31。v7 定案後 pipeline V=7+新凍結
      m53_dev_v7.csv。驗收:夾具翻盤(主批可用圖 0→X/Variant 25→Y)+
      catalogs7 泛化(列版型頁真實正確率+非列版型頁 v6→v7 零 diff+佇列外
      錯綁基線維持)。建議與 S2-1 打包共用 catalogs7。
      **dev 落地完成(2026-07-11,等使用者親驗 diff 證據包後才 catalogs7)**:
      v7=spike_geom.m53_blocks(7 常數全相對量)+三 orphan 出口救援(d=-2.0
      哨兵)+m3_scan 記帳(code_block_bound 欄/名鍵閘 aligned+blk/塊綁到
      icon_sus 照 M5-2 降級)。**雙假欄閘 dev 凍結(不准再調,泛化=catalogs7)**:
      band 欄帶淨空 ≤2×成員數(擋 FMG p274-276 包裝箱表 50-84 詞)+unif 成員
      高度 max/min ≤1.5(擋 p277 貨架照異質堆疊 1.73)——蓋不同型態、dev 無頁
      同時中,歸因可分離(使用者裁決 2026-07-11,非「同洞疊補丁」)。合成 14 案
      (P1-3 正例/T1-T9 陷阱含 T8 圖標欄、T8b 欄帶文字、T8c 異質成員+真列 1.00
      前置斷言、T9 末塊下界)+官方 selftest 案例(9)。dev 全量:v3-v6
      bit-identical 維持;v7 diff=5/289 頁全真列版型(Provenza p36 blk=10 逐筆
      目檢碼→同列色片全對;A02G p37-40=閘 ON 正確但救援 43 筆全被 M5-2 A'
      同版位訊號否決→佇列不變僅記帳欄移動);FMG 四頁零 diff;name_hyp=31。
      **已知限制(2026-07-11 裁決固化)**:①band 小成員數時閾值鬆(2 成員容
      4 詞),p277 型由 unif 補;②「列 y 均勻」(原票語)不實作——真列版型欄距
      本就不均(Uniche p13=3.22、Stream p14=1.45,色塊列數不同),實作會殺真
      陽性;殘餘暴露=**同尺寸圖不等距堆疊+帶內少詞+右側碼形 token 型假欄**,
      catalogs7 反例件監看;③列首色樣被 M5-2 icon_sus 否決、該檔救援全滅
      (安全方向:一筆不綁=無錯綁可能,佇列保留)——兩種機制:dev A02G 總目錄=A' 同版位訊號
      (43 筆);**catalogs6 夾具 Uniche/Vivo=B 訊號中位數膨脹(情境照撐高 doc
      中位,表格色樣 5,858<0.05×中位 6,882/15,386;=M5-2b 既知機制,夾具實測
      35 筆:Uniche 22+Vivo 13)**——要救=M5-2b/動 A'=另開票,現階段接受;
      ④末塊 0.92 頁高邊帶會切掉貼頁底的真列(A02G p38 M6RS 實例:Musk 列
      y≈775.4>邊帶線 774.5 差 0.9pt,codes_doc 有、v7 誠實 orphan 留佇列=
      安全側;0.92 凍結不調,catalogs7 GT 順帶量此型頻率)。
      **catalogs6 夾具翻盤數(2026-07-11,修復率非泛化;V=7 鏡射 runner,
      pipeline 本體未切,產出 product_i7/)**:主批 Variant 25→53、
      **可用產品圖 0→34**、佇列 286→156,守恆 14/14 OK;骨架檔復活=
      Art 0→4/Mystone 0→3/Pinch 0→4/Treverkmood 0→1(MH05→Mogano 目檢
      正確);未翻=Vivo/Uniche(限制③ B 訊號)。
      **M6RS 核可(2026-07-11,審查方)**:(b) 定性成立=T9 末塊 0.92 邊帶
      切掉、安全側行為符合設計;0.92 凍結不調;限制④頻率=catalogs7 GT 順帶量。
      審查紀律(通案,審查方指示):**任何「X 不受影響」的預測須列出所有可能
      觸發的皮帶逐條排除,不只排除最近討論的那條**(本案教訓=夾具預測只排除
      A' 同版位,漏了 M5-2 B 訊號中位膨脹)。
      **catalogs7 放行(2026-07-11,硬條件)**:①反例件必含 M5-2b 型考題
      (情境照撐高 doc 中位、真色樣被 B 訊號誤 icon)+原有非 Marazzi 誤觸發型
      (矩陣頁/InDesign 型+同尺寸不等距堆疊型),**誤觸發率單獨列、須=0**;
      ②全套建批紀律=seed+宣告、md5 逐位防重(USED_DIRS 加 catalogs6 之外
      仍要跑)、文件級隔離、分布偏置宣告、碰完即燒;③打包=M5-3+S2-1 照原案
      (S2-1 dev 先行、動偵測=新版本閘同流程),M5-2b 趕得上同批打包、
      趕不上單獨開票不硬塞。
- [ ] **M5-4|帶空格尺寸(★重分類=core scan 層版本閘票,非小幾何票;段3 診斷糾正
      2026-07-13)**:★交接稿診斷有誤——**非 SIZE_RE bug**。SIZE_RE(census.py)已含
      `\s*[x×]\s*` 空格容忍、full-text `SIZE_RE.findall` 收「15 x 15」(故 spec 頁偵測正常)。
      真相=**core/m3_scan.page_sizes 逐「詞」匹配**(對每個 fitz word 之 t[4] 跑 SIZE_RE),
      而 fitz `get_text('words')` 把「15 x 15」拆成 3 詞(`15`/`x`/`15`),單詞皆不成 pattern
      →尺寸抽取漏接(MOSA 全檔 allSizes=0=實錘,但因空格拆詞非 SIZE_RE)。修法=page_sizes
      **多詞尺寸重建**(相鄰 NUM/x/NUM 詞合併)。**扇出=122 頁/12 檔**(dev 量測:full-text≥3
      ∧ 逐詞=0)——MOSA×6(Solids/Classics/Tide/PIPO/Murals/Stage)、Level CG×2、Topcer
      VICTORIAN、twin_s、con_crea、teknostone,**非 MOSA 限定**。page_sizes 同時餵 row_size
      (碼-尺寸綁定)+allSizes→**重寫凍結基線 s21ext_dev_v12.csv(code_with_size 等)+改
      variantSizes/regime**=需**完整版本閘儀式**(v14 或併軌)、紅燈先行、全量 diff 白名單、
      新凍結。★排程註:M5-4 動 core scan 層+重寫凍結基線,與 v13 切版(m52b_dev_v13.csv 等)
      有基線交互,先後須定(建議先過 M5-2b 切版或明確凍結順序)。
- [ ] **M5-5|spread 判定內容訊號(★YAGNI 延後;段3 診斷確認 2026-07-13)**:MOSA 1.78 單頁
      寬幅被 fold_x(width>1.2×height)誤判 spread(core/m3_scan.py:89)。**本批傷害≈0**
      (MOSA 為骨架檔、無碼綁定,折縫僅影響 caption/size 指派、無實際錯綁)=風險票非 bug 票。
      修法=左右半獨立頁碼/鏡像邊距等內容訊號輔助,不只看比例;per-doc、新常數宣告校準凍結。
      YAGNI 延後至見實傷病例再開(與 M5-4 同排程考量)。
- ↑ S2-1/S2-2/S2-3 的 GT 數字已補入各票;S2-2 清 junk 可直接解鎖 Emil p15 名鍵頁
  (42 真 SKU 逐色標名,T## 污染索引)。

## M3 已完成(2026-07-09,報告 output/M3_REPORT.md;catalogs3 已燒毀)

- [x] **M3-R1**:v3=規則 1 x 約束(x 涵蓋才立即綁,鬆散同列降級到 2a/2b/3x 之後)+
      向量家具過濾(僅 fallback 分支;raster 直立木板誤殺已在 dev 自測修正)。
      GT:綁定正確率 39.7%→51.7%;矩陣頁色正確 65.7%→92.6%(Provenza 61/61);
      規則1搶綁 38.8%→26.9%。⚠「無色樣頁變 orphan」未達成(回退仍綁),留 M4。
- [x] **M3-R1b**:row_size 上線;尺寸正確率 41.7%——缺陷:複合尺寸碎片(2x3,2)、
      同列跨頁污染、跨列串位(M3_REPORT §5),修正=M4-R1b2。
- [x] **M3-R2**:2b 首驗通過(標題級 4/4,v2=v3 無副作用)→ 狀態升「已驗證(初步)」。
- [x] **M3-M1**:needs_review 佇列上線——抓到 98% 錯綁、誤 flag 14%;far 退役。

## 本輪(M4)——heldout4 已建成凍結(output/heldout4_DECLARATION.md),等核可後動工
## 優先序=使用者裁定;needs_review 接住率為每輪必報且不得低於 98%/誤flag 14.4% 基線

- [x] **M4-1|R1b2 尺寸關聯修正**——**驗收過(catalogs4 GT):(色,尺寸) 二元組
      36.8%→91.2%,Ergon 25 筆+Provenza 6 筆 2x3,2 碎片全修**。實作(m3_scan.py v4,綁定規則不動、v3 逐位元凍結驗證過):
      (1) 複合尺寸整 token 解析(COMP_RE ≥3 段取頭段:33x120x3,2x3,2→33x120、93x93x8mm
      →93x93;dev 86 複合 token 中 15 碎片+其餘全漏,一次治好 Topcer p9 跨欄搶綁——
      x 距離上限經 dev 目檢證實不需要);(2) 折縫過濾(頁寬/高>1.2=spread,dev 實測
      1.41-1.63 vs 單頁 0.71-0.85,尺寸不跨物理頁;Provenza p33 EK6M 60x120→60x60);
      (3) above 欄親和(x 重疊候選優先於左側列標籤,治 P36631 型跨列串位)。
      **列塊分割未做**:dev 無可證病例(表格列相鄰無空隙,分割也治不了),欄親和已
      覆蓋觀測病型;若 catalogs4 GT 見殘餘跨列串位再開票。
      已知殘口(非本票):正確尺寸只在 >4 字高外的區段/欄標頭 → v4 給 None(誠實孤兒,
      優於 v3 錯值);cm/mm 混雜屬 allSizes 正規化票。
- [x] **M4-2|ID 色名身分鍵**——**驗收:held-out 27/60=45%(唯一 token 全對、單 token
      跨系列碰撞全錯)→ 佇列地位/守門加嚴=M5-1,升級路=n-gram/SCH-3+S2-2 清 junk**。
      機制(m3_scan.py v4 name_bind/doc_name_index,5 道守門,全 per-doc/per-page 統計):
      (1) doc 級預掃:無碼色樣(圖說帶無偵測碼、非極端長寬比 ≥6:1)的圖說色名→實體
      索引;(2) 頁級閘門:碼數 ≥5 且 x 對齊率 ≤20%(=heldout4 硬條件 2 同訊號)的
      色名鍵值頁才啟動;(3) 列側:同列同折縫側+非全小寫(排版訊號)+可區分
      (同列碼數 ≤ max(3,頁碼數/3),擋系列詞 Lume/Rake);(4) 色名→ ≤3 實體
      (變體層唯一性,>3=跨系列常用色擋下),多色名取交集;(5) 曾 x 對齊的碼不吃
      救援(歸 Stage 5 碼身分合併)。dev 結果:name_bound=31/1469——Ariostea twin_s
      CODICI 頁 30/30 逐筆目檢全對(五色×6 碼全綁對 p27 色塊),另 1=FMG junk 數字
      (S2-2 桶);Marazzi/MOSA/Provenza 錯綁在開發中逐一發現並以守門 (1)(2)(5) 清零。
      needs_review 只放行這 31 筆,其餘佇列行為=v3。天花板(ponytail 註記):K=3 與
      單 token 色名 → SCH-3 系列範圍鍵/n-gram;Sodai 型無碼廠的 (系列,色名,尺寸)
      身分=Stage 5 組裝(色名圖說 130/191,圖說內含尺寸僅 19)。
      catalogs4 驗收對象不變:Ergon Tr3nd p22/23、Iris aura、balance-665、FMG terrapura。
- [x] **M4-3|R1 x 對齊全無 → orphan**——**驗收過:orphan 拆解=誠實化 97.9%/真退步
      2.1%(僅 10 筆:7 表格列首圖=M5-3、3 碰運氣);錯值輸出 481→58**。
      實作(spike_geom.py assign_words v4 分支):詞級 x 對齊全無(xrow/2a/2b/3x 皆空)
      → orphan,涵蓋兩條硬綁路徑=鬆散同列回退+無 xin 遠端 sec(Emil p13 型 30/45 錯綁
      即 sec 路徑,初版只堵 row 回退 15/45,依詞級定義擴至 sec 才 45/45)。
      觸發優先序(使用者背書):x 對齊 → 色名救援(M4-2)→ orphan;orphan=正確結果。
      **doc_name_index 釘 v3 幾何(使用者裁決)**:M4-3 orphan 化會讓包裝表頁色樣「變
      無碼」、表頭詞(FMG CRATE/PESO)以偽色名進索引多救 4 筆 junk 數字——為垃圾解凍
      M4-2 已逐筆驗證的 31 筆不值,釘住解耦,junk 歸 S2-2。
      dev 回歸(四項全綠):v3 位元一致;name_bound 31 逐筆同 M4-2 狀態(twin_s 30/30
      不動);Emil p13 左半 45/45 orphan(綁定殘留=空);needs_review 289 頁逐頁不變
      (orphan 131→518=錯值→誠實 None,全數留佇列)。dev 紀錄 output/m4_dev_v4_m43.csv。
      catalogs4 驗收對象:Emil Be-Square p15、0general ×11 頁。
- [x] **M4-GT1|立體圖 A/B 判定——判定:A(無害)**(2026-07-09,catalogs4 GT):
      剖面線圖/尺寸空心框/厚度 icon 全為無填色向量線稿,extract_swatches 正確忽略、
      無搶綁。但同場抓到同族真害「小圖形(填色/raster)搶 x 對齊」25 筆 → 開 M5-2。
      原票文存查:
      型錄常見強調厚度的磁磚立體圖,目前未被框選——「沒框選」有兩種,GT 時逐頁判定:
      **A(無害)**=被正確忽略:立體圖位置無色樣候選框、無代碼綁到它附近 → 「要不要
      辨識它」是往後加分題,不急。
      **B(有害)**=被誤收成色樣候選,或其大 bbox 的 y 帶罩住鄰近代碼搶綁文字(=規則 1
      家具搶綁的變種)→ 無論未來是否辨識,必須先當「家具過濾的延伸」擋掉,否則在污染
      資料。擋除鐵律:與 Stage 1 路由器相容(分流不丟頁)、per-doc 統計、不寫死廠商、
      不做一次性過濾(家具過濾誤殺 Millelegni 的教訓)。
      「把立體圖辨識成產品展示圖」=需看圖的第三類需求(SOP_新增辨識§三類),文字層
      給不了答案;等下游確認需要立體展示圖再開新票,現在不做。
- [x] **S2-1 量測**(2026-07-09,s2gap.py,普查階段):A 類長 SKU 漏抓 catalogs4=54 筆
      (全在 MOSA PIPO,該檔漏抓率 60%!);dev=14(多為三段複合尺寸洩漏=SIZE_RE 缺口);
      B 類全字母啟發式上界 793(多語詞彙淹沒,不可當數字,GT 抽頁精確化)。
      **修復票 S2-1 仍開著**(CODE_RE 上限、全字母偵測)。
- [ ] **M3-M1|指標/架構修正(非規則,隨 m3 掃描工具落實)**:
      (a) far 停用為仲裁佇列(M2:far 對真錯誤 recall=0、佇列 93.5% 白工);
      (b) 仲裁佇列改用「無 x 對齊色樣可綁的代碼」訊號;
      (c) 驗收主指標=GT 抽樣真實正確率,bound-ok/far 降為輔助並標注系統性高估
      (M2 實測 v1 +45.2pt / v2 +20.5pt)。

## Stage 2(有票,不在本輪修)

- [ ] **S2-1|SKU 偵測缺口:>8 字元與全字母代碼不進候選**。
      **B 類 GT 精確化(catalogs4,2026-07-09)**:Emil p15 單頁 42 真 SKU 僅偵測 11
      (**漏 31=74%**,EKDM/ECXU/EDPF 全字母型);Provenza ELJF/ELJG 同病;Treverkhome
      MJWA/MJWC/MJWM 漏抓連鎖污染名鍵索引(假無碼色樣)。
      證據:Ariostea P612562S8/PAS612562S8/UCC6S300562(整表漏抓)、
      Viva EGUC/EGUH/EGUT、Emil EHKZ、Level ELMS/EMYP。
      性質:**靜默漏抓整個產品**,比綁定錯誤更陰險(不出現在任何綁定指標)。
      **M4-2 普查增修(2026-07-09,dev 實證)**:
      (a) B 類新實錘:Viva EJJK/EJJL/EJJM/EJJN/EJJP+EJJR-EJJU(p21 Metalbrick/
          Battiscopa 整列)、Marazzi MFFE/MMZW、Provenza EJDJ/EJDK/EJDL(p34 馬賽克);
      (b) **C 類(新):純數字低重複碼**——Iris pietra_di_bilbao 868428 型(6 位一次性,
          digits 分支「同長 ≥8 個且重複 ≥2」吃不到)、41Zero42 7 位數同病(spec 頁
          occ=0);
      (c) **一次性長碼=A 類量測盲點**:Ariostea P100697R10/PMS100700(每碼僅出現一次,
          s2gap 的 ≥2 重複門檻數不到)→ A 類實際規模比 54 筆上界另有加項;
      (d) A 類精煉(排除 COMP_RE 複合尺寸)後 dev 真長 SKU 僅 FMG P175352MF6——
          M4-1 的 COMP_RE 已把 13/14 個假 A 類(三段尺寸洩漏)洗掉。
      **免費候選清單(2026-07-10,D5 色名 v2 副產品)**:product/<brand>/<stem>
      .capcodes.json=照片級色樣圖說窄帶外排除的名形 token(≤8 字母,含 prov+頁+次數)。
      Level 259 tokens 中 202 碼形,EMYP/ELMV/ELSU/EDET 等 E 系家族全數在列
      (=本票 B 類證據自動再現);混有色名/finish 雜訊,用「同字首家族 ≥N」先篩。
      **★I 批實錘(2026-07-11,升第二優先;I_REPORT §2 診斷二)**:Marazzi 主批
      靜默漏抓 47/251=19%,100%=B 類全字母(M+3 字母,與含數字碼同表格交錯):
      Uniche 52%(MA?? 家族 36 個)、Treverkmood 80%(MLNM/MLNN/MLNP/MLNL)、
      Vivo 29%(MMD? 家族 7 個)。**這些碼在表格 Codice 欄,capcodes sidecar
      (照片圖說來源)救不到,須修偵測本體**;結構擋板線索=同欄 x 對齊+同列有
      尺寸+與已偵測碼同欄形。夾具=catalogs6(Codice 欄錨定計數腳本可重建);
      建議與 M5-3 打包共用 catalogs7 驗收(同批表格頁可同時 GT 偵測與綁定)。
      **M6RS 附帶確認(2026-07-11,審查方核可)**:MFFF/MFFG=B 類漏抓實錘再+2
      (Esagona 21x18,2 SIZE_RE 正常命中,無本票外問題);MFFG 作為詞已被 v7
      塊綁到正確列色樣→**修好偵測本體後綁定現成**(v7 塊內詞自動歸列首色樣,
      本票不需動綁定層)。打包裁決:與 M5-3 共用 catalogs7 照原案定案。
      **dev 放行(2026-07-11,使用者;案例清單送審後才動偵測層)**:邊界=
      只用 dev 語料+catalogs6 夾具,catalogs7 全程不讀;流程照 M5-3 慣例=
      合成案例(含反例)先行→基線斷言先綠→清單審過才動 code;既知病例=
      MFFF/MFFG(A02G;MFFG 修好後須驗 v7 塊綁如預期接上)/MLNM(Treverkmood)
      /MAPZ(Uniche MA?? 家族)。
      **病灶定位(2026-07-11)**:m2_scan.code_candidates 對 alnum 候選硬性要求
      `any(isdigit) and any(isalpha)`——全字母碼結構性進不了候選(非門檻鬆緊,
      是分支缺席)。**設計初案(v8 版本閘,待審)**:全字母 token 升格候選須過
      per-doc 結構訊號(I 票線索=同欄 x 對齊+同列有尺寸+與已偵測碼同欄形):
      ①CODE_RE+isalpha+len3-8+不在 alpha_vocab;②錨定=同頁既有偵測碼
      (kept alnum)的 x 欄帶涵蓋該 token(單錨須夠用=Treverkmood 1 錨救 4);
      ③同列有尺寸與④長度同錨碼眾數(AND/OR 組合 dev 校準,禁廠商寫死);
      無錨檔(0 含數字碼)明確不救=本票邊界,歸 C 類/S2-3。已知交互:
      B 碼收進 codes_doc 後 doc_name_index 偽色名自動淨化(Emil p15 EDPT 型)
      =預期正增益,須回歸驗證;route_junk 四 RE 皆要求數字,與全字母分支
      天然不撞(斷言固化)。合成案例清單 v1(2026-07-11 送審中):
      P1 頁級錨定基本型(2 錨碼+2 全字母同欄同長→全收)/P2 單錨救多
      (1 錨+4 全字母=Treverkmood 型)/P3 色名鍵值頁(錨欄家族收、他欄色名
      不收=Emil p15 型)/T1 列首色名同長全字母在色樣欄 x→0 收/T2 表頭詞
      CODICE 在欄頂同 x→不收(擋板 dev 校準:同列尺寸/首行位置)/T3 泛用詞
      恰同欄(alpha_vocab 擋)/T4 系列詞高頻(LUME 型)→0 收/T5 無錨檔→
      0 收(不亂撿)/T6 散文頁偶然 x 重合單 token→不收(頻次/形態擋,dev
      校準)/T7 route_junk 不交互斷言/T8 v≤7 bit-identical 版本閘斷言/
      **T9 表面處理縮寫陷阱(2026-07-11 審查方補)**:NAT/LAP/RET/LUX 型
      token 在錨欄旁或帶內、同列有尺寸→不收(每列出現的高頻詞,考驗詞表
      機制;**定案③④組合下必須不收**)。
      **設計問題裁定(2026-07-11)**:
      問題一|錨=**per-page**(選邊)。理由:①夾具實測(Codice 欄錨定計數
      腳本重建,總數 47=I 批 GT 逐檔全對=交叉驗證過)**純 B 碼頁=0/7**
      (Uniche 4 頁/Treverkmood 1 頁/Vivo 2 頁,頁頁有 ≥1 頁級錨)——B 類
      病理=同表交錯,天然同頁有錨;②per-doc 錨=x 帶跨頁外推,版面異頁時
      把散文/他欄 token 拉進帶=誤收方向,違反「往嚴偏」。落選方(per-doc)
      入已知限制:未來若現純 B 碼頁(整頁全字母碼)=v8 誠實漏、碼不進候選
      →該頁維持現狀(不報警的靜默漏=本票已知殘口),catalogs7 GT 順帶量
      此型頻率;要救=per-doc 錨另開票。
      問題二|alpha_vocab 建法:**主體=per-doc 頻率統計**——finish 縮寫
      (NAT/LAP/RET)=每列出現的檔內高頻 token,per-doc occ 相對錨碼 occ
      分布的比值訊號擋(門檻 dev 校準;真 B 碼=一列一碼低 occ);現行
      dev corpus df≥8 詞表**降級為小停用詞補充**,並聲明語言邊界=拉丁字母
      +dev 語料出現語言(義/英為主),邊界外詞不承諾擋。
      **校準紀律(2026-07-11 審查方)**:③④組合 dev 校準完即凍結;往嚴偏
      ——第一指標=零誤收(偽碼入庫=MILANO70 型),救回量第二;T9 在定案
      組合下必須不收。T9 合成構造(審查方指示):縮寫須真實高頻(多列出現)
      +運行時前置斷言鎖住 occ 比值條件,防案例退化。
      **小表邊界(2026-07-11,審查方問、已裁定寫死)**:一兩列小表=縮寫 occ
      也低、比值訊號鈍化(無法區分「每列出現的高頻詞」與「一列一碼」)→
      **v8 全字母分支要求檔內「含尺寸列」總數 ≥ R_MIN(校準值,初始 3),
      不足則分支不啟動、全字母一律不收**(往嚴偏:寧誠實漏不誤收);此型檔
      B 碼=已知殘口,catalogs7 出現時行為有據=「不啟動」非「誤收」。
      合成案例 T10 固化此行為。
      夾具驗證清單(非合成):catalogs6 Uniche 36/Treverkmood 4/Vivo 7 漏抓
      修復率、MFFF/MFFG+MFFG 塊綁接上、Emil Be-Square p15 31 筆(catalogs4
      已知病例頁,Emil p13 夾具先例)。
      **dev 落地+校準送審中(2026-07-11,新視窗)**:v8 分支已入 m2_scan
      (alpha_codes+code_candidates alpha_vocab 參數;m3_scan:298/m4_dump:107
      呼叫點接上,v≤7 不用該參數)。13/13 全綠、v6/v7 dev 289 頁逐位不變
      (改動前後皆驗)、FMG 全頁零 diff、name_bound=31 不動、佇列逐頁零下降。
      **核可六閘字面校準(現在 core 內)結果**:夾具 38/47(Treverkmood 0/4
      ——④眾數被 EN14411/DIN51130 型認證雜訊錨淹沒 {8:2,7:2,4:1};MAPZ/MAEY/
      MAPY/MAQX/MAVD+MFFF/MFFE 死於⑤ occ≤2×med);dev 誤收 8 詞全 x 對齊或
      入索引:CREA/VERO(A02G 圖說系列名)、VEDI/LINEAL/THERMAL/MORE(原文
      全小寫散文)、FRICTION(Topcer)、CHIP(Emil c4)。**機制衝突實證:
      T9 NAT occ=3 必不收 vs MLNM occ=3/MLNL occ=5 必須收——「occ≤k×錨中位」
      在 k<3 與 k≥3 不可同真,占位門檻無解**。
      **變體 v5(scratchpad s21_variant.py,未進 core,待裁決)**:m1 原文全
      小寫不收(is_name 慣例)/m2 ④⑤改算「有效錨」(≥1 實例同列有尺寸)/
      m3 ⑤門檻=max(2×med, min(0.6×頁數, 5))(真碼 occ 有自然上界:Level 全 2、
      MFFE 4、MLNL 5;系列詞∝頁數:LOOK 20/VEIN 51)/m4 ②容差 0.02→0.005×
      頁寬(真碼表格對齊 0.0–0.5pt;CREA 7.8/FRICTION 6.8=流版偶合)/
      m6 錨形優勢比≥0.6(Iris 50%/Topcer 全錨 50% 擋、有效錨 0.67 漏)。
      v5 數據:13/13 全綠、**夾具 47/47**+MZUE/MZUG/MMDC 交叉引用真碼 3 筆、
      Level 147/Provenza 26/A02G 6(MFFF/MFFE/MFFG 全中)、Emil c4 +29、
      名鍵偽鍵 4→1;dev 全量 70 頁 diff 佇列零下降、MFFG p38=偵測→塊綁→A'
      降級佇列(M5-3 限制③路徑)。**殘存已知誤收 2:OPUS(Provenza,occ=5
      =MLNL 同值不可分)、OCT(Topcer 形狀詞,與既有 alnum junk 錨同族同欄,
      優勢比 0.67 過閘;調 0.7=對單檔擬合,不做)**——兩者皆 x 對齊(自信
      輸出),c7 GT 監看。**否決存查:m5「同列已有錨碼→不收」**(殺 Level
      矩陣/Provenza 收邊條一列多碼真碼 88+14 筆;I_REPORT「同表交錯」實為
      同列也混碼)。**代價存查(v5 vs 字面校準)**:Viva EJJL/EJJP(欄距
      12.8pt>容差)、A02G 索引頁交叉引用 9 筆(MQAF/MQDK 型,錨距 7-30pt)
      =誠實漏向;EJJR-EJJU/EJDJ-L 死於③該列無尺寸(兩校準同)=已知殘口。
      **三題裁決(2026-07-11,使用者)**:①m1-m4+m6 全採、v5 入 core(字面
      校準兩軸全劣、五機制皆 per-doc 有據、m5 測後否決紀律加分);②OPUS/OCT
      =接受存在但禁止無聲入庫,移交 S2-5 偽 Variant 旗標(該票範圍已擴),
      本票明記已知自信誤收 2 筆、c7 GT 量頻率,DOM 0.6 不調;③常數照列凍結
      +③④=AND;Emil p15 結構性漏(尺寸在表頭)與 v5 代價(Viva EJJL/EJJP、
      A02G 索引交叉引用 9 筆)入已知限制。v5 入 core 後全套重跑+落 v8 凍結
      CSV(output/s21_dev_v8.csv)→停下送審→審過才與 M5-3 打包 catalogs7。
      **裁決後全套重跑全綠(2026-07-11,v5 已入 core m2_scan.alpha_codes)**:
      13/13(原 6 綠同斷言)、selftest OK、v6 對凍結逐位一致、v7 重生鏈完整
      (對 v6 diff=已知 5 頁 M5-3 列版型、佇列 450/blk 10/demoted 43/nb 31
      全吻合;scratchpad 曾被清,v≤7 路徑=代碼級不可達+清前兩度逐位實證)、
      v8 vs v7=70 頁 diff/佇列零下降/FMG 零 diff/name_bound 31/MFFG p38 接縫
      (偵測→塊綁→A' 降級佇列);token 級只多不少逐檔斷言過;夾具 47/47 逐筆
      +交叉引用 3 筆;Emil c4 +29、名鍵索引 40→30 鍵、偽鍵 EDPT/EDPV/EDRP
      全淨化(CHIP=非碼,正確不收,原有名鍵雜訊非回歸)。**凍結
      output/s21_dev_v8.csv(sha256=aadd2eec…f2dc;codes 1525/aligned 1060/
      review 455/orphan 409/demoted 46/blk 10/name_hyp 31)。送審中:審過才
      與 M5-3 打包切 catalogs7;pipeline 仍釘 V=6 不動。**
- [ ] **S2-3|一次性/低重複碼偵測**(2026-07-09 自 S2-1 增修升格獨立票,**優先級與 M4
      同級**,使用者裁定「別丟 backlog 深處」)。
      **GT 實數(catalogs4,2026-07-09)**:0general 單檔 273 筆 distinct 9-14 字元
      長碼(BL60400AN 型 battiscopa),全部整檔僅出現 1 次、s2gap ≥2 門檻 0 筆可見、
      codes_doc 0 收錄——盲區正式坐實,規模遠超 A 類已知 54 筆:C 類低重複純數字碼(Iris 868428 六位
      一次性、41Zero42 七位)與 A 類一次性長碼(Ariostea P100697R10/PMS100700)是
      **所有靠重複度篩碼機制的共同盲點**——digits 分支要「同長 ≥8 且重複 ≥2」、s2gap
      量漏抓也用 ≥2 出現門檻,連量測工具都看不見 → A 類「54 筆」是下界非全貌。
      性質=「靜默漏抓整個產品」最陰險的一種:產品消失、指標看不見、量測工具也看不見。
      **catalogs4 GT 階段必辦:給一個真實數字(抽頁人工計數下界也行)。**
      **★I 批補件實錘(2026-07-11,升第三優先;I_REPORT §2 診斷三)——本票擴為
      「C 類+稀疏閘重建」**:①41Zero42 MILANO70 真 SKU=7 位數字 4101250-4101259
      偵測 0/10(且唯一真品頁 p9 SIZE 命中 2<3 沒過 spec 閘門=閘門漏頁首例);
      ②MOSA Murals 真碼=45 個 5 位數字(4 產品頁全過閘、色樣 69 個都在),digits
      分支本可整族撿回(36 distinct occ≥2 ≥8 門檻),但 `len(cands)<0.5×n_spec`
      =2<2 被 p10/11 兩個 occ=1 雜散 alnum(PM1261/PM2671)一票擋死 → 0 偵測。
      **教訓:稀疏判定用「未過濾 alnum 候選數」當分母極 brittle——occ=1 雜訊
      不該有一票之力**;重建方向=稀疏訊號改用 occ 加權/或雙軌並行(digits 族
      獨立達標即收,不依賴 alnum 稀疏),與「digits 分支不動」舊定案衝突處
      須以 I 證據重議。夾具=catalogs6 MILANO70+Murals。
- [x] **S2-2|候選純度(junk 分流)——dev 完成(2026-07-09,v5 版本閘,等 catalogs5
      打包驗收)**。實作(m2_scan.route_junk + code_candidates version 參數;v4 逐位
      凍結驗證過):四類分流保留(SCHEMA §7 過濾≠刪除)——band(單字母+1-2 位數且
      同字母家族 ≥3:A##/T## 價格帶、R## 防滑;孤立者如 FMG H10 保留,家族性=量表
      的 per-doc 結構訊號)、unit(CM2/MM3)、thickness(12MM)、size(33X120X5 洩漏)。
      dev 成績:junk 實例 -288(1469→1181),其中 230 筆原本「自信 x 對齊」=錯值
      輸出直接減量;needs_review -58(junk 誤佔佇列);twin_s 名鍵 30/30 不動。
      **教訓(dev 自測抓到)**:junk 清洗會翻轉 digits 分支的稀疏判定(Sodai 清 3 個
      junk → 憑空多 72 個件數型純數字 junk)→ 定案=sparsity 用未清洗集合、digits
      分支完全不動。**Emil p15 解鎖=0/11(M4 報告預測部分錯誤)**:junk 清掉後
      (54→13 乾淨候選)才看見後面三道閘——SAND/BLACK 在 dev 泛用詞表(is_name 擋)、
      IVORY/CONCRETE 5 實體 >K=3、B 類漏抓碼(EDPT 型)以偽色名污染索引;
      這些歸名鍵升級票(n-gram/SCH-3/泛用詞表與色名衝突)+ S2-1,非本票。
      **殘餘(明列)**:digits 分支 junk(FMG 80 個 2 位數件數/包裝碼)未清——頁碼
      過濾 all() 判準 dev 實測 0 命中已removed,根治=偵測分支結構訊號重建(S2-1/
      S2-3);BODY3/TR3ND 型系列詞+數字未涵蓋(無安全訊號)。
      catalogs5 驗收必報:junk 清洗的 GT 連鎖(誤殺真 SKU?)、band 家族≥3 在新廠商
      的泛化、Emil Nordika/名鍵加壓件上的名鍵行為。
- [x] **S2-4|非產品 token 污染——頁腳頁碼族=段4 判定不可分,規則 lane 結案、
      移交 VLM/人工 lane(2026-07-13;通案五溯源之一;結論文檔=
      output/s24_pagefoot_conclusion.md,通案六補落)**:兩軸皆無安全分離——
      軸1 token 級 all()=考古證明結構性必敗(offset+雙角色);軸2 實例級頁腳族
      (dev/s24_pagefoot_probe.py 全 7 語料實跑)=FMG 80/80 全混合(頁腳+
      code-role 並存)→ token 級安全路由移除 **0/80**=病灶側零效果,且
      VICTORIAN 真 SKU(裸數字 11/14/16)實例落頁腳族=實例級路由誤傷真碼方向。
      FMG 100 污染實例照舊出貨=已知紅字(spec 65/queue 35;探針=常態監看)。
      包裝表族 361 照舊歸 S2-1/S2-3 結構重建;價格帶逃逸修法候選另案。原票留底:
      (2026-07-10 稽核開票,audit.md §②+D2;探路完成、未實作)。
      定義=「抓進非產品」污染:膨脹產品數、污染 specByCode/orderCode,與漏抓
      (S2-1/S2-3)方向相反。dev 13 份來源筆數(spec=specByCode、oc=orderCode):
      1. FMG 頁腳頁碼族 100(spec 65/queue 35;印刷頁=PDF頁−2、同位兩簇 x≈40/580
         y≈83% 頁高、邊帶 100/100、跨 65+ 頁;3 筆升 B 型 Variant code=16/27/89)。
      2. FMG 包裝表數字族 361(spec 190/queue 171;集中 p274–277 僅 4 頁,值域
         10–90 高重複=件數/箱、m² 型)+衍生 oc 54、variant.code 3(spec 列被合併
         認領傳染)。=S2-2 殘餘所記「FMG 80 個 2 位數」的完整量化。
      3. 價格帶逃逸(頁家族<3 未觸發 band 分流):Provenza T104/A107=25
         (spec 18/oc 2/queue 5)、Emil T23/E220=53(spec 27/oc 14/queue 12)。
      4. Topcer R12 防滑等級=2(spec 1/oc 1;全檔唯一 Variant 的 orderCode 就是它)。
      5. 待使用者拍板真偽:Level E046/E048/E079=9、Sodai C482/C372=8。
      **頁腳頁碼通用過濾探路結論(audit.md D2)**:訊號=純數字∧跨頁同位聚類
      (20pt、≥5頁)∧邊帶(<8%/>92% 頁高)∧值−頁=常數族;dev 100/100 全中、
      其餘 12 份 0 誤抓(但其純數字候選=0,考驗未至)。實作=route_junk 新增
      pagefoot 分類(分流保留非刪除)、版本閘 v7。
      **考古結論(2026-07-10,前置功課①完成)**:舊判準把「頁碼」當 token 屬性
      並用 all() 全稱量化(該數字 token 的所有實例都得滿足頁碼判準),dev 0 命中
      有雙重保證——(a) FMG 印刷頁=PDF頁−2,「值=頁」等式永不成立;(b) 即使含
      offset,同一數值(15/30/40…)同時存在頁腳與 p274–277 包裝表兩種角色,
      全稱量化必破。教訓一句話:**頁碼是「實例位置」屬性不是「token」屬性,
      判準必須按實例分類(同位簇+邊帶+offset 族),token 層 all() 結構性必敗。**
      (存證極限:專案無 git、逐字稿搜尋不含工具呼叫內容,舊碼原文不可考;
      結論由現行 code_candidates digits 分支+dev 實測資料重建,證據在 audit.md D2。)
      其餘前置功課:②重驗 Sodai 稀疏翻轉案例(「digits 分支不動」定案在先,本訊號
      不碰稀疏判定但須證明);③41Zero42/Iris 真純數字 SKU 廠(S2-1 後)須 held-out 驗證。
      包裝表族不適用此過濾,歸 S2-1/S2-3 結構重建或 C packing 語境。價格帶逃逸
      候選修法=band 家族判定頁級升 doc 級(須評估 doc 級誤殺)。
      I 驗收建議新增回報:非產品污染率、color.en 溢收率(等使用者定 I 清單時採納)。

- [ ] **E-1|photo_level 場景照過濾(2026-07-10 使用者裁決開票;排 I 之後、不進當前
      MVP、不碰綁定 v6——純 E 裁圖輸出層)**。
      裁決:①場景照(房間/家具/擺設,Marazzi 型 dev 20 張)一張不得當 swatchCrop,
      全部排除;②材質特寫(純磁磚表面滿版近拍,FMG 型 dev 29 張)**保留**(使用者
      確認「要」)——因此過濾不能只看面積,須分「場景 vs 特寫」;③降級不刪除:
      場景照標 photo_level=scene、不出產品圖、Variant/綁定不動、進佇列複查;
      特寫標 photo_level=texture 照出;分不開的標待人工。
      機制(dev 已驗訊號,audit.md §④):兩段式——
      (a) 候選池=swatch bbox ≥10% 頁面積(dev 雙峰:正常色樣全 <10%、照片級全
          ≥20%,乾淨切);
      (b) 池內分類=4×4 宮格亮度 inter_std(<14 特寫、>23 場景、14–23 待人工;
          dev 50 張實測:特寫 28+邊界 1、場景 16+邊界 4、拼磚 1,邊界 6 張人工
          覆核全數可判)。
      驗收與排序:等 I 隨機批給頻率(Marazzi 佔剩餘池 63.5%,場景照型比重會放大,
      ROI 由 I 定)+I 的 GT 順驗分類器邊界帶誤分率。
      **c7 無偏頻率補記(2026-07-11,GT 歸因①)**:主批 10 檔中 **4 檔場景照
      主導**(Chill/Frammento/Limestone Wall/Rice);照片級綁定 47 筆全走 xrow
      舊路(v7 塊綁零筆、M53_AREA 3% 閘野外未失守);「綁定且圖可用率」主批
      總體 39.2% vs 自動綁定率 53.1%——差距 13.9pt 全是本票的病,修復 ROI
      直接讀這條(GT_REPORT §四歸因①)。
      **★I 頻率已出(2026-07-11)**:主批 25/25 Variant 全 photo-level、目檢≈全
      場景照(可用產品圖=0);拼磚版面頁 0/10 → 拼磚切分票不開。分類器邊界證據:
      亮白低對比場景誤分 texture(Room Wall 浴室 std=12.6,人工覆核=場景)——
      inter_std 單訊號不足,邊界帶人工覆核維持。註:M5-3 修好後列版型頁改出
      乾淨列首色樣,場景照綁定占比會大降,本票 ROI 屆時重估(排 M5-3/S2-1 後)。
      **拼磚版面頁(Topcer 型,一版多格磁磚+散置代號)**:幾何無法格級綁定
      (要圖格切分+格對代號,超出現有產線),使用者裁決=不硬綁,現況以 knownGaps
      聲明(見 pipeline.KNOWN_GAPS)+佇列標記;I 頻率超過閾值才開「拼磚切分」
      獨立票,I 前不動。

- [ ] **S2-5|系列名/品牌名偽碼防護(2026-07-11 I 批開票;I_REPORT §2 診斷三)**。
      現象:41Zero42 MILANO70——系列名「MILANO70」(×19)與品牌名「41ZERO42」
      為 8 字元 alnum 形 token,被 code_candidates 收為碼、在情境照圖說上 x 對齊、
      經 D 組裝成 1 個偽 Variant(**偽碼可入庫=污染,比漏抓更毒**)。
      per-doc 結構訊號候選(不寫死詞表):①token=檔名/頁首頁尾高頻詞(系列名
      本來就該進 seriesName 不該進碼池);②全 doc 高 occ+跨多頁均勻分佈
      (真 SKU 集中規格表頁;系列名滿天飛);③與 D5 capcodes 的「名形」判準
      互補。與 S2-4(非產品 token 污染)同族,驗收可打包。排序=第四梯隊
      (E-1 同批)。夾具=catalogs6 MILANO70。
      **範圍擴張(2026-07-11 裁決,S2-1 v8 移交)**:S2-1 已知自信誤收 2 筆
      ——OPUS(Provenza,occ=5 與真碼 MLNL 同值、occ 軸已證不可分)、OCT
      (Topcer 形狀詞,與既有 alnum junk 錨同族同欄、有效錨優勢比 0.67 過閘,
      V8_DOM 不調=單檔擬合)。裁決=「接受存在但禁止無聲入庫」:本票偽 Variant
      旗標機制須涵蓋此 2 型(全字母偽碼),c7 GT 順帶量頻率。夾具+=dev
      Provenza OPUS/Topcer OCT。
      **實作完成送審中(2026-07-12 工作包#3 線③,output/s25_design.md)**:
      pseudoCodeSuspect=P_fn 檔名∨P_cap 撞線(occ≥⑤thr 零餘裕)∨P_dom
      邊際檔(DOM<S25_DOM_MARGIN=0.7 唯一新常數);spread/hdr 軸實測淘汰
      (5102V 0.12≈OPUS 0.13)。已知病例 4/4 接住(MILANO70 偽 Variant 帶旗
      端到端)、dev 誤中 0、MLNL 餘裕不中=病例對分離;已知過標=Slow20 型
      4 筆(檔級連坐)+截斷系列名型(正中偽碼)。合成 SP-1~4+T26 註記
      惰性、四版本逐位、smoke 守恆零變化全綠。

## demo 診斷 D 類票(2026-07-14,記票不改;禁過擬合)

來源=demo_showcase 14 檔目視回報,診斷總帳=`output/demo_diagnosis_ledger.md`。
★三票共性=**判別度不足**;一律記票、**禁為單檔改規則**(過擬合是本專案原罪)。
★診斷關鍵反直覺結論(留存防重複樂觀):**A 類=空,現成切版(v13/E-1)不能解 demo 任何問題**
——v13 讓 Marazzi Rice 綁定 4→1(救回碼撞 L2 塌縮守衛)、E-1 是 `core/m3_scan.py:309`
`version==9` 精確閘的懸空側枝,現行 V=12 跳過、回放 Rice/Ariostea 逐項不變。

- [ ] **D-1|場景照綁成產品**(demo 問題 2)。病例=Marazzi Rice p7「Rice Blu Lux Scenario
      Tappeto Nero」(已綁 Variant、code=None、color.en=場景 caption),crop_authenticity C3 命中。
      病灶=**E-1 未前移 v13 主線 + E-1 面積閘(S1=swatch≥V9_G×頁)只涵蓋 A02G 型整頁 render**,
      demo 場景照達不到門檻(risk_replay V=9 實證不觸發)。正解二選一=①E-1 前移併主幹並重新
      校準/驗收(通案二分離量測+通案四組裝守恆)②移交 VLM lane。**禁為 Rice 單檔調閘**。
- [ ] **D-2|文字/caption 裁成色樣**(demo 問題 3)。病例=Ariostea 1general_ultra p26/119/133
      (裁框 100% 涵蓋碼 token,已綁 Variant),crop_authenticity C3 命中。少數、per-doc 訊號弱。
      與 D-1 同族(裁圖真實性),打包待 E-1 前移或 VLM。
- [ ] **D-3|surface 欄吃包裝詞**(demo 問題 4,最低優先)。field_prov F2=99 筆/4 檔
      (Ergon/Provenza/Viva,`surface='Box'/'Battiscopa Box'/'Tile Right Box'`)。**非誤綁=欄級噪音,
      產品本身是真磁磚**。輕修=加 `fieldQuality:needs_review` 旗或前端過濾 UNIT_WORD,不影響綁定。

★病理升級(2026-07-14,使用者追問 Emil Be-Square p16 後):問題 1 靜默漏抓之
Emil Be-Square p16(16 碼中 9 靜默:EKKQ/EKKR/EKKS/EKKV/EKKW/EKKX/EDPU/EDPW/EDRQ)
**定案=S2-1 ②型**(五死病灶、禁止第六案判決適用)——已歸檔②-vis 探針復現
(`S2VIS_DETAIL=16 dev/s2vis_probe.py "catalogs4/Emil" 2 base`):
6/9 落②機制族召回、3/9 欄成員<2=錨帶外(EMJ 族地位)、同頁噪音 25 筆
(IVORY/CONCRETE/MOSAICO/TESSERA/SLIM…全與真碼同確認格同列)S/N≈1:4。
**本頁登記入②型 VLM 考卷**;逐 token 帳+復現命令=output/demo_diagnosis_ledger.md 附錄A。
會話中曾提「結構槽位消去」新軸=**已撤回**(附錄B:同列詞兇手穿透+PE 型 0 綁定頁
無槽可學+禁止第六案);**過擬合陷阱 v2(技術 vs 用法框架,含第 5 條「第 N+1 案陷阱」)=附錄C**。

## Schema 擴張(SCHEMA v1.0 開票;本輪不實作)

- [ ] **SCH-1|系列敘述欄位抽取**(appearanceDesc/features/applicableSpaces/
      applicationScenes)。架構翻轉:Stage 1 從過濾器改路由器(不丟頁只分流),
      情境/介紹頁=這些欄位唯一來源;文字本體走文字層,選段/歸欄=文字 LLM,
      VLM 僅技術 icon 與無文字層掃描檔。
- [ ] **SCH-2|翻譯階段**(全 corpus 無中文;zh 欄位=獨立批次 LLM 翻譯+詞彙表,
      抽取後、入庫前)。
- [ ] **SCH-3|總覽型錄系列切分**(1general_ultra、Marazzi A02G 型一檔多系列;
      seriesId 不能以文件為鍵)。
- [ ] **SCH-4|specByCode 表格列解析**(規格表頁 SpecRow:code+size+surface+packing;
      與 S2-1 偵測缺口強耦合)。

## 資料源

- [ ] **DATA-1|非 PDF 資料源佔比**:Vogue 空、kytile=JPEG 檔名即 SKU。待問資料方
      佔比與是否需要獨立 pipeline(檔名解析路線)。
- [ ] **DATA-2|外部欄位**:origin、isClassic、platformCategory 非型錄可抽,
      需資料方主檔/業務標記/taxonomy 映射。
