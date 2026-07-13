# 包 A｜全池組裝層異常巡檢報告(工作包#8;通案三)

**工具**：`dev/anomaly_probe.py`（借 `dev/pkgB_hub_sep.py` 之 `_clusters`/`_area_pct`,100% 鏡射
`pipeline.assemble` union-find + SL-6~8 降級)。**只讀不改規則,core/pipeline 零改動。**

```
/opt/homebrew/bin/python3 dev/anomaly_probe.py catalogs catalogs2 catalogs3 catalogs4 catalogs5 catalogs6 catalogs7 12
```
(CWD=主樹專案根;語料在主樹。ver 預設 12=現行產線。)

## 目的
確認除已知守衛涵蓋者外,**無「第二個 L2 塌縮量級災難」**——即無有塌縮簽名(色名衝突 或
單頁大 area% hub)卻逃逸兩守衛的 ≥COLLAPSE_MIN(20)巨團。

## 塌縮簽名 vs 合法合併(關鍵界定)
overmerge 病灶 = **色名衝突**(不同色名綁定被錯融=color=None 塌縮)**或 單頁大 area% hub**
(一大塊情境/索引版塊吞併整頁不同碼)。**同色大合併不是災難**——即使跨 16 頁,那是 T7 設計
內合法(同碼/同色跨頁本應併成一 Variant),不進災難帳、只列 sanity sweep。

## 結果(v12 全 7 語料,84 檔)

### 守衛涵蓋之 ≥20 塌縮/過併 cluster(6)
| 類別 | 檔 | 頁 | 綁定 | 跨頁 | area% | 衝突 | 守衛 |
|---|---|---|---|---|---|---|---|
| 跨頁塌縮 | Topcer VICTORIAN | p3 | 1021 | 30 | 0.345 | ★ | 工作包#7 |
| 跨頁塌縮 | FMG terrapura-698 | p88 | 115 | 17 | 50.910 | ★ | 工作包#7 |
| 單頁過併 | Ariostea 0general | p152 | 82 | 1 | 8.483 | 同色 | **段1** |
| 單頁過併 | Ariostea 0general | p152 | 34 | 1 | 7.015 | 同色 | **段1** |
| 跨頁塌縮 | Marazzi Stream | p3 | 32 | 6 | 41.603 | ★ | 工作包#7 |
| 跨頁塌縮 | Provenza Unique Travertine | p33 | 30 | 2 | 1.340 | ★ | 工作包#7 |

4 跨頁塌縮 = 工作包#7 `--whitelist` 恰移除的 4 塊(逐筆吻合);2 單頁過併 = 段1 目標
（Ariostea p152 純碼索引頁:一大 hub 版塊各吞 34/82 碼,同色名→跨頁守衛照不到、以 area% 攔）。

### ★灰帶監看 單頁 hub 衝突 ∧ area%∈[2.36, 5.0)(1)
| 檔 | 頁 | 綁定 | area% | 衝突 |
|---|---|---|---|---|
| Emil Millelegni 2023.03b | p23 | 8 | 2.974 | ★ |

意義:單頁衝突 hub,area% 未達 AREA_T。**若增長至 ≥20 會兩守衛皆逃逸**(跨頁守衛要 pages≥2,
單頁守衛要 area%≥5.0)=單頁過併母體(現況 Ariostea 唯一)之薄弱補償。現 size=8 << 20,無虞;
列常態監看,新語料若見此型放大即回報。

### ★未攔 ≥20 巨團(守衛外=第二災難候選)= **0**
**斷言達成**:所有 ≥20 塌縮/過併簽名巨團皆落守衛。同色大合併(Topcer p5 42/16p、
Level CG p52·p179 各 24/2p)= 合法,不計。

## 結論
**✓ 無第二個 L2 塌縮量級災難。** 灰帶邊界 1 例(Emil p23,常態監看)。數字全庫內可復現
(通案三)。core/pipeline 零改動——本包純巡檢。
