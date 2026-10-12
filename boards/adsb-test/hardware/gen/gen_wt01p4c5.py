#!/usr/bin/env python3
"""Make the Wireless-Tag WT01P4C5-S1 (ESP32-P4 + ESP32-C5 module) symbol and hand-solder footprint.

Run from the repo root: python boards/adsb-test/hardware/gen/gen_wt01p4c5.py
then: kicad-cli sym upgrade + fp upgrade (the README lists the commands).

Source: WT01P4C5-S1 datasheet v1.3 (2026-01-27), section 3 (pin table + pin layout) and
section 6 (dimensions): 35.00 x 35.00 mm, 23 castellated pads per side at 1.40 mm pitch,
30.80 mm between end-pad centres, numbered anticlockwise from the top of the left side.
No vendor land pattern is published: the pads below are derived from that drawing.
CHECK against a real module (calipers) before ordering PCBs.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LIB = ROOT / "boards/adsb-test/hardware/kicad/lib"
NAME = "Wireless-Tag_WT01P4C5-S1"
FP = f"{NAME}_HandSolder"
DS = ("https://img03.71360.com/w3/77q677/20260127/9a1f9a9cd53575eaf50a76b38847ef97.pdf"
      "?dl=1&dlf=WT01P4C5-S1_datasheet_V1.3.pdf")

# pad -> (name, electrical type). From the datasheet pin description table.
B, P_IN, P_OUT, NC, IN = "bidirectional", "power_in", "power_out", "no_connect", "input"
PINS = {
    1: ("C5_EN", IN), 2: ("C5_IO1", B), 3: ("C5_IO2/MTMS", B), 4: ("C5_IO3/MTDI", B),
    5: ("C5_IO4/MTCK", B), 6: ("C5_IO5/MTDO", B), 7: ("C5_IO6", B), 8: ("C5_U0TXD", B),
    9: ("C5_U0RXD", B), 10: ("GND", P_IN), 11: ("P4_EN", IN), 12: ("GPIO0/XTAL_32K_N", B),
    13: ("GPIO1/XTAL_32K_P", B), 14: ("GPIO2", B), 15: ("GPIO3", B), 16: ("GPIO4", B),
    17: ("NC1", NC), 18: ("GPIO6", B), 19: ("GPIO7", B), 20: ("GPIO8", B), 21: ("GPIO9", B),
    22: ("GPIO10", B), 23: ("NC2", NC), 24: ("GPIO11", B), 25: ("GPIO20", B), 26: ("GPIO21", B),
    27: ("GPIO22", B), 28: ("GPIO23", B), 29: ("GND", P_IN), 30: ("DSI_DATAP1", B),
    31: ("DSI_DATAN1", B), 32: ("DSI_CLKN", B), 33: ("DSI_CLKP", B), 34: ("DSI_DATAP0", B),
    35: ("DSI_DATAN0", B), 36: ("GND", P_IN), 37: ("CSI_DATAN0", B), 38: ("CSI_DATAP0", B),
    39: ("CSI_CLKP", B), 40: ("CSI_CLKN", B), 41: ("CSI_DATAN1", B), 42: ("CSI_DATAP1", B),
    43: ("GND", P_IN), 44: ("USB_DM", B), 45: ("USB_DP", B), 46: ("GND", P_IN), 47: ("GND", P_IN),
    48: ("GPIO24/USB_JTAG_N", B), 49: ("GPIO25/USB_JTAG_P", B), 50: ("GPIO26", B), 51: ("GPIO27", B),
    52: ("GPIO28", B), 53: ("GPIO29", B), 54: ("GPIO30", B), 55: ("GPIO31", B), 56: ("GPIO32", B),
    57: ("GPIO33", B), 58: ("GPIO34", B), 59: ("GPIO35/BOOT", B), 60: ("GPIO36", B),
    61: ("GPIO37/U0TXD", B), 62: ("GPIO38/U0RXD", B), 63: ("ESP_LDO_VO4", P_OUT), 64: ("GPIO39", B),
    65: ("GPIO40", B), 66: ("GPIO41", B), 67: ("PWR_CTRL", IN), 68: ("VCC_5V0", P_IN),
    69: ("VCC_5V0", P_IN), 70: ("GND", P_IN), 71: ("GND", P_IN), 72: ("VBAT(NC)", NC),
    73: ("GPIO42", B), 74: ("GPIO43", B), 75: ("GPIO44", B), 76: ("GPIO45", B), 77: ("GPIO46", B),
    78: ("GPIO47", B), 79: ("GPIO48", B), 80: ("GPIO49", B), 81: ("GPIO50", B), 82: ("GPIO51", B),
    83: ("GPIO52", B), 84: ("GPIO53", B), 85: ("GPIO54", B), 86: ("C5_IO23", B), 87: ("C5_IO24", B),
    88: ("C5_IO25", B), 89: ("C5_IO26", B), 90: ("C5_IO27", B), 91: ("C5_IO28/BOOT", B), 92: ("GND", P_IN),
}
assert len(PINS) == 92


def q(s):
    return '"' + s.replace('"', '\\"') + '"'


def prop(name, value, at, hide=False):
    h = " (hide yes)" if hide else ""
    return f'(property {q(name)} {q(value)} (at {at[0]} {at[1]} 0){h} (effects (font (size 1.27 1.27))))'


# ------------------------------------------------------------------ symbol: pads 1-46 left, 47-92 right
W, STEP, LEN = 50.8, 2.54, 2.54
top = 23 * STEP
pins = []
for n, (name, typ) in PINS.items():
    i = (n - 1) % 46
    y = top - i * STEP - STEP / 2 - 1.27
    if n <= 46:
        x, rot = -W / 2 - LEN, 0
    else:
        x, rot = W / 2 + LEN, 180
    pins.append(f'(pin {typ} line (at {x:.2f} {y:.2f} {rot}) (length {LEN}) '
                f'(name {q(name)} (effects (font (size 1.27 1.27)))) (number {q(str(n))} (effects (font (size 1.27 1.27)))))')
sym = (f'(symbol {q(NAME)} (exclude_from_sim no) (in_bom yes) (on_board yes) '
       + prop("Reference", "U", (-W / 2, top + 2.54)) + prop("Value", "WT01P4C5-S1", (W / 2 - 10, top + 2.54))
       + prop("Footprint", f"ADSB_Test:{FP}", (0, 0), True) + prop("Datasheet", DS, (0, 0), True)
       + prop("Description", "Wireless-Tag WT01P4C5-S1: ESP32-P4 (360 MHz) + ESP32-C5 dual-band Wi-Fi 6 over SDIO, "
              "16 MB flash, 16/32 MB PSRAM, 5 V in, IPEX antenna, 92 castellated pads 1.4 mm", (0, 0), True)
       + prop("ki_keywords", "ESP32-P4 ESP32-C5 module WiFi6", (0, 0), True)
       + f'(symbol {q(NAME + "_0_1")} (rectangle (start {-W / 2} {top}) (end {W / 2} {-top - STEP}) '
         '(stroke (width 0.254) (type default)) (fill (type background))))'
       + f'(symbol {q(NAME + "_1_1")} ' + " ".join(pins) + "))")

sym_path = LIB / "ADSB_Test.kicad_sym"
text = sym_path.read_text(encoding="utf-8")
m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(NAME), text)
if m:   # replace the previous copy (balanced-paren block)
    depth, j = 0, m.start() + 2
    for k in range(j, len(text)):
        depth += {"(": 1, ")": -1}.get(text[k], 0)
        if depth == 0:
            text = text[:m.start()] + text[k + 1:]
            break
text = text.rstrip()
assert text.endswith(")")
text = text[:-1].rstrip() + "\n\t" + sym + "\n)\n"
sym_path.write_text(text, encoding="utf-8", newline="\n")

# ------------------------------------------------------------------ footprint
EDGE, PITCH = 17.5, 1.4
PAD_W = 0.9            # along the edge (0.5 mm gap at 1.4 mm pitch)
IN_, OUT = 1.2, 1.3    # pad runs 1.2 mm under the module and 1.3 mm past its edge (iron access)
plen, pc = IN_ + OUT, EDGE + (OUT - IN_) / 2
pads = []
for n in range(1, 93):
    side, i = divmod(n - 1, 23)
    off = -15.4 + i * PITCH
    if side == 0:
        x, y, w, h = -pc, off, plen, PAD_W           # left, top -> bottom
    elif side == 1:
        x, y, w, h = off, pc, PAD_W, plen            # bottom, left -> right
    elif side == 2:
        x, y, w, h = pc, -off, plen, PAD_W           # right, bottom -> top
    else:
        x, y, w, h = -off, -pc, PAD_W, plen          # top, right -> left
    pads.append(f'(pad "{n}" smd roundrect (at {x:.3f} {y:.3f}) (size {w:.3f} {h:.3f}) '
                f'(layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25))')
cy = EDGE + OUT + 0.25
body = EDGE
fp = (f'(footprint {q(FP)} (version 20241229) (generator "gen_wt01p4c5.py") (layer "F.Cu") '
      f'(descr {q("WT01P4C5-S1 35x35 mm, 92 castellated pads P1.4 mm, hand-solder pads (1.3 mm outside the edge). "
                  "Derived from datasheet v1.3 section 6: check against a real module. "
                  "IPEX Wi-Fi connector on the module top, top-right corner: leave room for the pigtail. "
                  "No exposed copper or untented vias under the module (it has RF test pads underneath)")}) '
      '(tags "ESP32-P4 ESP32-C5 module castellated") (attr smd) '
      f'(property "Reference" "REF**" (at 0 {-cy - 1.5}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15)))) '
      f'(property "Value" {q(FP)} (at 0 {cy + 1.5}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15)))) '
      f'(fp_rect (start {-body} {-body}) (end {body} {body}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab")) '
      f'(fp_line (start {-body} {-body + 2}) (end {-body + 2} {-body}) (stroke (width 0.1) (type solid)) (layer "F.Fab")) '
      f'(fp_rect (start {-cy} {-cy}) (end {cy} {cy}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd")) '
      f'(fp_circle (center {-cy - 0.6} -15.4) (end {-cy - 0.3} -15.4) (stroke (width 0.3) (type solid)) (fill yes) (layer "F.SilkS")) '
      f'(fp_text user "IPEX" (at 14.5 -14.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15)))) '
      + " ".join(pads) + ")")
(LIB / "ADSB_Test.pretty" / f"{FP}.kicad_mod").write_text(fp + "\n", encoding="utf-8", newline="\n")
print("symbol", NAME, "and footprint", FP, "written")
