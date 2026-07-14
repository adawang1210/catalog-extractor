# VLM 金絲雀車道 自架設計案(完整版;2026-07-14 草案送審中)

**狀態=草案,未核可,現有 repo 零實作**。本文目標=**可據以另開新 repo 實作**的完整設計:
含定位、架構、與現有專案的資料契約、資料物件模型、模組結構、驗證演算法、prompt、選型、
驗收、分期、待查清單。標「⚠待查」者交外部調研回填。

---

## 〇、硬約束(不可辯論的前提)

1. **禁用任何中國來源模型,含衍生品**(Qwen 全系/InternVL/MiniCPM/DeepSeek-VL 出局;
   olmOCR 底模 Qwen2-VL=出局)。**選模必查底模血統**——美國/歐洲機構出品 ≠ 非中國底模,
   須追到 model card 的 base model 鏈到底。
2. **只自架,不用任何第三方推理 API**(型錄=有版權廠商 PDF,不外送)。
   邊界待裁:租用 GPU 裸機(RunPod/Lambda)=自部署但資料上租用機器;「嚴格不出門」
   只有本地機器——**此線需使用者裁決**(§十一)。
3. **感測器非綁定器**:VLM 輸出**只進 needs_review 佇列**,永不直接入庫、永不成綁定依據。
   KPI=**省人工分鐘**,非追求完美正確率。
4. **確定性打底不可拋**:VLM 一律站在「文字層字串驗證」肩膀上——**座標(prov)永遠來自
   PDF 文字層,不用模型座標**。理由見 §一「為什麼不是純 VLM」。
5. 授權:出貨面只用 Apache 2.0 / MIT 權重;內部工具 AGPL(PyMuPDF)無虞照舊。
6. **零回流過擬合**:VLM 車道產出**永不**回饋調整現有幾何規則/凍結常數(鐵律 5/6 延伸)。

---

## 一、定位:加強現有架構,不是取代(A/B/C 三選項)

現有 `catalog-extractor` 引擎(規則式、V=12 凍結)做得好的是「乾淨規格頁+有數字錨的碼」
(量測正確率上界 ≈0.8–2.4%),做不到的是已歸檔的洞(純字母碼/拼磚/掃描頁/場景照)。

| 路線 | 誰主導 | 確定性驗證層 | 評價 |
|---|---|---|---|
| A. 規則主導 + VLM 補洞 | 規則引擎 | 有 | **本案採此為起點**;風險最低、考卷現成 |
| B. 純 VLM 端到端 | VLM 全包 | 無 | **否決**:見下「錯誤方向翻轉」 |
| C. VLM 主導 + 確定性打底 | VLM | 有 | 未來選項;待 P1 量出 VLM 可靠度後再議 |

**為什麼否決純 VLM(B)——四個硬傷**:
1. **錯誤方向從「漏」翻成「編」**:現有引擎錯在漏(靜默漏抓=少一筆,安全);VLM 錯在
   **幻覺**(自信生出不存在的碼/尺寸,危險)。對產品資料庫,假產品比漏產品嚴重得多。
2. **溯源崩解**:prov 硬需求=每欄指回精確座標;VLM 座標會飄。
3. **不可重現/不可凍結/不可回歸**:整套治理(紅燈先行、守恆對帳、版本凍結)建在確定性上;
   模型行為無法逐位凍結。
4. **逃不掉驗證層**:要信 VLM 的碼,終究得回文字層比對——故文字層/色樣幾何(現有引擎
   做得好的部分)丟不掉。

**結論**:VLM 一定要進來,但**站在確定性驗證的肩膀上**。先走 A(補洞、低風險),P1 量出
「召回/幻覺率/驗證層攔截率」三個數字後,再決定是否把更多主路讓給 VLM(C)。

---

## 二、系統架構(雙層:VLM 提名 → 確定性驗證)

```
                      ┌─────────────── 現有 catalog-extractor(不動)───────────────┐
   PDF ──────────────▶│  core/ 掃描綁定 → product.json（綁定成功）                    │
     │                │                 → review.json（待複查佇列）                    │
     │                │                 → disposition（每頁五態:auto/review/noprod/   │
     │                │                   nonspec/image）＋文字層＋色樣幾何             │
     │                └───────────────────────────┬───────────────────────────────────┘
     │                                            │ 讀(唯讀契約,§三)
     ▼                                            ▼
  ┌────────────────────── 新 repo:catalog-vlm-lane ──────────────────────┐
  │ V0 route   選頁:disposition ∈ {review,noprod,image} ∧ ¬已綁定頁       │
  │ V1 render  頁 → PNG（fitz, DPI 可設）                                   │
  │ V2 propose VLM 讀 PNG(+結構前哨 DocTags)→ VlmProposal（碼+色+尺寸提名）│
  │ V3 verify  ★確定性層(純程式碼):                                        │
  │            a 字串比對 PDF 文字層 → 命中=拿精確 bbox=prov;未命中=幻覺丟棄 │
  │            b 去重:已綁定/已佇列碼跳過                                   │
  │            c 交叉對帳:size/band 與 census 既有訊號比對,衝突標記        │
  │            d 色樣配對:碼 bbox → 最近色樣圖(重用 extract_swatches/OSR-1)│
  │ V4 emit    VerifiedCandidate → QueueItem（既有 schema）→ vlm_review.json │
  └───────────────────────────────┬───────────────────────────────────────┘
                                   │ 併入(同 schema,reason=vlm_candidate)
                                   ▼
              現有 viewer.py 前端（加一個框類「AI 建議·未驗證」）→ 人工確認 → 入庫
```

**與 OSR-1 的接力**:OSR-1(純幾何)說「這裡有磁磚,碼未知」;VLM 說「它的碼是 EKKQ」。
V3d 色樣配對正是把兩者接起來——VLM 補的碼,綁到 OSR-1 已顯示的孤兒色樣上(都只進佇列)。

---

## 三、與現有專案的資料契約(新 repo 唯讀,不改對方)

新 repo **不 import 也不修改** catalog-extractor 的 core/pipeline;只透過**檔案**耦合:

**輸入(新 repo 讀)**:
- `catalogsN/<brand>/<file>.pdf` — 原始型錄(文字層+頁圖來源)。
- `product/<brand>/<stem>.json` — 既有綁定(取「已綁定碼集」做去重)。
- `product/<brand>/<stem>.review.json` — 既有佇列(取「已佇列碼集」做去重)。
- **disposition**:每頁五態。現況存在於 viewer 產出的 DATA.pageState;契約化=請 catalog-extractor
  加一個只讀匯出 `disposition.json`(⚠待辦 C-1,小改、非規則),或新 repo 自行以既有閘重算
  (`len(SIZE_RE.findall(text))>=3` 等,鏡射不改)。

**輸出(新 repo 寫,不覆蓋對方檔)**:
- `vlm_review.json`(每 stem 一份,獨立檔;不寫進 product.json 本體)。
- 前端整合:viewer.py 讀 vlm_review.json 疊一個框類(小改前端,非規則)。

**契約凍結**:queue item 的 schema(§四)是兩 repo 的唯一介面,版本化(schema_version)。

---

## 四、資料物件模型(物體描述)

### 4.1 `PageTask`(V0 產,路由單位)
```json
{
  "pdf": "catalogs4/Emil/Be-Square....pdf",
  "stem": "Be-Square Catalogo 2025.01 Web",
  "brand": "Emil",
  "page": 16,
  "disposition": "review",            // review|noprod|image（只送這三態）
  "page_image": "cache/<stem>/p16.png",
  "known_codes": ["EDPT","EDPV","ED8K","..."],   // 既有已綁定∪已佇列（去重用）
  "text_tokens": [ {"text":"EKKQ","bbox":[42.5,540.1,70.3,551.0]}, ... ],  // fitz words
  "swatches":    [ {"bbox":[40,510,140,610]}, ... ]                        // extract_swatches
}
```

### 4.2 `VlmProposal`(V2 產,模型原始輸出,**未驗證**)
```json
{
  "page": 16,
  "page_type": "spec_grid",           // spec_grid|mosaic_layout|scene_photo|scan|other
  "candidates": [
    { "code": "EKKQ", "color_hint": "Ivory", "size_hint": "30x30",
      "band_hint": "A100", "confidence": "high",     // high|mid|low
      "evidence": "top-left grid cell, swatch above code" }
  ],
  "page_note": "6.5mm DECORI 頁,左欄 MOSAICO/LISTELLI 各三色",
  "_raw": "…模型原文(留存供除錯)…"
}
```

### 4.3 `VerifiedCandidate`(V3 產,**已過確定性驗證**)
```json
{
  "code": "EKKQ",
  "verify_status": "matched",         // matched|hallucinated|duplicate|conflict
  "bbox": [42.5,540.1,70.3,551.0],    // ★來自文字層,非模型
  "prov": {"pdf":"…","page":16,"bbox":[…],"method":"vlm_propose+textmatch"},
  "color_hint": "Ivory", "size_hint": "30x30", "band_hint": "A100",
  "confidence": "high",
  "size_consistent": true,            // c 交叉對帳:size_hint 是否與同列 SIZE_RE 一致
  "swatch_bbox": [40,510,140,610]     // d 配對到的色樣圖(重用 OSR-1 孤兒色樣)
}
```

### 4.4 `QueueItem`(V4 產,**寫入 vlm_review.json;沿用既有 review 佇列 schema**)
```json
{
  "schema_version": "vlm-1",
  "code": "EKKQ",
  "reason": "vlm_candidate",
  "prov": {"pdf":"…","page":16,"bbox":[…],"method":"vlm_propose+textmatch"},
  "vlm_meta": {"color_hint":"Ivory","size_hint":"30x30","band_hint":"A100",
               "confidence":"high","swatch_bbox":[…]},
  "source": {"model":"mistral-small-3.1","weights_sha":"…","prompt_version":"sg-v1",
             "run_id":"2026-07-15T…","doc_render_dpi":200}   // 沿用案5 來源版本聲明制度
}
```

### 4.5 `RunManifest`(每次批跑一份,可稽核/可復現)
```json
{ "run_id":"…","model":"…","weights_sha":"…","prompt_versions":{…},
  "corpora":["catalogs4",…],"pages_sent":183,"proposals":412,
  "verified":{"matched":..,"hallucinated":..,"duplicate":..,"conflict":..},
  "config_sha":"…","started":"…","finished":"…" }
```

---

## 五、模組結構(新 repo:catalog-vlm-lane)

```
catalog-vlm-lane/
  vlm_lane/
    route.py        # PageTask 生成:讀 PDF+既有 disposition/product/review → 選頁
    render.py       # 頁 → PNG（fitz, DPI 可設；快取）
    propose.py      # 呼叫 ModelBackend → VlmProposal（含 JSON 解析+重試）
    verify.py       # ★V3 確定性驗證(演算法見 §六);純程式,無模型
    emit.py         # VerifiedCandidate → QueueItem → vlm_review.json
    swatch_link.py  # V3d 碼 bbox → 最近色樣（重用 extract_swatches / OSR-1 訊號）
    models/
      base.py       # ModelBackend 介面：propose(image, doctags, fewshot) -> str
      mistral.py    # Mistral Small：Ollama / MLX-VLM / vLLM 後端可切
      granite.py    # granite-docling 結構前哨（DocTags）
    prompts/
      spec_grid.txt  mosaic.txt  scan.txt
      fewshot/       # 考卷頁的 in-context 例（含負例:無碼頁）
    config.py       # 模型名/DPI/門檻/後端/路徑（單一設定源）
  bin/
    vlm_probe.py    # P1:只讀量測,產報告不產佇列（通案三:數字可復現）
    vlm_run.py      # P2/P3:產 vlm_review.json
  tests/
    test_verify.py  # 紅燈先行:合成幻覺碼→斷言被 V3a 擋（實作前 RED）
    test_route.py   # 選頁/去重正確性
    exam/           # 考卷:②型 62 真碼 + p16 噪音 25 + 死亡帳兇手（GT 標註）
  contracts/
    queue_item.schema.json     # §四 QueueItem 的 JSON Schema（兩 repo 介面凍結）
    input_contract.md          # §三 契約文字
  README.md
```

依賴:PyMuPDF(fitz)、Pillow、模型後端(ollama-python / mlx-vlm / vllm 擇一)、jsonschema。
**不依賴** catalog-extractor 的 core/(只讀它的產出檔),避免耦合其凍結邏輯。

---

## 六、V3 確定性驗證演算法(核心;防幻覺)

輸入:`VlmProposal.candidates`、`PageTask.text_tokens`(文字層 words)、`known_codes`、
同頁 `SIZE_RE` 尺寸 token、`swatches`。逐 candidate:

```
1. code_norm = upper(strip(candidate.code))
2. 形檢:¬CODE_RE(code_norm) → 丟棄(reason=malformed)         # 沿用既有 CODE_RE,不放寬
3. 字串定位(★):在 text_tokens 找「完全相等」的 token
     命中1個  → bbox=該 token.bbox;verify_status=matched
     命中多個 → 取與 candidate 提示最一致者(色/尺寸同列),其餘記 ambiguous
     命中0個  → verify_status=hallucinated,丟棄+計數（幻覺率分子）
4. 去重:code_norm ∈ known_codes → verify_status=duplicate,丟棄（只補漏）
5. 交叉對帳(c):
     size_hint 存在 → 檢同列(±行高)是否有 SIZE_RE 且正規化相符 → size_consistent
     band_hint 存在 → 檢是否 BAND_RE ∧ 同檔家族 → 一致性旗（不硬否決,只標）
6. 色樣配對(d):碼 bbox 上方/同格最近 swatch（重用 OSR-1 孤兒色樣集）→ swatch_bbox
7. 產 VerifiedCandidate → V4 emit（reason=vlm_candidate,只進佇列）
```

**設計要點**:
- 步 3 是**嚴格完全相等**,不做模糊/子字串——寧可漏不可錯(幻覺歸零優先於召回)。
- **prov 一律來自步 3 的文字層 bbox**,模型座標從不採用。
- 幻覺(命中 0)不是失敗,是**被結構性擋在佇列外**——只影響召回,不污染。
- 全程無模型,**可逐位重現、可回歸測試**(補回確定性)。

**紅燈先行(tests/test_verify.py,實作前必 RED)**:
- 注入一個 PDF 沒有的碼「ZZZZ」→ 斷言 verify_status=hallucinated、不入 QueueItem。
- 注入已綁定碼 → 斷言 duplicate、不重複。
- 注入真碼 EKKQ(文字層有)→ 斷言 matched、bbox=文字層座標、入 QueueItem。

---

## 七、模型選型(硬約束過濾後)

**主力:Mistral Small 3.1 / 4**(法國,**Apache 2.0**,24B 級多模態)——非中國系裡文件
理解最強的自架級開源 VLM。⚠M-1 小字解析力、⚠M-2 Apple Silicon 推理棧待實測。

**結構前哨:granite-docling-258M**(IBM,**Apache 2.0**,IDEFICS3+SigLIP2+Granite=全非中國
血統)——頁→DocTags(帶座標版面/表格),餵主力當結構上下文;258M 筆電即跑。⚠M-3。

**替代池**(主力不合格依序試):Gemma 3 27B / Gemma 4(Google,⚠M-4 授權)、
Phi-4-multimodal 5.6B(微軟,MIT)、Llama Vision(Meta,社群授權)。
**fine-tune 備援**:Donut(NAVER 南韓,MIT)或主力 LoRA(⚠M-5)。

**後端**:Ollama(最省事)或 MLX-VLM(Apple 原生較快);vLLM 需 Linux/GPU。config 可切。

---

## 八、Prompt 設計(spec_grid 型;義/英混排型錄)

```
系統:你是磁磚型錄結構化抽取器。只輸出 JSON,不解釋。
使用者:這是磁磚型錄第 {page} 頁的圖。頁面結構提示(DocTags):{doctags}
任務:列出頁上所有【產品訂購碼】。產品訂購碼=識別單一產品的短代號(常 3–6 字元、
大寫字母與數字混合或全字母)。
【不要】列入:系列名、色名(Ivory/Concrete…)、材質/表面詞(Naturale/MOSAICO/
LISTELLI…)、認證詞(UNI/DIN/R10…)、包裝欄(BOX/PCS/ANGOLARE…)、尺寸(30x30)。
每個碼附:配對色樣的顏色描述、同列尺寸、價格帶(若有)、信心(high/mid/low)。
不確定的碼標 low 也要列出(下游會人工驗)。
輸出格式:{VlmProposal schema}
{fewshot:2–3 個考卷頁的正例 + 1 個「無碼頁」負例}
```

**要點**:①負例(無碼頁→空 candidates)防過度提名;②明確列「不要當碼」的類別=直接
對應死亡帳兇手(GOLD/UNI/ANGOLARE/MOSAICO);③mosaic/scan 頁用不同 prompt(§五 page_type)。

---

## 九、驗收(通案二分離量測;紅燈先行=鐵律7)

| 欄 | 考題 | 及格線(送審定案) |
|---|---|---|
| 召回 | ②型 62 真碼(PE21 26+PS21 14+PS22 13+p16 9) | ≥80%?(人工車道基線=0 自動) |
| 精度 | p16 噪音 25 + 死亡帳兇手(GOLD/UNI/ANGOLARE/MOSAICO) | 誤提案率<20%?(佇列可容忍) |
| 幻覺率 | V3a 命中 0 數 / 總提案 | 報告(出口端結構性歸零) |
| size 一致率 | size_hint vs 同列 SIZE_RE | 報告 |
| 拼磚/掃描 | Topcer / Iris 考卷 | 定性:能否列出格級碼/讀出掃描頁 |
| 端到端 KPI | 抽 N 頁人工計時:有 VLM 預填 vs 從零找 | 省人工分鐘 > 0 顯著 |

**停止線**:召回<50% ∨ 端到端不省時 → 車道降級回純人工,權重歸檔,不調參救(通案五)。

---

## 十、分期(每期收工=commit+報告;皆可中止)

- **P0 選型手測(半天)**:主力+前哨各跑考卷 5 頁(p16/PE21/Topcer/Iris/場景照),肉眼判
  「小字讀不讀得到」。不及格→替代池輪替。**產物**:選型結論+M-1/M-2 實測回填。
- **P1 探針(1–2 天)**:`bin/vlm_probe.py` 只讀跑全考卷 → §九 驗收表實數(通案二分離量測)。
  **此期=送審點,數字定案前不接佇列。** 紅燈 test_verify 先綠。
- **P2 佇列接線(送審通過後)**:V4 落地 vlm_review.json + 前端框類「AI 建議·未驗證」+
  來源版本聲明。smoke:佇列只增不減、product.json 本體零改。
- **P3 全池批跑 + KPI 計時實驗**:過夜批跑;產 RunManifest;人工計時得「省人工分鐘」。

---

## 十一、待查清單(交外部 AI 調研;回填後升送審版)

1. **M-1** Mistral Small 3.1/4 vision encoder 的 max input resolution / tiling;對 A4@150–200DPI
   型錄頁 6–8pt 小字的 OCR 級讀取實測。
2. **M-2** 2026-07 Ollama/LM Studio/MLX-VLM 對 Mistral Small vision 支援;Apple Silicon
   16/32/64GB 可跑量化檔、tokens/s、單頁延遲。
3. **M-3** granite-docling-258M 在拼貼/大圖/掃描頁的 DocTags 品質與失效模式。
4. **M-4** Gemma 4(2026-04)授權全文:商用限制/使用政策/衍生條款。
5. **M-5** MLX/PEFT 對 Mistral Small vision 的 LoRA fine-tune 支援、硬體、KIE 案例。
6. **R-1** 各候選在義/德/西語文件的公開評測。
7. **B-1** 非中國系開源 VLM 文件 KIE 公開基準對照表(DocVQA/ChartQA/SKU 抽取),排名+差距。
8. **B-2** 「VLM 提名+文字層驗證(grounding-by-string-matching)」架構的公開先例/坑。
9. **裁決線**:租 GPU 裸機是否算「不出門」(§〇-2)——只有使用者能定。
10. **C-1**(對現有 repo 的小改)catalog-extractor 是否加只讀 `disposition.json` 匯出,
    或新 repo 自行鏡射閘重算(不改對方規則)。

---

## 十二、另開新 repo 的 bootstrap 清單(給實作者/AI)

1. `git init catalog-vlm-lane`;放 §五 目錄骨架;README 首段複製 §〇 硬約束(選模血統紅線)。
2. 先寫 `contracts/queue_item.schema.json`(§四)+ `tests/test_verify.py`(紅燈先行,先 RED)。
3. 從 catalog-extractor 匯出考卷到 `tests/exam/`:②型 62 真碼 + p16 噪音 25(逐 token 帳見
   catalog-extractor `output/demo_diagnosis_ledger.md` 附錄A + `dev/s2vis_probe.py`)。
4. `render.py`+`route.py` 先跑通(只讀 PDF,不碰模型)→ 確認能生 PageTask。
5. `models/mistral.py` 接 Ollama/MLX → P0 手測 5 頁。
6. `verify.py` 讓紅燈轉綠 → `bin/vlm_probe.py` 跑考卷 → P1 送審數字。
7. **紀律移植**:紅燈先行、通案二分離量測、來源版本聲明、停止線、選模血統核對——全部沿用
   catalog-extractor 的 MVP_CONTRACT 精神(新 repo README 明列)。

---
零規則改動、零常數變更;本檔=純設計文檔,現有 repo 不動任何 code。新 repo 待使用者開立。
