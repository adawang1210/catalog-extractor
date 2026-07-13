#!/usr/bin/env python3
"""S2-4 頁腳頁碼族分離量測(段4;通案三入庫、只讀不改規則)。

頁腳頁碼污染=純數字 token 被稀疏分支收成碼,實為頁碼(FMG 頁腳族 dev 100)。族訊號
(audit.md D2):純數字 ∧ 跨頁同位聚類(x±X_TOL、≥MIN_PAGES 頁)∧ 邊帶(y_frac<EDGE 或
>1-EDGE)∧ 值−頁=常數族(頁碼隨物理頁遞增,含固定 offset)。本探針對每檔逐純數字碼實例
收 (page, x, y_frac),依上述四訊號找頁腳族,量分離:FMG 應中頁腳族、其餘純數字碼檔
(VICTORIAN/ultra/PIPO 真 SKU)0 誤中。

    /opt/homebrew/bin/python3 dev/s24_pagefoot_probe.py <corpus>...   (CWD=專案根)
"""
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402
from m2_scan import code_candidates  # noqa: E402

import os  # noqa: E402
X_TOL = float(os.environ.get("S24_XTOL", 20.0))    # 同位 x 容差(pt);頁腳同欄
MIN_PAGES = int(os.environ.get("S24_MINP", 5))     # 跨頁下限
EDGE = float(os.environ.get("S24_EDGE", 0.08))     # 邊帶=y_frac<EDGE 或 >1-EDGE(探路 <8%/>92%)


def _digit_instances(doc):
    """回傳 {token: [(page_idx, x_center, y_frac)]},僅純數字(2/3/5/6/7/8 位)。"""
    inst = defaultdict(list)
    for pno, page in enumerate(doc):
        h = page.rect.height or 1.0
        for w in page.get_text("words"):
            t = pipeline.norm(w[4])
            if t.isdigit() and len(t) in (2, 3, 5, 6, 7, 8):
                inst[t].append((pno, (w[0] + w[2]) / 2, ((w[1] + w[3]) / 2) / h))
    return inst


def _pagefoot_family(inst, digit_codes):
    """實例級頁腳族偵測(audit 教訓:頁碼是實例位置屬性,token 層 all() 必敗)。
    步1 邊帶實例依 x 分簇(±X_TOL)、簇內 值−頁=常數 且跨≥MIN_PAGES → 標記為「頁腳實例」。
    步2 token 唯有**全部**實例皆頁腳實例(無 code-role 非頁腳實例)才路由 pagefoot。
    回傳 (foot_tokens, detail{token:(footer_inst, total_inst)})。"""
    # 步1:收邊帶實例(token, page, x),分簇找 值−頁=常數 家族 → 頁腳實例集
    edge = []
    for t in digit_codes:
        for k, (pno, x, yf) in enumerate(inst.get(t, [])):
            if yf < EDGE or yf > 1 - EDGE:
                edge.append((int(t), pno, x, t, k))
    footer_inst = set()  # (token, instance_idx)
    edge.sort(key=lambda e: e[2])
    clusters, cur = [], []
    for e in edge:
        if cur and e[2] - cur[-1][2] > X_TOL:
            clusters.append(cur); cur = []
        cur.append(e)
    if cur:
        clusters.append(cur)
    for cl in clusters:
        off = defaultdict(list)
        for val, pno, x, t, k in cl:
            off[val - pno].append((t, k, pno))
        for _, members in off.items():
            if len({pno for _, _, pno in members}) >= MIN_PAGES:
                footer_inst |= {(t, k) for t, k, _ in members}
    # 步2:token 全部實例皆頁腳實例才路由(留 code-role)
    foot, detail = set(), {}
    for t in digit_codes:
        tot = len(inst.get(t, []))
        fin = sum(1 for k in range(tot) if (t, k) in footer_inst)
        if fin:
            detail[t] = (fin, tot)
            if fin == tot:            # 無非頁腳(code-role)實例 → 純頁碼
                foot.add(t)
    return foot, detail


def main(corpora):
    cv, av = pipeline.build_vocabs()
    pipeline.V = 12
    print(f"# S2-4 頁腳頁碼族分離(X_TOL={X_TOL} MIN_PAGES={MIN_PAGES} EDGE={EDGE})")
    for c in corpora:
        for p in sorted(Path(c).rglob("*.pdf")):
            if p.name.startswith("._"):
                continue
            try:
                doc = pipeline.fitz.open(p)
            except Exception:
                continue
            spec = [pg for pg in doc if len(pipeline.SIZE_RE.findall(pg.get_text())) >= 3]
            try:
                kept, _ = code_candidates(doc, cv, len(spec), 12, av)
            except Exception:
                continue
            digit_codes = {t for t in kept if t.isdigit()}
            if not digit_codes:
                continue
            inst = _digit_instances(doc)
            foot, detail = _pagefoot_family(inst, digit_codes)
            nonfoot = sorted(digit_codes - foot)
            # 混合 token=有頁腳實例但亦有 code-role 實例(不路由,實例級保留)
            mixed = sorted(t for t in detail if t not in foot)
            print(f"\n## {c}/{p.stem[:34]}  純數字碼={len(digit_codes)} → 純頁碼(移除)={len(foot)} "
                  f"混合(保留)={len(mixed)} 純非頁腳(保留)={len(nonfoot) - len(mixed)}")
            if foot:
                fs = sorted(foot, key=int)
                print(f"   純頁碼移除: {fs[:24]}{'…' if len(fs) > 24 else ''}")
            if mixed:
                print(f"   ★混合(頁腳+code-role,實例級保留 token): "
                      f"{[(t, detail[t]) for t in mixed[:10]]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
