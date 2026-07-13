# 案1|L2 零邊際合併權限總帳(工作包#10,2026-07-13;外審修正案)

## 一、裁決與範圍

外審裁決(審查方採納,制度化=MVP_CONTRACT 通案四案1擴充+通案五):sub-20 真塌縮
與合法團在 size 軸零邊際(段2 複校準:非塌縮上界 19=真塌縮 19 同值,[19,20] 相鄰;
fan-out 軸前已否決=兩軸皆不可分)→ **正解=取消自動決策權限,不換訊號軸**。在會把
23 頁黏成一筆的系統裡,拒絕合併是功能非失敗。只改 `pipeline.assemble()` cluster
後處置;A 綁定、版本釘 V=12、L2_COLLAPSE_MIN=20/AREA_T=5.0、A' 皮帶與 M5-2 icon
母體均不動。失敗方向=寧不合併不自信錯綁(鐵律2),降級帶 prov/swatch 資料無損。

前窗草稿(archive/pkg8_maintree_rescue/)同名常數僅斷言無實測、基於缺段1守衛的
main@8fdab6e 錯誤基線=棄用;本包全部重測(其半徑「2 頁」若落地會誤降合法團
≥10 個=本帳 §三之二實測反證)。

## 二、量測(通案二;dev/assembly_probe.py --borderline,全 7 語料 × v12/v13)

對現行雙守衛(跨頁≥20∧衝突/單頁≥20∧area%≥5.0)**放行**的 cluster 三分帳。

### 帶母體(跨頁∧色名衝突∧<20)大小分布(升序)

| 語料 | v12 | v13 |
|---|---|---|
| catalogs(dev) | 4×18,5,6,7,8×24,13,13,16×19,**18,19** | …,16×19,**19**(18 已併入 ≥20 被既有守衛接走) |
| catalogs2 | 4×16,8×20,16×19(全 ≤16) | 同 v12 |
| catalogs3 | 8 | 8 |
| catalogs4 | 5 | 5 |
| catalogs5 | 4,5,6,6,15 | 4,5,6,6,7,15 |
| catalogs6 | 2,5,6,7,9,9,10,10,11,12,12 | 3,5,…,12,12,**19**(Uniche v13 誘發) |
| catalogs7 | 11,15,15 | 3,4,4,4,5,5,5,11,15 |

**真塌縮側(GT/定性依據=段2 l2_v13_interaction --dump+本包身分核對)**:
- **A02G-18**(dev v12,5 頁,colors/raw=5/8)=V=12 產線既存 color=None 出貨(段2 帳
  「A02G 8 個 maxNone=18」之最大者);v13 下併入 119 巨團=既有守衛接走。
- **Topcer General-19**(dev,4 頁,colors/raw=2/4)=v12 既存+v13 同;colorRaw 全
  junk(表頭/規格段/碼片段),格式碼 OCT/STP/TR 橋接(段2 定性)。
- **Uniche-19**(catalogs6 v13,3 頁,colors/raw=1/3)=v13 誘發,同病理(同檔 20/27 之弟)。

**合法側上界=16**(Level/Level CG Light 型,2 頁欄頭矩陣,大量 16/8/4 團=包B GT
錨定合法型)。**[17,18) 空=淨空隙 17**。→ **L2_BORDERLINE_MIN=18**(宣告+校準+
凍結):三個已知真塌縮全落降級側、16 上界合法團全留保留側、帶內掃入合法=0。

### 半徑母體(帶處置後仍放行的跨頁 cluster)

- 非衝突跨頁 cluster 全語料僅存在於:Level/Level CG(**24/2p** 上界、16/8/4 皆 2p;
  dev+catalogs2)與 **Topcer VICTORIAN DESIGNS**(catalogs2:**42/16p、19/12p、
  11/8p**、4/4p;color=JOINT/DOT=馬賽克縫線詞彙 junk 色名=dev VICTORIAN 1021 塌縮
  姊妹檔之次臨界變體,V=12 產線既存出貨、無衝突簽名=帶與塌縮守衛皆照不到的型)。
- 衝突 sub-band(<18,合法保留)跨頁上界=**5 頁**(41Zero42 MILANO70 10/5p、
  Ariostea 3general 8/5p;4 頁=Treverkhome 15、Rice 15、Chill 15/11、Hello 12、
  Room Wall 12、Vivo 9(v13)…)。
- 頁軸:合法佔據 [2,5]、病理側下界 8 → **空隙 [6,7]**;吞併軸:合法上界 24(Level)、
  病理側下界 42 → **空隙 [25,41]**。
- 單頁域:合法單頁大團存在(Ariostea 0general v13 **25 綁定**、Provenza 19、Ergon 16
  …)→ **半徑不碰單頁**(單頁域=段1 AREA_T 守衛管轄+anomaly_probe 灰帶常態監看)。

→ **L2_AUTO_MERGE_MAX_PAGES=5、L2_AUTO_MERGED_FROM_MAX=24**(宣告+校準+凍結;
語意=已確認合法自動合併上界,超出=未經審計,撤銷自動權限送審,非判塌縮)。

## 三、動作與守恆

| 命中條件(跨頁=pages≥2) | review reason | 動作 |
|---|---|---|
| 跨頁∧衝突∧≥20 | assembly_collapse_suspect | 既有,不動 |
| 單頁∧≥20∧area%≥5.0 | singlepage_overmerge_suspect | 既有,不動 |
| 跨頁∧衝突∧[18,20) | **borderline_merge_suspect** | 案1① 整團降級 |
| 上皆非∧跨頁∧(pages>5 ∨ mergedFrom>24) | **assembly_merge_radius_suspect** | 案1② 整團降級 |

**伴生修正(實作中發現,案1 diff 內)**:`seriesSkeleton` 原定義=`not variants ∧ 有
色樣`——Topcer General 唯一 Variant 被帶撤權後翻成「無碼廠骨架」=語意錯誤(有 19 筆
綁定在佇列≠無碼廠),且骨架路徑裁全頁色樣撞退化 bbox 色樣使 write_out 崩潰(smoke
初跑實錘)。修正=骨架限定「0 綁定 ∧ 有色樣」(Sodai/41Zero42/Iris/MOSA 四骨架檔
不變=smoke 骨架檔列表回歸);被撤權檔之佇列(帶 prov/swatch)即人工材料,不翻骨架。

通案四守恆式擴充:`Σ mergedFrom+L2 降級+塌縮+單頁過併+次臨界+超半徑=凍結綁定總數`。
smoke 硬閘擴至四:塌縮逃逸/單頁過併逃逸/**次臨界逃逸**([18,20) 跨頁∧color=None 出貨)
/**超半徑逃逸**(>5 頁 ∨ 跨頁>24 綁定出貨),皆=0。
(注:逃逸閘以 color=None 代理衝突簽名,與既有塌縮逃逸閘同口徑;無衝突且無色名之
[18,20) 跨頁團=量測中不存在,若未來出現閘會誤鳴=fail-safe 方向,調查後處置。)

## 四、紅綠驗收(鐵律7 紅燈先行)

- 紅燈:dev/l2_borderline_selftest_draft.py 實作前 **AC-1(19)/AC-1b(18)/AC-3(6 頁鏈)
  /AC-4(26 綁定)=RED**(全部出成 Variant)、AC-2(16)/AC-5(上界 24 綁定+5 頁鏈)
  /AC-6(非干涉)=恆綠。實作後 **AC-1~6 全綠**。
- selftest:**T29 新增**(帶+半徑+上界合法/非干涉對偶)=29/29;**T27 AC-3 語意翻轉**
  (18→16=帶下緣外;18/19 案例移 T29)、**T28 AC-4 大小 40→24**(半徑上界內,保持
  「兩守衛皆不誤動」原意)——兩處為案1 之必然語意調整,非鬆動,draft 檔同步。
- m3 selftest OK(core/掃描層零改動);掃描層凍結 CSV 不動(assemble 層後處置,
  s21ext_dev_v12.csv byte-identical=smoke 頁級 9 欄 289/289 佐證)。

## 五、鐵律8 全量 diff(--whitelist-case1:案1 三常數 OFF↔ON,既有守衛保持 ON)

白名單=僅:dev A02G-18+Topcer General-19(v12)/Topcer General-19(v13,A02G 已入
≥20)、catalogs2 Topcer VICTORIAN DESI 11+19+42(v12/v13 同)、catalogs6 Uniche-19
(僅 v13)。**實跑(全 7 語料 × v12/v13,84 檔 ×2)=預測零偏離,全 ✓白名單守住**:

| 語料 | v12 移除 | v13 移除 | 白名單外新增 |
|---|---|---|---|
| catalogs(dev) | 2(A02G-18 None、TopcerGen-19 None) | 1(TopcerGen-19 None) | 0 |
| catalogs2 | 3(DESI 11 DOT/42 JOINT/19 JOINT) | 3(同 v12) | 0 |
| catalogs3~5,7 | 0 | 0 | 0 |
| catalogs6 | 0 | 1(Uniche-19 None) | 0 |

## 六、押帳與開帳(dev smoke;先押後開)

**押**:pages 289/289;Σ mergedFrom 1041+L2 0+塌縮 30+單頁 0+次臨界 37(2 團=
A02G-18+TopcerGen-19)+半徑 0=1108;Variant 201;n_codes 1564;四逃逸閘 0;最大
跨頁 5→3、最大吞併 24;prov 0;骨架檔四檔不變。
**開(實跑)=全數兌現零偏離**:`pages=289/289 頁級不一致=0;Σ1041+0+30+0+37+0=1108;
Variant=201;次臨界帶=2 團/37;超半徑=0;逃逸(塌縮=0/單頁=0/次臨界=0/超半徑=0);
最大跨頁=3 最大吞併=24;骨架檔=['41Zero42','Iris','MOSA','Sodai'];n_codes 1564;
prov=0;crop 缺檔=0;smoke OK`。佇列 562→596=456+D 衝突 140(ccc 69→67、regime
7→6=兩撤權 cluster 的摘要旗不再產;+37 borderline)。認領 spec 列 1251→1204(撤權
cluster 不認領;列全數留 specByCode=C 層守恆)。
**risk_diff(product 基線 vs product_case1)**:①新自動放行=0 ③新增/擴跨頁=0
④扇出上升=0 ⑤prov/角色變動=0;**②佇列項消失=3**=A02G ccc×1+Topcer ccc×1+
Topcer regime×1——恰為兩個被撤權 cluster 的 cluster 級摘要旗(旗的所指 Variant 已
不出貨),由 37 筆帶 prov/swatch 的 borderline 逐筆項取代=資訊嚴格增加、白名單內;
其餘摺疊=unchanged 201/removed 2(=白名單)。
(環境註:product/ 內 14 個他語料舊 session 殘留檔已移 scratchpad 隔離,risk_diff
需 before/after 同語料;跑後 product_case1 輪換為 product=現行鏡。)

## 七、殘餘已知缺口(誠實紅字)

- **<18 sub-band**:A02G 餘 7 個 color=None 跨頁團(≤13)等仍出貨,帶
  code_color_conflict 旗=非全靜默;依通案五=不再造判別器,歸 VLM/人工 lane。
- 合法側 16 上界若未來語料增長貼近 18=空隙縮窄,--borderline 為常態監看儀器。
- **crop_png 潛在脆弱**(案1 暴露的既存洞,未修=零現行觸發):骨架/裁圖路徑對退化
  bbox(寬或高 <1pt)色樣無防護,`get_pixmap→save` 直接崩潰;今由 Topcer 誤翻骨架
  觸發、修翻骨架後無現行觸發路徑。未來骨架檔若含退化色樣會重現(另票)。
- 帶/半徑=撤權送審,佇列增量 dev=+37 筆(佇列經濟帳 C 板材料)。

## 八、M5-2b(v13)切版 blocker 判定

sub-20 缺口已由不確定帶+爆炸半徑補上=與既有 ≥20 雙閘形成**雙向防線**;v13 世界
實測:Uniche-19 落帶、A02G-18 併入 ≥20 由既有守衛接走、DESI 三團半徑接走。
**技術 blocker 解除**(本包 smoke/全量 diff/通案四四硬閘全綠為準)——切版本身
仍需使用者親驗+通案四綠燈確認,不在本包自行執行。
