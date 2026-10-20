#!/usr/bin/env python3
"""ADSB_Test block floorplan: does everything fit on the board?

    python boards/adsb-test/hardware/floorplan/floorplan.py

Viewed from the COMPONENT (bottom) side: the panel is bonded to the other side.
x = 0 is the digital-connector edge, x = W the RF edge; y = 0 is the top long edge.

For each zone the required area is
    sum(fixed big parts' courtyards) + K x sum(other parts' courtyards)
where K covers spacing and routing for hand assembly on 4 layers. RF can frames
count as an envelope for the parts under them. Writes floorplan.svg (+ .png if
PyMuPDF is available) and prints a utilisation table.
"""
import collections
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from areas import parts  # noqa: E402

W, H = 204.9, 140.0            # board, mm: panel 164.9 x 100 + 20 mm all round, Q28 (override: --size WxH)
K = 2.4                        # spacing + routing factor for small parts (hand soldering; 1.6 felt too tight)
FIXED = 1.15                   # factor for big parts (fan-out only)
BIG = 150.0                    # courtyard mm2 above which a part is "fixed"
HOLE_KEEPOUT = 3.5             # mm radius (M2.5 screw head + clearance)

# Edge connectors: (ref, edge, along-edge size, depth, label); spread evenly between the hole keep-outs
# Since 2026-10-20 the RF edge is on the LEFT (bottom view) and the digital edge on the RIGHT, the side nearer
# the module, so the digital runs are shorter and further from the RF.
EDGE_PARTS = [("J901", "R", 10.6, 8.9, "User USB-C"), ("J1001", "R", 10.6, 8.9, "Dev USB-C"),
              ("J1101", "R", 17.2, 16.3, "USB-A"), ("J801", "R", 19.0, 22.3, "RJ45"),
              ("J1501", "R", 13.7, 13.1, "microSD"), ("SW401", "R", 11.4, 9.4, "POWER"),
              ("SW603", "R", 9.6, 7.3, "SLEEP"),
              ("J1403", "L", 8.2, 14.9, "SMA 1090/978"),
              ("J1201", "L", 8.2, 14.9, "SMA GNSS")]
# Top (long) edge parts at a fixed x: (ref, centre x from the left (RF) edge, along, depth, label). The Wi-Fi
# RP-SMA sits here, well away from the 1090/978 and GNSS SMAs on the RF edge.
TOP_PARTS = [("J602", 96.0, 12.2, 7.5, "Wi-Fi")]   # pads 7.5 mm in, barrel overhangs the edge


PANEL_W, PANEL_H = 164.9, 100.0   # 7" panel outline (AliExpress 1024x600 MIPI drawing; Waveshare 164.28 x 99.17 lens)


def layout(w, h):
    """Zone rectangles for a w x h board with the panel centred on the other side (bottom view).
    RF column on the left edge; power band along the top (power-in at the digital end); the module stays right
    of centre between the panel-cable sockets; Dev UARTs/programmer and the display supplies left of it; the
    digital-edge column (Dev hub, Ethernet, USB host, storage) on the right; LA header along the bottom."""
    global W, H, HOLES, EDGE, BATTERY, FPC
    W, H = w, h
    x0p, y0p = (W - PANEL_W) / 2, (H - PANEL_H) / 2
    cx, cy = W / 2, H / 2
    HOLES = [(4, 4), (W - 4, 4), (4, H - 4), (W - 4, H - 4)]   # case screws in the board corners (outside the panel)
    EDGE = []
    for side in "LR":
        items = [e for e in EDGE_PARTS if e[1] == side]
        lo, hi = 4 + HOLE_KEEPOUT + 0.5, H - 4 - HOLE_KEEPOUT - 0.5        # between the corner holes
        gap = (hi - lo - sum(e[2] for e in items)) / (len(items) - 1)
        y = lo
        for ref, sd, along, depth, label in items:
            EDGE.append((ref, sd, y + along / 2, along, depth, label))
            y += along + gap
    for ref, cx_, along, depth, label in TOP_PARTS:
        EDGE.append((ref, "T", cx_, along, depth, label))
    top = y0p + 24                                         # power band (44 mm at the 20 mm border)
    rf1 = max(36.0, x0p + 20)                              # RF column: left edge .. rf1
    dig0 = W - 24                                          # digital-edge column: dig0 .. right edge
    mcu0, mcu1 = x0p + 86, x0p + 122                       # module at panel x 92-120 (gen_pcb.py)
    la_h = 16.0                                            # LA header strip along the bottom
    span = dig0 - rf1
    dev_h = 0.62 * (H - la_h - top)                        # Dev UARTs/programmer above the display supplies
    col = top + 0.75 * (H - top)                           # digital-edge column split
    # panel cable slots, measured on the Waveshare board (gen_pcb.py SLOTS_FRONT): LCD 74-96 mm, 42.6-45.6 mm
    # up; touch 34-42 mm, 49.6-52.6 mm up (front view from the panel's left edge)
    FPC = [("LCD FPC", W - x0p - 85.0, 22, y0p + PANEL_H - 44.08), ("Touch FPC", W - x0p - 38.0, 8, y0p + PANEL_H - 51.08)]
    BATTERY = (mcu0 + 2, y0p + 12, mcu0 + 42, y0p + 85)   # 2 x 18650 across the board, over the MCU area
    return {
        "Bucks + switches + monitors": (rf1, 0, rf1 + 0.48 * span, top, ["Power Rails", "Power Monitor"]),
        "Charger + RTC": (rf1 + 0.48 * span, 0, rf1 + 0.78 * span, top, ["Charger Battery", "RTC"]),
        "Power in + User UART": (rf1 + 0.78 * span, 0, dig0, top, ["Power Input", "User USB-C"]),
        "m1421 + RF (can 27.5)": (2, 0, rf1, H / 2, ["M1421"]),
        "GNSS (can 17.8)": (2, H / 2, rf1, H, ["GPS"]),
        "Dev UARTs + m1421 programmer": (rf1, top, mcu0, top + dev_h, ["Dev UARTs", "Dev m1421 Programmer"]),
        "Display supplies + LCD FPC": (rf1, top + dev_h, mcu0, H - la_h, ["Display Touch"]),
        "MCU module + touch FPC": (mcu0, top, mcu1, H - la_h, ["MCU Module"]),
        "LA header (along the bottom)": (rf1, H - la_h, mcu1, H, ["Test Debug"]),
        "Dev hub + Ethernet + USB host": (mcu1, top, dig0, col, ["Dev USB Hub", "Ethernet", "USB Host"]),
        "Storage + expander": (mcu1, col, dig0, H, ["Storage Misc"]),
    }


ZONES = layout(W, H)

TALL = {  # bottom-side height above the PCB, mm (datasheets / typical)
    "J801": 13.5, "J301": 9.8, "J1601": 9.1, "J1101": 7.0, "C1103": 6.0, "SH1401": 5.1, "SH1201": 5.1,
    "SW601": 4.3, "SW602": 4.3, "SW1001": 4.3, "U601": 3.7, "J1201": 3.2, "J1403": 3.2,
}
# 2 x 18650 side by side behind the board (each 18.6 x 65 mm + holder), case depth budget ~ 4 mm under them
BATTERY_CLEARANCE = 4.0


def main(ps=None, quiet=False):
    ps = ps or parts()
    edge_refs = {e[0] for e in EDGE}
    need = collections.defaultdict(float)
    detail = collections.defaultdict(list)
    for p in ps:
        if p["ref"] in edge_refs:
            continue
        a = p["w"] * p["h"]
        if p["ref"].startswith("SH"):           # can frame = envelope, parts under it already counted
            continue
        f = FIXED if a > BIG else K
        need[p["sheet"]] += a * f
        if a > BIG:
            detail[p["sheet"]].append(p["ref"])
    # cans: area of the frame minus what is inside is free; add the envelope surplus
    for p in ps:
        if p["ref"] == "SH1401":
            inner = 17.2 * 24.5 * FIXED
            need["M1421"] += max(0.0, p["w"] * p["h"] - inner)
        if p["ref"] == "SH1201":
            inner = 11.8 * 10.6 * FIXED
            need["GPS"] += max(0.0, p["w"] * p["h"] - inner)

    rows, issues = [], []
    used = set()
    for name, (x0, y0, x1, y1, sheets) in ZONES.items():
        area = (x1 - x0) * (y1 - y0)
        for hx, hy in HOLES:
            if x0 - HOLE_KEEPOUT < hx < x1 + HOLE_KEEPOUT and y0 - HOLE_KEEPOUT < hy < y1 + HOLE_KEEPOUT:
                area -= 3.14159 * HOLE_KEEPOUT ** 2 / 2       # roughly half a keep-out inside the zone
        req = sum(need[s] for s in sheets)
        used.update(sheets)
        rows.append((name, x0, y0, x1, y1, area, req, sheets))
        if req > area * 0.9:
            issues.append(f"Zone '{name}' at {100 * req / area:.0f} %")
    missing = set(need) - used
    if missing:
        issues.append(f"Sheets without a zone: {sorted(missing)}")

    # fixed parts that must physically fit their zone (largest dimension check)
    sizes = {p["ref"]: (p["w"], p["h"], p["sheet"]) for p in ps}
    for name, x0, y0, x1, y1, area, req, sheets in rows:
        for s in sheets:
            for ref in detail[s]:
                w, h, _ = sizes[ref]
                zw, zh = x1 - x0, y1 - y0
                if not ((w <= zw and h <= zh) or (h <= zw and w <= zh)):
                    issues.append(f"{ref} ({w:.1f} x {h:.1f}) does not fit zone '{name}' ({zw:.0f} x {zh:.0f})")

    # edge budget
    for side in "LR":
        items = sorted([e for e in EDGE if e[1] == side], key=lambda e: e[2])
        for a, b in zip(items, items[1:]):
            gap = (b[2] - b[3] / 2) - (a[2] + a[3] / 2)
            if gap < 1.5:
                issues.append(f"Edge {side}: {a[5]} and {b[5]} only {gap:.1f} mm apart")
        for e in items:
            lo, hi = e[2] - e[3] / 2, e[2] + e[3] / 2
            for hx, hy in HOLES:
                near_edge = hx < 30 if side == "L" else hx > W - 30
                if near_edge and lo < hy + HOLE_KEEPOUT and hi > hy - HOLE_KEEPOUT and e[4] > abs(
                        (hx if side == "L" else W - hx)) - HOLE_KEEPOUT:
                    issues.append(f"Edge {side}: {e[5]} overlaps mounting hole at y={hy}")
        total = sum(e[3] for e in items)
        print(f"Edge {side}: {total:.1f} mm of connectors on {H:.0f} mm "
              f"({H - 2 * (4 + HOLE_KEEPOUT):.0f} mm between hole keep-outs)")

    # tall parts under the battery
    bx0, by0, bx1, by1 = BATTERY
    zone_of = {}
    for name, x0, y0, x1, y1, area, req, sheets in rows:
        for s in sheets:
            zone_of[s] = (x0, y0, x1, y1)
    tall_under = []
    for ref, hgt in TALL.items():
        if hgt <= BATTERY_CLEARANCE or ref not in sizes:
            continue
        s = sizes[ref][2]
        if ref in edge_refs or s not in zone_of:
            continue
        x0, y0, x1, y1 = zone_of[s]
        if x0 < bx1 and x1 > bx0 and y0 < by1 and y1 > by0:
            tall_under.append(f"{ref} ({hgt} mm, zone of '{s}')")
    if tall_under:
        issues.append("Keep these tall parts outside the battery footprint: " + ", ".join(tall_under))

    total_req = sum(r[6] for r in rows)
    total_area = sum(r[5] for r in rows)
    print(f"\n{'Zone':34s} {'size mm':>12s} {'area':>6s} {'need':>6s} {'fill':>5s}")
    for name, x0, y0, x1, y1, area, req, sheets in rows:
        print(f"{name:34s} {x1 - x0:5.0f} x {y1 - y0:4.0f} {area:6.0f} {req:6.0f} {100 * req / area:4.0f}%")
    print(f"{'Interior total':34s} {'':12s} {total_area:6.0f} {total_req:6.0f} {100 * total_req / total_area:4.0f}%")
    print("\nIssues:" if issues else "\nNo issues.")
    for i in issues:
        print(" -", i)
    svg(rows, ps, sizes)
    return rows, issues


def svg(rows, ps, sizes):
    s = 5.0
    pad = 30
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * s + 2 * pad}" height="{H * s + 2 * pad + 60}" '
           f'font-family="Arial" font-size="11"><rect width="100%" height="100%" fill="white"/>',
           f'<g transform="translate({pad},{pad})">',
           f'<rect x="0" y="0" width="{W * s}" height="{H * s}" fill="#e8f3e8" stroke="#060" stroke-width="2"/>',
           f'<rect x="{(W - PANEL_W) / 2 * s}" y="{(H - PANEL_H) / 2 * s}" width="{PANEL_W * s}" height="{PANEL_H * s}" fill="none" stroke="#999" '
           f'stroke-dasharray="6,4"/>']
    bx0, by0, bx1, by1 = BATTERY
    out.append(f'<rect x="{bx0 * s}" y="{by0 * s}" width="{(bx1 - bx0) * s}" height="{(by1 - by0) * s}" '
               f'fill="none" stroke="#c60" stroke-width="2" stroke-dasharray="10,5"/>'
               f'<text x="{bx0 * s + 4}" y="{by1 * s - 4}" fill="#c60">2 x 18650 behind (parts here &lt;= 4 mm)</text>')
    for name, x0, y0, x1, y1, area, req, sheets in rows:
        fill = req / area
        col = "#9d9" if fill < 0.75 else "#fd7" if fill < 0.9 else "#f88"
        out.append(f'<rect x="{x0 * s}" y="{y0 * s}" width="{(x1 - x0) * s}" height="{(y1 - y0) * s}" '
                   f'fill="{col}" fill-opacity="0.55" stroke="#333"/>')
        out.append(f'<text x="{x0 * s + 4}" y="{y0 * s + 14}" font-weight="bold">{name}</text>'
                   f'<text x="{x0 * s + 4}" y="{y0 * s + 28}">{100 * fill:.0f} % full</text>')
    for ref, side, c, along, depth, label in EDGE:
        if side == "T":
            x, y, w, h = c - along / 2, 0, along, depth
        elif side == "L":
            x, y, w, h = 0, c - along / 2, depth, along
        else:
            x, y, w, h = W - depth, c - along / 2, depth, along
        out.append(f'<rect x="{x * s}" y="{y * s}" width="{w * s}" height="{h * s}" fill="#69c" stroke="#036"/>'
                   f'<text x="{x * s + 3}" y="{(y + h / 2) * s + 4}" fill="white" font-size="10">{label}</text>')
    for label, x, wid, fy in FPC:
        out.append(f'<rect x="{(x - wid / 2) * s}" y="{(fy - 1) * s}" width="{wid * s}" height="{2 * s}" fill="#a3c" '
                   f'fill-opacity="0.9"/><text x="{(x - wid / 2) * s}" y="{(fy - 2) * s}" fill="#a3c" '
                   f'font-weight="bold">{label} slot (approx.)</text>')
    for hx, hy in HOLES:
        out.append(f'<circle cx="{hx * s}" cy="{hy * s}" r="{HOLE_KEEPOUT * s}" fill="#ccc" stroke="#555"/>')
    out.append(f'<text x="0" y="{H * s + 20}">ADSB_Test floorplan, component (bottom) side, {W:.0f} x {H:.0f} mm. '
               f'Left = RF edge, right = digital edge. Dashed grey = panel outline on the other side. '
               f'Fill = ({K} x small-part courtyards + {FIXED} x big parts) / zone area.</text>')
    out.append(f'<text x="0" y="{H * s + 36}">Green &lt; 75 %, yellow 75-90 %, red &gt; 90 %.</text></g></svg>')
    p = HERE / "floorplan.svg"
    p.write_text("\n".join(out), encoding="utf-8")
    try:
        import pymupdf
        doc = pymupdf.open(str(p))
        pdf = pymupdf.open("pdf", doc.convert_to_pdf())
        pdf[0].get_pixmap(dpi=96).save(str(HERE / "floorplan.png"))
    except ImportError:
        pass


if __name__ == "__main__":
    import argparse
    import io
    import contextlib
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="204.9x140", help="board size WxH in mm")
    ap.add_argument("--compare", action="store_true", help="fill summary for several board sizes")
    a = ap.parse_args()
    ps = parts()
    if a.compare:
        for g in (4, 6, 8, 10, 12, 14, 16):
            w, h = round(PANEL_W + 2 * g, 1), round(PANEL_H + 2 * g, 1)
            size = f"{w:g}x{h:g} (gap {g})"
            ZONES = layout(w, h)
            with contextlib.redirect_stdout(io.StringIO()):
                rows, issues = main(ps)
            worst = max(rows, key=lambda r: r[6] / r[5])
            tot = sum(r[6] for r in rows) / sum(r[5] for r in rows)
            print(f"{size:22s} overall {100 * tot:3.0f} %  fullest: {worst[0]} {100 * worst[6] / worst[5]:.0f} %  "
                  f"issues: {len(issues)}")
    w, h = map(float, a.size.split("x"))
    ZONES = layout(w, h)
    main(ps)
