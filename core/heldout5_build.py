#!/usr/bin/env python3
"""heldout5 建批:BFS 第 5 份起 + md5 遞補(比對既有四批全部檔案)+ 剩餘池盤點。

    python3 heldout5_build.py list       # 只盤點:每廠商池量/已用/剩餘(不下載)
    python3 heldout5_build.py fetch      # 下載選件到 catalogs5/

程序(照 heldout4 宣告):每廠商 BFS 順序收 PDF,md5(Drive md5Checksum,零下載
比對)與 USED_DIRS 任一批任一檔重複 → 順位遞補;池內互重(同 md5 多份)只算
一份;池竭則剔除廠商。文件級隔離由 md5 全域比對保證。
# ponytail: md5 用 Drive API 的 md5Checksum 欄位,不下載就能逐位級判重
"""
import hashlib
import sys
from pathlib import Path

from googleapiclient.discovery import build

from drive_sync import creds, list_children

ROOT = Path(__file__).parent.parent  # 檔案住 core/,專案根=上一層(2026-07-09 整理,唯一碼改動)
USED_DIRS = ["catalogs", "catalogs2", "catalogs3", "catalogs4", "catalogs5", "catalogs6"]
DEST = ROOT / "catalogs5"
# catalogs7 頁型遞補換下檔(2026-07-11 使用者裁決:fetch+核心訊號掃描=燒,
# 不留程度辯論;檔已移除、md5 在 output/catalogs7_DECLARATION.md 附錄,
# 永久喪失 held-out 資格、非綁定用途不禁):
BURNED_MD5 = {
    "b2e088a20394507785c524f9c73f4c7b": "catalogs7換下/FMG balance-665",
    "7fef19b4ffc82a8d03eed3f3ee9f5830": "catalogs7換下/FMG highway_maxfine-669",
    "a0e606a29592cc0616f0ceed35ba1547": "catalogs7換下/Provenza Karman 2023.03b",
    "d685b0804a28c325bab2eccdb967fe6b": "catalogs7換下/Provenza Gesso 2026.02",
    "d9b2c453875e1ccc41887eb012bc41ba": "catalogs7換下/Provenza AlterEgo 2024.04",
}


def local_md5s():
    used = dict(BURNED_MD5)
    for d in USED_DIRS:
        for p in (ROOT / d).rglob("*.pdf"):
            if p.name.startswith("._"):
                continue
            used[hashlib.md5(p.read_bytes()).hexdigest()] = f"{d}/{p.relative_to(ROOT / d)}"
    return used


def find_root(svc):
    """按名稱找 Eonian 2026(共用雲端硬碟或資料夾)。"""
    r = svc.drives().list(pageSize=100).execute().get("drives", [])
    for dr in r:
        if "eonian" in dr["name"].lower():
            return dr["id"]
    r = svc.files().list(
        q="name contains 'Eonian' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id,name)", supportsAllDrives=True, includeItemsFromAllDrives=True,
        corpora="allDrives").execute()["files"]
    assert r, "找不到 Eonian 2026"
    return r[0]["id"]


def vendor_pools(svc, root_id):
    """{vendor: [pdf(id,name,size,md5) BFS 順序,池內同 md5 去重]}"""
    pools = {}
    for top in list_children(svc, root_id):
        if top["mimeType"] != "application/vnd.google-apps.folder":
            continue
        queue, seen, pool = [top["id"]], set(), []
        while queue:
            kids = list_children_md5(svc, queue.pop(0))
            for f in kids:
                if f["mimeType"] == "application/pdf" and f.get("md5Checksum") not in seen:
                    seen.add(f.get("md5Checksum"))
                    pool.append(f)
            queue += [f["id"] for f in kids if f["mimeType"] == "application/vnd.google-apps.folder"]
        pools[top["name"].strip()] = pool
    return pools


def list_children_md5(svc, fid):
    files, page = [], None
    while True:
        r = svc.files().list(
            q=f"'{fid}' in parents and trashed=false",
            fields="nextPageToken,files(id,name,mimeType,size,md5Checksum)",
            pageSize=1000, pageToken=page,
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files += r["files"]
        page = r.get("nextPageToken")
        if not page:
            return files


def plan(pools, used):
    """回傳 (選件 {vendor: pdf}, 盤點列)。選件=BFS 首個未用 md5;盤點=池量/已用/剩餘。"""
    picks, rows = {}, []
    for vendor, pool in sorted(pools.items()):
        fresh = [f for f in pool if f.get("md5Checksum") not in used]
        n_used = len(pool) - len(fresh)
        if fresh:
            picks[vendor] = fresh[0]
        rows.append((vendor, len(pool), n_used, len(fresh),
                     fresh[0]["name"] if fresh else "—(池竭)"))
    return picks, rows


def main(mode):
    svc = build("drive", "v3", credentials=creds())
    used = local_md5s()
    print(f"已用檔案({len(USED_DIRS)} 批,md5 逐位)={len(used)}")
    pools = vendor_pools(svc, find_root(svc))
    picks, rows = plan(pools, used)
    print(f"\n{'廠商':<14}{'池(distinct md5)':>16}{'已用':>6}{'剩餘':>6}  本批選件")
    for v, tot, u, rem, pick in rows:
        print(f"{v:<14}{tot:>16}{u:>6}{rem:>6}  {pick}")
    print(f"\n剩餘池總量={sum(r[3] for r in rows)};本批選件後再撐:"
          f"{min_batches(rows)} 批(以「每批須 ≥6 家有件」估)")
    if mode == "fetch":
        DEST.mkdir(exist_ok=True)
        for vendor, f in picks.items():
            out = DEST / vendor / f["name"]
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.exists():
                continue
            from googleapiclient.http import MediaIoBaseDownload
            req = svc.files().get_media(fileId=f["id"])
            with open(out, "wb") as fh:
                dl = MediaIoBaseDownload(fh, req, chunksize=8 * 1024 * 1024)
                done = False
                while not done:
                    _, done = dl.next_chunk()
            got = hashlib.md5(out.read_bytes()).hexdigest()
            assert got == f["md5Checksum"], (vendor, f["name"], "md5 mismatch after download")
            print(f"fetched {vendor}/{f['name']} md5 ✓")
        # self-check:落地檔 md5 不得撞既有各批
        for p in DEST.rglob("*.pdf"):
            if p.name.startswith("._"):
                continue
            h = hashlib.md5(p.read_bytes()).hexdigest()
            assert h not in used, (str(p), "與既有批重複!", used.get(h))
        print(f"落地後 md5 全域複驗 ✓(與 {len(USED_DIRS)} 批零重複)")


def min_batches(rows, need=6):
    """還能建幾批:每輪每家扣 1(本批已扣),直到有件廠商 <need。"""
    rem = sorted((r[3] - (1 if r[3] else 0) for r in rows), reverse=True)
    n = 0
    while sum(1 for x in rem if x > 0) >= need:
        rem = [x - 1 for x in rem]
        n += 1
    return n


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("list", "fetch"):
        sys.exit(__doc__)
    main(sys.argv[1])
