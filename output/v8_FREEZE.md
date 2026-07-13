# v8 凍結說明(2026-07-12 定案切版;審查方預核之凍結文件)

定案依據(c7 GT 全案,證據=output/c7_gt/GT_REPORT.md):反例誤觸發 4/4=0;
主批 GT 綁定位置零錯(A102 值錯誤 4 筆=v5 S2-2 缺口另案立票,非 v7/v8 範圍);
T1 防線野外零失守;未配對 33/33 落既知分類、未知項=0。

## 版本系譜

- v6:2026-07-09 定案(S2-2+M5-1+M5-2;凍結 output/m52_dev_v6.csv)。
- v7=v6+M5-3 列首色樣版型救援(spike_geom.m53_blocks;非列版型頁 v6→v7 逐位零 diff)。
- v8=v7+S2-1 全字母 B 類碼偵測(m2_scan.alpha_codes;v≤7 路徑逐位不動)。
- **凍結基準 CSV=output/s21_dev_v8.csv**(dev 289+1 頁、九欄逐頁;pipeline --smoke 對帳標的)。

## code_block_bound 欄定義(審查方預留承諾,正式落文)

頁級計數欄(v7+ 出現):該頁中經 **M5-3 塊綁**離隊的碼數——
spike_geom.m53_blocks 四閘(X0_TOL/LEFT/UNIF/BAND)全 ON 時,would-be orphan
綁回所屬列首色樣,assign_words 以 **d=-2.0 哨兵**回傳;再經 M5-2 icon_sus
檢查(塊綁到疑似小圖形→降級,不計入本欄)。
- 佇列恆等式(v7+):`code_needs_review = n_codes − code_x_aligned − code_block_bound`。
- JSON 溯源:塊綁綁定 `prov.method="geom_v7_block"`(x 對齊=geom_v6_x_aligned)。
- 守恆:Σ mergedFrom = 凍結 code_x_aligned 總和 + code_block_bound 總和。

## 凍結常數清單(全數不動;動任何一個=新版本閘+完整儀式)

S2-1(m2_scan,v8):
- V8_X_TOL=0.005(②錨欄 x0 對齊容差×頁寬)
- V8_ROW_H=1.5(③同列 y 容差×字高)
- V8_OCC=2(⑤occ 錨中位臂)、V8_OCC_PG=0.6(⑤頁數臂)、V8_OCC_CAP=5(⑤絕對上蓋)
- V8_R_MIN=3(⑥檔內含尺寸列下限)、V8_DOM=0.6(⑦錨形優勢比下限)
- **③④=AND**(2026-07-11 校準定案;m5「同列已有錨碼不收」否決存查)

M5-3(spike_geom,v7):
- M53_MIN_COL=2、M53_H_MED=3、M53_AREA=0.03、M53_X0_TOL=0.02、M53_LEFT=0.45、
  M53_BOT=0.92、M53_PITCH=1.5、M53_BAND_W=2、M53_H_UNIF=1.5

沿革凍結(不因切版重開):S2-2 route_junk(BAND_RE ^[A-Z]\d{1,2}$ 等)、
M5-2 icon_sus(0.05/0.5×中位、50% 頁數)、M4 系(1.5×字高同列、4×字高 above、
折縫 1.2、名鍵 5 道守門)、頁級 spec 閘(SIZE_RE≥3)。

## 凍結時已知缺口(票務=BACKLOG;修任何一項=新版本閘)

1. S2-1 ③同列無尺寸(c7 頻率 31:PietraEssenza p19=14、PortlandStone p21 E 族=17)。
2. S2-1 ②欄內無錨/無錨頁(c7 頻率 29:PortlandStone p22 EMX=3、PietraEssenza p21 純 B 碼頁=26)+②錨帶外(p22 EMJ 族=10)。
3. S2-2 BAND_RE 量表 3 位數缺口(A102 型;c7 值錯誤 4 筆+嵌合 variant 1 實錘)。
4. M5-3 已知限制②(堆疊型假欄)仍零樣本(探針落空,GT_REPORT §一)、限制④末塊下界(c7 第 1 例)。
5. E-1 場景照搶綁(xrow 舊路;c7 實測 13.9pt、4/10 檔)=下一張修理單(v9 設計案)。

## catalogs7 身分變更(切版即日生效)

held-out 資格已耗盡(GT 全檔人眼判讀)→ 轉**已知病例夾具+回歸計分板**:
只稱修復率、永不用於調參;**禁止對 c7 調任何參數**(防過擬合硬條款,使用者
明令)。預設保留(catalogs6 先例);銷毀/凍結計分板=A 板,使用者可否決。
