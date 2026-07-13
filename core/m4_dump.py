#!/usr/bin/env python3
"""M4/M5 GT dump:抽樣頁各版本的色樣、code 指派、尺寸關聯 + name_bind 目標 + overlay。

    python3 core/m4_dump.py <corpus_dir> <vers 如 4,5,6> Vendor:docprefix:PAGE ...

m3_dump 的 M4 版(PROMPT 必辦:name_bind 目標寫進 JSON):
- corpus/版本組參數化(M4 當時=3,4 輸出 output/m4_gt;M5 打包驗收=4,5,6 輸出 m5_gt)。
- 逐 code 記 name_sw=(page,sw)|None(M4-ID 色名救援目標,含頁級閘門)。
- v5+:codes_doc 用清洗後候選(junk 分流);v6:icon_sus 降級碼標 demoted。
- overlay 碼框:藍=x對齊、綠=name_bound、橘=綁上非對齊、紫=孤兒、紅=v6 降級;
  標籤 s<id>|<尺寸>,F=far,D=降級,n<page>:<sw>=色名目標。
"""
import json
import sys
from pathlib import Path

import fitz

from census import SIZE_RE
from m1_scan import norm
from m2_scan import build_vocabs, code_candidates
from m3_scan import (doc_icon_stats, doc_name_index, fold_x, icon_sus, name_bind,
                     page_good_names, page_sizes, row_size)
from spike_geom import assign_words, extract_swatches

OUT = Path("output/m5_gt")


def find_pdf(corpus, vendor, prefix):
    hits = [p for p in Path(corpus, vendor).glob("*.pdf")
            if not p.name.startswith("._") and p.name.startswith(prefix)]
    assert len(hits) == 1, (corpus, vendor, prefix, hits)
    return hits[0]


def dump_version(pdf, pageno, ver, codes_doc, alpha_vocab, tag, name_ctx=None, icon_ctx=None):
    name_idx, aligned_doc = name_ctx if name_ctx else (None, set())
    doc = fitz.open(pdf)
    page = doc[pageno - 1]
    sws = extract_swatches(page, version=3 if ver >= 3 else 1)
    sus = {i for i, r in enumerate(sws)
           if ver >= 6 and icon_ctx and icon_sus(r, icon_ctx)}
    ph = page.rect.height
    words = page.get_text("words")
    sizes = page_sizes(words, ver)
    fold = fold_x(page)
    sw_words = {i: [] for i in range(len(sws))}
    codes = []
    for w, i, d in assign_words(page, sws, ver):
        if i is not None:
            sw_words[i].append(w)
        if norm(w[4]) not in codes_doc:
            continue
        cx = (w[0] + w[2]) / 2
        ok_x = i is not None and sws[i].x0 - 2 <= cx <= sws[i].x1 + 2
        codes.append({
            "code": w[4], "bbox": [round(v, 1) for v in w[:4]], "sw": i,
            "dist": round(d, 1), "_w": w,
            "aligned": ok_x and i not in sus,
            "demoted": ok_x and i in sus,
            "far": i is not None and d > max(2 * sws[i].height, 0.15 * ph),
            "size": row_size(sizes, w, ver, fold), "name_sw": None})
    n_codes, aligned = len(codes), sum(e["aligned"] for e in codes)
    if (ver >= 4 and name_idx is not None
            and n_codes >= 5 and aligned <= 0.2 * n_codes):  # scan_page 頁級閘門
        good = page_good_names(words, codes_doc, alpha_vocab, fold)
        for e in codes:
            if not e["aligned"] and not e["demoted"] and norm(e["code"]) not in aligned_doc:
                t = name_bind(e["_w"], words, name_idx, alpha_vocab, fold, good)
                if t is not None:
                    e["name_sw"] = [t[0] + 1, t[1]]  # 1-based 頁碼
    for e in codes:
        del e["_w"]
    sh = page.new_shape()
    for i, r in enumerate(sws):
        c = (0.8, 0, 0) if i in sus else (1, 0, 0)
        sh.draw_rect(r)
        sh.finish(color=c, width=2 if i in sus else 1)
        sh.insert_text(fitz.Point(r.x0 + 1, r.y0 + 8),
                       str(i) + ("!" if i in sus else ""), color=c, fontsize=7)
    for e in codes:
        r = fitz.Rect(e["bbox"])
        col = (1, 0, 0) if e["demoted"] else \
            ((0, 0, 1) if e["aligned"] else (1, 0.5, 0)) if e["sw"] is not None \
            else ((0, 0.6, 0) if e["name_sw"] else (0.5, 0, 0.8))
        sh.draw_rect(r)
        sh.finish(color=col, width=0.8)
        lbl = ("O" if e["sw"] is None else f"s{e['sw']}" + ("F" if e["far"] else "")
               + ("D" if e["demoted"] else "")) \
              + (f"n{e['name_sw'][0]}:{e['name_sw'][1]}" if e["name_sw"] else "") \
              + (f"|{e['size']}" if e["size"] else "")
        sh.insert_text(fitz.Point(r.x1 + 1, r.y1 + 2), lbl, color=col, fontsize=6)
    sh.commit()
    page.get_pixmap(dpi=130).save(OUT / f"{tag}_v{ver}.png")
    sw_text = {i: " ".join(w[4] for w in sorted(sw_words[i], key=lambda w: (round(w[1]), w[0])))[:150]
               for i in sw_words}
    doc.close()
    return {"swatches": [[round(v, 1) for v in r] for r in sws],
            "codes": codes, "sw_text": sw_text}


def doc_ctx(pdf, ver, code_vocab, alpha_vocab):
    """per (pdf, version) 的 codes_doc / name_ctx / icon_ctx(v5+ 候選清洗、v6 icon)。"""
    doc = fitz.open(pdf)
    spec = [p for p in doc if len(SIZE_RE.findall(p.get_text())) >= 3]
    if ver >= 5:
        codes_doc, _ = code_candidates(doc, code_vocab, len(spec), ver,
                                       alpha_vocab)  # v8:停用詞補充(v≤7 不用)
    else:
        codes_doc = code_candidates(doc, code_vocab, len(spec))
    name_ctx = doc_name_index(spec, codes_doc, alpha_vocab, ver) if ver >= 4 else None
    icon_ctx = doc_icon_stats(spec, ver) if ver >= 6 else None  # M5-2b 版本閘鏡射
    return codes_doc, name_ctx, icon_ctx


def main(corpus, vers, args):
    versions = [int(v) for v in vers.split(",")]
    pages = [tuple(a.split(":")[:2]) + (int(a.split(":")[2]),) for a in args]
    OUT.mkdir(parents=True, exist_ok=True)
    code_vocab, alpha_vocab = build_vocabs()
    ctx_cache = {}
    for vendor, prefix, pageno in pages:
        pdf = find_pdf(corpus, vendor, prefix)
        tag = f"{vendor}_{prefix.split()[0].replace('-','')[:10]}_p{pageno}"
        out = {"vendor": vendor, "pdf": pdf.name, "page": pageno}
        stat = []
        for ver in versions:
            if (pdf, ver) not in ctx_cache:
                ctx_cache[(pdf, ver)] = doc_ctx(pdf, ver, code_vocab, alpha_vocab)
            codes_doc, name_ctx, icon_ctx = ctx_cache[(pdf, ver)]
            out[f"v{ver}"] = dump_version(pdf, pageno, ver, codes_doc, alpha_vocab,
                                          tag, name_ctx, icon_ctx)
            c = out[f"v{ver}"]["codes"]
            stat.append(f"v{ver}: codes={len(c)} al={sum(e['aligned'] for e in c)} "
                        f"dm={sum(e['demoted'] for e in c)} nb={sum(bool(e['name_sw']) for e in c)}")
        (OUT / f"{tag}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
        print(f"{tag}: " + "  ".join(stat), flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
