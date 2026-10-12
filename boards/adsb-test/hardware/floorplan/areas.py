#!/usr/bin/env python3
"""Courtyard size of every placed part, from the netlist + footprint libraries.

    from areas import parts            # list of dicts: ref, sheet, fp, w, h, dnp
"""
import re
import subprocess
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
KICAD = ROOT / "boards/adsb-test/hardware/kicad"
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
STD_FP = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
NO_PART = set()      # test pads and solder jumpers take board area too


@lru_cache(maxsize=None)
def courtyard(fp_id):
    """(w, h) of the F.CrtYd outline in mm (pads bbox + 0.5 mm if no courtyard)."""
    lib, name = fp_id.split(":", 1)
    path = (KICAD / "lib/ADSB_Test.pretty" if lib == "ADSB_Test" else STD_FP / f"{lib}.pretty") / f"{name}.kicad_mod"
    text = path.read_text(encoding="utf-8")
    xs, ys = [], []
    for m in re.finditer(r'\((fp_line|fp_rect|fp_poly|fp_circle|fp_arc)\b(.*?)\(layer "F\.CrtYd"\)', text, re.S):
        body = m.group(2)
        for x, y in re.findall(r"\((?:start|end|xy|mid|center) (-?[\d.]+) (-?[\d.]+)\)", body):
            xs.append(float(x))
            ys.append(float(y))
    if not xs:
        for m in re.finditer(r'\(pad .*?\(at (-?[\d.]+) (-?[\d.]+).*?\(size ([\d.]+) ([\d.]+)\)', text, re.S):
            x, y, w, h = map(float, m.groups())
            xs += [x - w / 2, x + w / 2]
            ys += [y - h / 2, y + h / 2]
        return (max(xs) - min(xs) + 0.5, max(ys) - min(ys) + 0.5)
    return (max(xs) - min(xs), max(ys) - min(ys))


def parts():
    net = HERE / "_netlist.xml"
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", str(net),
                    str(KICAD / "ADSB_Test.kicad_sch")], check=True, capture_output=True)
    root = ET.parse(net).getroot()
    net.unlink()
    out = []
    for c in root.find("components").findall("comp"):
        lib = c.find("libsource").get("part")
        if lib in NO_PART:
            continue
        fp = c.findtext("footprint") or ""
        sheet = c.find("sheetpath").get("names").strip("/") or "Top"
        dnp = any(p.get("name") == "dnp" for p in c.findall("property"))
        w, h = courtyard(fp)
        out.append(dict(ref=c.get("ref"), sheet=sheet, fp=fp, w=w, h=h, dnp=dnp, value=c.findtext("value")))
    return out


if __name__ == "__main__":
    import collections
    ps = parts()
    by = collections.defaultdict(float)
    for p in ps:
        by[p["sheet"]] += p["w"] * p["h"]
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f"{k:16s} {v:8.0f} mm2")
    print("total", round(sum(by.values())), "mm2; board 188 x 97 =", 188 * 97)
    big = sorted(ps, key=lambda p: -p["w"] * p["h"])[:25]
    for p in big:
        print(f'  {p["ref"]:7s} {p["w"]:5.1f} x {p["h"]:5.1f}  {p["fp"].split(":")[-1]}')
