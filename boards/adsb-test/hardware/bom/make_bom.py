#!/usr/bin/env python3
"""Build the ADSB_Test bill of materials with suppliers, order codes and links.

    python boards/adsb-test/hardware/bom/make_bom.py [--boards N]

Reads the schematic netlist (exported with kicad-cli) and parts.csv (manufacturer part
numbers + supplier codes, checked on DigiKey/LCSC on the date in its stock column).
0805 resistors are mapped by rule to YAGEO RC0805 (1 %), whose DigiKey codes follow
311-<value>CRCT-ND (checked for 0R, 100R, 4.7k, 10k, 10M).

Writes next to this script:
  ADSB_Test_BOM.csv       full BOM, one line per part type
  ADSB_Test_BOM.md        readable version with order links and totals
  digikey_bom_upload.csv  DigiKey BOM Manager / cart upload (fitted DigiKey lines, x boards + spares)
"""
import argparse
import collections
import csv
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCH = ROOT / "boards/adsb-test/hardware/kicad/ADSB_Test.kicad_sch"
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
NO_PART = {"TestPoint", "MountingHole_Pad", "SolderJumper_2_Open"}     # copper features, nothing to buy


def dk_link(mpn):
    return f"https://www.digikey.com/en/products/result?keywords={quote(mpn)}"


def link_for(supplier, code, mpn):
    if code.startswith("http"):
        return code
    if supplier == "LCSC" and code:
        return f"https://www.lcsc.com/product-detail/{code}.html"
    return dk_link(mpn)


def yageo_0805(value):
    """'12.1k 1%' -> ('RC0805FR-0712K1L', '311-12.1KCRCT-ND'); 0R -> jumper."""
    v = value.split()[0]
    if v == "0R":
        return "RC0805JR-070RL", "311-0.0ARCT-ND"
    m = re.fullmatch(r"([\d.]+)([RkM])", v)
    s, unit = m.group(1), m.group(2)
    num = float(s)
    letter = {"R": "R", "k": "K", "M": "M"}[unit]
    code = s.replace(".", letter) if "." in s else s + letter            # 4.7k -> 4K7, 49.9 -> 49R9, 10k -> 10K
    sig = f"{num:.2f}" if num < 10 else f"{num:.1f}" if num < 100 else f"{num:.0f}"   # 3 significant figures
    return f"RC0805FR-07{code}L", f"311-{sig}{'' if unit == 'R' else letter}CRCT-ND"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", type=int, default=1, help="boards to build (upload quantities)")
    args = ap.parse_args()

    net = HERE / "ADSB_Test.netlist.xml"
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", str(net), str(SCH)],
                   check=True, capture_output=True)
    root = ET.parse(net).getroot()
    net.unlink()

    parts = list(csv.DictReader((HERE / "parts.csv").open(encoding="utf-8")))

    groups = collections.defaultdict(list)
    for c in root.find("components").findall("comp"):
        lib = c.find("libsource").get("part")
        val = c.findtext("value")
        fp = (c.findtext("footprint") or "").split(":")[-1]
        dnp = any(p.get("name") == "dnp" for p in c.findall("property"))
        groups[(lib, val, fp, dnp)].append(c.get("ref"))

    def find_part(lib, val, fp):
        for p in parts:
            if p["lib"] == lib and p["value"] == val and (not p["footprint"] or p["footprint"] in fp):
                return p
        return None

    rows, unmatched = [], []
    for (lib, val, fp, dnp), refs in groups.items():
        if lib in NO_PART:
            continue
        refs.sort(key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))
        p = find_part(lib, val, fp)
        if p is None and lib == "R" and "0805" in fp:
            mpn, dk = yageo_0805(val)
            p = {"manufacturer": "YAGEO", "mpn": mpn, "supplier": "DigiKey", "supplier_pn": dk, "unit_usd": "0.10",
                 "stock_2026_10_12": "", "notes": "0805 1% (code by YAGEO pattern)" if "JR" not in mpn else "0805 jumper"}
        if p is None:
            unmatched.append((lib, val, fp, refs))
            p = {k: "" for k in ("manufacturer", "mpn", "supplier", "supplier_pn", "unit_usd", "stock_2026_10_12", "notes")}
        info = {k: v for k, v in p.items() if k not in ("lib", "value", "footprint")}
        rows.append(dict(qty=len(refs), refs=" ".join(refs), value=val, footprint=fp, dnp="DNP" if dnp else "", lib=lib,
                         **info))

    order = ["U", "Q", "D", "L", "FB", "Y", "J", "SW", "SH", "BT", "RS", "R", "C"]
    rows.sort(key=lambda r: (order.index(re.sub(r"\d", "", r["refs"].split()[0]))
                             if re.sub(r"\d", "", r["refs"].split()[0]) in order else 99, r["dnp"],
                             int(re.sub(r"\D", "", r["refs"].split()[0]) or 0)))

    fields = ["line", "qty", "refs", "value", "footprint", "dnp", "manufacturer", "mpn", "supplier", "supplier_pn",
              "order_link", "unit_usd", "ext_usd", "stock_2026_10_12", "notes"]
    total = 0.0
    for i, r in enumerate(rows, 1):
        r["line"] = i
        r["order_link"] = link_for(r["supplier"], r["supplier_pn"], r["mpn"]) if r["mpn"] else ""
        ext = float(r["unit_usd"]) * r["qty"] if r["unit_usd"] else 0.0
        r["ext_usd"] = f"{ext:.2f}" if r["unit_usd"] else ""
        if not r["dnp"]:
            total += ext
    with (HERE / "ADSB_Test_BOM.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # DigiKey upload: fitted lines with a DigiKey code; spares for cheap parts (lost/tombstoned when hand soldering)
    up = collections.OrderedDict()
    for r in rows:
        if r["dnp"] or r["supplier"] != "DigiKey" or not r["supplier_pn"]:
            continue
        n = r["qty"] * args.boards
        price = float(r["unit_usd"] or 0)
        if price <= 0.30:
            n += max(5, math.ceil(n * 0.2))
        elif price <= 1.00:
            n += 2
        key = r["supplier_pn"]
        if key in up:
            up[key][0] += n
            up[key][2] += " " + r["refs"]
        else:
            up[key] = [n, r["mpn"], r["refs"]]
    with (HERE / "digikey_bom_upload.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Quantity", "Digi-Key Part Number", "Manufacturer Part Number", "Customer Reference"])
        for pn, (n, mpn, refs) in up.items():
            w.writerow([n, pn, mpn, refs[:48]])

    md = ["# ADSB_Test Rev 1 — bill of materials", "",
          "Generated by [`make_bom.py`](make_bom.py) from the schematic and [`parts.csv`](parts.csv). "
          "Supplier codes, prices (USD, qty 1, cut tape) and stock were checked on DigiKey / LCSC on **2026-10-12**; "
          "check stock again before ordering. Test points, mounting holes and solder jumpers are copper on the PCB "
          "and are not listed. Order links open the supplier's page for that part number.", "",
          f"**Fitted parts, 1 board: about ${total:.0f}** (excluding the WT01P4C5-S1 module, the m1421 and the PCB).", "",
          "Upload [`digikey_bom_upload.csv`](digikey_bom_upload.csv) to DigiKey's BOM Manager (or *Add to cart → "
          f"upload*). It covers {args.boards} board(s) plus spares for the cheap parts, and leaves out the DNP parts.", "",
          "| # | Qty | Refs | Value | Manufacturer | MPN | Supplier | Code | $ each | Stock | Notes |",
          "|---|-----|------|-------|--------------|-----|----------|------|--------|-------|-------|"]
    for r in rows:
        code = f"[{r['supplier_pn'] or 'search'}]({r['order_link']})" if r["order_link"] else ""
        if r["supplier_pn"].startswith("http"):
            code = f"[product page]({r['order_link']})"
        refs = r["refs"] if len(r["refs"]) <= 60 else r["refs"][:57] + "…"
        md.append(f"| {r['line']} | {r['qty']} | {refs} | {r['value']}{' **(DNP)**' if r['dnp'] else ''} | "
                  f"{r['manufacturer']} | {r['mpn']} | {r['supplier']} | {code} | {r['unit_usd']} | "
                  f"{r['stock_2026_10_12']} | {r['notes']} |")
    md += ["", "## Not on the schematic (order separately)", "",
           "| Item | Notes |", "|------|-------|",
           "| PCB + stencil | PCBWay, 4 layers, 1.6 mm, ENIG, impedance control (see docs/pcb-manufacturing.md) |",
           "| 7\" panel + touch | Same panel as the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (EK79007 + GT911) |",
           "| 2 × 18650 + 2S BMS pack with NTC | JST-XH 3-pin lead to J301 (XHP-3 housing + SXH-001T-P0.6 crimps) |",
           "| Wi-Fi antenna | U.FL (IPEX MHF1) pigtail + 2.4/5 GHz antenna for the WT01P4C5-S1 |",
           "| GNSS active antenna | SMA, 3.3 V |",
           "| 1090/978 MHz antenna | SMA |",
           "| Optional: Wireless-Tag WTDKP4C5-S1 dev board, ADSBee 1421 Dev Kit, DS3231M and LAN8720A breakouts | Phase 1 testing |"]
    if unmatched:
        md += ["", "## Lines without a part number yet", ""] + [f"- {l} {v} ({f}): {' '.join(r)}" for l, v, f, r in unmatched]
    (HERE / "ADSB_Test_BOM.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(rows)} lines, ~${total:.2f} fitted per board, {len(up)} DigiKey upload lines, {len(unmatched)} unmatched")
    for u in unmatched:
        print("  UNMATCHED", u)


if __name__ == "__main__":
    main()
