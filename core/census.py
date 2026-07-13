#!/usr/bin/env python3
"""M0 §0.1 corpus 普查(implement.md v2.1)。

    python3 census.py <PDF資料夾> [out.csv]
    python3 census.py --selftest
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import fitz  # ponytail: PyMuPDF(AGPL)——內部普查腳本不分發,見 PROMPT.md 慣例

# 多制尺寸 token:60x120 / 600x600mm / 60×60 / 18,2x21 / 12"x24"(鐵律:多制,不偏單一樣本族群)
SIZE_RE = re.compile(
    r'\b\d{1,4}(?:[.,]\d{1,2})?\s*[x×]\s*\d{1,4}(?:[.,]\d{1,2})?\s*(?:cm|mm)?(?=\b|")', re.I
)
TOKEN_RE = re.compile(r"\b[A-Z0-9]{3,8}\b")

FIELDS = [
    "file", "pages", "text_pages", "has_text_layer",
    "images_total", "img_px_median", "img_px_max",
    "vector_fill_rects", "size_hits", "code_tokens_repeated",
    "top_codes", "likely_no_code", "spec_signal_pages",
]


def census_doc(path, root=None):
    doc = fitz.open(path)
    n_pages = doc.page_count
    text_pages = images = vec_rects = size_hits = 0
    img_px, codes, spec_pages = [], Counter(), []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            text_pages += 1
        hits = len(SIZE_RE.findall(text))
        size_hits += hits
        if hits >= 3:  # ponytail: 粗訊號夠用,精分類是 Stage 1 的事
            spec_pages.append(i + 1)
        # 代碼候選 = 含數字的短 token,排除純數字(尺寸/頁碼/年份)
        codes.update(t for t in TOKEN_RE.findall(text)
                     if any(c.isdigit() for c in t) and not t.isdigit())
        for info in page.get_image_info():
            images += 1
            img_px.append(max(info["width"], info["height"]))
        vec_rects += sum(1 for d in page.get_drawings()
                         if d.get("fill") and d["rect"].width > 5 and d["rect"].height > 5)
    doc.close()
    repeated = [t for t, n in codes.most_common() if n >= 3]
    img_px.sort()
    return {
        "file": str(Path(path).relative_to(root)) if root else Path(path).name,  # 帶廠商子資料夾
        "pages": n_pages,
        "text_pages": text_pages,
        "has_text_layer": text_pages > 0,
        "images_total": images,
        "img_px_median": img_px[len(img_px) // 2] if img_px else 0,
        "img_px_max": img_px[-1] if img_px else 0,
        "vector_fill_rects": vec_rects,
        "size_hits": size_hits,
        "code_tokens_repeated": len(repeated),
        "top_codes": " ".join(repeated[:5]),
        "likely_no_code": not repeated,
        "spec_signal_pages": " ".join(map(str, spec_pages)),
    }


def main(pdf_dir, out_csv="output/census.csv"):
    rows = []
    for pdf in sorted(Path(pdf_dir).rglob("*.pdf")):
        if pdf.name.startswith("._"):  # macOS metadata on FAT
            continue
        try:
            rows.append(census_doc(pdf, root=pdf_dir))
        except Exception as e:  # 損毀/加密檔也是普查要記的事實,不中斷
            rows.append({f: "" for f in FIELDS} | {"file": pdf.name, "top_codes": f"ERROR: {e}"})
        print(rows[-1]["file"], "OK" if rows[-1]["pages"] != "" else "ERROR")
    Path(out_csv).parent.mkdir(exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} PDFs -> {out_csv}")


def selftest():
    import tempfile
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((72, 72), "MC1G 60x120  MC1G 30×60  MC1G 18,2x21 Rett.")
    p2 = doc.new_page()
    p2.draw_rect(fitz.Rect(50, 50, 150, 150), fill=(0.8, 0.2, 0.2))
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 40))
    pix.clear_with(200)
    p2.insert_image(fitz.Rect(200, 50, 240, 90), pixmap=pix)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        doc.save(tmp.name)
    r = census_doc(tmp.name)
    assert r["has_text_layer"] and r["text_pages"] == 1, r
    assert r["size_hits"] >= 3, r
    assert r["top_codes"].startswith("MC1G") and not r["likely_no_code"], r
    assert r["images_total"] == 1 and r["vector_fill_rects"] >= 1, r
    assert r["spec_signal_pages"] == "1", r
    print("selftest OK:", r)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
    elif len(sys.argv) > 1:
        main(*sys.argv[1:3])
    else:
        sys.exit(__doc__)
