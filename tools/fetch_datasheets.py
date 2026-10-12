#!/usr/bin/env python3
"""Download the reference documents listed in docs/datasheets.json.

Files go to datasheets/<category>/<id>.<ext> (git-ignored: vendor documents
are not redistributed in this public repo). A manifest with size, SHA-256 and
download date is written to datasheets/manifest.json, and docs/datasheets.md
(the committed index of links) is regenerated.

Usage:  python tools/fetch_datasheets.py [--only ID ...] [--index-only]
Only the Python standard library is used.
"""
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "docs" / "datasheets.json"
OUT = ROOT / "datasheets"
INDEX = ROOT / "docs" / "datasheets.md"
UA = "Mozilla/5.0 (board_bsp datasheet fetcher)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

MAGIC = {"pdf": b"%PDF", "zip": b"PK"}
BOARDS = {"ref": "Waveshare 7B", "adsb": "ADSB_Test", "superseded": "no longer used"}


def download(url):
    """urllib first; fall back to curl (browser UA, follows redirects) for sites that block Python."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        if data[:4] in (b"%PDF", b"PK\x03\x04"):
            return data
    except Exception:  # noqa: BLE001 - retry with curl below
        pass
    result = subprocess.run(
        ["curl", "-sSL", "--fail", "--max-time", "180", "-A", BROWSER_UA, url],
        capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip() or f"curl exit {result.returncode}")
    return result.stdout


def fetch(doc):
    ext = doc.get("ext", "pdf")
    dest = OUT / doc["category"] / f"{doc['id']}.{ext}"
    data = download(doc["url"])
    if not data.startswith(MAGIC.get(ext, b"")):
        raise ValueError(f"not a {ext.upper()} (got {data[:15]!r}); URL is probably a web page")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return {
        "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "fetched": datetime.date.today().isoformat(),
    }


def write_index(docs, manifest):
    lines = [
        "# Reference documents",
        "",
        "Datasheets and references for every part on the boards in this repo.",
        "Generated from [`datasheets.json`](datasheets.json) by",
        "[`tools/fetch_datasheets.py`](../tools/fetch_datasheets.py). **Don't edit by hand.**",
        "",
        "PDFs are downloaded locally into `datasheets/` (git-ignored: vendor documents are",
        "not redistributed in this public repo). Run `python tools/fetch_datasheets.py` to",
        "get them. \"Local\" shows whether the last run saved a copy.",
        "",
    ]
    cats = []
    for d in docs:
        if d["category"] not in cats:
            cats.append(d["category"])
    for cat in cats:
        lines += [f"## {cat}", "", "| Part | Document | Boards | Local |", "|------|----------|--------|-------|"]
        for d in docs:
            if d["category"] != cat:
                continue
            boards = ", ".join(BOARDS.get(b, b) for b in d.get("boards", []))
            if d["type"] == "link":
                local = "link only (open in a browser)" if d.get("manual") else "link only"
            elif d["id"] in manifest and "sha256" in manifest[d["id"]]:
                local = f"yes ({manifest[d['id']]['fetched']})"
            elif d.get("manual"):
                local = "no: site blocks scripts, save by hand"
            else:
                local = "no"
            lines.append(f"| {d['part']} | [{d['title']}]({d['url']}) | {boards} | {local} |")
        lines.append("")
    INDEX.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="document ids to fetch")
    ap.add_argument("--index-only", action="store_true", help="only regenerate docs/datasheets.md")
    args = ap.parse_args()

    docs = json.loads(LIST.read_text(encoding="utf-8"))["documents"]
    man_path = OUT / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}
    known = {d["id"] for d in docs}
    manifest = {k: v for k, v in manifest.items() if k in known}

    failed = []
    if not args.index_only:
        for d in docs:
            if d["type"] != "file" or (args.only and d["id"] not in args.only):
                continue
            local = OUT / d["category"] / f"{d['id']}.{d.get('ext', 'pdf')}"
            if d.get("manual") and local.exists() and local.read_bytes()[:2] in (b"%P", b"PK"):
                data = local.read_bytes()   # saved by hand: don't hammer a site that blocks scripts
                manifest[d["id"]] = {
                    "path": str(local.relative_to(ROOT)).replace("\\", "/"),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "fetched": "manual",
                }
                print(f"ok    {d['id']}  (saved by hand)")
                continue
            try:
                manifest[d["id"]] = fetch(d)
                print(f"ok    {d['id']}  ({manifest[d['id']]['bytes'] // 1024} KiB)")
            except Exception as e:  # noqa: BLE001 - report and continue
                manual = OUT / d["category"] / f"{d['id']}.{d.get('ext', 'pdf')}"
                if manual.exists() and manual.read_bytes()[:2] in (b"%P", b"PK"):
                    data = manual.read_bytes()
                    manifest[d["id"]] = {
                        "path": str(manual.relative_to(ROOT)).replace("\\", "/"),
                        "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "fetched": "manual",
                    }
                    print(f"ok    {d['id']}  (saved by hand)")
                    continue
                manifest[d["id"]] = {"error": str(e)[:200]}
                if d.get("manual"):
                    print(f"SKIP  {d['id']}: site blocks scripts; save by hand to {manual.relative_to(ROOT)}")
                    continue
                failed.append(d["id"])
                print(f"FAIL  {d['id']}: {e}")
        OUT.mkdir(exist_ok=True)
        man_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    write_index(docs, manifest)
    print(f"\n{len(failed)} failed" + (": " + ", ".join(failed) if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
