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

All placement data is in the arrays at the top of this file, all with ONE coordinate rule (see there):
(x, y) = footprint origin in mm from the board's top-right corner as seen in KiCad's normal view
(x grows to the left, y down), rot = the orientation KiCad shows.
  EDGE_LEFT / EDGE_RIGHT / EDGE_TOP   edge connectors and switches: position along the edge only
                                      (snapped to the edge and turned to face out automatically)
  BIG                                 big parts (module, cans, sockets, headers): "REF": (x, y, rot)
  SLOTS_FRONT                         panel-cable slots (panel front-view coordinates, measured)
  PLACE                               one list per schematic page: ("REF", x, y, rot);
                                      uncommented lines are placed, commented lines parked beside the board
dump_placement.py (KiCad's Python) reads the saved PCB and refreshes every number (PLACE, BIG, EDGE_*), so
parts moved in KiCad are kept: `... python.exe boards/adsb-test/hardware/gen/dump_placement.py --write`.
Re-running OVERWRITES ADSB_Test.kicad_pcb. Before re-running after moving parts in KiCad, run
dump_placement.py --write so the moves are kept.
"""
import collections
import json
import re
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
PAPER = ("A2", 594.0, 420.0)        # page: board centred, parked parts in columns either side
OX, OY = (PAPER[1] - W) / 2, (PAPER[2] - H) / 2   # board top-left corner on the KiCad page
HOLE_IN = 4.0                       # corner hole centres, mm in from both edges

# ================================================================ PLACEMENT ARRAYS
# ONE coordinate rule for every array below (and the PLACE lists):
#   x, y   = the footprint ORIGIN (the position KiCad shows in the part's Properties), in mm from the board's
#            TOP-RIGHT corner as seen in KiCad's normal (top) view; x grows to the LEFT, y grows DOWN.
#            (= looking at the component side: from the top-left, x to the right. RF edge at x = 0,
#            digital edge at x = 204.9.)  KiCad's grid origin is put on that corner, so with
#            "relative to grid origin" KiCad shows X = -x, Y = y.
#   rot    = the orientation KiCad shows for the part (all parts are on the bottom side).
# dump_placement.py --write refreshes every number below from the saved PCB (moves made in KiCad).

# Edge parts: x (or y for the top edge) is snapped to the edge automatically and the part is turned to face
# out, so only the position ALONG the edge is given: ("REF", y) on the left/right edges, ("REF", x) on the top.
EDGE_LEFT = [("J1403", 33.0), ("J1201", 117.0)]                       # RF edge (x = 0)
EDGE_RIGHT = [("J901", 13.3), ("J1001", 29.22), ("J1101", 48.43), ("J801", 76.29), ("J1501", 93.52),
              ("SW401", 113.38), ("SW603", 124.93)]                   # digital edge (x = 204.9)
EDGE_TOP = [("J602", 108.0)]          # Wi-Fi RP-SMA, away from the RF-edge SMAs

# Big parts: "REF": (x, y, rot), same rule as PLACE. A part and its can (U1401/SH1401, U1201/SH1201) have
# different origins: move both together.
BIG = {
    "U601":   (126.81, 58.0, 180),    # OSPTEK ESP32-P4C5 module, between the LCD and touch sockets (short MIPI)

    "U1401":  (30.0, 34.75, 0),       # m1421, under can SH1401 (RF column, left edge)
    "SH1401": (30.0, 35.0, 180),

    "U1201":  (25.0, 117.96, 0),      # MAX-M10S, under can SH1201
    "SH1201": (25.0, 118.0, 180),

    "J1601":  (131.13, 127.25, 270),  # LA5016 2x20 header, horizontal along the bottom edge

    "J1301":  (99.9, 67.97, 180),     # LCD 30-pin FPC: in line with its slot (SLOTS_FRONT), opening towards it
    "J1302":  (146.9, 60.97, 180),    # touch 6-pin FPC: in line with its slot, opening towards it

    "J301":   (123.5, 8.47, 180),     # battery connector, charger zone (outside the battery footprint)

    "SW601":  (162.65, 9.75, 180),    # BOOT  (top band near the digital edge, clear of the battery)
    "SW602":  (173.65, 9.75, 180),    # RESET
    "J601":   (108.38, 10.5, 180),    # Wi-Fi U.FL (jumper from the module IPEX), just behind J602

    "J1401":  (15.0, 56.0, 180),      # m1421 JTAG (below the m1421 can)
    "J1402":  (25.0, 53.65, 180),     # ADSBee Dev Kit header (1x6, vertical, next to the m1421)

    "J1801":  (36.28, 86.51, 0),      # RP2040 GPIO header (DNP)
    "SW1801": (3.75, 77.75, 180),     # RP2040 BOOTSEL (Dev zone)
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

# Zone packer (floorplan.py zones): off now that PLACE lists every part. Set True to pack the key parts that are
# still commented out in PLACE into their zones (handy to seed a new layout, then dump_placement.py --write).
AUTO_ZONES = False
AUTO_PREFIX = ("U", "J", "SW", "Y", "BT")   # + LEDs
SPACE = 1.25                         # mm kept clear round each courtyard (2.5 mm between parts: room for the iron)

# One list per schematic page: ("REF", x, y, rot), same rule as above. Uncommented = placed, commented = parked.
# Parts placed by EDGE_* / BIG and the corner holes are listed as comments for reference only.
# >>> PLACE (rewritten by dump_placement.py --write; edit freely, keep the markers)
PLACE = {
    # ------------------------------------------------ page 2: Power Input
    "Power Input": [
        ("U201", 156.48, 4.42, 180),         # STUSB4500QTR
        # ("Q201", -50.41, 79.82, 180),      # FDS9435A
        # ("D202", -36.76, 78.74, 180),      # SS34
        # ("RS201", -79.11, 78.69, 180),     # 20m
        # ("R201", -57.51, 77.94, 180),      # 1k
        # ("R202", -62.76, 77.94, 180),      # 10k
        # ("R203", -68.01, 77.94, 180),      # 100k
        # ("R204", -73.26, 77.94, 180),      # 10k
        # ("C202", -13.90, 77.97, 180),      # 1uF
        # ("C203", -19.21, 77.97, 180),      # 1uF
        # ("C204", -24.52, 77.97, 180),      # 1uF 25V
        # ("C205", -29.83, 77.97, 180),      # 10uF 25V
        # ("TP201", -13.27, 85.32, 180),     # PD_ATTACH
        # ("TP202", -17.32, 85.32, 180),     # VBUS_USER
        # ("JP201", -43.51, 78.24, 180),     # Dev VBUS -> charger (default open)
    ],
    # ------------------------------------------------ page 3: Charger Battery
    "Charger Battery": [
        ("U301", 116.66, 9.75, 180),         # BQ25798
        ("U302", 145.91, 10.04, 180),        # MCP1703 3.0V (2 uA Iq)
        ("D301", 130.76, 2.25, 180),         # CHG (amber)
        # ("D302", -56.85, -116.31, 180),    # BAT43W
        # ("D303", -63.15, -116.31, 180),    # BAT43W
        # ("L301", -71.54, -113.92, 180),    # 2.2uH
        # J301: placed by BIG  (2S Li-ion pack (BAT+, GND, NTC))
        ("BT301", 140.43, 4.68, 180),        # CR1220 (optional)
        # ("RS301", -40.72, -107.12, 180),   # 10m
        # ("RS302", -47.17, -107.12, 180),   # 10m
        # ("R301", -79.39, -116.52, 180),    # 8.2k 1%
        # ("R302", -13.87, -107.87, 180),    # 10k
        # ("R303", -19.12, -107.87, 180),    # 5.23k 1%
        # ("R304", -24.37, -107.87, 180),    # 30.1k 1%
        # ("R305", -29.62, -107.87, 180),    # 100R
        # ("R306", -34.87, -107.87, 180),    # 2.2k
        # ("C301", -13.90, -120.00, 180),    # 47nF
        # ("C302", -19.21, -120.00, 180),    # 47nF
        # ("C303", -24.52, -120.00, 180),    # 10uF 25V
        # ("C304", -29.83, -120.00, 180),    # 10uF 25V
        # ("C305", -35.14, -120.00, 180),    # 10uF 25V
        # ("C306", -40.45, -120.00, 180),    # 10uF 25V
        # ("C307", -45.76, -120.00, 180),    # 10uF 25V
        # ("C308", -51.07, -120.00, 180),    # 100nF 25V
        # ("C309", -56.38, -120.00, 180),    # 4.7uF 10V
        # ("C310", -61.69, -120.00, 180),    # 10uF 25V
        # ("C311", -67.00, -120.00, 180),    # 10uF 25V
        # ("C312", -72.31, -120.00, 180),    # 10uF 25V
        # ("C313", -77.62, -120.00, 180),    # 10uF 25V
        # ("C314", -13.90, -116.49, 180),    # 10uF 25V
        # ("C315", -19.21, -116.49, 180),    # 100nF 25V
        # ("C316", -24.52, -116.49, 180),    # 10uF 25V
        # ("C317", -29.83, -116.49, 180),    # 10uF 25V
        # ("C318", -35.14, -116.49, 180),    # 1nF 50V
        # ("C319", -40.45, -116.49, 180),    # 1uF 25V
        # ("C320", -45.76, -116.49, 180),    # 1uF
        # ("C321", -51.07, -116.49, 180),    # 1uF
        # ("TP301", -52.42, -107.57, 180),   # CHG_QON
        # ("TP302", -56.47, -107.57, 180),   # BAT_PACK
        # ("TP303", -60.52, -107.57, 180),   # VSYS
        # ("TP304", -64.57, -107.57, 180),   # VBUS_CHG
        # ("TP305", -68.62, -107.57, 180),   # VBACKUP
    ],
    # ------------------------------------------------ page 4: Power Rails
    "Power Rails": [
        ("U411", 69.61, 2.59, 180),          # TPS62933
        ("U421", 63.11, 2.59, 180),          # TPS62933
        ("U430", 98.94, 3.09, 180),          # TPS22917
        ("U431", 91.44, 3.09, 180),          # TPS22917
        ("U432", 83.94, 3.09, 180),          # TPS22917
        ("U433", 76.44, 3.09, 180),          # TPS22917
        # ("L411", -49.78, 119.33, 180),     # 4.7uH
        # ("L421", -58.33, 119.33, 180),     # 4.7uH
        # SW401: placed by EDGE_RIGHT  (POWER (slide))
        # ("RS401", -51.22, 125.43, 180),    # 10m
        # ("RS402", -57.67, 125.43, 180),    # 20m
        # ("RS403", -64.12, 125.43, 180),    # 50m
        # ("RS404", -70.57, 125.43, 180),    # 50m
        # ("RS405", -77.02, 125.43, 180),    # 100m
        # ("RS406", -14.47, 129.81, 180),    # 100m
        # ("RS407", -20.92, 129.81, 180),    # 1R
        # ("RS408", -27.37, 129.81, 180),    # 1R
        # ("RS409", -33.82, 129.81, 180),    # 100m
        # ("R411", -65.23, 117.43, 180),     # 100k
        # ("R412", -70.48, 117.43, 180),     # 28k
        # ("R413", -75.73, 117.43, 180),     # 52.3k 1%
        # ("R414", -13.87, 124.68, 180),     # 10k 1%
        # ("R423", -19.12, 124.68, 180),     # 31.6k 1%
        # ("R424", -24.37, 124.68, 180),     # 10k 1%
        # ("R430", -29.62, 124.68, 180),     # 100R
        # ("R431", -34.87, 124.68, 180),     # 100R
        # ("R432", -40.12, 124.68, 180),     # 100R
        # ("R433", -45.37, 124.68, 180),     # 100R
        # ("C411", -13.90, 113.61, 180),     # 10uF 25V
        # ("C412", -19.21, 113.61, 180),     # 10uF 25V
        # ("C413", -24.52, 113.61, 180),     # 100nF
        # ("C414", -29.83, 113.61, 180),     # 33nF
        # ("C415", -35.14, 113.61, 180),     # 100nF
        # ("C416", -41.05, 113.78, 180),     # 22uF 10V
        # ("C417", -47.56, 113.78, 180),     # 22uF 10V
        # ("C421", -53.47, 113.61, 180),     # 10uF 25V
        # ("C422", -58.78, 113.61, 180),     # 10uF 25V
        # ("C423", -64.09, 113.61, 180),     # 100nF
        # ("C424", -69.40, 113.61, 180),     # 33nF
        # ("C425", -74.71, 113.61, 180),     # 100nF
        # ("C426", -14.50, 117.63, 180),     # 22uF 10V
        # ("C427", -21.01, 117.63, 180),     # 22uF 10V
        # ("C430", -26.92, 117.46, 180),     # 1nF
        # ("C431", -32.23, 117.46, 180),     # 1nF
        # ("C432", -37.54, 117.46, 180),     # 1nF
        # ("C433", -42.85, 117.46, 180),     # 1nF
        # ("TP401", -39.07, 129.36, 180),    # 5V
        # ("TP402", -43.12, 129.36, 180),    # 3V3
        # ("TP403", -47.17, 129.36, 180),    # VSYS
        # ("TP410", -51.22, 129.36, 180),    # 5V_SDR
        # ("TP411", -55.27, 129.36, 180),    # 5V_LCD
        # ("TP412", -59.32, 129.36, 180),    # 3V3_MCU
        # ("TP413", -63.37, 129.36, 180),    # 3V3_SD
        # ("TP414", -67.42, 129.36, 180),    # 3V3_ETH
        # ("TP415", -71.47, 129.36, 180),    # 3V3_GPS
        # ("TP416", -75.52, 129.36, 180),    # 3V3_M1421
        # ("TP417", -79.57, 129.36, 180),    # 3V3_PERIPH
    ],
    # ------------------------------------------------ page 5: Power Monitor
    "Power Monitor": [
        ("U501", 55.74, 3.90, 180),          # PAC1954 (PM1)
        ("U502", 47.74, 3.90, 180),          # PAC1954 (PM2)
        ("U503", 68.74, 9.40, 180),          # PAC1954 (PM3)
        # ("R501", -29.80, 99.57, 180),      # 0R (0x10)
        # ("R502", -35.05, 99.57, 180),      # 499R 1% (0x11)
        # ("R503", -40.30, 99.57, 180),      # 806R 1% (0x12)
        # ("R504", -45.55, 99.57, 180),      # 10k
        # ("C501", -13.90, 99.60, 180),      # 100nF
        # ("C502", -19.21, 99.60, 180),      # 100nF
        # ("C503", -24.52, 99.60, 180),      # 100nF
    ],
    # ------------------------------------------------ page 6: MCU Module
    "MCU Module": [
        # U601: placed by BIG  (ESP32-P4C5 Core (OSPTEK))
        ("Y601", 108.48, 46.04, 180),        # 32.768kHz
        # J601: placed by BIG  (U.FL Wi-Fi (from module IPEX))
        # J602: placed by EDGE_TOP  (RP-SMA Wi-Fi 2.4/5 GHz)
        # SW601: placed by BIG  (BOOT)
        # SW602: placed by BIG  (RESET)
        # SW603: placed by EDGE_RIGHT  (SLEEP/WAKE)
        # ("R601", -64.06, 59.53, 180),      # 10M
        # ("R602", -69.31, 59.53, 180),      # 2.2k
        # ("R603", -74.56, 59.53, 180),      # 2.2k
        # ("R604", -79.81, 59.53, 180),      # 4.7k
        # ("R605", -13.87, 63.38, 180),      # 10k
        # ("R606", -19.12, 63.38, 180),      # 330R
        # ("R607", -24.37, 63.38, 180),      # 10k
        # ("R608", -29.62, 63.38, 180),      # 10k
        # ("R609", -34.87, 63.38, 180),      # 470R
        # ("C601", -14.50, 59.74, 180),      # 22uF 10V
        # ("C602", -21.01, 59.74, 180),      # 22uF 10V
        # ("C603", -26.92, 59.56, 180),      # 100nF
        # ("C604", -32.23, 59.56, 180),      # 1uF
        # ("C605", -37.54, 59.56, 180),      # 22pF
        # ("C606", -42.85, 59.56, 180),      # 22pF
        # ("C607", -48.16, 59.56, 180),      # 1uF
        # ("C608", -53.47, 59.56, 180),      # 100nF
        # ("C609", -58.78, 59.56, 180),      # 100nF
        # ("TP601", -39.52, 63.69, 180),     # C5_IO27
        # ("TP602", -43.57, 63.69, 180),     # C5_IO25
        # ("TP603", -47.62, 63.69, 180),     # C5_IO24
        # ("TP604", -51.67, 63.69, 180),     # C5_IO23
        # ("TP605", -55.72, 63.69, 180),     # C5_IO6
        # ("TP606", -59.77, 63.69, 180),     # C5_IO5
        # ("TP607", -63.82, 63.69, 180),     # C5_IO4
        # ("TP608", -67.87, 63.69, 180),     # SLEEP_WAKE
        # ("TP609", -71.92, 63.69, 180),     # P4_GPIO20
        # ("TP610", -75.97, 63.69, 180),     # P4_GPIO36
        # ("TP611", -80.02, 63.69, 180),     # C5_PU
    ],
    # ------------------------------------------------ page 7: RTC
    "RTC": [
        ("U701", 136.91, 11.00, 180),        # DS3231M
        # ("R701", -24.49, 143.94, 180),     # 10k
        # ("C701", -13.90, 143.97, 180),     # 100nF
        # ("C702", -19.21, 143.97, 180),     # 100nF
        # ("TP701", -29.14, 144.24, 180),    # RTC_INT
    ],
    # ------------------------------------------------ page 8: Ethernet
    "Ethernet": [
        ("U801",  175.0, 70.0, 180),        # LAN8720A
        ("FB801", 175.0, 64.0, 180),        # 600R@100MHz
        ("Y801",  165.0, 70.0,  90),        # 25MHz
        # J801: placed by EDGE_RIGHT  (HR911105A)
        # ("R801", -74.78, 4.53, 180),       # 12.1k 1%
        # ("R802", -80.03, 4.53, 180),       # 10k
        # ("R803", -13.87, 8.38, 180),       # 10k
        # ("R804", -19.12, 8.38, 180),       # 10k
        # ("R805", -24.37, 8.38, 180),       # 1.5k
        # ("R806", -29.62, 8.38, 180),       # 10k
        # ("R807", -34.87, 8.38, 180),       # 33R
        # ("R808", -40.12, 8.38, 180),       # 49.9R 1%
        # ("R809", -45.37, 8.38, 180),       # 49.9R 1%
        # ("R810", -50.62, 8.38, 180),       # 49.9R 1%
        # ("R811", -55.87, 8.38, 180),       # 49.9R 1%
        # ("R812", -61.12, 8.38, 180),       # 270R
        # ("R813", -66.37, 8.38, 180),       # 270R
        # ("R814", -71.62, 8.38, 180),       # 10k
        # ("R815", -76.87, 8.38, 180),       # 10k
        # ("R816", -13.87, 11.83, 180),      # 10k
        # ("C801", -14.50, 4.74, 180),       # 10uF
        # ("C802", -20.41, 4.56, 180),       # 100nF
        # ("C803", -26.32, 4.74, 180),       # 10uF
        # ("C804", -32.23, 4.56, 180),       # 100nF
        # ("C805", -37.54, 4.56, 180),       # 100nF
        # ("C806", -42.85, 4.56, 180),       # 1uF
        # ("C807", -48.16, 4.56, 180),       # 470pF
        # ("C808", -53.47, 4.56, 180),       # 27pF
        # ("C809", -58.78, 4.56, 180),       # 27pF
        # ("C810", -64.09, 4.56, 180),       # 22nF
        # ("TP801", -18.52, 12.13, 180),     # ETH_REF_CLK
        # ("TP802", -22.57, 12.13, 180),     # ETH_1V2
    ],
    # ------------------------------------------------ page 9: User USB-C
    "User USB-C": [
        ("U901", 156.51, 13.40, 180),        # CP2102N-A02-GQFN24
        ("U902", 177.21, 3.09, 180),         # USBLC6-2SC6
        ("D901", 170.26, 2.25, 180),         # TX green
        ("D902", 177.76, 18.25, 180),        # RX yellow
        # ("D903", -31.45, 216.26, 180),     # SMAJ20A
        # J901: placed by EDGE_RIGHT  (User USB-C (PD sink + UART))
        # ("R901", -38.40, 215.46, 180),     # 22.1k
        # ("R902", -43.65, 215.46, 180),     # 47.5k
        # ("R903", -48.90, 215.46, 180),     # 10k
        # ("R904", -54.15, 215.46, 180),     # 1k
        # ("R905", -59.40, 215.46, 180),     # 1k
        # ("C901", -13.90, 215.50, 180),     # 1uF
        # ("C902", -19.21, 215.50, 180),     # 100nF
        # ("C903", -24.52, 215.50, 180),     # 10uF 25V
    ],
    # ------------------------------------------------ page 10: Dev USB Hub
    "Dev USB Hub": [
        ("U1001", 154.21, 47.09, 180),       # USBLC6-2SC6
        ("U1002", 146.73, 47.09, 180),       # AP2112K-3.3
        ("U1003", 175.51, 49.40, 180),       # USB2514B
        ("Y1001", 164.01, 47.40, 180),       # 24MHz
        # J1001: placed by EDGE_RIGHT  (Dev USB-C)
        # ("R1001", -78.79, -67.89, 180),    # 5.1k
        # ("R1002", -13.87, -64.04, 180),    # 5.1k
        # ("R1003", -19.12, -64.04, 180),    # 10k
        # ("R1004", -24.37, -64.04, 180),    # 10k
        # ("R1005", -29.62, -64.04, 180),    # 10k
        # ("R1006", -34.87, -64.04, 180),    # 10k
        # ("R1007", -40.12, -64.04, 180),    # 10k
        # ("R1008", -45.37, -64.04, 180),    # 10k
        # ("R1009", -50.62, -64.04, 180),    # 12k 1%
        # ("R1010", -55.87, -64.04, 180),    # 10k
        # ("R1011", -61.12, -64.04, 180),    # 100k
        # ("R1012", -66.37, -64.04, 180),    # 100k
        # ("R1013", -71.62, -64.04, 180),    # 1M
        # ("C1001", -13.90, -67.86, 180),    # 1uF
        # ("C1002", -19.81, -67.69, 180),    # 10uF
        # ("C1003", -25.72, -67.86, 180),    # 1uF
        # ("C1004", -31.03, -67.86, 180),    # 1uF
        # ("C1005", -36.34, -67.86, 180),    # 100nF
        # ("C1006", -41.65, -67.86, 180),    # 27pF
        # ("C1007", -46.96, -67.86, 180),    # 27pF
        # ("C1008", -52.27, -67.86, 180),    # 100nF
        # ("C1009", -57.58, -67.86, 180),    # 100nF
        # ("C1010", -62.89, -67.86, 180),    # 100nF
        # ("C1011", -68.20, -67.86, 180),    # 100nF
        # ("C1012", -73.51, -67.86, 180),    # 4.7uF
        # ("TP1001", -76.27, -63.74, 180),   # VBUS_DEV
        # ("TP1002", -80.32, -63.74, 180),   # 3V3_DEV
    ],
    # ------------------------------------------------ page 11: USB Host
    "USB Host": [
        ("U1101", 164.86, 55.04, 180),       # TPS259621DDA
        ("U1102", 154.21, 53.59, 180),       # USBLC6-2SC6
        # J1101: placed by EDGE_RIGHT  (USB-A (SDR hub))
        # ("R1101", -40.75, 196.31, 180),    # 604R 1%
        # ("R1102", -46.00, 196.31, 180),    # 402k 1%
        # ("R1103", -51.25, 196.31, 180),    # 10k
        # ("R1104", -56.50, 196.31, 180),    # 100k
        # ("C1101", -13.90, 196.35, 180),    # 10nF
        # ("C1102", -19.21, 196.35, 180),    # 1uF
        # ("C1103", -27.34, 198.92, 180),    # 150uF 10V
        # ("C1104", -35.47, 196.35, 180),    # 100nF
        # ("TP1101", -61.15, 196.62, 180),   # VBUS_HOST
        # ("TP1102", -65.20, 196.62, 180),   # USBA_FAULT
    ],
    # ------------------------------------------------ page 12: GPS
    "GPS": [
        # U1201: placed by BIG  (MAX-M10S)
        ("D1202",   5.0, 105.0, 180),        # PPS green

        ("D1201",  12.0, 115.0,  90),        # ESD7351XV2T1G
        ("L1201",   7.5, 120.0,  90),        # 47nH
        ("R1201",  12.0, 120.0, 270),        # 10R
        ("C1204",   7.5, 127.0, 270),        # 10nF

        # J1201: placed by EDGE_LEFT  (SMA GNSS (active antenna))
        # SH1201: placed by BIG  (RF can frame (DNP))
        # ("R1202", -51.07, 26.38, 180),     # 1k
        # ("C1201", -14.50, 26.58, 180),     # 10uF
        # ("C1202", -20.41, 26.41, 180),     # 100nF
        # ("C1203", -25.72, 26.41, 180),     # 100nF
        # ("TP1201", -55.72, 26.68, 180),    # GPS_EXTINT
        # ("TP1202", -59.77, 26.68, 180),    # GPS_SAFEBOOT
        # ("TP1203", -63.82, 26.68, 180),    # GPS_RESET_N
        # ("TP1204", -67.87, 26.68, 180),    # GPS_PPS
    ],
    # ------------------------------------------------ page 13: Display Touch
    "Display Touch": [
        ("U1301", 94.83, 96.69, 180),        # AP3012KTR-E1
        ("U1302", 87.33, 96.69, 180),        # AP2112K-1.8
        ("U1303", 102.31, 96.69, 180),       # AP3032KTR-G1
        # ("D1301", -73.47, -23.53, 180),    # 1N5819HW
        # ("D1302", -14.72, -18.85, 180),    # BAT54S
        # ("D1303", -21.17, -19.68, 180),    # BZT52C7V5S
        # ("D1304", -27.67, -18.85, 180),    # BAT54S
        # ("D1305", -34.12, -19.68, 180),    # BZT52C18S
        # ("D1306", -40.26, -19.68, 180),    # 1N5819HW
        # ("L1301", -46.74, -18.58, 180),    # 10uH
        # ("L1302", -53.35, -18.58, 180),    # 10uH 0.55A
        # J1301: placed by BIG  (LCD FPC 30p 0.5mm)
        # J1302: placed by BIG  (Touch FPC 6p 0.5mm)
        # ("R1301", -59.28, -19.88, 180),    # 10k
        # ("R1302", -64.53, -19.88, 180),    # 22k 1%
        # ("R1303", -69.78, -19.88, 180),    # 3.3k 1%
        # ("R1304", -75.03, -19.88, 180),    # 220R 1%
        # ("R1305", -13.87, -13.83, 180),    # 51k 1%
        # ("R1306", -19.12, -13.83, 180),    # 220R 1%
        # ("R1307", -24.37, -13.83, 180),    # 51k 1%
        # ("R1308", -29.62, -13.83, 180),    # 2k 1%
        # ("R1309", -34.87, -13.83, 180),    # 1k 1%
        # ("R1310", -40.12, -13.83, 180),    # 100k
        # ("R1311", -45.37, -13.83, 180),    # 0R
        # ("R1312", -50.62, -13.83, 180),    # 5.1k 1%
        # ("R1313", -56.47, -13.65, 180),    # 1.3R 1%
        # ("R1314", -62.32, -13.83, 180),    # 68k
        # ("R1315", -67.57, -13.83, 180),    # 10k
        # ("R1316", -72.82, -13.83, 180),    # 0R
        # ("R1317", -78.07, -13.83, 180),    # 10k
        # ("R1318", -13.87, -10.02, 180),    # 10k
        # ("R1319", -19.12, -10.02, 180),    # 0R
        # ("R1320", -24.37, -10.02, 180),    # 10k
        # ("R1321", -29.62, -10.02, 180),    # 0R
        # ("R1322", -34.87, -10.02, 180),    # 0R
        # ("R1323", -40.12, -10.02, 180),    # 0R
        # ("R1324", -45.37, -10.02, 180),    # 10k
        # ("C1301", -14.50, -27.38, 180),    # 10uF
        # ("C1302", -20.41, -27.55, 180),    # 1uF
        # ("C1303", -25.72, -27.55, 180),    # 1uF 25V
        # ("C1304", -31.03, -27.55, 180),    # 100nF 25V
        # ("C1305", -36.94, -27.38, 180),    # 10uF 25V
        # ("C1306", -42.85, -27.55, 180),    # 100nF 50V
        # ("C1307", -48.16, -27.55, 180),    # 1uF 25V
        # ("C1308", -53.47, -27.55, 180),    # 100nF 25V
        # ("C1309", -59.38, -27.38, 180),    # 10uF 25V
        # ("C1310", -65.29, -27.55, 180),    # 100nF 50V
        # ("C1311", -70.60, -27.55, 180),    # 1uF 50V
        # ("C1312", -75.91, -27.55, 180),    # 100nF 50V
        # ("C1313", -14.50, -23.53, 180),    # 10uF 25V
        # ("C1314", -21.01, -23.53, 180),    # 10uF
        # ("C1315", -26.92, -23.70, 180),    # 100nF
        # ("C1316", -32.23, -23.70, 180),    # 1uF
        # ("C1317", -37.54, -23.70, 180),    # 1uF
        # ("C1318", -43.45, -23.53, 180),    # 10uF
        # ("C1319", -49.96, -23.53, 180),    # 1uF 50V
        # ("C1320", -56.47, -23.53, 180),    # 1uF 50V
        # ("C1321", -62.38, -23.70, 180),    # 100nF
        # ("C1322", -67.69, -23.70, 180),    # 100nF
        # ("TP1301", -50.02, -9.72, 180),    # AVDD
        # ("TP1302", -54.07, -9.72, 180),    # VGH
        # ("TP1303", -58.12, -9.72, 180),    # VGL
        # ("TP1304", -62.17, -9.72, 180),    # VCOM
        # ("TP1305", -66.22, -9.72, 180),    # VCC_1V8
        # ("TP1306", -70.27, -9.72, 180),    # LED_P
    ],
    # ------------------------------------------------ page 14: M1421
    "M1421": [
        # U1401: placed by BIG  (ADSBee m1421)
        ("U1402", 55.0, 25.0, 180),         # 74LVC1G97 (AND)
        ("U1403", 55.0, 32.0, 180),         # 74LVC1G32
        ("U1404", 55.0, 39.0, 180),         # 74LVC1G07
        ("U1405", 11.0, 32.0, 270),         # SCN-2-11+
        ("D1401",  5.0, 20.0, 180),         # RED 1090
        ("D1402",  5.0, 15.0, 180),         # GREEN UAT
        ("D1403",  7.5, 32.0,  90),         # ESD7351XV2T1G
        # J1401: placed by BIG  (m1421 JTAG (J-Link))
        # J1402: placed by BIG  (ADSBee 1421 Dev Kit)
        # J1403: placed by EDGE_LEFT  (SMA 1090/978)
        # SH1401: placed by BIG  (RF can frame (DNP))
        # ("R1401", -28.59, 40.93, 180),     # 100k
        # ("R1402", -33.84, 40.93, 180),     # 100k
        # ("R1403", -39.09, 40.93, 180),     # 100k
        # ("R1404", -44.34, 40.93, 180),     # 100k
        # ("R1405", -49.59, 40.93, 180),     # 100k
        # ("R1406", -54.84, 40.93, 180),     # 287R
        # ("R1407", -60.09, 40.93, 180),     # 115R
        # ("R1408", -65.34, 40.93, 180),     # 100R
        # ("R1409", -70.59, 40.93, 180),     # 100k
        # ("C1401", -13.90, 40.96, 180),     # 1uF
        # ("C1402", -19.21, 40.96, 180),     # 100nF
        # ("TP1401", -75.24, 41.24, 180),    # SD23
        # ("TP1402", -79.29, 41.24, 180),    # SD24
        # ("TP1403", -13.27, 45.28, 180),    # SD25
        # ("TP1404", -17.32, 45.28, 180),    # LD11
        # ("TP1405", -21.37, 45.28, 180),    # LD09
        # ("TP1406", -25.42, 45.28, 180),    # LD08
        # ("TP1407", -29.47, 45.28, 180),    # LRST
        # ("TP1408", -33.52, 45.28, 180),    # CSMI
        # ("TP1409", -37.57, 45.28, 180),    # CSMO
        # ("TP1410", -41.62, 45.28, 180),    # CSCK
        # ("TP1411", -45.67, 45.28, 180),    # LRCS
        # ("TP1412", -49.72, 45.28, 180),    # LBSY
    ],
    # ------------------------------------------------ page 15: Storage Misc
    "Storage Misc": [
        ("U1501", 175.76, 120.05, 180),      # TCA6408APW
        # ("Q1501", -31.85, 159.51, 180),    # AO3401A
        # J1501: placed by EDGE_RIGHT  (microSD (push-pull, detect))
        # ("R1501", -37.95, 158.49, 180),    # 10k
        # ("R1502", -43.20, 158.49, 180),    # 10k
        # ("R1503", -48.45, 158.49, 180),    # 10k
        # ("R1504", -53.70, 158.49, 180),    # 10k
        # ("R1505", -58.95, 158.49, 180),    # 10k
        # ("R1506", -64.20, 158.49, 180),    # 10k
        # ("R1507", -69.45, 158.49, 180),    # 10k
        # ("R1508", -74.70, 158.49, 180),    # 10k
        # ("R1509", -79.95, 158.49, 180),    # 10k
        # ("R1510", -13.87, 163.76, 180),    # 100k
        # ("R1511", -19.12, 163.76, 180),    # 100k
        # ("R1512", -24.37, 163.76, 180),    # 100k
        # ("R1513", -29.62, 163.76, 180),    # 100k
        # ("C1501", -14.50, 158.69, 180),    # 10uF
        # ("C1502", -20.41, 158.52, 180),    # 100nF
        # ("C1503", -25.72, 158.52, 180),    # 100nF
        # ("TP1501", -34.27, 164.06, 180),   # SD_VDD
    ],
    # ------------------------------------------------ page 16: Test Debug
    "Test Debug": [
        # J1601: placed by BIG  (Kingst LA5016 (2x20 keyed))
        # ("R1601", -13.87, 178.31, 180),    # 100R
        # ("R1602", -19.12, 178.31, 180),    # 100R
        # ("R1603", -24.37, 178.31, 180),    # 100R
        # ("R1604", -29.62, 178.31, 180),    # 100R
        # ("R1605", -34.87, 178.31, 180),    # 100R
        # ("R1606", -40.12, 178.31, 180),    # 100R
        # ("R1607", -45.37, 178.31, 180),    # 100R
        # ("R1608", -50.62, 178.31, 180),    # 100R
        # ("R1609", -55.87, 178.31, 180),    # 100R
        # ("R1610", -61.12, 178.31, 180),    # 100R
        # ("R1611", -66.37, 178.31, 180),    # 100R
        # ("R1612", -71.62, 178.31, 180),    # 100R
        # ("R1613", -76.87, 178.31, 180),    # 100R
        # ("R1614", -13.87, 181.76, 180),    # 100R
        # ("R1615", -19.12, 181.76, 180),    # 100R
        # ("R1616", -24.37, 181.76, 180),    # 100R
        # ("R1617", -29.62, 181.76, 180),    # 0R
        # ("TP1601", -34.27, 182.06, 180),   # LA_PWM1
        # ("TP1602", -38.32, 182.06, 180),   # LA_PWM2
        # ("TP1603", -42.37, 182.06, 180),   # GND
        # ("TP1604", -46.42, 182.06, 180),   # GND
        # ("TP1605", -50.47, 182.06, 180),   # GND
        # ("TP1606", -54.52, 182.06, 180),   # GND
        # H1601: corner mounting hole
        # H1602: corner mounting hole
        # H1603: corner mounting hole
        # H1604: corner mounting hole
    ],
    # ------------------------------------------------ page 17: Dev UARTs
    "Dev UARTs": [
        ("U1701", 98.01, 52.00, 180),        # FT2232HL
        ("U1702", 85.01, 48.00, 180),        # 93LC56B
        ("U1703", 64.33, 47.09, 180),        # 74LVC1G07
        ("U1704", 49.83, 47.09, 180),        # 74LVC1G125
        ("U1705", 64.33, 53.59, 180),        # 74LVC1G07
        ("U1706", 49.83, 53.59, 180),        # 74LVC1G125
        # ("Q1701", -73.13, -91.96, 180),    # MMBT3904
        # ("Q1702", -14.72, -86.69, 180),    # MMBT3904
        # ("Q1703", -21.67, -86.69, 180),    # MMBT3904
        # ("Q1704", -28.62, -86.69, 180),    # MMBT3904
        ("Y1701", 74.11, 47.40, 180),        # 12MHz
        # ("J1701", 0.0, 0.0, 180),          # FT2232H ch A port (pins DNP), 2x10
        # ("J1702", 0.0, 0.0, 180),          # FT2232H ch B port (pins DNP), 2x10
        # ("R1701", -34.72, -87.71, 180),    # 12k 1%
        # ("R1702", -39.97, -87.71, 180),    # 10k
        # ("R1703", -45.22, -87.71, 180),    # 2.2k
        # ("R1704", -50.47, -87.71, 180),    # 10k
        # ("R1705", -55.72, -87.71, 180),    # 10k
        # ("R1706", -60.97, -87.71, 180),    # 10k
        # ("R1707", -66.22, -87.71, 180),    # 10k
        # ("R1708", -71.47, -87.71, 180),    # 10k
        # ("R1709", -76.72, -87.71, 180),    # 10k
        # ("R1710", -13.87, -82.44, 180),    # 10k
        # ("R1711", -19.12, -82.44, 180),    # 10k
        # ("R1712", -24.37, -82.44, 180),    # 10k
        # ("C1701", -13.90, -92.96, 180),    # 100nF
        # ("C1702", -19.21, -92.96, 180),    # 100nF
        # ("C1703", -24.52, -92.96, 180),    # 100nF
        # ("C1704", -29.83, -92.96, 180),    # 100nF
        # ("C1705", -35.14, -92.96, 180),    # 4.7uF
        # ("C1706", -40.45, -92.96, 180),    # 27pF
        # ("C1707", -45.76, -92.96, 180),    # 27pF
        # ("C1708", -51.07, -92.96, 180),    # 100nF
        # ("C1709", -56.38, -92.96, 180),    # 100nF
        # ("C1710", -61.69, -92.96, 180),    # 100nF
        # ("C1711", -67.00, -92.96, 180),    # 100nF
        # ("TP1701", -29.02, -82.14, 180),   # FT_A_DTR
        # ("TP1702", -33.07, -82.14, 180),   # FT_A_RTS
        # ("TP1703", -37.12, -82.14, 180),   # FT_B_DTR
        # ("TP1704", -41.17, -82.14, 180),   # FT_B_RTS
    ],
    # ------------------------------------------------ page 18: Dev m1421 Programmer
    "Dev m1421 Programmer": [
        ("U1801", 50.0,  70.0,  90),        # RP2040
        ("U1802", 50.0,  83.0,   0),        # W25Q16JVSS
        ("U1803", 42.0,  60.0,   0),        # 74LVC1G125
        ("U1804", 51.0,  60.0,   0),        # 74LVC1G125
        ("U1805", 58.0,  60.0,   0),        # 74LVC1G125
        ("U1806", 65.0,  60.0,   0),        # 74LVC1G125
        ("D1801",  5.0,  70.0, 180),        # 1N4148W
        ("D1802",  5.0,  60.0, 180),        # WS2812B
        ("Y1801", 65.0,  70.0,  90),        # 12MHz
        # J1801: placed by BIG  (RP2040 GPIO (pins DNP))
        ("J1802",  5.0,  90.0, 180),        # RP2040 SWD
        # SW1801: placed by BIG  (BOOTSEL (programmer))
        # ("R1801", -25.48, -45.98, 180),    # 27R
        # ("R1802", -30.73, -45.98, 180),    # 27R
        ("R1803", 58.0, 67.0,   0),     # 1k for Y1801
        # ("R1804", -41.23, -45.98, 180),    # 10k
        # ("R1805", -46.48, -45.98, 180),    # 10k
        # ("R1806", -51.73, -45.98, 180),    # 1k
        # ("R1807", -56.98, -45.98, 180),    # 330R
        # ("R1808", -62.23, -45.98, 180),    # 0R
        # ("R1809", -67.48, -45.98, 180),    # 0R
        # ("R1810", -72.73, -45.98, 180),    # 10k
        # ("R1811", -77.98, -45.98, 180),    # 100k
        # ("R1812", -13.87, -42.13, 180),    # 0R
        # ("R1813", -19.12, -42.13, 180),    # 0R
        # ("C1801", -13.90, -49.46, 180),    # 27pF
        # ("C1802", -19.21, -49.46, 180),    # 27pF
        # ("C1803", -24.52, -49.46, 180),    # 1uF
        # ("C1804", -29.83, -49.46, 180),    # 1uF
        # ("C1805", -35.14, -49.46, 180),    # 100nF
        # ("C1806", -40.45, -49.46, 180),    # 100nF
        # ("C1807", -45.76, -49.46, 180),    # 100nF
        # ("C1808", -51.07, -49.46, 180),    # 100nF
        # ("C1809", -56.38, -49.46, 180),    # 100nF
        # ("C1810", -61.69, -49.46, 180),    # 100nF
        # ("C1811", -67.00, -49.46, 180),    # 100nF
        # ("C1812", -72.31, -49.46, 180),    # 100nF
        # ("C1813", -77.62, -49.46, 180),    # 100nF
        # ("C1814", -13.90, -45.95, 180),    # 100nF
        # ("TP1801", -23.77, -41.83, 180),   # RP_SWCLK
        # ("TP1802", -27.82, -41.83, 180),   # RP_SWDIO
        # ("TP1803", -31.87, -41.83, 180),   # RP_RUN
    ],
}
# <<< PLACE

# ================================================================ derived from the arrays
PANEL_BOTTOM = (H + PH) / 2            # bottom-view y of the panel's bottom edge
# (name, bottom-view x centre, length, bottom-view y centre, height)
SLOTS = [(n, W - (W - PW) / 2 - (a + b) / 2, b - a, PANEL_BOTTOM - (up + h / 2), h) for n, a, b, up, h in SLOTS_FRONT]
# edge parts: ref -> (side, origin position along the edge)
EDGE = {**{r: ("L", v) for r, v in EDGE_LEFT}, **{r: ("R", v) for r, v in EDGE_RIGHT},
        **{r: ("T", v) for r, v in EDGE_TOP}}
PLACED_BY_PAGE = {e[0]: tuple(e[1:]) for page in PLACE.values() for e in page}


def mm(v):
    return pcbnew.FromMM(v)


def top(bx, by):
    """bottom-view (bx, by) -> KiCad top-view point (mirror in x)."""
    return pcbnew.VECTOR2I(mm(OX + W - bx), mm(OY + by))


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


def place_on_edge(fp, side, along):
    """Turn the part to face out of its edge, snap it to the edge ('PCB Edge' marker, edge-mount pads or body front)
    and put its ORIGIN at `along`: y for 'L' (RF edge, x = 0) and 'R' (digital edge), x for 'T' (top edge)."""
    if side == "T":
        turn_to(fp, (0, -1))
        em = edge_marker(fp)
        front = em[1] if em else front_box(fp).GetTop()
        fp.SetPosition(pcbnew.VECTOR2I(top(along, 0).x, fp.GetPosition().y + int(mm(OY) - front)))
        return
    turn_to(fp, (1, 0) if side == "L" else (-1, 0))
    target_x = mm(OX + W) if side == "L" else mm(OX)
    em = edge_marker(fp)
    if em:                                   # the marker line on the board edge
        front = em[0]
    else:                                    # body (or edge-mount pads) flush with the edge
        b = front_box(fp)
        front = b.GetRight() if side == "L" else b.GetLeft()
    fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x + int(target_x - front), mm(OY + along)))


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
    text = re.sub(r'\(paper "[^"]*"\)', f'(paper "{PAPER[0]}")', text, count=1)   # page size (no Python API)
    PCB.write_text(text, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- zone placement of the key parts
# ICs, connectors, switches, crystals, LEDs and the coin-cell holder go into their sheet's zone from
# floorplan.py (same bottom-view coordinates). Passives and test pads stay parked: they go next to their IC by hand.
sys.path.insert(0, str(ROOT / "boards/adsb-test/hardware/floorplan"))
import floorplan  # noqa: E402


def is_auto(ref, fpid):
    pre = re.sub(r"\d.*", "", ref)
    return pre in AUTO_PREFIX or (pre == "D" and "LED" in fpid.upper())


def fp_box(fp):
    """Courtyard box (bottom courtyard after the flip), else the body."""
    for layer in (pcbnew.B_CrtYd, pcbnew.F_CrtYd):
        try:
            cy = fp.GetCourtyard(layer)
            if cy.OutlineCount():
                return cy.BBox()
        except Exception:  # noqa: BLE001 - older API: fall back to the body box
            break
    return body_box(fp)


def place_in_zones(board, fps_by_sheet, occupied):
    """Pack each sheet's key parts into its zone (top-view coordinates). Returns the refs left over."""
    zones = {}
    for name, (x0, y0, x1, y1, sheets) in floorplan.layout(W, H).items():
        for s in sheets:
            zones[s] = (name, mm(OX + W - x1), mm(OY + y0), mm(OX + W - x0), mm(OY + y1))
    left = []
    step, sp = mm(0.5), mm(SPACE)
    for sheet, fps in fps_by_sheet.items():
        if sheet not in zones:
            left += [f.GetReference() for f in fps]
            continue
        _, zx0, zy0, zx1, zy1 = zones[sheet]
        for fp in sorted(fps, key=lambda f: -fp_box(f).GetArea()):
            done = False
            for turn in (0, 90):
                if turn:
                    fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 90)
                b = fp_box(fp)
                w, h = b.GetWidth() + 2 * sp, b.GetHeight() + 2 * sp
                y = zy0
                while y + h <= zy1 and not done:
                    x = zx0
                    while x + w <= zx1:
                        cand = pcbnew.BOX2I(pcbnew.VECTOR2I(x, y), pcbnew.VECTOR2L(w, h))
                        if not any(cand.Intersects(o) for o in occupied):
                            fp.Move(pcbnew.VECTOR2I(x + sp - b.GetX(), y + sp - b.GetY()))
                            occupied.append(cand)
                            done = True
                            break
                        x += step
                    y += step
                if done:
                    break
            if not done:
                left.append(fp.GetReference())
    return left


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
    ds.SetGridOrigin(top(0, 0))          # bottom-view board corner: KiCad X (relative) = -bx, Y = by
    ds.SetAuxOrigin(top(0, 0))
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
        elif ref in BIG or ref in PLACED_BY_PAGE:                        # BIG / PLACE: origin (x, y) + rotation
            x, y, rot = BIG[ref] if ref in BIG else PLACED_BY_PAGE[ref]
            fp.SetOrientationDegrees(rot)
            fp.SetPosition(top(x, y))
            placed.append(ref)
        else:
            parked[c["sheet"]].append(fp)
    refs = {c["ref"] for c in comps}
    for ref in PLACED_BY_PAGE:
        if ref not in refs:
            print("  PLACE lists a part that is not in the schematic:", ref)
        elif ref in EDGE or ref in BIG:
            print("  PLACE entry ignored (placed by EDGE_*/BIG):", ref)

    # optional: key parts still commented out in PLACE into their zones, clear of everything placed so far,
    # the slots and the corner holes
    zoned = 0
    occupied = [fp_box(f) for f in board.GetFootprints() if f.GetReference() in placed]
    for _, bx, length, by, height in SLOTS:
        c = top(bx, by)
        occupied.append(pcbnew.BOX2I(pcbnew.VECTOR2I(c.x - mm(length / 2 + 1), c.y - mm(height / 2 + 1)),
                                     pcbnew.VECTOR2L(mm(length + 2), mm(height + 2))))
    for hx, hy in corners:
        c = top(hx, hy)
        occupied.append(pcbnew.BOX2I(pcbnew.VECTOR2I(c.x - mm(4), c.y - mm(4)), pcbnew.VECTOR2L(mm(8), mm(8))))
    auto = collections.defaultdict(list)
    if AUTO_ZONES:
        for sheet, fps in parked.items():
            for f in fps:
                if is_auto(f.GetReference(), f.GetFPID().GetLibItemName().wx_str()):
                    auto[sheet].append(f)
        left = place_in_zones(board, auto, occupied)
        zoned = sum(len(v) for v in auto.values()) - len(left)
        for sheet in parked:
            parked[sheet] = [f for f in parked[sheet] if f not in auto[sheet] or f.GetReference() in left]
        if left:
            print("  did not fit their zone (parked):", " ".join(sorted(left)))

    # park the rest on the page either side of the board, one block per sheet
    columns = [OX + W + 12, OX + W + 92, OX - 92, OX - 172]
    col = 0
    col_x, y = columns[col], 15.0
    for sheet in sorted(parked):
        if not parked[sheet]:
            continue
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
        if y > PAPER[2] - 60 and col + 1 < len(columns):
            col += 1
            col_x, y = columns[col], 15.0

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
    print(f"wrote {PCB.name}: {len(comps)} parts, {len(placed)} placed ({len(PLACED_BY_PAGE)} from PLACE), "
          f"{zoned} by the zone packer, "
          f"{sum(len(v) for v in parked.values())} parked, "
          f"{len(nets)} nets")


if __name__ == "__main__":
    main()
