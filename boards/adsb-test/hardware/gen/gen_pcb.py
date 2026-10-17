#!/usr/bin/env python3
"""Start the ADSB_Test PCB: outline, holes, panel-cable slots, edge connectors and the big parts.

Run with KiCad's own Python (it needs the pcbnew module):
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" boards/adsb-test/hardware/gen/gen_pcb.py

* Board 180.9 x 116 mm (Q28: panel 164.9 x 100 centred with an 8 mm border), 4 layers, 1.6 mm.
* ALL parts are on the BOTTOM side (the panel is bonded to the top). Placements below are given in
  BOTTOM VIEW (looking at the component side, digital edge on the left), as in docs/floorplan.md;
  the script mirrors them into KiCad's top-view coordinates.
* Every footprint gets its schematic link (KIID path) and pad nets, so "Update PCB from Schematic"
  keeps working and the ratsnest shows. Parts not placed here are parked beside the board, grouped
  by sheet, for manual placement.

Re-running OVERWRITES ADSB_Test.kicad_pcb. Once layout work starts in KiCad, stop re-running it
(or only use it on a copy).
"""
import collections
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[4]
KICAD = ROOT / "boards/adsb-test/hardware/kicad"
PCB = KICAD / "ADSB_Test.kicad_pcb"
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
STD = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

W, H = 180.9, 116.0                 # board
PW, PH = 164.9, 100.0               # panel (on the top side)
OX, OY = 100.0, 100.0               # board top-left corner on the KiCad page
HOLE_IN = 4.0                       # corner hole centres, mm in from both edges


def mm(v):
    return pcbnew.FromMM(v)


def top(bx, by):
    """bottom-view (bx, by) -> KiCad top-view point (mirror in x)."""
    return pcbnew.VECTOR2I(mm(OX + W - bx), mm(OY + by))


# ---------------------------------------------------------------- placements (bottom view, mm)
def edge_positions():
    """Same spread as floorplan.py: connectors evenly spaced between the corner-hole keep-outs."""
    left = [("J901", 10.6), ("J1001", 10.6), ("J1101", 17.2), ("J801", 19.0), ("J1501", 13.7), ("SW401", 11.4), ("SW603", 9.6)]
    right = [("J1403", 8.2), ("J1201", 8.2)]
    out = {}
    for side, items in (("L", left), ("R", right)):
        lo, hi = HOLE_IN + 4.0, H - HOLE_IN - 4.0
        gap = (hi - lo - sum(a for _, a in items)) / (len(items) - 1)
        y = lo
        for ref, along in items:
            out[ref] = (side, y + along / 2)
            y += along + gap
    return out


EDGE = edge_positions()
# interior big parts: ref -> (bx, by, mouth) ; mouth = direction the connector opening faces (bottom view)
BIG = {
    "U601": (124.0, 44.0, None),            # OSPTEK ESP32-P4C5 module, above the panel-cable sockets
    "U1401": (158.0, 30.0, None),           # m1421, under can SH1401
    "SH1401": (158.0, 30.0, None),
    "U1201": (160.0, 94.0, None),           # MAX-M10S, under can SH1201
    "SH1201": (160.0, 94.0, None),
    "J1601": (95.0, 104.0, "rot90"),        # LA5016 2x20 header, horizontal along the bottom edge
    "J1301": (W - (W - PW) / 2 - 76.0, None, "+y"),    # LCD 30-pin FPC, opening towards its slot (y set below)
    "J1302": (W - (W - PW) / 2 - 42.0, None, "+y"),    # touch 6-pin FPC, opening towards its slot (y set below)
    "J301": (64.0, 9.0, None),              # battery connector (outside the battery footprint)
    "SW601": (110.0, 12.0, None),           # BOOT  (top band, clear of the battery)
    "SW602": (122.0, 12.0, None),           # RESET
    "SW1801": (40.0, 82.0, None),           # RP2040 BOOTSEL (Dev zone)
    "J1401": (150.0, 54.0, None),           # m1421 JTAG (below the m1421 can)
    "J1402": (140.0, 14.0, None),           # ADSBee Dev Kit header (1x6, vertical, above the module)
    "J1801": (70.0, 60.0, None),            # RP2040 GPIO header (DNP)
}
# Panel-cable slots, given in FRONT-VIEW mm from the panel's left edge (as the panel drawings are dimensioned):
#   LCD 30-pin tail: Midas MDT070005 drawing 72.88 +/-0.5 mm (tail ~17 mm wide), AliExpress panel ~71 mm to the tail
#   centre -> slot 56..96 mm covers both readings. Touch tail: 37.5 mm to its left edge, ~10-14 mm wide -> 32..52 mm.
# The tails fold back behind the panel and come through the PCB past the wide part with the chip (as on the
# Waveshare board, where both slots/sockets are near the middle). SLOT_IN = distance of the slot centre in from
# the panel's bottom edge; the LCD tail is ~45 mm long with ~19.5 mm of wide (chip) section first.
SLOTS_FRONT = [("LCD FPC slot", 56.0, 96.0), ("Touch FPC slot", 32.0, 52.0)]
SLOT_IN, SLOT_W, SOCKET_GAP = 30.0, 2.5, 7.0
SLOT_Y = (H + PH) / 2 - SLOT_IN
SLOTS = [(n, W - (W - PW) / 2 - (a + b) / 2, b - a) for n, a, b in SLOTS_FRONT]   # (name, bottom-view x, length)
for _r in ("J1301", "J1302"):          # sockets just inside their slots, openings facing the slot
    BIG[_r] = (BIG[_r][0], SLOT_Y - SOCKET_GAP, BIG[_r][2])


# ---------------------------------------------------------------- netlist
def netlist():
    xml = KICAD / "_pcbgen_netlist.xml"
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml),
                    str(KICAD / "ADSB_Test.kicad_sch")], check=True, capture_output=True)
    r = ET.parse(xml).getroot()
    xml.unlink()
    comps = []
    for c in r.find("components").findall("comp"):
        sp = c.find("sheetpath")
        comps.append(dict(ref=c.get("ref"), value=c.findtext("value"), fp=c.findtext("footprint") or "",
                          path=sp.get("tstamps") + c.findtext("tstamps"), sheet=sp.get("names").strip("/") or "Top",
                          dnp=any(p.get("name") == "dnp" for p in c.findall("property"))))
    pins = {}
    for n in r.find("nets").findall("net"):
        for node in n.findall("node"):
            pins[(node.get("ref"), node.get("pin"))] = n.get("name")
    return comps, pins


def load_fp(fpid):
    lib, name = fpid.split(":", 1)
    path = KICAD / "lib/ADSB_Test.pretty" if lib == "ADSB_Test" else STD / f"{lib}.pretty"
    fp = pcbnew.FootprintLoad(str(path), name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ---------------------------------------------------------------- geometry helpers
def pad_centroid(fp):
    ps = list(fp.Pads())
    return (sum(p.GetPosition().x for p in ps) / len(ps), sum(p.GetPosition().y for p in ps) / len(ps))


def edge_marker(fp):
    """Midpoint of the footprint's 'PCB Edge' line (Dwgs.User), if it has one."""
    txt = [t for t in fp.GraphicalItems() if isinstance(t, pcbnew.PCB_TEXT) and "PCB Edge" in t.GetText()]
    lines = [g for g in fp.GraphicalItems() if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == pcbnew.Dwgs_User
             and g.GetShape() == pcbnew.SHAPE_T_SEGMENT]
    if not txt or not lines:
        return None
    tp = txt[0].GetPosition()

    def mid(g):
        return ((g.GetStart().x + g.GetEnd().x) / 2, (g.GetStart().y + g.GetEnd().y) / 2)
    return min((mid(g) for g in lines), key=lambda m: (m[0] - tp.x) ** 2 + (m[1] - tp.y) ** 2)


def body_box(fp):
    return fp.GetBoundingBox(False)          # without text


def facing(fp):
    """Unit direction (top-view) the connector opening faces: from its pads towards the body / edge marker."""
    px, py = pad_centroid(fp)
    em = edge_marker(fp)
    if em:
        dx, dy = em[0] - px, em[1] - py
    else:
        b = body_box(fp)
        dx, dy = b.GetCenter().x - px, b.GetCenter().y - py
    if abs(dx) >= abs(dy):
        return (1 if dx > 0 else -1, 0)
    return (0, 1 if dy > 0 else -1)


def turn_to(fp, want):
    for _ in range(4):
        if facing(fp) == want:
            return
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 90)
    raise RuntimeError(f"{fp.GetReference()}: could not orient")


def place_on_edge(fp, side, by):
    """side 'L' = digital edge (top-view right), 'R' = RF edge (top-view left)."""
    want = (1, 0) if side == "L" else (-1, 0)
    turn_to(fp, want)
    target_x = mm(OX + W) if side == "L" else mm(OX)
    em = edge_marker(fp)
    pos = fp.GetPosition()
    if em:                                   # put the marker line on the board edge
        fp.SetPosition(pcbnew.VECTOR2I(pos.x + int(target_x - em[0]), mm(OY + by)))
    else:                                    # body front flush with the edge
        b = body_box(fp)
        front = b.GetRight() if side == "L" else b.GetLeft()
        fp.SetPosition(pcbnew.VECTOR2I(pos.x + int(target_x - front), mm(OY + by)))
    # recentre along the edge on the body, not the origin
    b = body_box(fp)
    fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x, fp.GetPosition().y + int(mm(OY + by) - b.GetCenter().y)))


def outline(board):
    def seg(a, b, layer=pcbnew.Edge_Cuts, width=0.1):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(a)
        s.SetEnd(b)
        s.SetLayer(layer)
        s.SetWidth(mm(width))
        board.Add(s)

    def rect(x0, y0, x1, y1, layer=pcbnew.Edge_Cuts, width=0.1):
        r = pcbnew.PCB_SHAPE(board)
        r.SetShape(pcbnew.SHAPE_T_RECT)
        r.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
        r.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        r.SetLayer(layer)
        r.SetWidth(mm(width))
        board.Add(r)
        return r

    rect(OX, OY, OX + W, OY + H)
    # panel outline (top side) for reference, on User.1-like drawing layer
    px0, py0 = OX + (W - PW) / 2, OY + (H - PH) / 2
    rect(px0, py0, px0 + PW, py0 + PH, layer=pcbnew.Dwgs_User, width=0.15)
    for name, bx, length in SLOTS:
        cx = OX + W - bx
        rect(cx - length / 2, OY + SLOT_Y - SLOT_W / 2, cx + length / 2, OY + SLOT_Y + SLOT_W / 2)
    t = pcbnew.PCB_TEXT(board)
    t.SetText("ADSB_Test Rev A - ALL COMPONENTS ON THE BOTTOM SIDE (panel bonded to the top).\n"
              "Dwgs.User rectangle = panel outline. Slots = panel FPC pass-throughs (check against the real panel).")
    t.SetPosition(pcbnew.VECTOR2I(mm(OX), mm(OY - 8)))
    t.SetLayer(pcbnew.Dwgs_User)
    t.SetTextSize(pcbnew.VECTOR2I(mm(1.5), mm(1.5)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


def main():
    comps, pins = netlist()
    board = pcbnew.CreateEmptyBoard() if hasattr(pcbnew, "CreateEmptyBoard") else pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    outline(board)

    nets = {}
    for name in sorted(set(pins.values())):
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n

    corners = [(HOLE_IN, HOLE_IN), (W - HOLE_IN, HOLE_IN), (HOLE_IN, H - HOLE_IN), (W - HOLE_IN, H - HOLE_IN)]
    holes = iter(corners)
    parked = collections.defaultdict(list)
    placed = []
    for c in sorted(comps, key=lambda c: c["ref"]):
        if not c["fp"]:
            print("  no footprint:", c["ref"])
            continue
        fp = load_fp(c["fp"])
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        if hasattr(fp, "SetDNP"):
            fp.SetDNP(c["dnp"])
        board.Add(fp)
        for pad in fp.Pads():
            net = pins.get((c["ref"], pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])
        fp.SetPosition(top(0, 0))
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)      # bottom side
        ref = c["ref"]
        if ref.startswith("H16"):                                         # corner mounting holes
            bx, by = next(holes)
            fp.SetPosition(top(bx, by))
            placed.append(ref)
        elif ref in EDGE:
            side, by = EDGE[ref]
            place_on_edge(fp, side, by)
            placed.append(ref)
        elif ref in BIG:
            bx, by, mouth = BIG[ref]
            if mouth == "rot90":
                fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 90)
            elif mouth:
                turn_to(fp, {"+y": (0, 1), "-y": (0, -1), "+x": (-1, 0), "-x": (1, 0)}[mouth])
            fp.SetPosition(top(bx, by))
            b = body_box(fp)                                             # centre the body on the target
            fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x + int(top(bx, by).x - b.GetCenter().x),
                                           fp.GetPosition().y + int(top(bx, by).y - b.GetCenter().y)))
            placed.append(ref)
        else:
            parked[c["sheet"]].append(fp)

    # park the rest beside the board (top-view right of the board), one column block per sheet
    x0, y = OX + W + 15, OY
    col_x = x0
    for sheet in sorted(parked):
        fps = parked[sheet]
        t = pcbnew.PCB_TEXT(board)
        t.SetText(f"[{sheet}] {len(fps)} parts")
        t.SetLayer(pcbnew.Dwgs_User)
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.5), mm(1.5)))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        t.SetPosition(pcbnew.VECTOR2I(mm(col_x), mm(y)))
        board.Add(t)
        y += 4
        cx, row_h = col_x, 0
        for fp in fps:
            b = body_box(fp)
            w, h = pcbnew.ToMM(b.GetWidth()), pcbnew.ToMM(b.GetHeight())
            if cx + w > col_x + 70:
                cx, y = col_x, y + row_h + 1.5
                row_h = 0
            fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x + int(mm(cx + w / 2) - b.GetCenter().x),
                                           fp.GetPosition().y + int(mm(y + h / 2) - b.GetCenter().y)))
            cx += w + 1.5
            row_h = max(row_h, h)
        y += row_h + 8
        if y > OY + 260:
            col_x, y = col_x + 80, OY

    pcbnew.SaveBoard(str(PCB), board)
    print(f"wrote {PCB.name}: {len(comps)} parts, {len(placed)} placed, {sum(len(v) for v in parked.values())} parked, "
          f"{len(nets)} nets")


if __name__ == "__main__":
    main()
