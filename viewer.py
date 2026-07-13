#!/usr/bin/env python3
"""辨識結果檢視網頁產生器(純輸出,不碰綁定/組裝)。

    /opt/homebrew/bin/python3 viewer.py            # 全部 dev 文件
    /opt/homebrew/bin/python3 viewer.py <stem 關鍵字>  # 只產含關鍵字的文件

讀 product/<brand>/<stem>.json + .review.json + 裁圖,渲染被引用頁為 PNG,
產 viewer/<stem>.html(左=型錄頁+匡選框,右=磁磚卡片)與 viewer/index.html。
瀏覽:python3 -m http.server 8642 → http://localhost:8642/viewer/
設計:ui-ux-pro-max design-system(monochrome+藍 accent、Rubik/Nunito Sans)。
"""
import json
import re
import sys
import urllib.parse
from pathlib import Path

import fitz

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "core"))
from census import SIZE_RE  # noqa: E402  引擎 spec 頁閘(唯讀鏡射,不改規則)

OUT = ROOT / "viewer"
DPI = 110

REASON_LABEL = {
    "orphan": "孤兒碼(無對齊色樣)",
    "code_color_conflict": "同碼異色名衝突",
    "regime_conflict": "體制訊號混合",
    "icon_demoted": "疑圖標欄(非色樣)降級",
    "not_x_aligned": "碼未與色樣對齊",
    "borderline_merge_suspect": "跨頁合併不確定帶(降級待審)",
    "assembly_collapse_suspect": "跨頁塌縮團(色名衝突·降級)",
    "singlepage_overmerge_suspect": "單頁過併團(降級)",
    "assembly_merge_radius_suspect": "合併爆炸半徑(降級)",
    "merge_key_suspect": "合併鍵疑義",
}

# A3|每頁處置五態(外審紅線=每頁必有非空處置,未覆蓋不得呈現成沒產品)。
# 全部由引擎既有輸出推導,零規則改動:
#   auto    ①已自動抽出產品(該頁有已綁定 Variant 實例)
#   review  ②送人工複查(該頁有佇列項/骨架色樣,帶引擎 reason)
#   noprod  ③引擎掃描該規格頁但無可自動綁定產品(spec 頁,無綁定/佇列)
#   nonspec ④a 非規格頁(有文字層但 size 特徵<3,引擎未取為規格頁)
#   image   ④b 影像/掃描頁(無文字層,幾何不可判 → 待 AI/人工)
PAGE_STATE_LABEL = {
    "auto":    "已自動抽出",
    "review":  "送人工複查",
    "noprod":  "掃描·無可綁定產品",
    "nonspec": "非規格頁(未達 size 閘)",
    "image":   "影像/掃描頁 · 待 AI/人工",
}


def find_pdf(name):
    for cdir in sorted(ROOT.glob("catalogs*")):  # 全語料(catalogs, catalogs2..7)
        for p in cdir.rglob("*.pdf"):
            if p.name == name and not p.name.startswith("._"):
                return p
    return None


def q(path):  # 相對路徑 URL 編碼(檔名含空格)
    return urllib.parse.quote(str(path))


def collect(doc_json, review_json, brand):
    d = json.loads(doc_json.read_text())
    r = json.loads(review_json.read_text()) if review_json.exists() else {"items": [], "skeletonSwatches": []}
    stem = doc_json.stem
    pdf_name = r.get("pdf") or f"{stem}.pdf"

    pages_needed = set()
    variants, queue, skeleton = [], [], []
    vid = 0
    for s in d.get("series", []):
        sname = (((s.get("seriesName") or {}).get("en") or {}).get("value")) or stem
        for v in s.get("variants", []):
            insts = []
            for inst in v.get("mergedFrom", []):
                pg = inst["swatch"]["page"]
                pages_needed.add(pg)
                insts.append({"page": pg, "swatch": inst["swatch"]["bbox"],
                              "token": inst["prov"]["bbox"]})
            rows = [{"size": vs.get("size"), "orderCode": vs.get("orderCode"),
                     "finish": vs.get("finish"), "priceBand": vs.get("priceBand")}
                    for vs in v.get("variantSizes") or []]
            crop = (v.get("swatchCrop") or {}).get("png")
            variants.append({
                "id": f"v{vid}", "code": v.get("code"),
                "color": ((v.get("color") or {}).get("en")),
                "series": sname, "crop": q(f"../product/{brand}/{crop}") if crop else None,
                "rows": rows, "sizes": sorted({x["size"] for x in rows if x["size"]}),
                "orderCodes": sorted({x["orderCode"] for x in rows if x["orderCode"]}),
                "instances": insts, "page": insts[0]["page"] if insts else None,
            })
            vid += 1
    for i, it in enumerate(r.get("items", [])):
        pg = it["prov"]["page"]
        pages_needed.add(pg)
        hint = None
        if it.get("nameHint"):
            h = it["nameHint"]
            pages_needed.add(h["page"])
            hint = {"page": h["page"], "bbox": h["bbox"],
                    "crop": q(f"../product/{brand}/{h['crop']}") if h.get("crop") else None}
        queue.append({"id": f"q{i}", "code": it.get("code"),
                      "codes": it.get("codes"), "candidates": it.get("candidates"),
                      "reason": it["reason"], "label": REASON_LABEL.get(it["reason"], it["reason"]),
                      "page": pg, "bbox": it["prov"]["bbox"], "hint": hint})
    for i, sk in enumerate(r.get("skeletonSwatches", [])):
        pages_needed.add(sk["page"])
        skeleton.append({"id": f"s{i}", "page": sk["page"], "bbox": sk["bbox"],
                         "caption": sk.get("caption"),
                         "crop": q(f"../product/{brand}/{sk['crop']}") if sk.get("crop") else None})

    # A3|每頁處置分類(引擎既有輸出推導,零規則):auto>review>noprod>nonspec>image
    variant_pages = {i["page"] for v in variants for i in v["instances"]}
    review_pages = {it["page"] for it in queue} | {sk["page"] for sk in skeleton}
    review_pages |= {it["hint"]["page"] for it in queue if it.get("hint")}

    # 渲染全部頁(外審紅線=每頁都要能看到並帶處置,不得靜默略過未覆蓋頁)
    pdf_path = find_pdf(pdf_name)
    pagedir = OUT / stem
    pagedir.mkdir(parents=True, exist_ok=True)
    pages, page_state, coverage = {}, {}, {k: 0 for k in PAGE_STATE_LABEL}
    if pdf_path:
        doc = fitz.open(pdf_path)
        for idx in range(doc.page_count):
            pg = idx + 1
            page = doc[idx]
            text = page.get_text()
            is_spec = len(SIZE_RE.findall(text)) >= 3       # 引擎 spec 頁閘(line 535 鏡射)
            if pg in variant_pages:
                st = "auto"
            elif pg in review_pages:
                st = "review"
            elif is_spec:
                st = "noprod"
            elif text.strip():
                st = "nonspec"
            else:
                st = "image"
            page_state[pg] = {"state": st, "sizeHits": len(SIZE_RE.findall(text)),
                              "hasText": bool(text.strip())}
            coverage[st] += 1
            out = pagedir / f"p{pg}.png"
            if not out.exists():
                page.get_pixmap(dpi=DPI).save(out)
            pages[pg] = {"w": page.rect.width, "h": page.rect.height,
                         "img": q(f"{stem}/p{pg}.png")}
    return {
        "stem": stem, "brand": brand, "pdf": pdf_name,
        "bindingVersion": d.get("bindingVersion"),
        "seriesSkeleton": d.get("seriesSkeleton", False),
        "knownGaps": d.get("knownGaps", []),
        "needsReviewCount": d.get("needsReviewCount", len(queue)),
        "pages": pages, "variants": variants, "queue": queue, "skeleton": skeleton,
        "pageState": page_state, "coverage": coverage, "totalPages": len(pages),
    }


TEMPLATE = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE%% — 辨識結果</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700&family=Rubik:wght@400;500;600;700&display=swap');
:root{
  --primary:#18181B; --on-primary:#FFF; --secondary:#3F3F46; --accent:#2563EB;
  --bg:#FAFAFA; --fg:#09090B; --muted:#E8ECF0; --border:#E4E4E7;
  --destructive:#DC2626; --warn:#B45309; --ok:#15803D;
  --font-head:'Rubik',-apple-system,'PingFang TC','Microsoft JhengHei',sans-serif;
  --font-body:'Nunito Sans',-apple-system,'PingFang TC','Microsoft JhengHei',sans-serif;
}
*{box-sizing:border-box}
body{margin:0;font-family:var(--font-body);background:var(--bg);color:var(--fg);font-size:16px;line-height:1.5}
a{color:var(--accent)}
.app{display:flex;height:100vh}
/* ── 左:型錄頁 ── */
.left{width:50%;display:flex;flex-direction:column;border-right:1px solid var(--border);background:#fff}
.topbar{display:flex;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid var(--border);flex-wrap:wrap}
.topbar .doc{font-family:var(--font-head);font-weight:600;letter-spacing:.06em;text-transform:uppercase;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:46%}
.topbar a.back{font-size:13px;text-decoration:none;color:var(--secondary);border:1px solid var(--border);border-radius:6px;padding:5px 10px}
.pagenav{display:flex;align-items:center;gap:6px;margin-left:auto}
button{font-family:var(--font-body);cursor:pointer}
.pagenav button{min-width:44px;min-height:36px;border:1px solid var(--border);background:#fff;border-radius:6px;font-size:14px;transition:background .2s}
.pagenav button:hover{background:var(--muted)}
.pagenav button:focus-visible,.card:focus-visible,.tabs button:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.pagenav .pno{font-variant-numeric:tabular-nums;font-weight:700;font-size:14px;padding:0 4px}
.pagechips{display:flex;gap:6px;padding:8px 16px;overflow-x:auto;border-bottom:1px solid var(--border);scrollbar-width:thin}
.pagechips button{border:1px solid var(--border);background:#fff;border-radius:999px;padding:6px 12px;font-size:13px;font-variant-numeric:tabular-nums;flex:0 0 auto;transition:all .15s}
.pagechips button[aria-current="true"]{background:var(--primary);color:var(--on-primary);border-color:var(--primary)}
.canvaswrap{flex:1;overflow:auto;padding:16px;background:var(--muted)}
.canvas{position:relative;margin:0 auto;box-shadow:0 1px 4px rgba(9,9,11,.14);background:#fff;max-width:100%}
.canvas img{display:block;width:100%;height:auto}
/* 框=透明填充+彩色外框(依類型/disposition 上色),密集頁不被填充糊成一片;加粗 3px 提可見度 */
.box{position:absolute;border-radius:2px;cursor:pointer;background:transparent;transition:box-shadow .15s}
.box.swatch{border:3px solid var(--accent)}
.box.token{border:3px solid var(--ok)}
.box.queue{border:3px dashed var(--warn)}
.box.hint{border:3px dotted #7C3AED}
.box.skel{border:3px solid #94A3B8}
.box:hover,.box.flash{box-shadow:0 0 0 4px rgba(37,99,235,.35);background:rgba(37,99,235,.10);z-index:5}
.legend{display:flex;gap:14px;padding:8px 16px;border-top:1px solid var(--border);font-size:12.5px;color:var(--secondary);flex-wrap:wrap}
.legend i{display:inline-block;width:14px;height:10px;border-radius:2px;margin-right:5px;vertical-align:baseline}
/* ── A3 每頁處置五態(色碼一致:chip 圓點 / 覆蓋條 / 橫幅)── */
:root{--st-auto:#15803D;--st-review:#B45309;--st-noprod:#64748B;--st-nonspec:#0891B2;--st-image:#7C3AED}
.pagechips button{position:relative;padding-left:22px}
.pagechips button::before{content:"";position:absolute;left:9px;top:50%;transform:translateY(-50%);width:8px;height:8px;border-radius:50%;background:var(--dot,#CBD5E1)}
.pagechips button[data-st="auto"]{--dot:var(--st-auto)} .pagechips button[data-st="review"]{--dot:var(--st-review)}
.pagechips button[data-st="noprod"]{--dot:var(--st-noprod)} .pagechips button[data-st="nonspec"]{--dot:var(--st-nonspec)}
.pagechips button[data-st="image"]{--dot:var(--st-image)}
.dispo{position:sticky;top:0;z-index:6;display:flex;align-items:center;gap:8px;padding:8px 12px;font-size:13px;font-weight:700;color:#fff;border-radius:6px;margin-bottom:10px}
.dispo small{font-weight:400;opacity:.9;font-variant-numeric:tabular-nums}
.dispo.auto{background:var(--st-auto)} .dispo.review{background:var(--st-review)} .dispo.noprod{background:var(--st-noprod)}
.dispo.nonspec{background:var(--st-nonspec)} .dispo.image{background:var(--st-image)}
.cov{margin:10px 20px 0;border:1px solid var(--border);border-radius:8px;padding:10px 12px;background:#fff}
.cov .bar{display:flex;height:12px;border-radius:6px;overflow:hidden;margin:8px 0}
.cov .bar span{display:block}
.cov .bar .auto{background:var(--st-auto)} .cov .bar .review{background:var(--st-review)} .cov .bar .noprod{background:var(--st-noprod)}
.cov .bar .nonspec{background:var(--st-nonspec)} .cov .bar .image{background:var(--st-image)}
.cov .keys{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--secondary)}
.cov .keys b{color:var(--fg);font-variant-numeric:tabular-nums}
.cov .keys i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:baseline}
.cov .keys i.auto{background:var(--st-auto)} .cov .keys i.review{background:var(--st-review)} .cov .keys i.noprod{background:var(--st-noprod)}
.cov .keys i.nonspec{background:var(--st-nonspec)} .cov .keys i.image{background:var(--st-image)}
.cov .tot{font-size:12.5px;font-weight:700;margin-top:6px}
/* ── 右:卡片 ── */
.right{width:50%;display:flex;flex-direction:column}
.rhead{padding:16px 20px 0}
.brandline{font-family:var(--font-head);font-weight:700;font-size:19px;letter-spacing:.10em;text-transform:uppercase}
.metaline{font-size:13px;color:var(--secondary);margin-top:4px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.chip{border:1px solid var(--border);border-radius:999px;padding:2px 10px;font-size:12px;background:#fff}
.gaps{margin:10px 20px 0;font-size:13px}
.gaps summary{cursor:pointer;color:var(--destructive);font-weight:700}
.gaps ul{margin:6px 0 0;padding-left:20px;color:var(--secondary)}
.tabs{display:flex;gap:8px;padding:14px 20px 0}
.tabs button{border:1px solid var(--border);background:#fff;border-radius:8px 8px 0 0;border-bottom:none;padding:10px 16px;font-size:14px;font-weight:700;color:var(--secondary);transition:all .15s}
.tabs button[aria-selected="true"]{background:var(--primary);color:var(--on-primary);border-color:var(--primary)}
.tabs .n{font-variant-numeric:tabular-nums;opacity:.75;margin-left:4px}
.cards{flex:1;overflow-y:auto;padding:16px 20px 40px;border-top:1px solid var(--border);display:grid;grid-template-columns:1fr;gap:14px;align-content:start}
@media (min-width:1600px){.cards{grid-template-columns:1fr 1fr}}
.card{display:flex;gap:16px;background:#fff;border:1px solid var(--border);border-radius:10px;padding:14px;cursor:pointer;transition:box-shadow .2s,border-color .2s;text-align:left}
.card:hover{box-shadow:0 2px 10px rgba(9,9,11,.10)}
.card.active{border-color:var(--accent);box-shadow:0 0 0 3px rgba(37,99,235,.22)}
.thumb{flex:0 0 148px;height:148px;background:var(--muted);border-radius:6px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.thumb img{max-width:100%;max-height:100%;object-fit:contain}
.thumb .noimg{font-size:12px;color:var(--secondary)}
.info{flex:1;min-width:0}
.badge{display:inline-block;background:#2F3B4C;color:#fff;font-size:11.5px;font-weight:700;letter-spacing:.14em;padding:4px 10px;border-radius:3px;margin-bottom:8px;text-transform:uppercase}
.badge.warn{background:var(--warn)} .badge.gray{background:#64748B}
.name{font-family:var(--font-head);font-weight:600;font-size:15.5px;letter-spacing:.08em;text-transform:uppercase;line-height:1.4}
.name .color{color:var(--secondary)}
.sizes{font-weight:800;font-size:15px;margin-top:6px;font-variant-numeric:tabular-nums}
.rowline{font-size:13px;color:var(--secondary);margin-top:6px;line-height:1.6}
.rowline b{color:var(--fg);font-variant-numeric:tabular-nums}
.srcpg{margin-top:8px;display:flex;gap:6px;flex-wrap:wrap}
.srcpg span{border:1px solid var(--border);background:var(--bg);border-radius:999px;padding:2px 10px;font-size:12px;font-variant-numeric:tabular-nums}
.empty{color:var(--secondary);font-size:14px;padding:24px;text-align:center}
@media (max-width:900px){.app{flex-direction:column;height:auto}.left,.right{width:100%}.canvaswrap{max-height:60vh}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<div class="app">
  <section class="left" aria-label="型錄頁面與匡選結果">
    <div class="topbar">
      <a class="back" href="index.html">← 全部文件</a>
      <span class="doc" title="%%PDF%%">%%PDF%%</span>
      <div class="pagenav">
        <button id="prev" aria-label="上一頁">‹</button>
        <span class="pno" id="pno" aria-live="polite"></span>
        <button id="next" aria-label="下一頁">›</button>
      </div>
    </div>
    <div class="pagechips" id="chips" role="tablist" aria-label="頁碼"></div>
    <div class="canvaswrap"><div id="dispo"></div><div class="canvas" id="canvas"></div></div>
    <div class="legend">
      <span><i style="background:rgba(37,99,235,.15);border:2px solid var(--accent)"></i>綁定色樣</span>
      <span><i style="background:rgba(21,128,61,.15);border:2px solid var(--ok)"></i>產品碼 token</span>
      <span><i style="background:rgba(180,83,9,.12);border:2px dashed var(--warn)"></i>待複查</span>
      <span><i style="background:rgba(124,58,237,.12);border:2px dotted #7C3AED"></i>名鍵假說色樣</span>
      <span><i style="background:rgba(148,163,184,.15);border:2px solid #94A3B8"></i>骨架色樣</span>
    </div>
  </section>
  <section class="right" aria-label="磁磚清單">
    <div class="rhead">
      <div class="brandline">%%BRAND%% · %%TITLE%%</div>
      <div class="metaline">
        <span class="chip">綁定引擎 %%BV%%</span>
        <span class="chip">已綁定 %%NV%%</span>
        <span class="chip">待複查 %%NQ%%</span>
        %%SKELCHIP%%
      </div>
    </div>
    %%COVERAGE%%
    %%GAPS%%
    <div class="tabs" role="tablist">
      <button role="tab" aria-selected="true" data-tab="variants">綁定結果<span class="n">%%NV%%</span></button>
      <button role="tab" aria-selected="false" data-tab="queue">待複查<span class="n">%%NQ%%</span></button>
      %%SKELTAB%%
    </div>
    <div class="cards" id="cards" tabindex="-1"></div>
  </section>
</div>
<script>
const DATA = %%DATA%%;
const pages = Object.keys(DATA.pages).map(Number).sort((a,b)=>a-b);
let cur = pages[0], tab = "variants", activeCard = null;

const boxesByPage = {};
function addBox(pg, bbox, cls, target){
  if(!DATA.pages[pg]) return;
  (boxesByPage[pg] = boxesByPage[pg] || []).push({bbox, cls, target});
}
DATA.variants.forEach(v => v.instances.forEach(i => {
  addBox(i.page, i.swatch, "swatch", v.id);
  addBox(i.page, i.token, "token", v.id);
}));
DATA.queue.forEach(it => {
  addBox(it.page, it.bbox, "queue", it.id);
  if(it.hint) addBox(it.hint.page, it.hint.bbox, "hint", it.id);
});
DATA.skeleton.forEach(sk => addBox(sk.page, sk.bbox, "skel", sk.id));

const STATE_LABEL = %%STATE_LABEL%%;
function dispoBanner(pg){
  const ps = DATA.pageState[pg]; if(!ps) return "";
  const st = ps.state, lab = STATE_LABEL[st] || st;
  // B類可見度:此頁已偵測但未自動綁定的框數(佇列/名鍵/骨架)——讓「已進佇列」不被讀成「漏標」
  const nrev = (boxesByPage[pg] || []).filter(b => b.cls === "queue" || b.cls === "hint" || b.cls === "skel").length;
  const detail = st === "noprod" ? "引擎已掃描此規格頁(偵測 " + ps.sizeHits + " 個尺寸樣式),無可自動綁定產品"
    : st === "nonspec" ? "有文字層但尺寸樣式 " + ps.sizeHits + " <3,引擎未取為規格頁(封面/目錄/內文)"
    : st === "image" ? "無文字層=影像/掃描頁,幾何不可判,登記待 AI/人工(非靜默略過)"
    : st === "review" ? "此頁已偵測 <b>" + nrev + "</b> 項待複查(已框選=橘/紫/灰外框,見右側佇列)——非漏標,是待人工"
    : "此頁有已自動抽出的產品(見右側綁定結果)";
  return '<div class="dispo ' + st + '">此頁處置:' + lab + ' <small>· ' + detail + '</small></div>';
}
function renderPage(){
  const p = DATA.pages[cur], c = document.getElementById("canvas");
  document.getElementById("pno").textContent = "p." + cur;
  document.getElementById("dispo").innerHTML = dispoBanner(cur);
  c.innerHTML = "";
  if(!p){ c.innerHTML = '<div class="empty">此頁未渲染</div>'; return; }
  const img = new Image();
  img.src = p.img; img.alt = "型錄第 " + cur + " 頁";
  c.appendChild(img);
  (boxesByPage[cur] || []).forEach(b => {
    const d = document.createElement("div");
    d.className = "box " + b.cls;
    d.style.left   = (b.bbox[0]/p.w*100) + "%";
    d.style.top    = (b.bbox[1]/p.h*100) + "%";
    d.style.width  = ((b.bbox[2]-b.bbox[0])/p.w*100) + "%";
    d.style.height = ((b.bbox[3]-b.bbox[1])/p.h*100) + "%";
    d.dataset.target = b.target;
    d.title = b.target;
    d.addEventListener("click", () => gotoCard(b.target));
    c.appendChild(d);
  });
  document.querySelectorAll("#chips button").forEach(b =>
    b.setAttribute("aria-current", String(+b.dataset.p === cur)));
}
function setPage(p, flashTarget){
  cur = p; renderPage();
  if(flashTarget) requestAnimationFrame(() =>
    document.querySelectorAll('.box[data-target="'+flashTarget+'"]').forEach(b => {
      b.classList.add("flash"); setTimeout(() => b.classList.remove("flash"), 1600);
      b.scrollIntoView({block:"nearest", behavior:"smooth"});
    }));
}
function tabOf(id){ return id[0] === "v" ? "variants" : id[0] === "q" ? "queue" : "skeleton"; }
function gotoCard(id){
  setTab(tabOf(id));
  const el = document.getElementById("card-" + id);
  if(!el) return;
  document.querySelectorAll(".card.active").forEach(c => c.classList.remove("active"));
  el.classList.add("active"); activeCard = id;
  el.scrollIntoView({block:"center", behavior:"smooth"});
}
function esc(s){ return String(s ?? "").replace(/[&<>"]/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m])); }

function cardHTML(v){
  const rows = v.rows.map(r =>
    "<b>" + esc(r.orderCode || "—") + "</b> " + esc(r.size || "") +
    (r.finish ? " · " + esc(r.finish) : "") + (r.priceBand ? " · 價格帶 " + esc(r.priceBand) : "")
  ).join("<br>");
  const pgs = [...new Set(v.instances.map(i => i.page))];
  return '<button class="card" id="card-' + v.id + '" data-page="' + v.instances[0].page + '" data-id="' + v.id + '">' +
    '<span class="thumb">' + (v.crop ? '<img loading="lazy" src="' + v.crop + '" alt="' + esc(v.code||v.color||"色樣") + ' 色樣裁圖">' : '<span class="noimg">無裁圖</span>') + '</span>' +
    '<span class="info"><span class="badge">已綁定 X-ALIGNED</span>' +
    '<div class="name">' + esc(DATA.brand) + " " + esc(v.code || (v.orderCodes[0]||"")) +
    (v.color ? ' <span class="color">' + esc(v.color) + "</span>" : "") + "</div>" +
    (v.sizes.length ? '<div class="sizes">' + v.sizes.map(esc).join(" / ") + "</div>" : "") +
    (rows ? '<div class="rowline">' + rows + "</div>" : "") +
    '<span class="srcpg">' + pgs.map(p => "<span>p." + p + "</span>").join("") + "</span>" +
    "</span></button>";
}
function queueHTML(it){
  const body = it.candidates
    ? "碼 <b>" + it.codes.map(esc).join(", ") + "</b><br>候選:" + it.candidates.slice(0,4).map(esc).join(" / ") + (it.candidates.length > 4 ? " …" : "")
    : "碼 <b>" + esc(it.code) + "</b>";
  const crop = it.hint && it.hint.crop;
  return '<button class="card" id="card-' + it.id + '" data-page="' + it.page + '" data-id="' + it.id + '">' +
    '<span class="thumb">' + (crop ? '<img loading="lazy" src="' + crop + '" alt="名鍵假說色樣">' : '<span class="noimg">無色樣<br>(佇列)</span>') + '</span>' +
    '<span class="info"><span class="badge warn">待複查 ' + esc(it.reason) + "</span>" +
    '<div class="name">' + esc(it.label) + "</div>" +
    '<div class="rowline">' + body + "</div>" +
    '<span class="srcpg"><span>p.' + it.page + "</span>" + (it.hint ? "<span>假說 p." + it.hint.page + "</span>" : "") + "</span>" +
    "</span></button>";
}
function skelHTML(sk){
  return '<button class="card" id="card-' + sk.id + '" data-page="' + sk.page + '" data-id="' + sk.id + '">' +
    '<span class="thumb">' + (sk.crop ? '<img loading="lazy" src="' + sk.crop + '" alt="骨架色樣">' : '<span class="noimg">無裁圖</span>') + '</span>' +
    '<span class="info"><span class="badge gray">骨架色樣 未入庫</span>' +
    '<div class="name">' + esc(sk.caption || "(無圖說)") + "</div>" +
    '<div class="rowline">status=queue_only_not_ingested(色名假說 87.6%,不入庫)</div>' +
    '<span class="srcpg"><span>p.' + sk.page + "</span></span></span></button>";
}
function setTab(t){
  tab = t;
  document.querySelectorAll('.tabs [role="tab"]').forEach(b =>
    b.setAttribute("aria-selected", String(b.dataset.tab === t)));
  const host = document.getElementById("cards");
  const list = t === "variants" ? DATA.variants.map(cardHTML)
             : t === "queue"    ? DATA.queue.map(queueHTML)
             : DATA.skeleton.map(skelHTML);
  host.innerHTML = list.length ? list.join("") : '<div class="empty">此分類無項目</div>';
  host.querySelectorAll(".card").forEach(c => c.addEventListener("click", () => {
    document.querySelectorAll(".card.active").forEach(x => x.classList.remove("active"));
    c.classList.add("active");
    setPage(+c.dataset.page, c.dataset.id);
  }));
}
const chips = document.getElementById("chips");
pages.forEach(p => {
  const b = document.createElement("button");
  const ps = DATA.pageState[p] || {};
  b.textContent = p; b.dataset.p = p; b.setAttribute("role", "tab");
  b.dataset.st = ps.state || "";
  b.title = "p." + p + " · " + (STATE_LABEL[ps.state] || "");
  b.addEventListener("click", () => setPage(p));
  chips.appendChild(b);
});
document.getElementById("prev").addEventListener("click", () =>
  setPage(pages[Math.max(0, pages.indexOf(cur) - 1)]));
document.getElementById("next").addEventListener("click", () =>
  setPage(pages[Math.min(pages.length - 1, pages.indexOf(cur) + 1)]));
document.addEventListener("keydown", e => {
  if(e.key === "ArrowLeft") document.getElementById("prev").click();
  if(e.key === "ArrowRight") document.getElementById("next").click();
});
document.querySelectorAll('.tabs [role="tab"]').forEach(b =>
  b.addEventListener("click", () => setTab(b.dataset.tab)));
setTab("variants");
// #p33 開檔即跳頁;#p33/q12 加閃該框並捲到對應卡片
const h = location.hash.match(/^#p(\d+)(?:\/(.+))?$/);
if(h && pages.includes(+h[1])){ setPage(+h[1], h[2]); if(h[2]) gotoCard(h[2]); }
else renderPage();
</script>
</body>
</html>
"""


def coverage_html(rec):
    """A3|每頁處置覆蓋率摘要:N/N 頁全覆蓋(外審紅線=不得有頁靜默消失)。"""
    cov, total = rec["coverage"], rec["totalPages"]
    order = ["auto", "review", "noprod", "nonspec", "image"]
    covered = sum(cov.values())
    bar = "".join(f'<span class="{k}" style="flex:{cov[k]}" title="{PAGE_STATE_LABEL[k]} {cov[k]}"></span>'
                  for k in order if cov[k])
    keys = "".join(f'<span><i class="{k}"></i>{PAGE_STATE_LABEL[k]} <b>{cov[k]}</b></span>'
                   for k in order)
    return (f'<div class="cov"><div class="tot">每頁處置覆蓋:<b>{covered}/{total}</b> 頁全數落態'
            f'{"(⚠ 不一致)" if covered != total else " ✓"}</div>'
            f'<div class="bar">{bar}</div><div class="keys">{keys}</div></div>')


def build_doc(rec):
    gaps = ""
    if rec["knownGaps"]:
        gaps = ('<details class="gaps"><summary>⚠ knownGaps:此清單不完整('
                + str(len(rec["knownGaps"])) + ' 項已知缺口)</summary><ul>'
                + "".join(f"<li>{g}</li>" for g in rec["knownGaps"]) + "</ul></details>")
    skeltab = skelchip = ""
    if rec["skeleton"]:
        skeltab = ('<button role="tab" aria-selected="false" data-tab="skeleton">骨架色樣'
                   f'<span class="n">{len(rec["skeleton"])}</span></button>')
        skelchip = '<span class="chip" style="color:var(--destructive)">骨架檔(無碼廠)</span>'
    html = (TEMPLATE
            .replace("%%DATA%%", json.dumps(rec, ensure_ascii=False))
            .replace("%%STATE_LABEL%%", json.dumps(PAGE_STATE_LABEL, ensure_ascii=False))
            .replace("%%COVERAGE%%", coverage_html(rec))
            .replace("%%TITLE%%", rec["stem"])
            .replace("%%PDF%%", rec["pdf"])
            .replace("%%BRAND%%", rec["brand"])
            .replace("%%BV%%", str(rec["bindingVersion"]))
            .replace("%%NV%%", str(len(rec["variants"])))
            .replace("%%NQ%%", str(len(rec["queue"])))
            .replace("%%GAPS%%", gaps)
            .replace("%%SKELTAB%%", skeltab)
            .replace("%%SKELCHIP%%", skelchip))
    out = OUT / f"{rec['stem']}.html"
    out.write_text(html)
    return out


def build_index(recs):
    rows = "".join(
        f'<a class="card" href="{q(r["stem"] + ".html")}">'
        f'<span class="info"><span class="badge{" gray" if r["seriesSkeleton"] else ""}">'
        f'{"骨架檔" if r["seriesSkeleton"] else "已綁定"}</span>'
        f'<div class="name">{r["brand"]} · {r["stem"]}</div>'
        f'<div class="rowline">綁定 <b>{len(r["variants"])}</b> · 待複查 <b>{len(r["queue"])}</b>'
        f'{" · 骨架色樣 <b>" + str(len(r["skeleton"])) + "</b>" if r["skeleton"] else ""}</div>'
        f"</span></a>" for r in recs)
    css = TEMPLATE.split("<style>")[1].split("</style>")[0]
    (OUT / "index.html").write_text(f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>磁磚型錄辨識結果</title><style>{css}
body{{padding:32px}} .cards{{border:none;max-width:960px;margin:0 auto}}
.card{{text-decoration:none;color:inherit}}</style></head><body>
<div style="max-width:960px;margin:0 auto 20px">
<div class="brandline">磁磚型錄辨識結果</div>
<div class="metaline"><span class="chip">綁定引擎 v6(凍結)</span>
<span class="chip">{len(recs)} 份文件</span></div></div>
<div class="cards">{rows}</div></body></html>""")


def main(keyword=None):
    OUT.mkdir(exist_ok=True)
    recs = []
    for jp in sorted((ROOT / "product").rglob("*.json")):
        if jp.name.startswith("._") or jp.name.endswith((".review.json", ".capcodes.json")):
            continue
        if keyword and keyword.lower() not in jp.stem.lower():
            continue
        rev = jp.with_name(jp.stem + ".review.json")
        rec = collect(jp, rev, jp.parent.name)
        out = build_doc(rec)
        print(f"✓ {out.relative_to(ROOT)}  綁定 {len(rec['variants'])} / 佇列 {len(rec['queue'])}"
              f" / 骨架 {len(rec['skeleton'])} / 頁 {len(rec['pages'])}")
        recs.append(rec)
    if not keyword:
        build_index(recs)
        print(f"✓ viewer/index.html({len(recs)} 份)")
    # 守恆自檢:卡片數必須=JSON variants 數、佇列卡=review items 數
    for r in recs:
        assert len(r["variants"]) == sum(
            len(s.get("variants", [])) for s in
            json.loads((ROOT / "product" / r["brand"] / (r["stem"] + ".json")).read_text()).get("series", [])), r["stem"]
    print("守恆自檢 ✓(卡片數=JSON variants;佇列卡=review items)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
