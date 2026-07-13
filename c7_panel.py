#!/usr/bin/env python3
"""GT 人工監測面板產生器(機械產出,無人為篩選;判讀表=output/c7_gt/GT_PROTOCOL.md 鎖死)。

    /opt/homebrew/bin/python3 c7_panel.py        # 必須從主工作樹專案根執行

產出(全在 viewer/c7_gt/,由 8642 伺服器供人工 GT 閱讀):
- judge_quarzite_p6/      Quarzite p6 定性頁(4 碼綠框、色樣零框+定性題)
- judge_<stem>/           兩個零綁定檔全檔逐頁渲染+佇列項橙框(無框=系統完全沒看見)
- panel.html              單一入口:①~⑥待判項+回報格式+狀態區

零改動紀律:只讀 product_c7/ 既有輸出與 catalogs7/ 原檔,不碰任何規則檔;
渲染疊框在記憶體頁上,PDF 原檔不動。
"""
import html
import json
import urllib.parse
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).parent          # ponytail: 必須=主工作樹(worktree 無 catalogs7/product_c7,前窗死因)
GT = ROOT / "viewer" / "c7_gt"
DPI_FULL = 120                        # 全檔逐頁(7/23 頁,無需分頁)
DPI_ONE = 150

HEAD = "<meta charset='utf-8'><body style='font-family:sans-serif;max-width:980px;margin:2em auto'>"
FMT = "檔名|紅線:全對/錯N條(哪條)|漏抓:無/有(哪區)|照片級:可用/不可用/混"


def pdf_of(stem):
    return next(p for p in (ROOT / "catalogs7").rglob("*.pdf") if p.stem == stem)


def review_items(stem):
    rj = next(p for p in (ROOT / "product_c7").rglob("*.review.json") if p.name == stem + ".review.json")
    return json.loads(rj.read_text())["items"]


def draw_boxes(page, boxes, color):
    """boxes=[(label,bbox)];疊框在記憶體頁上,機械全畫不篩選。"""
    sh = page.new_shape()
    for label, bb in boxes:
        sh.draw_rect(fitz.Rect(bb))
        sh.finish(color=color, width=1.2)
        sh.insert_text(fitz.Point(bb[0], bb[1] - 2), label, color=color, fontsize=6)
    sh.commit()


def render_full(stem, note):
    """零綁定檔全檔逐頁+佇列橙框。回傳(頁數, 佇列筆數)。"""
    items = review_items(stem)
    by_page = Counter(i["prov"]["page"] for i in items)
    out = GT / ("judge_" + stem.replace(" ", "_"))
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_of(stem))
    body = [HEAD, f"<h1>{html.escape(stem)} — 全檔判讀頁</h1>",
            f"<p><b>{note}</b></p>",
            f"<p>橙框=佇列項(needs_review,機械疊框無篩選;本檔共 {len(items)} 筆)。"
            "<b>無框=系統完全沒看見,請判原頁上有無產品。</b>"
            f"回報格式:<code>{FMT}</code></p>"]
    drawn = 0
    for pno in range(1, len(doc) + 1):
        page = doc[pno - 1]
        boxes = [(i["code"], i["prov"]["bbox"]) for i in items if i["prov"]["page"] == pno]
        draw_boxes(page, boxes, (1, 0.55, 0))
        drawn += len(boxes)
        fn = f"p{pno:03d}.png"
        page.get_pixmap(dpi=DPI_FULL).save(out / fn)
        body.append(f"<h2 id='p{pno}'>p{pno}(佇列 {by_page.get(pno, 0)} 筆)</h2>"
                    f"<img src='{fn}' style='max-width:100%'>")
    assert drawn == len(items), f"{stem}: 疊框 {drawn} != 佇列 {len(items)}(守恆破)"
    (out / "index.html").write_text("\n".join(body))
    print(f"{stem}: 全檔 {len(doc)} 頁、佇列 {len(items)} 筆 → {out}/index.html")
    return len(doc), len(items)


def render_quarzite_p6():
    stem = "Mystone Quarzite_catalog_W5-04_en"
    items = [i for i in review_items(stem) if i["prov"]["page"] == 6]
    out = GT / "judge_quarzite_p6"
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_of(stem))
    page = doc[5]
    draw_boxes(page, [(i["code"], i["prov"]["bbox"]) for i in items], (0, 0.55, 0))
    page.get_pixmap(dpi=DPI_ONE).save(out / "p006.png")
    codes = ", ".join(i["code"] for i in items)
    (out / "index.html").write_text(f"""{HEAD}
<h1>Quarzite p6 定性(GT_REPORT §四歸因②唯一未歸類項)</h1>
<p>系統偵測現況:<b>碼 {len(items)} 個(綠框:{html.escape(codes)}),色樣偵測=0 框</b>
(n_sw=0,故 4 碼全進佇列、無可綁對象)。</p>
<p><b>定性題:該頁真相是哪一種?(二選一)</b></p>
<ol>
<li><b>版面事實</b>——該頁真的沒有色樣(純情境照頁),系統行為正確(誠實佇列)。</li>
<li><b>偵測缺口</b>——頁上其實有色樣,但系統沒框到(色樣偵測漏)。</li>
</ol>
<p>回報:「Quarzite p6|版面事實」或「Quarzite p6|偵測缺口(色樣在哪一區)」。</p>
<img src='p006.png' style='max-width:100%'>""")
    print(f"Quarzite p6: 碼 {len(items)} 框 → {out}/index.html")
    return len(items)


def enc(p):
    return urllib.parse.quote(str(p))


def write_panel(n_ard, n_pie, n_qp6):
    ev = {s: f"{s.replace(' ', '_')}/index.html" for s in [
        "Dover_catalog_683-04_en", "Slow20_catalog_A0FW-04_en",
        "PortlandStone Catalogo 2026.02 Web", "Mystone Quarzite_catalog_W5-04_en"]}
    pdfs = {k: "/" + enc(pdf_of(k).relative_to(ROOT)) for k in [
        "Dover_catalog_683-04_en", "Slow20_catalog_A0FW-04_en",
        "Mystone Ardesia20_catalog_413-04_en", "PietraEssenza Catalogo 2025.10 Web",
        "Mystone Quarzite_catalog_W5-04_en", "PortlandStone Catalogo 2026.02 Web"]}
    rows = [
        ("①", "Dover 紅線抽查(v7 主戰場,帳面 100%,抽查=蓋章)",
         f"<a href='{ev['Dover_catalog_683-04_en']}'>證據頁(9 筆塊綁)</a>|<a href='{pdfs['Dover_catalog_683-04_en']}'>原始 PDF</a>"),
        ("②", "Slow20 紅線抽查+整排隱形產品掃描(漏抓請對原始 PDF 全頁)",
         f"<a href='{ev['Slow20_catalog_A0FW-04_en']}'>證據頁(9 筆綁定)</a>|<a href='{pdfs['Slow20_catalog_A0FW-04_en']}'>原始 PDF</a>"),
        ("③", f"Mystone Ardesia20 全檔判讀(系統整檔零產出、SIZE_RE 整檔未命中;佇列 {n_ard} 筆——原檔裡到底有沒有產品?有=整本靜默漏的實錘)",
         f"<a href='judge_Mystone_Ardesia20_catalog_413-04_en/index.html'>全檔判讀頁</a>|<a href='{pdfs['Mystone Ardesia20_catalog_413-04_en']}'>原始 PDF</a>"),
        ("④", f"PietraEssenza 全檔判讀(Emil 首觸,21 碼全佇列零自動輸出;佇列 {n_pie} 筆——版型長相一句直覺描述)",
         f"<a href='judge_PietraEssenza_Catalogo_2025.10_Web/index.html'>全檔判讀頁</a>|<a href='{pdfs['PietraEssenza Catalogo 2025.10 Web']}'>原始 PDF</a>"),
        ("⑤", f"Quarzite p6 定性:版面事實(該頁真的沒有色樣) vs 偵測缺口(有色樣但系統沒框到);{n_qp6} 碼零色樣",
         "<a href='judge_quarzite_p6/index.html'>定性判讀頁</a>"),
        ("⑥", "PortlandStone/Quarzite 已綁筆紅線抽查(76+22 筆)",
         f"<a href='{ev['PortlandStone Catalogo 2026.02 Web']}'>PortlandStone 證據頁</a>|<a href='{ev['Mystone Quarzite_catalog_W5-04_en']}'>Quarzite 證據頁</a>|"
         f"<a href='{pdfs['PortlandStone Catalogo 2026.02 Web']}'>PS 原 PDF</a>|<a href='{pdfs['Mystone Quarzite_catalog_W5-04_en']}'>Qz 原 PDF</a>"),
    ]
    trs = "\n".join(f"<tr><td>{n}</td><td>{t}</td><td>{links}</td><td>☐ 待判</td></tr>"
                    for n, t, links in rows)
    (GT / "panel.html").write_text(f"""{HEAD}
<h1>catalogs7 GT 人工監測面板</h1>
<p>判讀表=<code>output/c7_gt/GT_PROTOCOL.md</code>(鎖死)|工作表=<code>output/c7_gt/GT_REPORT.md</code>|
<a href='index.html'>全部證據頁總覽</a>。證據全部機械產生、無人為篩選;GT 期間規則零改動。</p>
<h2>待判項 ①~⑥</h2>
<p>回報格式(每項照填):<code>{FMT}</code><br>
⑤ 專用格式見其判讀頁(二選一)。</p>
<table border=1 cellpadding=6 style='border-collapse:collapse'>
<tr><th></th><th>判讀項</th><th>頁面</th><th>狀態</th></tr>
{trs}
</table>
<h2>狀態區</h2>
<ul>
<li><b>已判</b>:roads-465 p15(96 筆塊綁全對,分支二;反例誤觸發條款 4/4=0 通過)。</li>
<li><b>待判</b>:上表 ①~⑥(全部完成 → GT_REPORT §五 → 打包送審=v7/v8 定案裁決)。</li>
<li><b>佇列外抽驗累積</b>:n=199(103+96)、95% 上界≈1.5%;主批 180 筆(124 x對齊+56 塊綁)
驗完若零發現 → n=379、上界≈0.8%。</li>
<li><b>備份待辦</b>:bundle=<code>~/catalog-extractor-20260711.bundle</code>(77M,
md5 <code>73b23397ce12b2037b387051d191dd50</code>);使用者親手跑
<code>/usr/bin/python3 core/drive_backup.py ~/catalog-extractor-20260711.bundle</code>,
完成標準=工具印出的 Drive md5Checksum 與上列 md5 一致。</li>
</ul>""")
    print(f"panel → {GT}/panel.html")


def main():
    n_qp6 = render_quarzite_p6()
    n_ard = render_full("Mystone Ardesia20_catalog_413-04_en",
                        "系統整檔零產出(SIZE_RE 整檔未命中=0 spec 頁、0 偵測、0 佇列)。"
                        "判讀問題:原檔裡到底有沒有產品?有=整本靜默漏的實錘。")[1]
    n_pie = render_full("PietraEssenza Catalogo 2025.10 Web",
                        "Emil 首觸:21 碼全佇列、零自動輸出。判讀問題:紅線+漏抓照格式,"
                        "另加一句版型長相直覺描述。")[1]
    write_panel(n_ard, n_pie, n_qp6)


if __name__ == "__main__":
    main()
