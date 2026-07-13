# 執行 Prompt（每次實作 session 以此為起點）

你在 `/Volumes/USB DISK/catalog-extractor/` 實作磁磚型錄擷取 pipeline。

## 啟動步驟
1. 讀 `.claude/skills/ponytail/SKILL.md` 並以 **full** 強度全程套用:寫任何程式碼前先走階梯(需要存在嗎→codebase 已有→stdlib→原生功能→既有依賴→一行→最小實作),不砍驗證/錯誤處理/安全;非平凡邏輯留一個可跑的 self-check;刻意簡化標 `# ponytail:` 註解。
2. 讀 `implement.md`(v2.1,已定稿)——它是唯一的規格來源,遵守其通用性鐵律:per-document 統計、禁 per-vendor/樣本族群寫死、禁「距離最近」綁定、LLM 不做像素裁圖。

## 工作順序（依 implement.md §14,依序、不跳關）
M0(§0 先決事項)→ M1 → M2 → M3 → M4 → M5。
**目前任務(2026-07-11):I 批驗收完成=專案轉折點(★先讀 output/I_REPORT.md)。**
catalogs6(主批 10/10 Marazzi)實測:可用產品圖=0、佇列 86%、B 類靜默漏抓 19%。
三洞已定位:①M5-3 列首色樣版型=Marazzi 主力版型(v6 誠實 orphan,非錯綁)
②S2-1 B 類全字母碼 ③C 類+稀疏閘 brittle(MILANO70 偽碼三重失敗/Murals 45 真碼
被 2 個 occ=1 token 擋死)。優先序已重排(使用者核准):M5-3(v7 版本閘,綁定
規則改動、v6 凍結不動)→ S2-1 → C 類/稀疏閘 → E-1+S2-5。held-out:catalogs6=
已知病例夾具(驗收效力已燒)、泛化=另建 catalogs7(USED_DIRS 屆時加 catalogs6)。
I 批產出在 product_i/(已併掛 viewer);MVP 後修復舊序(色名→S2-4→漏抓)作廢。
**目前狀態(2026-07-11,外審行動清單執行後):①git 已建(工作樹=USB、庫=
內接碟 ~/catalog-extractor.gitdir;每輪收工必 commit;雲端備份方式待使用者)
②「零錯」口徑退役(MVP_CONTRACT 統計口徑節)③跨文件紅字入 KNOWN_GAPS
⑤econ_queue_v1.md ④⑥設計案在 BACKLOG。**S2-1 v8 定案(夾具 47/47,凍結
s21_dev_v8.csv)。⑦catalogs7 已跑批(c7_run.py→product_c7/+output/
c7_scan_v8.csv+c7_run_summary.md):主批自動綁定率 53.1%(曲線第二點,I 批
=18.4%)、守恆 14/14。**roads-465 紅線已 GT 裁定(2026-07-11,分支二)=真列
版型 96 筆全對,反例條款通過 4/4=0;探針落空(限制②堆疊型仍未量測)+頁型
掃描定義存疑入 GT_REPORT;抽驗累積 n=199(上界≈1.5%)。**GT 全案收卷+v8 定案切版(2026-07-12)**:主批判定
入 GT_REPORT §五(召回總表:漏 71 全既知機制)+歸因 §六;Quarzite p6=版面
事實 → 33/33 既知、c7 零新型;A102=量表碼值錯誤 4 筆(S2-2 BAND_RE 缺口票)
→ 抽驗 n=375、上界≈0.8%。pipeline 已切 V=8(凍結=s21_dev_v8.csv+
v8_FREEZE.md;回歸全綠:selftest、v5-v8 bit-identical、v3/v4=既知歷史語意、
smoke 289/289 守恆)。catalogs7 轉夾具(禁調參;銷毀=A 板)。
**裁決落地(2026-07-12)**:①統計=雙口徑並列(原始 379/4/≈2.4% **現行有效**
至 S2-2 延伸修復落地;剔除 375/0/≈0.8% 並列)入 MVP_CONTRACT §三之二+
GT_REPORT;嵌合 variant 已加 knownDefect 註記。②D 紅線 1/4 死因(合併鍵
信任 code+cluster 級偵測無解鏈)入 S2-2 延伸票(D 加固=子項)。③審查紀律
通案(前提被否證→後續 Phase 自動凍結;V=8 切版經事後追認不回退、不得引為
先例)入 MVP_CONTRACT §三之三。④S2-2 延伸票釘死:禁形狀級修法(M961 同形
真碼實證),限 per-doc 脈絡訊號,設計送審制。⑤E-1 方向核可;①~④已驗收
(2026-07-12 二輪),②加 D 加固分離驗證條款、c7 用途三分類邊界((i)修復率/
(ii)零變化斷言准、(iii)調參禁;本次=類型(ii)不得引為(iii)先例)入 BACKLOG。
**E-1 v3.1 已核可+實作完成、全綠停下(2026-07-12)**:判定式=
photo_sus=S1∧¬((S2a∧唯一對齊碼)∨S2b)、V9_G=0.10(校準=dev+合成;中位臂
被 dev 否決);T6 翻面+T6u 對偶;dev 降級 79=分離量測逐筆吻合、夾具修復率
c7=41/47、catalogs6=58、塊綁 152/152+137/137 零變化、v8 逐位不變。
送審包=e1_design_v9.md v3.1 節+證據頁 viewer/e1_*(A02G/Topcer/FMG);
**V=9 切版等使用者親驗**(pipeline 仍 V=8)。新審查紀律:判別訊號送審必附
dev 已知病例分離量測(MVP_CONTRACT §三之三通案二);c7 身分定規入 BACKLOG。
GT 期已結束;c7 禁調參+紅線即停照舊。手工車道第 1 筆=Ardesia20。
**S2-2 延伸完結(2026-07-12 五裁決全落):pipeline 已切 V=10**(凍結=
s22_dev_v10.csv+v10_FREEZE.md,版本非線性:v9=E-1 懸空側枝、v11 預留;
證據頁 viewer/s22_l1_v10/ 七頁免親驗放行)。L2 v2(C3=P∧橋接∧∃≥2 他碼)
已落地:dev 降級 0=純備援、SL-6「雙偽逃逸+L2 接住」入常備回歸(T23 四部)、
白名單僅 dHardening 標頭;已知限制=P 共模單點(殘餘=無家族字母毒碼型
T104,GT 監看)。通案二範圍擴充(任何有綁定效果的產線層條件)入
MVP_CONTRACT §三之三。**口徑升級(2.4%→0.8%)證據包三件齊
(s22ext_design 末節),待使用者一句核可生效。**E-1 親驗照舊懸空。
**工作包#1(S2-1 延伸)交付(2026-07-12,送審中=output/s21ext_design.md)**:
③型「塊內尺寸繼承」設計+分離量測(新收錄 125 種全真碼零散文)+SM 基線綠,
實作=v12 下一包待放行;②型兩候選實測否決、29 筆殘留+GT 監看。
**工作包#2(v12 實作)交付(2026-07-12,送審中=s21ext_design.md 實作結果節
+v12_FREEZE.md+凍結 s21ext_dev_v12.csv;pipeline 仍 V=10)**:SM-1~SM-6
全綠、v8/v9 側枝/v10 逐位、GT 修復 29/31 兌現、佇列零消失、c6 零 diff;
偏離二處已歸因(UT 41/43、TdM 30/24=模擬器語意差,129 種全真碼散文 0)、
RUN_GAP=2.0 未動(as-built 校準=分離帶 1.75/2.22)。**四裁決已落
(2026-07-12)**:(a)(b)(c) 核備入檔(UT 5 筆=訊號軸不可分歸檔、FREEZE
校準改寫=分離帶非先見);通案三入 MVP_CONTRACT(設計期量測工具一律入庫,
模擬器失傳=根因)+工具已入庫 dev/s21ext_*。**(d) 使用者親驗通過
(2026-07-12,紅框無異議)=V=12 已切版**(smoke 對 s21ext_dev_v12.csv、
四版本逐位、n_codes 1564 守恆全綠)。
**工作包#3 完結送審(2026-07-12,雙線總帳)**:步1 v12 已切版。
線①=blocksz 量測完成 → **②型第五次陣亡,預案歸檔「現有幾何訊號不可分、
待 VLM 金絲雀承接(D 板),禁止第六案」**(s2vis_design.md 兇手逐筆帳;
召回側 100% 證據保全=VLM 考卷)。線③=S2-5 偽碼旗標已實作
(s25_design.md):pseudoCodeSuspect=P_fn 檔名∨P_cap 撞線∨P_dom 邊際檔
(S25_DOM_MARGIN=0.7 唯一新常數),病例 4/4(MILANO70 偽 Variant 端到端
帶旗)、dev 誤中 0、MLNL 對照分離;SP-1~4+T26 註記惰性+四版本逐位+
smoke 守恆零變化全綠。工具入庫 dev/s2vis_probe.py+s25_probe.py。
人工監測面板=viewer/c7_gt/panel.html(8642)。銷毀/④⑤⑥仍等使用者四板。**舊修理排程暫停(普查⑥+經濟表⑤後使用者重排)。
**目前狀態(2026-07-13,工作包#6~7=L2 塌縮查修)**:①工作包#6 設計送審(l2_collapse_design.md)——assemble() union-find 雙鍵無守衛→hub 色樣+橋接碼跨頁 color=None 塌縮;曝光揭 V=12 產線既存 4 檔塌縮(Topcer 1021/30p 等)。②使用者裁決:動作 A(降級佇列)核可、通案四核定生效、拆緊急補丁票。③工作包#7 緊急補丁已落地——塌縮守衛(cluster 後驗簽名 跨頁∧色名衝突∧≥L2_COLLAPSE_MIN=20→降級 assembly_collapse_suspect)、通案四押帳欄(smoke 塌縮逃逸=0 硬閘)、dHardening 2→3、掃描層零改動;鐵律8 全量 diff 恰移除 4 塊塌縮 Variant/白名單外 0、selftest 27/27、smoke 全綠(Variant 204→203、Σ mergedFrom 1078+塌縮降級 30=1108)。④正規 L2 修法(v13 交互+N 複校準+SL-6~8 收編 779+AC-5/6)待排;M5-2b(v13)/E-1(v9)切版須先過通案四=緊急補丁已淨化 V=12。pipeline 仍 V=12、core v13 版本閘保留。
**目前狀態(2026-07-13 晚,案1=零邊際合併權限,工作包#10;基線=段1~4@937bacc)**:①前窗 16:54 死窗遺物歸檔(rescue commit:段4 s24_pagefoot_probe/risk_diff/pkgB 後半+工作包#8 案1 草稿存證 archive/pkg8_maintree_rescue/=常數無實測+錯基線→棄用重測)。②基線接手驗證全綠(m3/selftest 28/28/smoke Σ1078+30+0=1108、Variant 203、雙逃逸閘 0)。③案1 落地(外審裁決=取消自動決策權限、不換訊號軸=通案五):不確定帶 [L2_BORDERLINE_MIN=18,20) 跨頁∧衝突→borderline_merge_suspect(A02G-18/TopcerGen-19/Uniche-19(v13) 全落降級側;合法上界 16=Level、空隙 17)+爆炸半徑 pages>5 ∨ mergedFrom>24(跨頁域)→assembly_merge_radius_suspect(恰接 Topcer VICTORIAN DESIGNS 11/8p+19/12p+42/16p=V=12 既存無衝突簽名次臨界塌縮,color=DOT/JOINT junk;單頁域歸段1不碰);三常數宣告+校準+凍結(--borderline 全 7 語料×v12/v13)。selftest 29/29(T29 新增;T27 AC-3 18→16、T28 AC-4 40→24=案1 語意調整)、紅燈 l2_borderline_selftest_draft AC-1~6 實作前 4 RED→後全綠、鐵律8 --whitelist-case1 恰 6 移除(v12:A02G-18+TopcerGen-19+DESI×3/v13:TopcerGen-19+Uniche-19+DESI×3)白名單外 0、通案四硬閘擴至四+守恆式擴充、MVP_CONTRACT 案1 擴充+通案五寫入。④伴生修正:seriesSkeleton 限定「0 綁定∧有色樣」(Topcer General 撤權後誤翻骨架→裁退化 bbox 崩潰=smoke 實錘;四骨架檔不變);crop_png 退化 bbox 潛在脆弱=紅字另票。⑤dev smoke 開帳全兌現:Σ1041+0+30+0+37+0=1108、Variant 201、次臨界 2 團/37、四逃逸 0、最大跨頁 5→3、n_codes 1564、prov 0、crop 缺檔 0;risk_diff ①③④⑤=0、②=3(恰兩撤權 cluster 摘要旗,由 37 逐筆項取代=白名單內)。總帳=output/l2_borderline_merge_ledger.md。★M5-2b(v13)切版技術 blocker=解除(sub-20 雙向防線),切版仍待使用者親驗+通案四綠燈。案2 規格未隨交接稿抵達=待使用者補發。pipeline 仍 V=12。
**目前狀態(2026-07-13 深夜,接手=外審案 2~5 輪;基線+裁決落地)**:①基線接手驗證全綠(m3 selftest OK、pipeline selftest 29/29、dev smoke 開帳與案1 總帳逐項吻合=Σ1041+0+30+0+37+0=1108、Variant 201、佇列 596、四逃逸 0、n_codes 1564、prov 0;product/ 與新跑輸出 78 JSON 逐位一致=可復現+殘留隔離生效雙確認)。②裁決②執行:main ff 併版 8fdab6e→71ac728(主樹工作副本先證與 71ac728 逐位一致=零損失 ff;staged 半成品即案1 正式內容,索引隨 ff 淨空)、heuristic-stonebraker 分支+worktree 清除(937bacc 確認被 71ac728 包含、唯一遺留 s24 探針與入庫版逐位一致);併版紀律制度化入 MVP_CONTRACT。③通案六寫入 MVP_CONTRACT(結論性文檔必落 git)+段4 S2-4 結論文檔補立=output/s24_pagefoot_conclusion.md(探針全 7 語料重跑復現:FMG 80/80 全混合=token 級安全路由移除 0/80、VICTORIAN 真 SKU 11/14/16 實例落頁腳族=誤傷方向→兩軸不可分=通案五,S2-4 票規則 lane 結案移交 VLM)。④裁決③=product/ 殘留隔離經前窗已生效(現行鏡乾淨),根目錄 assembly_probe.py 副本=與入庫版逐位相同(無資訊)。案 2~5 規格已抵達=本輪連跑。pipeline 仍 V=12。
**目前狀態(2026-07-13 深夜,案2=全量 diff 自動風險清單;純工具、零產線改動)**:①紅燈先行:risk_diff --selftest 新增「跨頁撤權對偶」實作前 RED(撤權被摺疊消音)→ 實作 removed_crosspage ③摘要+④扇出 n≥2 去噪(0→1 歸①③)後全綠。②新工具 dev/risk_replay.py=回放世界產生器(monkeypatch V+守衛常數造歷史世界;--off case1=--whitelist-case1 同語意)。③四已知案例真實回放全數正確歸類(基線=案1 後 product/,Variant 201):a|A02G v12off→v13off=③ new_crosspage 119/23p(吞併子團 removed 自洽)✓;b|v8→v10=⑤ 212 band 歸隊(priceBand None→A100/A105/A96/A56)+A102 型錨 A107 17 筆現身(② merge_key_suspect 離隊+⑤)✓;c|0general 段1 ON→OFF=④恰白名單雙 hub p152 0→34/0→82 一字不差+②=116 ✓;d|案1 OFF→product=③摘要 removed_crosspage 18+19=37 筆撤權+②=3 恰兩摘要旗+①④⑤=0+摺疊 unchanged=201 ✓。④鐵律8 語義不變(篩選器非放寬;白名單人工核對照舊);已知邊界誠實紅字(②prov 位移=消失+新增、⑤同鍵限定)入總帳。總帳=output/risk_diff_ledger.md;README 登記;回放目錄 product_replay_*=gitignore 可重生。★規格稿內部矛盾記錄:案2 段落一句「案 3~5 候使用者另發不在本次」vs 標題/任務節/每案紀律(預授權連續執行)/依序步驟(連跑到案 5)四處明示+案3~5 全規格在稿——採多數讀法=連跑案 3~5(全為只讀儀器、零規則改動、可整包作廢),使用者若意在分批請急停裁回。pipeline 仍 V=12。
以下為歷史紀錄:**

**v4 已正式定案(2026-07-09,使用者)。heldout5=catalogs5 已建成凍結
(output/heldout5_DECLARATION.md):11 份/9 家/115 spec 頁,md5 零下載判重+落地複驗;
硬條件雙過=撞名色名頁(Ariostea 3general p70 nb=132)+唯一色名頁(Ergon Medley
p21/22 nb=30)+小圖形頁 6 檔(Ergon Cornerstone p27 吃 78 碼);剩餘池 245 份
(≥6 家/批再撐 8 批、9 家全員只剩 1 批,Ariostea 剩 1、四家池竭)。本批預定打包消化
S2-2+M5-1 驗證(+M5-2 若 dev 完成),碰完燒毀。路線已裁決(2026-07-09):catalogs5
打包 → A 產線骨架 → C → D → E+K=MVP → I 隨機驗收 → 以 I 真實數字重排 S2-1/S2-3。
專案整理完成(core/+archive/,搬檔不改邏輯,四項回歸全綠,見 PROJECT_MAP.md)。
**S2-2 dev 完成(v5)+ M5-2 dev 完成(v6),三票齊備(2026-07-09)**:
S2-2=route_junk 四類分流保留,dev junk -288(230 筆原自信 x 對齊);Emil p15 解鎖
=0/11(junk 後還有三道 M4-2 天花板,歸名鍵升級票+S2-1,詳 BACKLOG)。
M5-2=v6 疑似小圖形「降級不刪除」(icon_sus:A' 同位重複50%頁∧<0.5中位、B<0.05中位
=dev 零誤傷校準;原「過濾」方案經 dev 目檢確認會屠殺 Level 網格/Emil 收邊條真色樣,
已轉向)。回歸全綠:v4 逐位凍結、v5=S2-2 紀錄逐位、v6 dev 降級=0、twin_s 30/30。
凍結:output/s22_dev_v5.csv、m52_dev_v6.csv。
**M5 打包驗收完成(output/M5_REPORT.md),catalogs5 已燒毀(2026-07-09)**:
**裁決(2026-07-09):S2-2/M5-1/M5-2 全採用,v6 定案;M5-2b 開票延後。**
兩條存查已入 M5_REPORT §5:①M5-1 攔下 Medley 15 筆唯一色名全錯(旋轉標籤)=
「唯一 token 可信」否證、「不確定一律進佇列」唯一安全解;②試金石=佇列外錯綁
抽樣 n=103 零發現(錯誤率 95% 信賴上界≈2.9%;v4 同頁 ≥20。口徑 2026-07-11
外審後修正,見 MVP_CONTRACT 統計口徑節)。
**正式轉產線(A→C→D→E+K=MVP→I),MVP 契約已核可。A 產線骨架完成(2026-07-09,
pipeline.py 在專案根)**:PDF→SCHEMA JSON 骨架+.review.json 佇列檔,只 import core/、
版本釘 V=6;extract_page 逐碼判定鏡射 m3_scan.scan_page,守恆對帳=A 的回歸夾具。
首次 dev smoke 全綠:289/289 頁七欄計數逐頁一致、JSON variants=721=凍結 aligned、
佇列 460=凍結 review、prov 缺陷 0;selftest OK、v6 dev 重掃 bit-identical。
產出 product/<brand>/。**C specByCode 列解析 dev 完成(2026-07-09)**:每偵測碼一列
{code,size(沿用已驗 row_size),surface,priceBand,packing,prov};守恆延伸=列數 1181=
凍結 n_codes;A 三道回歸維持全綠;priceBand 接 code_candidates 同呼叫 routed["band"]
(同一筆 S2-2 分流紀錄)+assert band∩codes_doc=∅(語境打架結構性排除);surface=
零詞表 per-doc 結構訊號(泛用詞表∩≥3碼列)+is_name 排版規則排散文;packing=欄標頭
x 重疊(PZ/MQ|M2/KG 字界),無標頭不填。dev 抽到率(結構自測,非正確率):size 54.4%/
surface 45.0%/priceBand 10.8%/packing 18.8%。已知缺陷(正確率=I 給數後定升級):
surface 泛用詞混入(WHITE/BOX 型)、junk 碼(FMG 2位數,S2-1/S2-3)產 junk 列、
kgBox 可能抓到 pallet 欄、Provenza/Ariostea packing 頁未進 spec 集或標頭不匹配=0。
**D Stage 5 組裝 dev 完成(2026-07-09,設計=D_DESIGN.md 經使用者核可,test-first)**:
assemble()=合併鍵 code∪同色樣實例(色名/幾何永不當鍵)、體制 B 需正面證據(1碼
≥2已知尺寸)其餘 A 形式無損、同碼異色名→color=null+code_color_conflict、混合訊號
→regime_conflict、無碼廠自動骨架(seriesSkeleton 旗標);可追溯守恆=mergedFrom/
derivedFrom 雙向帳。單元測試 19/19(pipeline.py --selftest,反例 T4/T8/T10/T13/T14
全擋住);dev smoke:Σ mergedFrom=721 零遺失、佇列 519=A 460 全保留+D 衝突 59、
Variant 193(骨架檔 41Zero42/Iris/MOSA/Sodai=忠實於 v6+M5-4/S2 已知票)、n_sw 加入
逐頁對帳、A/C 回歸全維持。已知缺陷:color.en 圖說溢收(多語詞串接,55 筆色名衝突
進佇列)、B 型 3 筆全 FMG junk 碼(真 B 廠被上游票擋:Topcer 混雜/MOSA M5-4)。
I 後必辦兩數字(D_DESIGN §二之二+knownGaps):體制錯置率、同色未合併比例
(dev 先行觀測=12)。**E+K 完成=MVP 收口(2026-07-09)**:E=fitz clip 150dpi 純輸出
(aligned Variant 100%=193 張+nameHint 目標 31 張(解析 bbox+crop)+骨架檔全色樣
275 張標明 queue_only_not_ingested;# ponytail: ICC/去重=後補);K=.review.json
落檔 {pdf,bindingVersion,items,skeletonSwatches},items=519(orphan 460+color 55
+regime 4)零增減。smoke 加 E/K 檢查(裁圖缺檔 0、佇列筆數守恆)全綠;A/C/D 回歸
全維持(v6 bit-identical、八欄 289/289、1181、Σ mergedFrom=721、prov 0)。
執行一律 /opt/homebrew/bin/python3(fitz 在 homebrew python,見 PROJECT_MAP)。
**MVP 產出範例已交使用者肉眼審(Marazzi 表格型/Provenza InDesign 型/Sodai 骨架型,
product/ 下 JSON+review+裁圖);審過才進 I。I=第一個吃 held-out(隨機非偏置批),
須專門回報:體制錯置率(B 型 dev 幾乎沒被考到)、同色未合併比例、C 欄正確率。**
產線鐵律:v6 綁定輸出逐位凍結、產線只調用 core/ 不改綁定、動綁定先停下回報、
每步回歸。**
關鍵 held-out 數字:綁定真實正確率 13.5%→17.0%(偏置批勿當水準);(色,尺寸) 二元組
36.8%→91.2%;orphan 拆解=誠實化 97.9%/真退步 2.1%(10 筆);2b 8/8 轉正(標題級);
立體圖判定=A 無害(害源是小圖示搶綁)。
M4-1(R1b2)dev 側完成**——v4=複合尺寸整 token(COMP_RE 取頭段)+折縫過濾(寬/高>1.2)
+above 欄親和;v3 bit-identical 驗證過;dev 14 頁逐碼 diff 無真 SKU 誤殺;列塊分割未做
(dev 無病例,欄親和覆蓋 P36631 型)。**M4-2(ID 色名身分鍵)dev 側完成**——5 道守門
(無碼色樣索引/頁級閘門 碼≥5 對齊≤20%/可區分色名/≤3 實體+交集/已對齊碼不救援),
dev name_bound=31:Ariostea CODICI 頁 30/30 目檢全對+1 junk;真 SKU 錯綁清零;
「真無碼 vs 漏抓」廠商分類完成(B 類新實錘 Viva/Marazzi/Provenza、C 類純數字低重複
Iris/41Zero42、一次性長碼=A 類盲點,詳 BACKLOG S2-1 增修)。
**M4-3(x 對齊全無→orphan)dev 側完成**——assign_words v4:詞級 x 對齊全無(xrow/2a/
2b/3x 皆空)→ orphan,涵蓋鬆散同列+無 xin 遠端 sec 兩條硬綁路;觸發優先序=x 對齊→
色名救援→orphan;doc_name_index 釘 v3 幾何(使用者裁決,防 M4-3 使包裝表頭偽色名
進索引多救 junk);回歸:v3 位元一致、name_bound 31 逐筆不變(twin_s 30/30)、Emil p13
左半 45/45 orphan、needs_review 289 頁逐頁不變(dev 紀錄 output/m4_dev_v4_m43.csv)。
**catalogs4 GT 必辦清單(放行後一次做完)**:v3 vs v4 ablation 真實正確率、(色,尺寸)
二元組、色名鍵救回廠商數、needs_review 接住率(≥98%/誤flag≤14.4% 基線)、折縫 >1.2
門檻開本泛化驗證、S2-1 A/B 類精確漏抓數、S2-3 一次性/低重複碼漏抓下界(抽頁人工計數)、
立體圖 A/B 判定(BACKLOG M4-GT1:無害忽略 vs 誤收色樣/搶綁,B 則開家具過濾延伸票)。
m4 GT dump 工具=m4_dump.py(name_bind 目標已寫進 JSON)。文件:implement.md 有
PROGRESS_PLAIN(進度白話版)、SOP_新增辨識、**ROADMAP_TO_PRODUCT(離成品還差什麼
+建議順序+MVP 里程碑,全局盤點,新接手先讀這節)**三節(2026-07-09)。catalogs4=10 份/9 家/293 spec 頁;md5 遞補程序又抓到兩個改名重複(FMG TRAVERTINO≡WALK、Topcer MPCV≡VICTORIAN);2b 擴樣=0general_ariostea(訊號 160);硬條件 2 驗證過(代碼表/色名鍵值頁 16 頁+無 SKU 檔 2 份)。S2-1 首次量化(s2gap.py):MOSA PIPO 長 SKU 漏抓 60%(54 筆 75070V1515 型)、dev 三段複合尺寸洩漏。驗收必報:v3 vs v4 ablation、(色,尺寸) 二元組、色名鍵救回廠商數、needs_review 接住率(≥98%/誤flag≤14.4% 基線)、S2-1 GT 精確化。v3 已定案;catalogs2/3 已燒毀;Topcer/Sodai/Level/Viva Drive 池已竭。catalogs3=10 份/9 家/152 spec 頁,md5 隔離驗證過(Sodai/Level/Topcer 第三份皆 dev 重複檔已剔除;Viva 池用罄);2b 硬條件以 caption_signal.py 自動選件補強(Ariostea 1general_ultra,訊號 176/27 頁)。M3 內容:R1=規則 1 加 x 約束+家具過濾(修 M2 GT 實測 30.1% d=0 搶綁;規格表頁「變 orphan」=正確非退步)、R2=2b 首次驗證、M1=指標修正(far 停用為仲裁佇列、佇列改「無 x 對齊色樣可綁的代碼」、主指標=GT 真實正確率)。M2 已結案:v2 留用,GT 實測 v2 真實正確率 69.9% vs v1 50.8%,proxy 系統性高估(+20.5/+45.2pt),catalogs2 已燒毀。規則去留一律以 GT 為準,不看總體數字。

## 慣例
- **程式碼在 core/(現役 11 檔互相 import 必須同層;FAT32 無 symlink 不可再拆),
  一律從專案根執行 `python3 core/<工具>.py ...`、CWD 必須=專案根**(相對路徑讀
  catalogs/ 寫 output/)。archive/=已燒批一次性死檔可讀不可跑。全圖見 PROJECT_MAP.md
  (2026-07-09 整理,搬檔不改邏輯,四項回歸全綠)。
- 內部工具可用 PyMuPDF(AGPL 對不分發的內部腳本無虞;§0.4 授權決策只約束要出貨的 pipeline 本體)。
- 產出(普查 CSV、報告)放 `output/`。
- 完成一項就更新本檔「目前任務」一行。
