# 案5|管線狀態守恆 + 來源版本聲明 總帳(dev/pipeline_conservation_scan.py)

純追蹤/儀器、只讀、不改產線(通案三入庫)。讀 product 形制目錄(JSON+review),兩節。

跑法:`/opt/homebrew/bin/python3 dev/pipeline_conservation_scan.py product [--md5] [--max N]`
      `… --selftest`

## 紅燈先行(鐵律7)
合成 selftest:AC-P1 候選消失+P1b 對照/AC-P2 幽靈候選/AC-P3 滯塞/AC-B1 跨版本 size
衝突/AC-B1b 版次年解析。selftest 6/6 全綠。

## 【A 管線狀態守恆】每候選(specByCode 碼)生命週期 discovered→published/review
- **P1 候選無帳消失**:D−P−R≠∅(specByCode 碼既非 published Variant 亦不在 review)。
- **P2 幽靈候選**:R−D≠∅(review 碼不在 specByCode=來源不明)。
- **P3 佇列滯塞**:review_ratio=|R|/|D|≥0.9 且**非骨架檔**(骨架=設計上全 review 不算)。

全池(product/,13 檔)census 實測:
| 指標 | 值 |
|---|---|
| ★候選無帳消失合計(P1) | **0** |
| ★幽靈候選合計(P2) | **0** |
| P3 佇列滯塞(非骨架) | 3(Ariostea twin_s 100%、Marazzi A02G 93%、Topcer 100%) |

★**守恆硬不變量 D=P∪R(spec_only=0 ∧ phantom=0)於每一檔成立**=引擎「候選零消失」
正面驗證。P3=候選卡佇列健康信號(twin_s/A02G/Topcer=已知場景照/mosaic 難檔,多數候選
落 review=needs_review 長期未處理代理);骨架檔(Iris/MOSA/Sodai=seriesSkeleton)全 review
屬設計、不旗(鐵律2 精修)。

## 【B 來源版本聲明】不建實體解析,只存不可變聲明
每檔 brand/pdf/版次年(檔名解析 20\\d\\d.\\d\\d)/碼數/md5(--md5)。全 13 檔聲明產出
(md5 全算、版次年 6/13 可解析=有年份檔名者)。
- **B1 跨版本衝突候選**:同 brand 同碼於 ≥2 不同 pdf → size 相異=conflict。
  全池(product/)= **0**(每 brand 單一型錄、無同碼跨檔=誠實無重疊;selftest 已證邏輯)。
- ★MD5 侷限誠實入帳:MD5 只擋**完全相同檔**;翻譯/重排/改封面版(同產品異檔)MD5 不同
  →須 brand+版次+文字/視覺相似度家族分組偵測(=VLM/人工 lane,通案五,不在此工具實作)。
  本工具以 brand+code 跨檔重現作衝突候選代理。

## 停止線判定:**未觸發**(守恆成立)
規格停止線=管線守恆掃出「候選無故消失」災難級(P1/P2 大量)。實測 P1=0、P2=0
(硬不變量成立)→ 不凍結。P3/B 為健康/追蹤信號,交 VLM/人工 lane。

## 已知邊界(誠實紅字)
- 守恆基於**靜態產線輸出**(product/ JSON):無跨版本歷史時間軸,「長期未處理」以 review_ratio
  代理、非真時序(真時序需 risk_replay 造歷史世界對照)。「修正後再入組裝二次錯誤」需執行
  軌跡=靜態不可得,歸 VLM/人工 lane。
- B1 跨版本=brand+code 精確重現;相似度家族(改版偵測)非 MD5、非精確碼=明列為未實作 lane。

儀器不裁決;守恆 0/0 為正面驗證,P3/B=人工/VLM 材料。pipeline/core/凍結常數零改動,V 仍 12。
