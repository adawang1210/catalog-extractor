# demo 前端 14 檔問題診斷 總帳(2026-07-14)

**性質**:診斷審查(只讀查證+歸類),對使用者目視 demo_showcase 14 檔後回報的 5 問題。
**紀律**:零規則改動、零凍結常數變更、零過擬合;`pipeline.py`/`core/`未動。問題 5(前端框樣式)
+問題 1 的 B 類可見度=純呈現層,已於本輪同步落地(`viewer.py` CSS/JS,見末節)。
**通案六**:本檔=結論性文檔落 git,尤其「A 類=空、切版非 demo 解」這個**反直覺實測判定**必須留存,
防未來重複「切版即解」的樂觀假設。

## 方法與儀器

- 對齊 PROMPT/MVP_CONTRACT(通案一~六)+ knownGaps。
- 現行 V=12 引擎輸出=`/Volumes/USB DISK/demo_showcase/product`(A4 seed=20260713 抽樣,每語料 2 檔)。
- 既有只讀儀器跑 demo 產出:`dev/crop_authenticity_scan.py`(C1–C4)、`dev/field_prov_scan.py`(F1–F5)。
- **切版回放**:`dev/risk_replay.py` monkeypatch `pipeline.V` 造 v13/v9 世界(--nocrop),
  比對 V=12 基線——這是本次否證「切版即解」的關鍵手段。

## 14 檔頁級處置覆蓋(共 733 頁)

| 態 | 頁數 | 意義 |
|---|---|---|
| auto(已綁定產品) | 81 | 有框(藍/綠) |
| review(已偵測·進佇列) | 116 | 有框(橘 dashed/紫/灰)=**B 類主體** |
| noprod(掃描規格頁·無可綁) | 69 | 無框;(a)真無產品 或 (c)靜默漏抓混雜 |
| nonspec(未達 size 閘) | 453 | 無框;大宗=封面/目錄/內文/情境跨頁(正確無產品) |
| image(影像/掃描頁) | 14 | 無框;C 類 VLM 候選 |

## ① 問題 1~4 逐案歸類

| # | 問題 | 代表案例(檔·頁) | 儀器證據 | 歸類 | 結論 |
|---|---|---|---|---|---|
| 1 | 磁磚漏標 | Iris slide-556(30p 全 0 綁/0 佇)、MOSA Tide(V0) | coverage+knownGaps | **C** | 低重複純數字碼=S2-1 C 類 known gap,整檔靜默漏,VLM lane |
| 1 | 磁磚漏標 | Topcer VICTORIAN(Q1168=collapse1021+radius72) | 佇列 reasons | **B+C** | 已全進佇列(有框);拼磚/馬賽克幾何不可格級綁=通案五 VLM |
| 1 | 磁磚漏標 | FMG WALK(Q211)/Marazzi SistemT(Q50)/Emil(Q39/Q35) | 佇列=orphan | **B** | 引擎已偵測進佇列、前端有框;「看起來漏」=呈現不明顯 |
| 2 | 標到場景照 | Marazzi Rice p7「Rice Blu Lux **Scenario** Tappeto Nero」(已綁 Variant，code=None) | crop C3 | **D** | ★E-1/v9 回放**不觸碰**(見③);A02G 型不在 demo |
| 3 | 標到文字 | Ariostea p26/119/133(裁框 100% 涵蓋碼 token，已綁 Variant) | crop C3 | **D** | 文字/caption 裁成色樣;E-1 回放不觸碰(非照片級 S1) |
| 4 | 標到包裝外觀 | Ergon Medley p23/Provenza Revival p22/Viva Metallica p21(`surface='Box'/'Battiscopa Box'/'Tile Right Box'`) | field F2=99 筆/4 檔 | **D-輕** | `surface` 欄吃包裝詞=欄級噪音，**產品本身是真磁磚、非誤綁** |

補:crop C1_crop_reuse=2(Topcer p30≡p05 逐位相同裁圖)=馬賽克塌縮副作用，併 Topcer C 類。

## ② 問題 1「漏標」三分解(頁級，跨 14 檔)

- **(b) 偵測到但未綁定=進佇列**:**116 頁**,含 **1743 佇列項 + 88 骨架 = 1831 個框**,
  前端**已顯示**(dashed/灰)。→ **B 類**:呈現問題,非漏。**這是「漏標」感知的壓倒性主體。**
- **(a) 無產品(正確)**:大宗落 nonspec(453)+真 noprod。非缺陷。
- **(c) 靜默漏抓(產品完全沒被偵測)**:藏於 noprod(69)+image(14)+部分 nonspec。
  **無法用儀器精確計數(需逐頁 GT=I 批的活)**,但機制/病灶已收斂:Iris slide-556(整檔)、
  MOSA Tide、S2-1 B 碼/S2-3 長碼/C 類純數字型(PietraEssenza p21 純 B 碼頁)。
  與 I_REPORT「B 類靜默漏抓 19%」一致。

## ③ 切版 ROI(A 類)——★實測否證「切版即解」

| 切版 | demo 實測(risk_replay) | 判定 |
|---|---|---|
| **v13(M5-2b 救回 369 碼)** | Rice V=12→V=13:icon_demoted 26→0 **但**誘發 44 `assembly_collapse_suspect`、綁定 **4→1(反而更少)**。救回碼過連通臨界→撞 L2 塌縮守衛→整團進佇列 | **非 A 類**:demo 救回目標(A02G/Uniche/Re-Play)**不在 14 檔**;Rice 反退步 |
| **E-1/v9(場景照降級)** | Rice V=9、Ariostea V=9:與 V=12 **逐項相同**;`photo_demoted` 未觸發、Rice p7 場景照仍綁定 | **非 A 類**:E-1 的 S1 面積閘校準在 A02G 型整頁 render，demo 場景照達不到門檻 |

**★E-1 結構事實**:E-1 在 `core/m3_scan.py:309` 是 `if version == 9:`(**精確等於，非 ≥**),
現行 V=12 路徑完全跳過。E-1 是名副其實「懸空側枝」——**不是撥一個開關的切版**;要修問題 2,
須把 E-1 前移併進 v13 主線並重新校準/驗收(通案二+四),那是**引擎工作，非切版**。

**A 類清單 = 空。demo 14 檔沒有任何一個問題靠現成切版就消失。**

## ④ 純前端可立即做(B 類 + 問題 5)= 本輪已落地

- 問題 5 框樣式:透明填充 + 外框加粗 3px + 依類型/disposition 上色(已有色)。
- 問題 1 B 類可見度:review 頁 disposition banner 加「此頁已偵測 N 項待複查…非漏標，是待人工」。
- 範圍=`viewer.py` CSS(`.box.*`)+ `dispoBanner()` JS,**零碰 `collect()`/綁定/座標**。
- 驗證:14 檔重生;FMG WALK p275(64 框密集頁)實測 queue 框 `border:3px dashed`、
  `background:rgba(0,0,0,0)` 透明、banner 顯「已偵測 64 項待複查」。py_compile OK。

## ⑤ D 類(記票不改，禁過擬合)+ C 類(VLM 洞)

**D 類**(共性=判別度不足;一律記票、禁為單檔改規則):
- **D-1 場景照綁成產品**(問題 2):Rice p7 型,code=None、color.en=場景 caption。
  病灶=E-1 未前移主線 + 面積閘只涵蓋 A02G 型整頁 render。正解=E-1 前移重校準 或 VLM。
- **D-2 文字/caption 裁成色樣**(問題 3):Ariostea p26/119/133(C3,裁框 100% 涵蓋碼 token)。少數、訊號弱。
- **D-3 surface 欄吃包裝詞**(問題 4):F2=99 筆/4 檔。非誤綁、欄級噪音;加 `fieldQuality` 旗即可、最低優先。

**C 類**(已在歸檔清單，無新增):
- Topcer VICTORIAN 拼磚/馬賽克(通案五)、Iris/41Zero42 純數字整檔漏、純 B 碼頁(PietraEssenza p21)。

## ⑥ 嚴重性真實分佈

- 問題 1「最嚴重」→ 真實=**多數 B 類**(116 頁已進佇列、前端不明顯)+ 少數 C 類已知 VLM。真嚴重性**中→低**。
- 「以為切版能救」→ **A 類=空**;v13 讓 Rice 反退步、E-1 碰不到 demo 場景照。**需修正期待**。
- 問題 2/3(場景照/文字框)→ **D 類真殘留**,無現成切版可解;要嘛前移 E-1(引擎+重驗)、要嘛 VLM。真嚴重性**中**。
- 問題 4 包裝 → **D-輕**、cosmetic。真嚴重性**低**。

**一句話**:看起來最嚇人的「漏標」大半是前端沒把「已進佇列」畫清楚(B 類,已隨問題 5 一起修);
真正要動引擎的是問題 2/3,而且**別指望切版**。全程零規則、零常數、零過擬合。
