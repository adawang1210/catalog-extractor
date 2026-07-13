# PROJECT_MAP(2026-07-09 整理;換窗接手先讀 PROMPT.md,再用本檔找東西)

歸類整理紀錄:只搬檔不改邏輯;唯一程式碼改動=core/heldout5_build.py 的 ROOT 路徑常數
(`parent`→`parent.parent`,使用者單獨批准);搬後四項回歸全綠(selftest、v3/v4 dev
重掃 vs 凍結基準逐位一致、heldout5_build list 實跑)。

## 執行方式(重要)

**⚠ python 直譯器:PyMuPDF(fitz)裝在 homebrew python——若 PATH 把 /usr/bin 排前
會 `No module named 'fitz'`,保險寫法一律 `/opt/homebrew/bin/python3 core/<工具>.py`。**
**⚠ 例外:Drive 工具(drive_sync/heldout5_build)要用 `/usr/bin/python3`——
googleapiclient 裝在系統 python 3.9,homebrew python 3.14 沒有(2026-07-09 實測)。**
**一律從專案根目錄執行:`python3 core/<工具>.py ...`,CWD 必須=專案根**——
多支程式以相對路徑讀 `catalogs/`、寫 `output/`(m2_scan.build_vocabs 硬編
`Path("catalogs")`),換工作目錄會壞。磁碟是 FAT32,不支援 symlink,
core/ 內 11 檔互相 import、必須同層,不可再拆資料夾。

## core/ —— 現役程式(11 檔+token.json)

| 檔案 | 用途 |
|---|---|
| **m3_scan.py** | **主入口**:v2/v3/v4 綁定掃描+佇列統計(`python3 core/m3_scan.py <corpus> v4 out.csv`;`--selftest` 跑合成資料自檢)。v4=定案版(M4-1/2/3+M5-1 佇列記帳) |
| spike_geom.py | 綁定引擎核心:extract_swatches / assign_words(v1-v4 版本閘控在此) |
| census.py | SIZE_RE、corpus 普查(M0) |
| m1_scan.py | norm / CODE_RE 函式庫(舊 M1 main 留存,現當 library 用) |
| m2_scan.py | build_vocabs / code_candidates(候選偵測;詞彙表硬編讀 catalogs/=dev) |
| m4_dump.py | GT dump:抽樣頁 v3/v4 overlay PNG+JSON(含 name_bind 目標)→ output/m4_gt/ |
| m5_signal.py | held-out 硬條件自動訊號(色名鍵頁/小圖形頁;建批選件用,不看頁) |
| caption_signal.py | held-out 建批 2b(圖說在上)訊號 |
| s2gap.py | S2-1 偵測缺口量測(A 類長 SKU/B 類全字母上界) |
| drive_sync.py | Google Drive 同步(token.json 同層,`__file__` 相對) |
| heldout5_build.py | 建批+池盤點(list/fetch)。⚠ heldout6 時 USED_DIRS 須加 "catalogs5" |
| token.json | Drive OAuth token(跟 drive_sync 走) |

## archive/ —— 一次性死檔(可讀不可跑;對象語料已燒毀)

m2_diff.py / m2_dump.py / m2_gt_verdict.py(M2,catalogs2)、
m3_dump.py / m3_gt_verdict.py(M3,catalogs3)。gt_verdict 兩檔=當輪人工 GT
判定的固化紀錄(審計證據),只讀不跑;無任何現役檔 import 它們。

## output/ —— ★凍結區,整個資料夾碰不得★

所有 bit-identical 回歸的對照證據都在這裡,不可刪、不可移:
- **凍結基準 CSV**:m3_dev_v3.csv(v3 dev)、m4_dev_v4_m43.csv(M4 三票後 v4 dev)、
  **m5_dev_v4_m51.csv(M5-1 後 v4 dev=現行基準)**;m1_*/m2_* 歷史紀錄。
- **宣告**:heldout2/3/4/5_DECLARATION.md(建批程序+硬條件+偏置聲明)。
- **報告**:M1/M2/M3/M4_REPORT.md;spike/REPORT.md。
- **GT 證據**:m2_gt/、m3_gt/、m4_gt/(overlay PNG、JSON、GT_VERDICTS.csv=人工
  逐筆判定,凍結不可改)。
- census*.csv:各批普查。

## 語料資料夾(全部留根、不可改名)

| 資料夾 | 狀態 |
|---|---|
| catalogs/ | **dev**(開發自測;m2_scan 詞彙表來源) |
| catalogs2/3/4 | **已燒 held-out**:永不再用於調規則/驗收;保留=回歸夾具(如 catalogs3 Emil p13 orphan 夾具)與證據 |
| catalogs5/ | **凍結 held-out,未考,碰不得**(打包批:S2-2+M5-1+M5-2;組成見 heldout5_DECLARATION.md) |

## 產線(2026-07-09 起)

- **pipeline.py(專案根)**:產線 A 骨架——`python3 pipeline.py <pdf>|--smoke [outdir]`,
  PDF→SCHEMA JSON 骨架+.review.json 佇列檔;只 import core/、版本釘 v6,
  extract_page 鏡射 m3_scan.scan_page 逐碼判定,--smoke=守恆對帳(逐頁 vs
  output/m52_dev_v6.csv)+prov 完整性。產出 product/<brand>/(可重生,非凍結區)。
- **viewer.py(專案根)**:辨識結果檢視網頁產生器(純輸出,不 import core、不碰綁定)——
  讀 product/ JSON+裁圖、渲染被引用頁,產 viewer/(可重生)。
  `/opt/homebrew/bin/python3 viewer.py [stem關鍵字]`;
  瀏覽 `/opt/homebrew/bin/python3 -m http.server 8642` → http://localhost:8642/viewer/。
  左=型錄頁+匡選框(綁定色樣/碼token/佇列/名鍵假說/骨架),右=卡片(點卡跳頁、點框選卡)。

## 其他

- implement.md(規格書,含 PROGRESS_PLAIN / SOP_新增辨識 / ROADMAP_TO_PRODUCT /
  LLM key 常見困惑 四節)、SCHEMA.md(目標資料契約)、MVP_CONTRACT.md(MVP 交付邊界,
  已核可)、BACKLOG.md(工作票)、PROMPT.md(每 session 起點)。
- skills/ 與 .claude/skills/:ponytail skill 疑似重複安裝(.claude/ 是生效路徑);
  不刪只記。
- __pycache__/:Python 生成物、非資產,會在 core/ 下自動重生,可隨手刪。

## GT 流程用哪些工具(SOP 速查)

建批:core/heldout5_build.py(md5 判重+池盤點)→ 硬條件訊號 core/m5_signal.py /
core/caption_signal.py → 宣告寫 output/heldoutN_DECLARATION.md。
驗收:core/m3_scan.py 對批各版本掃一次 → core/m4_dump.py 抽樣頁 dump overlay →
人工目檢逐筆 GT(判定固化成 verdict 腳本,歸檔)→ 報告 output/MN_REPORT.md →
**燒毀該批**(永不再用於調規則)。
