# 鐵律 8 風險摘要總帳(工作包 #9 雛形;案2 擴充+回放驗收 2026-07-13)

工具:`python3 dev/risk_diff.py <before_outdir> <after_outdir>`(`--selftest` 合成回歸)。
回放世界產生器:`python3 dev/risk_replay.py <outdir> <corpus...> [--ver N] [--off case1,collapse,seg1] [--only substr]`(CWD=專案根;monkeypatch 版本/守衛常數,零改產線)。

它不改版本閘,也不裁決白名單;只把全量輸出差異縮成必須人工看的五類:

1. **①新自動放行**:新增 Variant,或同身分 Variant 的 `None→有值`(進直接輸出路徑)。
2. **②佇列項消失**:needs_review 項在 after 缺席(reason+code+prov+swatch 逐欄比對)。
3. **③跨頁合併/撤權**:新增或變跨頁的 Variant(`new_crosspage`);**跨頁 Variant 消失
   =`removed_crosspage` cluster 級摘要(筆數+頁)——案2 新增,撤權不得摺疊消音**。
4. **④單一來源扇出**:單 swatch/token 綁定數突增(**n≥2 才算扇出**;0→1 歸①③呈現=案2 去噪)。
5. **⑤欄位來源/角色變動**:Variant/variantSize/specByCode 可回指欄位的值或 prov 改變。

其餘**逐位相同**只計 `unchanged_variants`;單頁 Variant 移除(撤權安全方向)計
`other_variant_removed` 不逐筆(跨頁移除已入③)。白名單外任一五類項目仍是紅線;
工具是人工閱讀的篩選器,不是放寬鐵律 8 的機制。

## 案2 驗收|已知案例真實回放(2026-07-13;基線=案1 後 product/=V12 現行鏡,
## Σ1041+0+30+0+37+0=1108、Variant 201;全部數字可由下列命令逐字復現)

**紅燈先行(鐵律7)**:--selftest 新增「跨頁撤權對偶」——實作前 RED(撤權被摺疊消音
`AssertionError: 撤權未現身類③摘要: []`)→ 實作 `removed_crosspage` 後全綠。

| 案例 | 回放命令(before after) | 期待類 | 實跑結果 |
|---|---|---|---|
| a|v13 交互 A02G 119 跨頁 | `risk_replay product_replay_a02g_v12off catalogs --only A02G --off case1,collapse,seg1` vs 同 `--ver 13` | ③ | **✓ ③ new_crosspage 119/23頁**(另 removed_crosspage 18/8/6/5…=被 119 吞併的 v12 子團=機制自洽;②=55 含 med_ex 救回 icon_demoted 離隊=M5-2b 帳) |
| b|S2-2 毒碼歸隊 | `risk_replay product_replay_v8 catalogs --ver 8` vs `product_replay_v10 --ver 10` | ⑤ | **✓ ⑤=212**(priceBand None→A100/A105/A96/A56 band 歸隊+列 prov 位移,Provenza/Emil 兩檔=歷史帳 3 頁);**A107(dev A102 型錨)17 筆現身**=② merge_key_suspect/orphan 離隊+⑤ 角色變動;①=3=歸隊後 p34 釋出真 Variant |
| c|段1 單頁過併 | `risk_replay product_replay_0gen_on catalogs4 --only 0general` vs 同 `--off seg1` | ④ | **✓ ④恰為段1 白名單雙 hub:p152 色樣 0→34、0→82**(一字不差);②=116=34+82 綁定離隊、①=2 |
| d|案1 撤權 37 筆 | `risk_replay product_replay_case1off catalogs --off case1` vs **product/**(現行鏡) | ③摘要+② | **✓ ③摘要=removed_crosspage 18(A02G p3/4/6/7/10)+19(TopcerGen p5/9/21/22)=37 筆**;②=3 恰為兩撤權團摘要旗(A02G ccc+Topcer ccc/regime=案1 總帳 §六 復現);①④⑤=0;摺疊 unchanged=201=基線 Variant 數、other_removed=0 |

**鐵律8 語義不變**:案例 d 白名單=案1 總帳白名單,五類清單逐項落白名單內、白名單外
零容忍照舊由人工核對;摺疊只吃逐位相同與單頁移除計數。回放世界目錄
`product_replay_*`(.gitignore,可由 risk_replay.py 重生);product/ 未被觸碰。

已知邊界(誠實紅字):②以 (reason,code,prov,swatch) 全欄相等判「同一項」——佇列項
prov 有任何位移會呈現為「消失+新增」,消失側仍會亮=fail-safe 方向;⑤只比對兩側同
鍵欄位,系列級鍵(specByCode id)重排會轉出現在①/摺疊帳,現行 id 穩定(b:page:idx)
未觸發。
