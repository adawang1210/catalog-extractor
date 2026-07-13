#!/usr/bin/env python3
"""包 B｜單頁 hub 過併——人眼定性證據頁(機械疊框、無人為判定;只讀不改規則)。

    /opt/homebrew/bin/python3 pkgB_hub_evidence.py            # 跑內建 MANIFEST 全代表頁
    /opt/homebrew/bin/python3 pkgB_hub_evidence.py --list     # 只印代表頁清單(不渲染)

★ 定位(鐵律1):單頁 hub 的「合法大合併 vs 真過併」＝綁定正確性判定＝**只認人工 GT**
(A102 嵌合體靠 GT 非儀器的教訓)。本腳本**不自判**,只**機械**把包 A --bind 掃出的
單頁 hub(單色樣綁≥HUB_MIN 碼、跨頁守衛照不到)疊框渲染,按**可觀察子型**分組,每子型
挑 2-3 代表頁送使用者人眼定性。定性結果(各子型=合法/過併)由使用者裁定後,才回饋
判別子設計。50 個單頁 hub 不逐一送審=代表頁批量套用。

疊框(機械,無篩選):
  細灰框 = 該頁全部色樣(spike_geom;上下文,看 hub 是大情境照還是小色片)
  粗藍框 = ★HUB 色樣(單色樣綁≥HUB_MIN 碼;標綁碼數+佔頁面積%+解析色名)
  紅框   = HUB 吸附的每個碼詞(標 code;prov bbox=真碼詞位置)
判讀問句(送使用者):HUB 藍框底下的紅框碼,**是否全是「同一色樣的尺寸/表面碼」
(合法規格表/矩陣頁,如 Provenza 型)**?還是含「不屬於此色樣、被吸走的鄰欄/他色碼」
(真過併)?——合法矩陣頁(Provenza 型)須判「不過併」;失敗方向=寧不合併,但誤殺
合法規格表=漏真產品(反面陷阱)。

忠實度:bindings 複用 dev/assembly_probe(monkeypatch 攔 assemble 真實 bindings),
碼詞 bbox=b['prov']['bbox']、色樣 bbox=b['swatch']['bbox']=產線真值。輸出 viewer/
pkgB_hubs/(不入庫;viewer 產出慣例)。
"""
import html
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dev"))

import fitz                                     # noqa: E402
import pipeline                                 # noqa: E402
import assembly_probe as ap                     # noqa: E402  複用綁定捕捉(100% 鏡射 assemble)
from spike_geom import extract_swatches         # noqa: E402

HUB_MIN = 8   # 同 dev/anomaly_probe.py(單色樣綁碼數門檻;報告用非產線常數)
DPI = 150

# 代表頁 MANIFEST(來源=output/pkgA_anomaly_report.md §3.2 之 50 單頁 hub 清單;
# 按可觀察子型分組、每子型 2-3 代表。stem 用子字串比對,page 為 1-based)
MANIFEST = [
    # (子型, corpus, stem 子字串, [頁號])
    ("G1 單色多碼(color.en=單一真色名)", "catalogs5", "Cornerstone Evolution", [27]),
    ("G1 單色多碼(color.en=單一真色名)", "catalogs7", "Tele Di Marmo Revolution", [19]),
    ("G1 單色多碼(color.en=單一真色名)", "catalogs2", "walk_on-609", [31]),
    ("G2 圖說溢收(color.en=整段圖說串)", "catalogs4", "0general_ariostea", [152]),
    ("G2 圖說溢收(color.en=整段圖說串)", "catalogs2", "SistemT", [4, 5]),
    ("G2 圖說溢收(color.en=整段圖說串)", "catalogs5", "Medley", [21]),
    ("G3 合法矩陣表候選(Provenza 型;須判不過併)", "catalogs2", "UniqueMarble", [16]),
    ("G3 合法矩陣表候選(Provenza 型;須判不過併)", "catalogs", "Unique Travertine", [33]),
]

GROUP_Q = {
    "G1": "紅框碼是否全為『Slate/Thassos/WALK…』該單一色樣底下的尺寸/表面碼(合法)?"
          "還是 hub 情境照吸走了整表他色碼(過併)?",
    "G2": "color.en 解析成整段圖說串(junk)=已知『圖說溢收』;綁定層問:紅框碼是否"
          "仍屬同一色樣(僅色名 junk、綁定合法),還是連綁定都把整頁多色/多欄吸成一團(過併)?",
    "G3": "Provenza 矩陣頁:一色樣代表一系列、底下多尺寸碼。紅框碼是否恰為該色樣的"
          "尺寸列(合法大合併,須落『不過併』側)?此組=判別子的合法錨,不得誤殺。",
}


def _find_pdf(corpus, sub):
    for p in sorted((ROOT / corpus).rglob("*.pdf")):
        if not p.name.startswith("._") and sub.lower() in p.stem.lower():
            return p
    raise SystemExit(f"找不到 {corpus}/*{sub}*")


def _hub_map(binds, pno):
    """該頁 hub 色樣 → 其吸附綁定。回傳 {sw_bbox_tuple: [binds]}(僅 sw-fan≥HUB_MIN)。"""
    by_sw = defaultdict(list)
    for b in binds:
        if b["swatch"]["page"] == pno:
            by_sw[tuple(b["swatch"]["bbox"])].append(b)
    return {sw: bl for sw, bl in by_sw.items()
            if len({b["code"] for b in bl}) >= HUB_MIN}


def render(out, body):
    vocabs = pipeline.build_vocabs()
    cur_group = None
    for label, corpus, sub, pages in MANIFEST:
        gkey = label.split()[0]
        if label != cur_group:
            body.append(f"<h1 style='background:#eef;padding:6px'>{html.escape(label)}</h1>")
            body.append(f"<p style='color:#036'><b>判讀問句:</b>{html.escape(GROUP_Q[gkey])}</p>")
            cur_group = label
        pdf = _find_pdf(corpus, sub)
        _, binds, _ = ap._metrics(pdf, vocabs, 12)
        doc = fitz.open(pdf)
        slug = (corpus + "_" + pdf.stem).replace(" ", "_").replace("–", "-")[:40]
        for pno in pages:
            hubs = _hub_map(binds, pno)
            page = doc[pno - 1]
            pa = abs(page.rect)
            sh = page.new_shape()
            # 細灰框=全部色樣(上下文:看 hub 是大情境照還是小色片)
            for r in extract_swatches(page, version=3):
                sh.draw_rect(fitz.Rect(r))
                sh.finish(color=(0.6, 0.6, 0.6), width=0.5)
            # 粗藍框=HUB 色樣;紅框=其吸附碼詞
            for sw, bl in sorted(hubs.items(), key=lambda x: -len(x[1])):
                codes = sorted({b["code"] for b in bl})
                cen = _resolve_color(bl)
                rr = fitz.Rect(sw)
                sh.draw_rect(rr)
                sh.finish(color=(0, 0, 1), width=1.8)
                sh.insert_text(fitz.Point(rr.x0, rr.y0 - 3),
                               f"HUB 綁{len(codes)}碼 {abs(rr) / pa * 100:.1f}%頁 "
                               f"色名={cen[:40]}", color=(0, 0, 1), fontsize=6)
                for b in bl:
                    bb = b["prov"]["bbox"]
                    if not bb:
                        continue
                    sh.draw_rect(fitz.Rect(bb) + (-1, -1, 1, 1))
                    sh.finish(color=(0.85, 0, 0), width=1.2)
                    sh.insert_text(fitz.Point(bb[0], bb[1] - 2), b["code"],
                                   color=(0.85, 0, 0), fontsize=5)
            sh.commit()
            png = f"{slug}_p{pno}.png"
            page.get_pixmap(dpi=DPI).save(out / png)
            nhub = len(hubs)
            ncode = sum(len({b['code'] for b in bl}) for bl in hubs.values())
            body.append(f"<h3>{html.escape(corpus)}/{html.escape(pdf.stem)} — p{pno}"
                        f"(HUB 色樣 {nhub}、吸附碼 {ncode})</h3>"
                        f"<img src='{png}' style='max-width:100%;border:1px solid #999'>")
            print(f"{corpus}/{pdf.stem} p{pno}: HUB={nhub} 碼={ncode} -> {png}", flush=True)


def _resolve_color(bl):
    """鏡射 assemble 的 color_en 解析(僅供標示;非判定)。"""
    cols = sorted({b["color"] for b in bl if b["color"]})
    raws = sorted({b.get("colorRaw", b["color"]) for b in bl if b.get("colorRaw", b["color"])})
    if len(cols) == 1 and len(raws) <= 1:
        return cols[0]
    return f"None(衝突;raw={len(raws)}名)" + (f" 例:{raws[0][:30]}" if raws else "")


if __name__ == "__main__":
    if "--list" in sys.argv:
        for label, corpus, sub, pages in MANIFEST:
            print(f"{label} | {corpus} | {sub} | 頁 {pages}")
        sys.exit(0)
    out = ROOT / "viewer" / "pkgB_hubs"
    out.mkdir(parents=True, exist_ok=True)
    body = ["<meta charset='utf-8'><body style='font-family:sans-serif;max-width:1100px'>",
            "<h1>包 B｜單頁 hub 過併——人眼定性證據頁</h1>",
            "<p><b>細灰框</b>=該頁全部色樣;<b>粗藍框</b>=HUB 色樣(單色樣綁≥8 碼、"
            "跨頁塌縮守衛照不到);<b>紅框</b>=HUB 吸附的每個碼詞。機械疊框無篩選。<br>"
            "<b>總判讀:每個 HUB 藍框底下的紅框碼,是同一色樣的尺寸/表面碼(合法規格表/"
            "矩陣頁)?還是含被吸走的他色碼(真過併)?</b> 定性請逐子型裁定。</p>"]
    render(out, body)
    idx = out / "index.html"
    idx.write_text("\n".join(body), encoding="utf-8")
    print("\nindex:", idx)
