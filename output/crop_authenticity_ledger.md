# 案4|裁圖真實性掃描器 總帳(dev/crop_authenticity_scan.py)

純儀器、只讀、不修只曝光(通案三入庫)。補「場景照非唯一影像」盲區。掃產線裁圖
(product/<brand>/<stem>_crops/*.png)四類真實性風險。技術=PIL+numpy 自算 dhash
(零新依賴)。**不改任何產線行為、不裁決白名單。**

跑法:`/opt/homebrew/bin/python3 dev/crop_authenticity_scan.py "product=." [--max N] [--sheet OUT.html]`
      `… --selftest`

## 紅燈先行(鐵律7)
合成裁圖 selftest:AC-1 一圖多用(逐位相同 PNG)/AC-2 低解析+近均勻/AC-3 裁到碼文字
+AC-3b 框外對照/AC-4 同色樣多產品/AC-5 乾淨零旗。selftest 7/7 全綠。

## 四偵測器
- **C1 一圖多用**:dhash(8x8 列差分)完全相同(ham=0)且跨 ≥2 不同 Variant。
- **C2 退化裁圖**:低解析(min 邊 <16px)/近全白空裁(灰階 std <1.0)/透明層 alpha。
- **C3 裁到碼文字**:swatchCrop 裁框 bbox 涵蓋同頁碼 token bbox ≥60%=裁到文字冒充色樣。
- **C4 同色樣多產品**:≥2 不同碼 Variant 共用同頁近同 swatch bbox(IoU ≥0.85)。

## 全池頻率表(product/,現行 V=12)
| 類 | 筆 | 說明 |
|---|---|---|
| C1_crop_reuse | 0 | 無逐位相同裁圖=無真一圖多用 |
| C2_degenerate | 1 | Level CG p84 std=0.4=近全白空裁 |
| C3_crop_text | 8 | 裁框涵蓋碼 token=場景照/caption 裁入(A02G×6, Ariostea×1, Provenza×1) |
| C4_shared_swatch | 0 | 無共用 swatch bbox 多產品 |

## 驗證錨(E-1 場景照)命中 + 視覺確認
C3 命中 **Marazzi A02G 場景頁 9/12/18/19/22/27**——變體名為整段 caption
(如「CROGIOLO Grande Look Pietra Sicilia Bianco Riga Ink Lume…」)。★視覺核實 p9 裁圖=
整張浴室場景 render(青色磁磚)含 "CROGIOLO"+"MQ9D Grande Stone Look…120x278cm" 文字=
**場景照冒充色樣、裁到碼+caption 文字**,非乾淨色片。=E-1(v9)場景照降級所要處理的病灶,
V=12 現行產線仍出貨(E-1 未切=已知紅字)。Ariostea twin_s p30、Provenza p26 同型。

## 停止線判定:**未觸發**(非災難級)
規格停止線=大量一圖多用 或 裁到文字冒充色樣 災難級。實測 C1=0、C3=8(集中於已知
場景照檔 A02G,非全池瀰漫),非 L2 塌縮量級 → 不凍結。findings 交 VLM/人工 lane
(通案五;E-1 場景照 lane 已知)。

## 已知邊界(誠實紅字,鐵律2 校準)
- **C1 HAM 校準**:初版 HAM=6(近似)對小色樣條(如 Viva Steel/Dark 107x35)誤判
  不同深色為近似(實測 ham=5)→收緊 ham=0(僅逐位相同)。8x8 dhash 對低細節色樣條
  解析力不足=near-dup 不可靠、不採;真「一圖多用」須逐位相同才旗。
- **C2 UNIFORM 校準**:初版 std<4.0 誤殺合法純色磁磚(std 2-5 屬正常紋理)→收緊
  std<1.0(僅近全白空裁)。純色磁磚不誤旗。
- **C3 呈現**:裁框涵蓋 token=幾何事實(裁圖區含碼位置);是否「冒充色樣」須人工
  複核裁圖(contact-sheet 供圖)。A02G 型 100% 涵蓋+caption 變體名=高信度場景照。
- C4/C1 本池零筆=無反證,非「保證無問題」(dhash 解析限制下的地板)。

contact-sheet(--sheet):輕量 HTML 引裁圖供人工複核(不入 git=引 gitignore 裁圖,可重生)。
儀器不裁決;findings=人工/VLM 材料。pipeline/core/凍結常數零改動,V 仍 12。
