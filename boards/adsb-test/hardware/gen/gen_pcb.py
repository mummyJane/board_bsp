#!/usr/bin/env python3
"""Start the ADSB_Test PCB: outline, holes, panel-cable slots, edge connectors and the big parts.

Run with KiCad's own Python (it needs the pcbnew module):
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" boards/adsb-test/hardware/gen/gen_pcb.py

* Board 204.9 x 140 mm (Q28: panel 164.9 x 100 centred with a 20 mm border), 4 layers, 1.6 mm.
* ALL parts are on the BOTTOM side (the panel is bonded to the top). Placements below are given in
  BOTTOM VIEW (looking at the component side, RF edge on the left, digital edge on the right), as in docs/floorplan.md;
  the script mirrors them into KiCad's top-view coordinates.
* Every footprint gets its schematic link (KIID path) and pad nets, so "Update PCB from Schematic"
  keeps working and the ratsnest shows. Parts not placed here are parked beside the board, grouped
  by sheet, for manual placement.

Re-running OVERWRITES ADSB_Test.kicad_pcb. Once layout work starts in KiCad, stop re-running it
(or only use it on a copy).
"""
import collections
import json
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

PW, PH = 164.9, 100.0               # panel (on the top side)
GAP = 20.0                          # border round the panel (Q28: 20 mm since 2026-10-20, room for hand soldering)
W, H = PW + 2 * GAP, PH + 2 * GAP   # board 204.9 x 140
PX0, PY0 = (W - PW) / 2, (H - PH) / 2   # panel corner (bottom view; the panel is centred, so either corner)
OX, OY = 100.0, 100.0               # board top-left corner on the KiCad page
HOLE_IN = 4.0                       # corner hole centres, mm in from both edges


def mm(v):
    return pcbnew.FromMM(v)


def top(bx, by):
    """bottom-view (bx, by) -> KiCad top-view point (mirror in x)."""
    return pcbnew.VECTOR2I(mm(OX + W - bx), mm(OY + by))


# ---------------------------------------------------------------- placements (bottom view, mm)
def edge_positions():
    """Same spread as floorplan.py: connectors evenly spaced between the corner-hole keep-outs.
    Bottom view: RF edge on the left, digital edge on the right (nearer the module) since 2026-10-20."""
    left = [("J1403", 8.2), ("J1201", 8.2)]
    right = [("J901", 10.6), ("J1001", 10.6), ("J1101", 17.2), ("J801", 19.0), ("J1501", 13.7), ("SW401", 11.4), ("SW603", 9.6)]
    out = {}
    for side, items in (("L", left), ("R", right)):
        lo, hi = HOLE_IN + 4.0, H - HOLE_IN - 4.0
        gap = (hi - lo - sum(a for _, a in items)) / (len(items) - 1)
        y = lo
        for ref, along in items:
            out[ref] = (side, y + along / 2)
            y += along + gap
    out["J602"] = ("T", PX0 + 88.0)   # Wi-Fi RP-SMA on the top long edge, away from the RF-edge SMAs (by = bx here)
    return out


EDGE = edge_positions()
# interior big parts: ref -> (bx, by, mouth) ; mouth = direction the connector opening faces (bottom view).
# Parts tied to the panel (module, sockets) are given from the panel corner (PX0, PY0); parts tied to an edge
# keep their distance from that edge.
BIG = {
    "U601": (PX0 + 106.3, PY0 + 38.0, None),   # OSPTEK ESP32-P4C5 module, between the LCD and touch sockets (short MIPI)
    "U1401": (22.9, 32.0, None),            # m1421, under can SH1401 (RF column, left edge)
    "SH1401": (22.9, 32.0, None),
    "U1201": (20.9, H - 22.0, None),        # MAX-M10S, under can SH1201
    "SH1201": (20.9, H - 22.0, None),
    "J1601": (PX0 + 87.0, H - 12.0, "rot90"),  # LA5016 2x20 header, horizontal along the bottom edge
    "J1301": (0.0, None, "+y"),             # LCD 30-pin FPC, opening towards its slot (x, y set from the slot below)
    "J1302": (0.0, None, "+y"),             # touch 6-pin FPC, opening towards its slot (x, y set from the slot below)
    "J301": (PX0 + 106.0, 9.0, None),       # battery connector, charger zone (outside the battery footprint)
    "SW601": (W - 39.0, 12.0, None),        # BOOT  (top band near the digital edge, clear of the battery)
    "SW602": (W - 28.0, 12.0, None),        # RESET
    "SW1801": (PX0 + 54.0, PY0 + 37.0, None),  # RP2040 BOOTSEL (Dev zone)
    "J601": (PX0 + 88.0, 10.5, None),       # Wi-Fi U.FL (jumper from the module IPEX), just behind J602
    "J1401": (30.9, 56.0, None),            # m1421 JTAG (below the m1421 can)
    "J1402": (40.9, 14.0, None),            # ADSBee Dev Kit header (1x6, vertical, next to the m1421)
    "J1801": (PX0 + 37.0, PY0 + 48.0, None),   # RP2040 GPIO header (DNP)
}
# Panel-cable slots, measured on the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (2026-10-20), back view, from its
# bottom edge and its USB side:
#   LCD   22 x 3 mm, bottom of hole 41 mm up, near (right) side 68 mm from the USB side
#   touch  8 x 3 mm, bottom of hole 48 mm up, near (right) side 122 mm from the USB side
# Converted to FRONT-VIEW mm from the panel's left edge (the USB side is the panel's right edge, front view; the
# Waveshare PCB is 164 mm wide, as the panel) and mm up from the panel's bottom edge (+1.58 mm: the Waveshare PCB
# edge sits that far in from the lens edge). They agree with the panel drawings (touch tail from 37.5 mm, LCD
# tail ~73-90 mm). Each: (name, left, right, bottom of hole up from the panel bottom, slot height).
WS_W, WS_EDGE = 164.0, 1.58
SLOTS_FRONT = [("LCD FPC slot", WS_W - 90.0, WS_W - 68.0, 41.0 + WS_EDGE, 3.0),
               ("Touch FPC slot", WS_W - 130.0, WS_W - 122.0, 48.0 + WS_EDGE, 3.0)]
SOCKET_GAP = 7.0                       # slot centre -> socket centre, further in (towards the panel's middle)
PANEL_BOTTOM = (H + PH) / 2            # bottom-view y of the panel's bottom edge
# (name, bottom-view x centre, length, bottom-view y centre, height)
SLOTS = [(n, W - (W - PW) / 2 - (a + b) / 2, b - a, PANEL_BOTTOM - (up + h / 2), h) for n, a, b, up, h in SLOTS_FRONT]
for _r, (_n, _x, _l, _y, _h) in zip(("J1301", "J1302"), SLOTS):   # sockets just inside their slots, facing them
    BIG[_r] = (_x, _y - SOCKET_GAP, BIG[_r][2])


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
                          dnp=any(p.get("name") == "dnp" for p in c.findall("property")),
                          no_bom=any(p.get("name") == "exclude_from_bom" for p in c.findall("property")),
                          fields={f.get("name"): f.text or "" for f in c.iterfind("fields/field")
                                  if f.get("name") not in ("Footprint", "Datasheet", "Description")}))
    pins = {}
    for n in r.find("nets").findall("net"):
        for node in n.findall("node"):
            name = n.get("name")
            if name.startswith("unconnected-("):       # KiCad escapes '/' in pin names inside these net names
                name = "unconnected-(" + name[len("unconnected-("):].replace("/", "{slash}")
            pins[(node.get("ref"), node.get("pin"))] = name
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


def front_box(fp):
    """Box whose outer side goes on the board edge when the footprint has no 'PCB Edge' marker: the pads for
    edge-mount (end-launch) connectors, whose barrel overhangs the edge; otherwise the body."""
    if "EdgeMount" in fp.GetFPID().GetLibItemName().wx_str():
        b = pcbnew.BOX2I()
        for p in fp.Pads():
            b.Merge(p.GetBoundingBox())
        b.Inflate(mm(0.5), mm(0.5))            # pads 0.5 mm in from the edge (copper-to-edge clearance)
        return b
    return body_box(fp)


def place_on_edge(fp, side, by):
    """side 'L' = bottom-view left edge (RF; top-view right), 'R' = bottom-view right edge (digital), 'T' = top long edge
    (by is then the bottom-view x)."""
    if side == "T":
        turn_to(fp, (0, -1))
        em = edge_marker(fp)
        b = front_box(fp)
        front = em[1] if em else b.GetTop()
        fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x, fp.GetPosition().y + int(mm(OY) - front)))
        b = body_box(fp)
        fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x + int(top(by, 0).x - b.GetCenter().x), fp.GetPosition().y))
        return
    want = (1, 0) if side == "L" else (-1, 0)
    turn_to(fp, want)
    target_x = mm(OX + W) if side == "L" else mm(OX)
    em = edge_marker(fp)
    pos = fp.GetPosition()
    if em:                                   # put the marker line on the board edge
        fp.SetPosition(pcbnew.VECTOR2I(pos.x + int(target_x - em[0]), mm(OY + by)))
    else:                                    # body (or edge-mount pads) flush with the edge
        b = front_box(fp)
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
    for name, bx, length, by, height in SLOTS:
        cx = OX + W - bx
        rect(cx - length / 2, OY + by - height / 2, cx + length / 2, OY + by + height / 2)
    t = pcbnew.PCB_TEXT(board)
    t.SetText("ADSB_Test Rev A - ALL COMPONENTS ON THE BOTTOM SIDE (panel bonded to the top).\n"
              "Dwgs.User rectangle = panel outline. Slots = panel FPC pass-throughs (from the Waveshare board).")
    t.SetPosition(pcbnew.VECTOR2I(mm(OX), mm(OY - 8)))
    t.SetLayer(pcbnew.Dwgs_User)
    t.SetTextSize(pcbnew.VECTOR2I(mm(1.5), mm(1.5)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


# PCBWay standard 4-layer 1.6 mm stack-up (pcbway.com/multi-layer-laminated-structure.html, #1, read 2026-10-20):
# 1 oz outer (0.5 oz + plating), 7628 prepreg 0.1855 mm after lamination (Dk 4.74), 1.1 mm core with 1 oz copper
# (Dk 4.6). The pcbnew Python API cannot edit the stack-up, so it goes into the file's (setup) after saving.
# Impedance widths for this stack-up: tools/impedance.py, net classes in gen_netclasses.py.
STACKUP = """\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.1855) (material "7628") (epsilon_r 4.74) (loss_tangent 0.02))
\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 2" (type "core") (thickness 1.03) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.1855) (material "7628") (epsilon_r 4.74) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints yes)
\t\t)
"""


def add_stackup():
    text = PCB.read_bytes().decode("utf-8").replace("\r\n", "\n")
    if "(stackup" not in text:
        assert "\t(setup\n" in text, "no (setup) section in the board file"
        text = text.replace("\t(setup\n", "\t(setup\n" + STACKUP, 1)
    PCB.write_text(text, encoding="utf-8", newline="\n")


def main():
    comps, pins = netlist()
    board = pcbnew.CreateEmptyBoard() if hasattr(pcbnew, "CreateEmptyBoard") else pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    # PCBWay standard capabilities (docs/pcb-manufacturing.md): 0.127 mm track/space, 0.25 mm drill / 0.5 mm via
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_MinClearance = mm(0.127)
    ds.m_MinThroughDrill = mm(0.25)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_ViasMinAnnularWidth = mm(0.125)
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
        fp.SetExcludedFromBOM(c["no_bom"])
        for name, text in c["fields"].items():         # symbol fields (Check, Note, ...) as hidden footprint fields
            fp.SetField(name, text)
            fp.GetField(name).SetVisible(False)
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

    # SaveBoard also rewrites ADSB_Test.kicad_pro from this fresh board, which has no net classes: keep the
    # project's net_settings (written by gen_netclasses.py) across the save
    pro = PCB.with_suffix(".kicad_pro")
    net_settings = json.loads(pro.read_text(encoding="utf-8")).get("net_settings")
    pcbnew.SaveBoard(str(PCB), board)
    d = json.loads(pro.read_text(encoding="utf-8"))
    if net_settings:
        d["net_settings"] = net_settings
        pro.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8", newline="\n")
    add_stackup()
    print(f"wrote {PCB.name}: {len(comps)} parts, {len(placed)} placed, {sum(len(v) for v in parked.values())} parked, "
          f"{len(nets)} nets")


if __name__ == "__main__":
    main()
