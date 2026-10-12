#!/usr/bin/env python3
"""Make the OSPTEK ESP32-P4C5 Core module (ESP32-P4 + ESP32-C5HF4) symbol and hand-solder footprint.

Run from the repo root: python boards/adsb-test/hardware/gen/gen_osptek_p4c5.py
then: kicad-cli sym upgrade --force (library) and fp upgrade (the README lists the commands).

Source: https://github.com/osptek/esp32-p4c5-core-board (docs CC BY 4.0):
pages/pin-definition_EN.md (88-pin table), images/pinout.png (pin 1 top-left, anticlockwise),
images/dimensions.png: 25.00 x 25.00 mm, 22 stamp holes per side at 1.00 mm pitch, 21.00 mm
between the end pads, pads 0.70 x 1.30 mm. P4 <-> C5 inside: SDIO on P4 GPIO14-19, C5 CHIP_PU on
P4 GPIO54 (pad 82), C5 GPIO2 on P4 GPIO6 (pad 21) - the same as the Waveshare reference board.
The repo also has an Altium PcbLib; cross-check this footprint against it before ordering PCBs.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LIB = ROOT / "boards/adsb-test/hardware/kicad/lib"
NAME = "OSPTEK_ESP32-P4C5_Core"
FP = f"{NAME}_HandSolder"
DS = "https://github.com/osptek/esp32-p4c5-core-board"

B, P_IN, P_OUT, IN = "bidirectional", "power_in", "power_out", "input"
names = {1: "GND", 2: "LAN_OUT", 3: "GND", 4: "C5_U0RXD", 5: "C5_U0TXD", 6: "C5_IO28/BOOT", 7: "C5_IO27",
         8: "C5_IO26", 9: "C5_IO25", 10: "C5_IO24", 11: "C5_IO23", 12: "C5_IO6", 13: "C5_IO5", 14: "C5_IO4",
         15: "GND", 33: "GND", 34: "DSI_D1P", 35: "DSI_D1N", 36: "DSI_CLKN", 37: "DSI_CLKP", 38: "DSI_D0P",
         39: "DSI_D0N", 40: "GND", 41: "CSI_D0N", 42: "CSI_D0P", 43: "CSI_CLKP", 44: "CSI_CLKN", 45: "CSI_D1N",
         46: "CSI_D1P", 47: "GND", 48: "USB_DM", 49: "USB_DP", 52: "GND", 66: "ESP_LDO_VO4", 83: "GND",
         84: "RTC_VBAT", 85: "ESP_3V3", 86: "ESP_3V3", 87: "CHIP_PU", 88: "GPIO0/XTAL_32K_N"}
gpio = {16: 1, 17: 2, 18: 3, 19: 4, 20: 5, 21: 6, 22: 7, 23: 8, 24: 9, 25: 10, 26: 11, 27: 12, 28: 13,
        29: 20, 30: 21, 31: 22, 32: 23, 50: 24, 51: 25, 53: 26}
gpio.update({54 + i: 27 + i for i in range(12)})          # pads 54-65 = GPIO27-38
gpio.update({67 + i: 39 + i for i in range(16)})          # pads 67-82 = GPIO39-54
suffix = {1: "/XTAL_32K_P", 6: "/C5_IO2", 24: "/USB_JTAG_N", 25: "/USB_JTAG_P", 35: "/BOOT", 37: "/U0TXD",
          38: "/U0RXD", 54: "/C5_CHIP_PU"}
for pad, g in gpio.items():
    names[pad] = f"GPIO{g}{suffix.get(g, '')}"
assert sorted(names) == list(range(1, 89))
types = {n: (P_IN if v in ("GND", "ESP_3V3", "RTC_VBAT") else P_OUT if v == "ESP_LDO_VO4" else
             IN if v == "CHIP_PU" else B) for n, v in names.items()}


def q(s):
    return '"' + s.replace('"', '\\"') + '"'


def prop(name, value, at, hide=False):
    h = " (hide yes)" if hide else ""
    return f'(property {q(name)} {q(value)} (at {at[0]} {at[1]} 0){h} (effects (font (size 1.27 1.27))))'


# ------------------------------------------------------------------ symbol: pads 1-44 left, 45-88 right
W, STEP, LEN = 45.72, 2.54, 2.54
top = 22 * STEP
pins = []
for n in range(1, 89):
    i = (n - 1) % 44
    y = top - i * STEP - STEP
    x, rot = (-W / 2 - LEN, 0) if n <= 44 else (W / 2 + LEN, 180)
    pins.append(f'(pin {types[n]} line (at {x:.2f} {y:.2f} {rot}) (length {LEN}) '
                f'(name {q(names[n])} (effects (font (size 1.27 1.27)))) (number {q(str(n))} (effects (font (size 1.27 1.27)))))')
sym = (f'(symbol {q(NAME)} (exclude_from_sim no) (in_bom yes) (on_board yes) '
       + prop("Reference", "U", (-W / 2, top + 2.54)) + prop("Value", "ESP32-P4C5 Core (OSPTEK)", (W / 2 - 18, top + 2.54))
       + prop("Footprint", f"ADSB_Test:{FP}", (0, 0), True) + prop("Datasheet", DS, (0, 0), True)
       + prop("Description", "OSPTEK ESP32-P4C5 core module: ESP32-P4 (rev v3.x) + ESP32-C5HF4 over SDIO, 16 MB flash, "
              "32 MB PSRAM, 3.3 V, IPEX antenna, 88 stamp holes 1.0 mm, 25 x 25 mm", (0, 0), True)
       + prop("ki_keywords", "ESP32-P4 ESP32-C5 module WiFi6", (0, 0), True)
       + f'(symbol {q(NAME + "_0_1")} (rectangle (start {-W / 2} {top}) (end {W / 2} {-top - STEP}) '
         '(stroke (width 0.254) (type default)) (fill (type background))))'
       + f'(symbol {q(NAME + "_1_1")} ' + " ".join(pins) + "))")

sym_path = LIB / "ADSB_Test.kicad_sym"
text = sym_path.read_text(encoding="utf-8")
for old in (NAME, "Wireless-Tag_WT01P4C5-S1"):           # replace our copy, drop the superseded module
    m = re.search(r'\n\s*\(symbol "%s"\s' % re.escape(old), text)
    if m:
        start = text.index("(", m.start())
        depth = 0
        for k in range(start, len(text)):
            depth += {"(": 1, ")": -1}.get(text[k], 0)
            if depth == 0:
                text = text[:m.start()] + text[k + 1:]
                break
text = text.rstrip()
assert text.endswith(")")
text = text[:-1].rstrip() + "\n\t" + sym + "\n)\n"
sym_path.write_text(text, encoding="utf-8", newline="\n")
old_fp = LIB / "ADSB_Test.pretty/Wireless-Tag_WT01P4C5-S1_HandSolder.kicad_mod"
if old_fp.exists():
    old_fp.unlink()

# ------------------------------------------------------------------ footprint (top view)
EDGE, PITCH = 12.5, 1.0
PAD_W = 0.7
IN_, OUT = 1.0, 1.3    # 1.0 mm under the module (castellation), 1.3 mm past the edge for the iron
plen, pc = IN_ + OUT, EDGE + (OUT - IN_) / 2
pads = []
for n in range(1, 89):
    side, i = divmod(n - 1, 22)
    off = -10.5 + i * PITCH
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
fp = (f'(footprint {q(FP)} (version 20241229) (generator "gen_osptek_p4c5.py") (layer "F.Cu") '
      f'(descr {q("OSPTEK ESP32-P4C5 Core, 25 x 25 mm, 88 stamp holes P1.0 mm. Pads 0.7 mm wide, 1.0 mm under the "
                  "module and 1.3 mm past its edge (hand solder). From the OSPTEK dimension drawing; cross-check against "
                  "their PcbLib. IPEX antenna socket at the top-left corner (pin 1 side)")}) '
      '(tags "ESP32-P4 ESP32-C5 module castellated stamp") (attr smd) '
      f'(property "Reference" "REF**" (at 0 {-cy - 1.5}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15)))) '
      f'(property "Value" {q(FP)} (at 0 {cy + 1.5}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15)))) '
      f'(fp_rect (start {-EDGE} {-EDGE}) (end {EDGE} {EDGE}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab")) '
      f'(fp_line (start {-EDGE} {-EDGE + 2}) (end {-EDGE + 2} {-EDGE}) (stroke (width 0.1) (type solid)) (layer "F.Fab")) '
      f'(fp_rect (start {-cy} {-cy}) (end {cy} {cy}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd")) '
      f'(fp_circle (center {-cy - 0.6} -10.5) (end {-cy - 0.3} -10.5) (stroke (width 0.3) (type solid)) (fill yes) (layer "F.SilkS")) '
      f'(fp_text user "IPEX" (at -9.5 -9.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15)))) '
      + " ".join(pads) + ")")
(LIB / "ADSB_Test.pretty" / f"{FP}.kicad_mod").write_text(fp + "\n", encoding="utf-8", newline="\n")
print("symbol", NAME, "and footprint", FP, "written; WT01P4C5-S1 removed")
