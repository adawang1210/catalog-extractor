# VLM 金絲雀車道 自架設計草案(D 板落地;2026-07-14 草案送審中)

**狀態=草案,未經使用者核可,零實作**。本文=設計案+待查清單;所有「待查」項
可交外部調研後回填,回填完才進送審版。

---

## 〇、硬約束(不可辯論的前提)

1. **禁用任何中國來源模型,含衍生品**(Qwen 全系/InternVL/MiniCPM/DeepSeek-VL 出局;
   olmOCR 雖為 Allen AI 出品但底模 Qwen2-VL=出局)。**選模必查底模血統**,美國機構
   出品≠非中國底模。
2. **只自架,不用任何第三方推理 API**(型錄=有版權廠商 PDF,不外送)。
   邊界待裁:租用 GPU 裸機(RunPod/Lambda 型)=自部署但資料上到租用機器——
   「嚴格不出門」只有本地 Mac;**此線需使用者裁決**。
3. **感測器非綁定器**(D 板定位):VLM 輸出只進 needs_review 佇列,永不直接入庫、
   永不成為綁定依據。KPI=**省人工分鐘**,非正確率完美。
4. 產線鐵律不動:pipeline/core 零改動;VLM 車道=獨立旁路腳本;
   「LLM 不做像素裁圖」照舊(裁圖仍走 fitz,VLM 只提案 token/配對)。
5. 授權:出貨面只用 Apache 2.0/MIT 權重;內部工具 AGPL(PyMuPDF)無虞照舊。

## 一、承接病灶=考卷(全部已歸檔,證據可重生)

| 病灶 | 考卷內容 | 已知真碼/病例數 | 出處 |
|---|---|---|---|
| S2-1 ②型純字母碼(五死) | PE p21 26 + PS p21 14 + PS p22 13 + Be-Square p16 9 | **62 筆真碼**+p16 噪音 25 筆(精度考題) | s2vis_design.md+demo_diagnosis_ledger 附錄A |
| S2-1 B類/S2-3 長碼/C類純數字 | Iris slide-556 整檔、MOSA Tide、0general 273 筆型 | 檔級 | knownGaps+I_REPORT |
| 拼磚/馬賽克版面 | Topcer VICTORIAN(1021 綁定佇列)、Topcer General p9(15 裸數字磚) | 頁級 | l2_collapse_design+工作包#6 任務B |
| 掃描/影像頁 | demo 14 檔 image 態 14 頁 | 頁級 | demo ledger |
| 場景照/文字裁框(D-1/D-2) | Rice p7、Ariostea p26/119/133 | 4 例 | crop_authenticity C3 |
| S2-4 頁碼污染 | FMG 80/80 混合實例 | 80 | s24_pagefoot_conclusion |
| S2-5 偽碼仲裁 | MILANO70 4/4(已有旗標,VLM 可當第二意見) | 4 | s25_design |

## 二、模型選型(硬約束過濾後)

**主力:Mistral Small 3.1 或 Small 4**(法國,**Apache 2.0**,24B 級多模態)
- 理由:非中國系裡文件理解最強的自架級開源 VLM;授權乾淨;2026 實況=Mistral
  Large 3/Small 4 均已轉 Apache 2.0。
- ⚠待查 M-1:視覺編碼器對 A4 型錄頁**小字**的實際解析力(input resolution 上限/
  tiling 策略)——型錄碼字常 6-8pt,這是成敗關鍵。
- ⚠待查 M-2:Apple Silicon 推理棧現況(Ollama/LM Studio/MLX-VLM 對其 vision 支援、
  量化版 RAM 需求[粗估 Q4≈14-16GB,待實證]、每頁推理秒數)。

**結構前哨:granite-docling-258M**(IBM,**Apache 2.0**,IDEFICS3+SigLIP2+Granite
=全非中國系血統)
- 角色:頁面→DocTags(帶座標的版面/表格結構),餵給主力當結構上下文;258M 筆電即跑。
- ⚠待查 M-3:對「非典型文件」版面(拼磚頁/場景照頁)的輸出品質。

**替代池**(主力不合格時依序試):Gemma 3 27B / Gemma 4 E27B(Google;
⚠待查 M-4:Gemma 4 授權條款細節)、Phi-4-multimodal 5.6B(微軟,MIT)、
Llama 3.2 Vision 11B / Llama 4(Meta,社群授權)。
**fine-tune 備援**:Donut(NAVER 南韓,MIT)或主力 LoRA(⚠待查 M-5:MLX 上
LoRA fine-tune Mistral Small vision 可行性/成本)。

## 三、架構(雙層提案-驗證;防幻覺=確定性程式碼)

```
V0 頁面路由(既有 disposition,零新規則)
   送 VLM:review 態(demo=116 頁)+ noprod 態 + image 態 + 佇列密集頁
   不送:auto 已綁頁(除非抽驗)、nonspec 封面目錄 → 省算力
V1 結構前哨(granite-docling):頁 render → DocTags(版面+表格+座標)
V2 提案(Mistral Small):輸入=頁 render(DPI ⚠待查 T-1:150 或 200)+ DocTags
   + few-shot 考卷例;輸出=嚴格 JSON(見 §四 schema)
V3 確定性驗證層(核心;純程式碼,非模型):
   a. 字串驗證:提案碼必須存在於該頁 PDF 文字層(fitz)→ 命中=拿精確 bbox=prov;
      未命中=幻覺,丟棄+計數(幻覺率=驗收欄)
   b. 已知集合排除:已綁定/已佇列碼跳過(只補漏,不重複)
   c. 交叉對帳:與 census SIZE_RE/band 分流既有訊號比對,衝突標記
V4 產出:.review.json 佇列項,新 reason=vlm_candidate(帶 prov+模型名+權重版本
   +prompt 版本聲明=沿用案5 來源版本聲明制度);前端 viewer 標「AI 建議·未驗證」
```

**不做的事**:V2 不輸出 bbox 當 prov(模型座標不可信;prov 一律來自 V3a 文字層)、
不裁圖、不綁定、不寫入 product JSON 本體。

## 四、V2 輸出 schema(草案)

```json
{
  "page": 16,
  "page_type": "spec_grid | mosaic_layout | scene_photo | scan | other",
  "candidates": [
    {"code": "EKKQ", "color_hint": "Ivory", "size_hint": "30x30",
     "band_hint": "A100", "confidence": "high|mid|low",
     "evidence": "grid cell top-left, swatch above code"}
  ],
  "page_note": "自由文字:此頁結構描述(供人工參考)"
}
```
prompt 草案方向(義/英混排型錄):「你在讀磁磚型錄第 N 頁。列出所有**產品訂購碼**
(不是系列名/色名/材質詞/認證詞/包裝欄位),每碼附其配對色樣的顏色描述與尺寸。
不確定就標 low。只輸出 JSON。」+ few-shot 2-3 頁考卷例(含一頁「無碼頁」負例)。

## 五、驗收設計(通案二;紅燈先行=鐵律7)

| 欄 | 考題 | 及格線(草案,送審定案) |
|---|---|---|
| 召回 | ②型 62 筆真碼 | ≥80%?(待使用者定;人工車道基線=0 自動) |
| 精度 | p16 噪音 25 筆+死亡帳兇手(ANGOLARE/GOLD/UNI 型) | 誤提案率<20%?(佇列可容忍,人工單筆確認秒級) |
| 幻覺率 | V3a 攔截數/總提案 | 報告欄(V3a 結構性歸零出口端) |
| 拼磚頁 | Topcer 考卷 | 定性:能否列出格級碼 |
| 端到端 KPI | 抽 N 頁人工計時:有 VLM 預填 vs 從零找 | 省人工分鐘>0 顯著 |

停止線:召回<50% 或 端到端不省時 → 車道降級回純人工,權重歸檔,不調參救(通案五精神)。

## 六、部署與吞吐(粗估,全部待實證)

- 硬體:使用者 Mac(Apple Silicon;⚠待查 D-1:實機 RAM——決定 24B Q4 可否本地)。
- 推理棧:首選 Ollama(最省事)或 MLX-VLM(Apple 原生,通常較快);vLLM 需 Linux/GPU。
- 量:demo 14 檔篩選後約 130-200 頁;全池 84 檔粗估 700-1200 頁(⚠待量:跑 V0 路由
  統計即得,只讀)。若每頁 30-90 秒(⚠待測),全池=6-30 小時,可過夜批跑,可接受。
- 若本地不夠力:降級鏈=Small 4 → Gemma 3 12B → Phi-4-multimodal;或租 GPU(見 §〇-2 待裁線)。

## 七、分期(每期收工=commit+報告;皆可中止)

- **P0 選型手測(半天)**:主力+前哨各跑考卷 5 頁(p16/PE p21/Topcer/Iris/場景照),
  肉眼判「能不能讀」。不及格→替代池輪替。
- **P1 探針(1-2 天)**:`dev/vlm_probe.py`(只讀、產報告不產佇列)跑全考卷
  → §五驗收表實數=通案二分離量測。**此期結束=送審點,數字定案前不接佇列。**
- **P2 佇列接線(送審通過後)**:V4 落地(reason=vlm_candidate)+viewer 呈現
  「AI 建議·未驗證」+來源版本聲明。
- **P3 全池批跑+KPI 計時實驗**。

## 八、風險誠實表

| 風險 | 緩解 |
|---|---|
| 小字讀不到(解析度)| P0 手測即知;DPI 調升+tiling;不行換模 |
| 幻覺碼 | V3a 字串驗證=結構性歸零(出口端);率高只影響召回不污染佇列 |
| 多語(義/德/西)| 考卷含多語頁;⚠待查 R-1:各模型多語文件表現 |
| 誤導性預填(人工盲信)| 前端強制「AI 建議·未驗證」+confidence 顯示;KPI 實驗含錯誤預填成本 |
| 模型血統誤判 | 選模 checklist:查 model card 的 base model 鏈到底 |
| 過擬合回流 | VLM 車道產出**永不**回饋調整幾何規則/凍結常數(鐵律 5/6 延伸) |

## 九、待查清單(可直接交外部 AI 調研;回填後升送審版)

1. **M-1**:Mistral Small 3.1/4 vision encoder 的 max input resolution 與 tiling 策略;
   對 A4@150-200DPI 型錄頁 6-8pt 小字的 OCR 級讀取實測/評測。
2. **M-2**:2026-07 當下 Ollama/LM Studio/MLX-VLM 對 Mistral Small vision 的支援狀態、
   Apple Silicon 各 RAM 檔位(16/32/64GB)可跑的量化檔與 tokens/s、單頁圖推理延遲。
3. **M-3**:granite-docling-258M 在非典型版面(拼貼/大圖/掃描)的 DocTags 品質;
   是否有已知失效模式。
4. **M-4**:Gemma 4(2026-04)授權全文——商用限制、使用政策、衍生條款。
5. **M-5**:MLX 或 PEFT 對 Mistral Small vision 的 LoRA fine-tune 支援、所需硬體、
   文件 KIE fine-tune 的公開案例。
6. **R-1**:上述各模型在義大利語/德語/西語文件上的公開評測。
7. **B-1**:非中國系開源 VLM 的文件 KIE 公開基準對照表(DocVQA/ChartQA/
   自建 SKU 抽取類),排名+差距量級。
8. **B-2**:「VLM 提案+文字層驗證」此類雙層防幻覺架構的公開先例/論文
   (grounding-by-string-matching),有無已知坑。

---
零規則改動、零常數變更;本檔=純設計文檔。核可與待查回填前不動任何 code。
