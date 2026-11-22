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
dump_placement.py --write so the moves are kept. Tracks, vias and hand-drawn zones ARE kept (copied over by net
name); options: --clear-routing (drop all routing), --keep-locked (keep only items locked in KiCad).
Ground plane / fills / ground vias are regenerated every run (COPPER settings below; helpers in copper.py).
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

PW, PH = 164.9, 100.0  # panel (on the top side)
GAP = 20.0  # border round the panel (Q28: 20 mm since 2026-10-20, room for hand soldering)
W, H = PW + 2 * GAP, PH + 2 * GAP  # board 204.9 x 140
PX0, PY0 = (W - PW) / 2, (
    H - PH
) / 2  # panel corner (bottom view; the panel is centred, so either corner)
PAPER = ("A2", 594.0, 420.0)  # page: board centred, parked parts in columns either side
OX, OY = (PAPER[1] - W) / 2, (
    PAPER[2] - H
) / 2  # board top-left corner on the KiCad page
HOLE_IN = 4.0  # corner hole centres, mm in from both edges

# ================================================================ COPPER
# Layers (parts on B.Cu): B.Cu = parts + critical routing, In2.Cu = SOLID GROUND (the reference plane right under
# the component side: every 50/90/100 ohm trace runs on B.Cu over it; no tracks on it - it is a "power" layer, so
# Freerouting leaves it alone), In1.Cu = power + slow signals, F.Cu = slow signals. Ground fill on the other three.
PLANE = "In2.Cu"
GND_FILLS = ("B.Cu", "In1.Cu", "F.Cu")
ZONE_CLEARANCE = 0.2  # also the 50R CPWG gap to ground
EDGE_PULLBACK = 0.5  # zones stop this far from the board edge
GND_VIAS = True  # a via (0.6/0.3) beside every small SMD ground pad, joined by a 0.3 mm stub
# Power islands: (net, layer, ICs, radius mm). A copper island on `layer` round each IC, covering the net's pads
# within `radius` of it, and a via beside each of those pads: tracks wide enough for power do not fit into the
# 0.4/0.5 mm-pitch pins, a via per pin into an island does. The islands are joined to each other by ordinary tracks.
POWER_ISLANDS = [
    ("3V3_DEV", "In1.Cu", ("U1003", "U1701", "U1801"), 9.0),
]
# Routing is KEPT across a rebuild: tracks, vias and hand-drawn zones in the old ADSB_Test.kicad_pcb are copied into
# the new one by net name. Pass --clear-routing to drop them all, --keep-locked to keep only items locked in KiCad.
# (The AUTO_* zones and the AUTO_GND_VIAS group are regenerated every run.)

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
EDGE_LEFT = [("J1403", 33.0), ("J1201", 117.0)]  # RF edge (x = 0)

EDGE_RIGHT = [
    ("J901", 13.3), # USB C USER
    
    ("J1001", 29.22), # USB C Dev
    
    ("J1101", 60.0), # USB A host
    
    ("J1501", 90.0), # SD

    ("J801", 120.0), # Ethernet
]  # digital edge (x = 204.9)

EDGE_TOP = [("J602", 108.0), 
            ("SW401", 180.0), 
            ("SW603", 160.0),
]  # Wi-Fi RP-SMA, away from the RF-edge SMAs

# Big parts: "REF": (x, y, rot), same rule as PLACE. A part and its can (U1401/SH1401, U1201/SH1201) have
# different origins: move both together.
BIG = {
    "J1301": (
        99.9,
        67.97,
        180,
    ),  # LCD 30-pin FPC: in line with its slot (SLOTS_FRONT), opening towards it
    "J1302": (
        146.9,
        60.97,
        180,
    ),  # touch 6-pin FPC: in line with its slot, opening towards it
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
SLOTS_FRONT = [
    ("LCD FPC slot", WS_W - 90.0, WS_W - 68.0, 41.0 + WS_EDGE, 3.0),
    ("Touch FPC slot", WS_W - 130.0, WS_W - 122.0, 48.0 + WS_EDGE, 3.0),
]

# Zone packer (floorplan.py zones): off now that PLACE lists every part. Set True to pack the key parts that are
# still commented out in PLACE into their zones (handy to seed a new layout, then dump_placement.py --write).
AUTO_ZONES = False
AUTO_PREFIX = ("U", "J", "SW", "Y", "BT")  # + LEDs
SPACE = (
    1.25  # mm kept clear round each courtyard (2.5 mm between parts: room for the iron)
)

# One list per schematic page: ("REF", x, y, rot), same rule as above. Uncommented = placed, commented = parked.
# Parts placed by EDGE_* / BIG and the corner holes are listed as comments for reference only.
# >>> PLACE (rewritten by dump_placement.py --write; edit freely, keep the markers)
PLACE = {
    # ------------------------------------------------ page 2: Power Input
    "Power Input": [
        ("U201",  180.0, 23.0,   0),  # STUSB4500QTR
        ("C204",  185.0,  5.0,  90),  # 1uF 25V
        ("C202", 177.27, 28.67, 270),  # 1uF
        ("C203", 184.62, 24.22, 90),  # 1uF

        ("Q201",  180.0, 15.0,   0),  # FDS9435A
        ("RS201", 170.0, 15.0,   0),  # 20m
        ("C205",  170.0, 20.0,   0),  # 10uF 25V
        ("D202",  160.0, 15.0,   0),  # SS34
        ("JP201", 160.0, 20.0,   0),  # Dev VBUS -> charger (default open)

        ("R201",  190.0, 17.0, 180),  # 1k
        ("R202",  190.0, 20.0, 180),  # 10k
        ("R203",  190.0, 23.0, 180),  # 100k
        ("R204",  190.0, 26.0, 180),  # 10k

        ("TP202", 170.0, 10.0, 180),  # VBUS_USER
        ("TP201", 175.0, 18.0, 180),  # PD_ATTACH
    ],
    # ------------------------------------------------ page 3: Charger Battery
    "Charger Battery": [
        ("J301",  135.0, 132.0, 180),  # battery connector, charger zone (outside the battery footprint)

        ("U301",  130.0, 120.0, 180),  # BQ25798

        ("L301", 129.1, 109.09, 180),  # 2.2uH

        ("C301", 125.72, 115.7, 180),  # 47nF
        ("C302", 134.34, 115.17, 90),  # 47nF

        ("C303", 128.7, 124.92, 270),  # 10uF 25V
        ("C304", 122.6, 121.2, 0),  # 10uF 25V

        ("C305", 125.1, 118.27, 0),  # 10uF 25V
        ("C306",  118.0, 120.0,   0),  # 10uF 25V
        ("C307",  118.0, 123.0,   0),  # 10uF 25V
        ("C308", 129.2, 115.03, 90),  # 100nF 25V

        ("C309", 126.05, 121.84, 270),  # 4.7uF 10V

        ("C310", 146.0, 129.0, 0),  # 10uF 25V
        ("C311",  145.0, 126.0, 180),  # 10uF 25V
        ("C312",  145.0, 123.0, 180),  # 10uF 25V
        ("C313",  145.0, 120.0, 180),  # 10uF 25V
        ("C314", 134.88, 118.7, 180),  # 10uF 25V
        ("C315", 131.79, 115.17, 90),  # 100nF 25V
        ("RS302", 140.0, 110.0,   0),  # 10m VSys Charge

        ("C316", 137.91, 116.12, 180),  # 10uF 25V
        ("C317",  137.0, 123.0, 180),  # 10uF 25V
        ("RS301", 133.0, 126.0,   0),  # 10m VBat Charge

        ("C319",  140.0, 107.0, 180),  # 1uF 25V
        ("U302",  140.0, 102.0,   0),  # MCP1703 3.0V (2 uA Iq)
        ("C320",  140.0,  98.0,   0),  # 1uF
        ("D302",  140.0,  95.0, 180),  # BAT43W
        ("C321",  140.0,  91.0, 180),  # 1uF

        ("D301",  147.0, 137.0, 180),  # CHG (amber)
        ("R306",  147.0, 133.0, 180),  # 2.2k

        ("BT301", 160.0, 135.0, 180),  # CR1220 (optional)
        ("D303",  152.0, 135.0, 180),  # BAT43W

        ("R301",  134.0, 102.0,  90),  # 8.2k 1%
        ("R302",  130.0, 102.0,  90),  # 10k
        ("R303",  126.0, 102.0,  90),  # 5.23k 1%
        ("R304",  122.0, 102.0,  90),  # 30.1k 1%
        ("R305",  118.0, 102.0,  90),  # 100R

        ("C318", 138.25, 119.59, 270),  # 1nF 50V

        ("TP301", 131.0, 138.0, 180),  # CHG_QON
        ("TP302", 134.0, 138.0, 180),  # BAT_PACK
        ("TP303", 137.0, 138.0, 180),  # VSYS
        ("TP304", 140.0, 138.0, 180),  # VBUS_CHG
        ("TP305", 143.0, 138.0, 180),  # VBACKUP
    ],
    # ------------------------------------------------ page 4: Power Rails
    "Power Rails": [
        # SW401: placed by EDGE_RIGHT  (POWER (slide))

        ("C416", 148.31, 84.71, 0),     # 22uF 10V
        ("C417", 146.83, 81.64, 0),     # 22uF 10V
        ("L411", 154.81, 84.71, 0),     # 4.7uH
        ("C415", 159.34, 79.15, 270),     # 100nF
        ("R413", 162.69, 79.25, 0),     # 52.3k 1%
        ("R414", 157.94, 74.86, 90),     # 10k 1%
        ("U411",  156.0,  80.0, 180),     # TPS62933 B5V
        ("C411", 155.26, 76.26, 90),     # 10uF 25V
        ("C412", 152.59, 76.79, 90),     # 10uF 25V
        ("C413", 151.81, 80.25, 0),     # 100nF
        ("C414", 161.39, 75.73, 180),     # 33nF
        ("R411",  145.0,  88.0, 180),     # 100k
        ("R412",  145.0,  92.0, 180),     # 28k
 
        ("RS401", 170.0,  71.0, 180),     # 10m PM3 CH4
        ("RS409", 176.0,  71.0, 180),     # 100m PM3 CH3 (3V3_PERIPH)
        ("C426",  170.0,  76.0, 180),     # 22uF 10V
        ("C427",  170.0,  79.0, 180),     # 22uF 10V
        ("L421", 171.19, 86.51, 90),     # 4.7uH
        ("U421",  170.0,  92.0, 180),     # TPS62933 B3V3

        ("C421",  163.0,  82.0,   0),     # 10uF 25V
        ("C422", 166.76, 93.24, 270),     # 10uF 25V
        ("C423", 169.7, 95.69, 270),     # 100nF
        ("C424", 165.8, 89.79, 0),     # 33nF
        ("C425",  163.0,  98.0,   0),     # 100nF

        ("R423",  175.0,  93.0, 180),     # 31.6k 1%
        ("R424",  175.0,  96.0, 180),     # 10k 1%

        ("U430",  120.0,  68.0,   0),     # TPS22917 LCD
        ("R430",  116.0,  68.0, 270),     # 100R
        ("C430",  120.0,  64.0, 180),     # 1nF
        ("RS403", 125.0,  65.0, 270),     # 50m PM2 Ch1
        ("TP411", 115.0,  72.0, 180),     # 5V_LCD

        ("U431",  156.0,  90.0,   0),     # TPS22917 Ethernet
        ("R431",  150.0,  90.0,  90),     # 100R
        ("C431", 153.26, 93.33, 0),     # 1nF
        ("RS406", 156.0,  97.0, 180),     # 100m PM CH4
        ("TP414", 156.0, 101.0, 180),     # 3V3_ETH

        ("U432",   38.0, 100.0, 180),     # TPS22917 GPS
        ("R432",   38.0, 104.0, 180),     # 100R
        ("C432",   38.0, 107.0, 180),     # 1nF
        ("RS407",  32.0, 100.0, 180),     # 1R PM3 Ch1
        ("TP415",  34.0, 104.0, 180),     # 3V3_GPS

        ("U433",   45.0,  17.0,   0),     # TPS22917 M1421
        ("R433", 40.25, 17.0, 0),     # 100R
        ("C433",   45.0,  13.0, 180),     # 1nF
        ("RS408",  50.0,  17.0, 270),     # 1R PM3 Ch1
        ("TP416",  55.0,  17.0, 180),     # 3V3_M1421

        ("RS404", 100.0, 105.0,   0),     # 50m PM2 Ch 2 MCU
        ("RS405", 180.0,  95.0, 180),     # 100m PM2 Ch 3 SD
        ("RS402", 176.0,  77.0, 180),     # 20m PM1 CH4 (SDR usb A)


        ("TP401",  156.0,  57.0, 180),    # 5V
        ("TP402",  169.0,  65.0, 180),    # 3V3
        ("TP403",  134.0,  97.0, 180),    # VSYS
        ("TP410",  175.0,  80.0, 180),    # 5V_SDR
        ("TP412",  100.0, 110.0, 180),    # 3V3_MCU
        ("TP413", 183.77, 77.54, 90),    # 3V3_SD
        ("TP417", 178.0, 80.05, 270),    # 3V3_PERIPH
    ],
    # ------------------------------------------------ page 5: Power Monitor
    "Power Monitor": [
        ("C501", 104.79, 119.75, 0),  # 100nF
        ("U501",  110.0, 120.0, 180),  # PAC1954 (PM1) CH1 VBUS_USER RS201, CH2 VBAT (bidirectional) RS301, CH3 VSYS RS301, CH4 5V_SDR RS402
        ("R501",  110.0, 115.0, 180),  # 0R (0x10)
        ("R504",  110.0, 110.0, 180),  # 10k

        ("U502",  120.0,  50.0, 270),  # PAC1954 (PM2) CH1 5V_LCD RS403, CH2 3V3_MCU (P4+C5 module) RS404, CH3 3V3_SD RS405, CH4 3V3_ETH RS406
        ("R502",  126.0,  50.0,  90),  # 499R 1% (0x11)
        ("C502", 120.88, 45.87, 180),  # 100nF

        ("R503",   46.0,  90.0,  90),  # 806R 1% (0x12)
        ("U503",   41.0,  90.0,  90),  # PAC1954 (PM3) CH1 3V3_GPS RS407, CH2 3V3_M1421 RS408, CH3 3V3_PERIPH RS409, CH4 3V3 total RS401
        ("C503",   36.0,  90.0,  90),  # 100nF
    ],
    # ------------------------------------------------ page 6: MCU Module
    "MCU Module": [
        ("U601",   80.0, 100.0, 180),  # OSPTEK ESP32-P4C5 module, between the LCD and touch sockets (short MIPI)

        ("SW601", 110.0, 132.0, 180),  # BOOT  (top band near the digital edge, clear of the battery)
        ("SW602", 120.0, 132.0, 180),  # RESET

        # SW603: placed by EDGE_RIGHT  (SLEEP/WAKE)
        ("C609",   70.0, 120.0,  90),  # 100nF
        ("R609",   74.0, 120.0,  90),  # 470R
        ("R608",   78.0, 120.0,  90),  # 10k
        
        ("J601",  108.0,  10.0, 270),  # Wi-Fi U.FL (jumper from the module IPEX), just behind J602
        # J602: placed by EDGE_TOP  (RP-SMA Wi-Fi 2.4/5 GHz)

        ("Y601", 60.67, 98.43, 270),  # 32.768kHz
        ("C605", 59.8, 96.09, 0),  # 22pF for Y601
        ("C606", 60.16, 103.54, 270),  # 22pF for Y601
        ("R601", 63.01, 99.88, 270),  # 10M  for Y601

        ("R602",   63.0, 110.0, 180),  # 2.2k
        ("R603",   63.0, 114.0, 180),  # 2.2k

        ("R605",   63.0,  93.0, 180),  # 10k

        ("R606",   82.0,  82.0,  90),  # 330R

        ("R604",  100.0,  95.0,   0),  # 4.7k

        ("R607",   63.0,  87.0, 180),  # 10k
        ("C607",   63.0,  90.0,   0),  # 1uF
 
        ("C601",   65.0,  82.0,  90),  # 22uF 10V
        ("C602",   69.0,  82.0,  90),  # 22uF 10V
        ("C603",   73.0,  82.0,  90),  # 100nF

        ("C608", 76.55, 84.39, 180),  # 100nF

        ("C604", 95.55, 90.26, 270),  # 1uF


        ("TP601",  45.0,  95.0, 180),  # C5_IO27
        ("TP602",  45.0,  98.0, 180),  # C5_IO25
        ("TP603",  45.0, 101.0, 180),  # C5_IO24
        ("TP604",  45.0, 104.0, 180),  # C5_IO23
        ("TP605",  45.0, 107.0, 180),  # C5_IO6
        ("TP606",  45.0, 110.0, 180),  # C5_IO5
        ("TP607",  45.0, 113.0, 180),  # C5_IO4

        ("TP608",  82.0, 120.0, 180),  # SLEEP_WAKE

        ("TP609",  85.0, 120.0, 180),  # P4_GPIO20
        ("TP610",  88.0, 120.0, 180),  # P4_GPIO36

        ("TP611",  85.0,  82.0, 180),  # C5_PU
    ],
    # ------------------------------------------------ page 7: RTC
    "RTC": [
        ("U701",  190.0, 135.0,  90),  # DS3231M
        ("R701",  184.0, 135.0,  90),  # 10k
        ("C701", 183.96, 138.47, 0),  # 100nF
        ("C702", 194.18, 133.76, 270),  # 100nF
        ("TP701", 172.0, 135.0, 180),  # RTC_INT
    ],
    # ------------------------------------------------ page 8: Ethernet
    "Ethernet": [
        # J801: placed by EDGE_RIGHT  (HR911105A)

        ("U801",  170.0, 115.0, 270),       # LAN8720A

        ("FB801", 180.0, 125.0,  90),       # 600R@100MHz
        ("R805",  176.0, 125.0,  90),       # 1.5k
        
        ("Y801", 164.05, 115.88, 270),       # 25MHz
        ("C808", 159.55, 113.28, 0),       # 27pF
        ("C809", 159.55, 118.48, 0),       # 27pF
        
        ("R801",  176.0, 121.0, 270),       # 12.1k 1%

        ("R804",  156.0, 123.0,  90),       # 10k
        ("R806",  160.0, 123.0,  90),       # 10k
        ("R814",  164.0, 123.0,  90),       # 10k
        ("R815",  168.0, 123.0,  90),       # 10k
        ("R816",  172.0, 123.0,  90),       # 10k

        ("R807",  156.0, 128.0,  90),       # 33R
        ("R808",  160.0, 128.0,  90),       # 49.9R 1%
        ("R809",  164.0, 128.0,  90),       # 49.9R 1%
        ("R810",  168.0, 128.0,  90),       # 49.9R 1%
        ("R811",  172.0, 128.0,  90),       # 49.9R 1%

        ("R802",  198.0, 128.0,  90),       # 10k       LED1
        ("R812",  194.0, 128.0,  90),       # 270R

        ("R803",  190.0, 128.0,  90),       # 10k       LED2
        ("R813",  186.0, 128.0,  90),       # 270R


        ("C801",  150.0, 105.0,  90),       # 10uF
        ("C803",  154.0, 105.0,  90),       # 10uF
        ("C802", 168.81, 110.36, 180),       # 100nF
        ("C804", 172.38, 109.5, 90),       # 100nF
        ("C805", 174.75, 115.26, 90),       # 100nF
        ("C806", 164.33, 109.54, 0),       # 1uF
        ("C807", 168.88, 106.81, 90),       # 470pF
        ("C810", 174.91, 110.65, 90),       # 22nF
        
        ("TP801", 178.0, 118.0, 180),       # ETH_REF_CLK
        ("TP802", 178.0, 112.0, 180),       # ETH_1V2
    ],
    # ------------------------------------------------ page 9: User USB-C
    "User USB-C": [
        # J901: placed by EDGE_RIGHT  (User USB-C (PD sink + UART))
        ("U902", 190.0, 12.0, 180),  # USBLC6-2SC6
        ("C903", 188.0,  5.0,  90),  # 10uF 25V
        ("D903", 193.0,  5.0,  90),  # SMAJ20A

        ("U901", 150.0, 13.0,   0),  # CP2102N-A02-GQFN24
        ("C901", 154.57, 13.0, 270),  # 1uF
        ("C902", 152.06, 7.5, 90),  # 100nF

        ("D901", 155.0,  3.0,   0),  # TX green
        ("R904", 142.0,  7.0, 180),  # 1k

        ("D902", 150.0,  3.0,   0),  # RX yellow
        ("R905", 142.0,  3.0, 180),  # 1k

        
        ("R901", 142.0, 12.0, 180),  # 22.1k
        ("R902", 142.0, 16.0,   0),  # 47.5k

        ("R903", 142.0, 21.0, 180),  # 10k
    ],
    # ------------------------------------------------ page 10: Dev USB Hub
    "Dev USB Hub": [
        # J1001: placed by EDGE_RIGHT  (Dev USB-C)
        ("U1001",  190.0, 40.0, 180),  # USBLC6-2SC6
        ("R1001", 198.55, 35.99, 0),  # 5.1k
        ("R1002",  200.0, 40.0, 180),  # 5.1k

        ("U1002",  185.0, 30.0,   0),  # AP2112K-3.3
        ("C1001",  190.0, 30.0,  90),  # 1uF
        ("TP1001", 190.0, 35.0, 180),  # VBUS_DEV
        ("C1002",  180.0, 30.0,  90),  # 10uF
        ("TP1002", 180.0, 35.0, 180),  # 3V3_DEV

        ("U1003",  165.0, 42.0, 270),  # USB2514B

        ("Y1001", 171.83, 39.1, 270),  # 24MHz
        ("C1006", 176.33, 36.5, 180),  # 27pF for Y1001
        ("C1007", 176.33, 41.7, 180),  # 27pF for Y1001
        ("R1013",  182.0, 42.0, 270),  # 1M

        ("R1003",  140.0, 50.0,  90),  # 10k
        ("R1004",  144.0, 50.0,  90),  # 10k

        ("R1005",  148.0, 50.0, 270),  # 10k
        ("R1006",  152.0, 50.0, 270),  # 10k

        ("R1007",  156.0, 50.0, 270),  # 10k
        ("R1008",  160.0, 50.0, 270),  # 10k

        ("R1010",  164.0, 50.0, 270),  # 10k
        
        ("R1009",  168.0, 50.0, 270),  # 12k 1%

        ("R1011",  172.0, 50.0, 270),  # 100k
        ("R1012",  176.0, 50.0, 270),  # 100k
        
        ("C1003", 158.31, 42.0, 0),  # 1uF
        ("C1004", 171.75, 45.19, 180),  # 1uF
        ("C1005",  154.0, 28.0,   0),  # 100nF
        ("C1008", 158.35, 39.49, 0),  # 100nF
        ("C1009", 159.26, 45.58, 270),  # 100nF
        ("C1010", 163.65, 35.31, 90),  # 100nF
        ("C1011", 155.88, 44.48, 0),  # 100nF
        ("C1012",  160.0, 35.0,   0),  # 4.7uF
    ],
    # ------------------------------------------------ page 11: USB Host
    "USB Host": [
        # J1101: placed by EDGE_RIGHT  (USB-A (SDR hub))
        ("U1102",  175.0, 57.0, 180),  # USBLC6-2SC6

        ("U1101",  175.0, 65.0, 180),  # TPS259621DDA
        ("C1103",  185.0, 70.0, 270),  # 150uF 10V
        ("C1104", 180.34, 62.66, 90),  # 100nF

        ("R1101",  165.0, 55.0,   0), # 604R 1%
        ("R1102",  165.0, 59.0,   0), # 402k 1%
        ("R1103",  165.0, 63.0,   0), # 10k
        ("R1104",  165.0, 67.0,   0), # 100k
        
        ("C1101",  165.0, 71.0,   0), # 10nF
        ("C1102", 169.62, 61.26, 90), # 1uF

        ("TP1101", 187.0, 77.0, 180), # VBUS_HOST
        ("TP1102", 180.0, 77.0, 180), # USBA_FAULT
    ],
    # ------------------------------------------------ page 12: GPS
    "GPS": [
        ("U1201",  25.0, 118.0,   0),     # MAX-M10S, under can SH1201
        ("SH1201", 25.0, 118.0, 180),
        ("D1201",  12.0, 115.0,  90),     # ESD7351XV2T1G
        ("L1201",  12.0, 120.0,  90),     # 47nH
        ("R1201",  12.0, 125.0,  90),     # 10R
        ("C1204",   7.5, 125.0, 270),     # 10nF

        # J1201: placed by EDGE_LEFT  (SMA GNSS (active antenna))

        ("D1202",   5.0, 105.0, 180),     # PPS green
        ("R1202",  10.0, 105.0,   0),     # 1k


        ("C1201",  38.0, 115.0, 180),     # 10uF
        ("C1202", 36.2, 117.79, 180),     # 100nF

        ("C1203", 36.05, 120.49, 180),     # 100nF

        ("TP1203", 24.25, 107.26, 90),     # GPS_RESET_N

        ("TP1201", 24.0, 130.0, 180),     # GPS_EXTINT
        ("TP1204", 24.0, 134.0, 180),     # GPS_PPS

        ("TP1202", 20.0, 130.0, 180),     # GPS_SAFEBOOT
    ],
    # ------------------------------------------------ page 13: Display Touch
    "Display Touch": [
        # J1301: placed by BIG  (LCD FPC 30p 0.5mm)
        # J1302: placed by BIG  (Touch FPC 6p 0.5mm)
        
        ("U1302", 135.0,  43.0,   0),  # AP2112K-1.8
        ("C1316", 140.0,  43.0, 270),  # 1uF
        ("C1317", 130.0,  43.0,  90),  # 1uF

        ("U1301", 135.0,  60.0, 180),  # AP3012KTR-E1
        ("L1301", 131.01, 54.81, 270),  # 10uH
        ("D1301", 130.0,  59.0, 180),  # 1N5819HW
        ("C1303", 125.0,  60.0, 270),  # 1uF 25V
        ("C1304", 121.0,  60.0, 270),  # 100nF 25V
        ("C1305", 117.0,  60.0, 270),  # 10uF 25V
        ("R1302", 113.0,  60.0, 270),  # 22k 1%
        ("R1303", 113.0,  65.0, 270),  # 3.3k 1%
        ("C1301", 139.0,  60.0, 270),  # 10uF
        ("C1302", 139.0,  65.0, 270),  # 1uF
        ("R1301", 135.0,  65.0,  90),  # 10k

        ("R1308", 109.0,  55.0, 270),  # 2k 1%
        ("R1309", 105.0,  55.0,  90),  # 1k 1%
        ("C1314", 101.0,  55.0,  90),  # 10uF
        ("C1315",  97.0,  55.0,  90),  # 100nF

        ("R1318", 109.0,  61.0, 270),  # 10k
        ("R1323", 105.0,  61.0,  90),  # 0R
        ("R1324", 100.0,  61.0, 270),  # 10k
        ("R1317",  96.0,  61.0, 270),  # 10k
        ("R1322",  93.0,  61.0,  90),  # 0R

        ("U1303", 135.0,  75.0, 180),  # AP3032KTR-G1
        ("L1302", 131.01, 69.81, 270),  # 10uH 0.55A
        ("D1306", 130.0,  74.0, 180),  # 1N5819HW
        ("R1311", 125.0,  74.0, 270),  # 0R
        ("C1320", 121.0,  73.0, 270),  # 1uF 50V
        ("R1314", 129.0,  80.0,  90),  # 68k
        ("R1312", 124.0,  80.0, 270),  # 5.1k 1%
        ("R1313", 119.0,  80.0,  90),  # 1.3R 1%
        ("C1321", 129.0,  85.0, 270),  # 100nF
        ("R1315", 125.0,  85.0,  90),  # 10k
        ("R1316", 119.0,  85.0, 270),  # 0R
        ("C1318", 139.0,  75.0, 270),  # 10uF
        ("C1319", 139.0,  81.0, 270),  # 1uF 50V
        ("R1310", 135.0,  80.0,  90),  # 100k

        ("R1320", 113.0,  80.0, 270),  # 10k
        ("R1319", 108.0,  80.0,  90),  # 0R
        ("C1322", 105.0,  80.0, 270),  # 100nF

        ("R1321", 135.0,  56.0, 270),  # 0R

        ("C1310",  84.0,  49.0,   0),  # 100nF 50V
        ("C1306",  84.0,  52.0,   0),  # 100nF 50V
        ("D1302",  84.0,  57.0,  90),  # BAT54S
        ("C1307",  84.0,  61.0, 180),  # 1uF 25V
        ("R1304",  84.0,  64.0, 180),  # 220R 1%
        ("C1308",  84.0,  67.0, 180),  # 100nF 25V
        ("R1305",  84.0,  71.0, 180),  # 51k 1%
        ("D1303",  84.0,  74.0,   0),  # BZT52C7V5S
        ("C1309",  84.0,  78.0, 180),  # 10uF 25V

        ("D1304",  77.0,  53.0,  90),  # BAT54S
        ("C1311",  77.0,  57.0,   0),  # 1uF 50V
        ("R1306",  77.0,  61.0,   0),  # 220R 1%
        ("C1312",  77.0,  65.0,   0),  # 100nF 50V
        ("D1305",  77.0,  69.0,   0),  # BZT52C18S
        ("C1313",  77.0,  72.0,   0),  # 10uF 25V
        ("R1307",  77.0,  76.0,   0),  # 51k 1%
        
        ("TP1301", 88.0,  57.0, 180),  # AVDD
        ("TP1302", 91.0,  57.0, 180),  # VGH
        ("TP1303", 94.0,  57.0, 180),  # VGL
        ("TP1304", 88.0,  60.0, 180),  # VCOM
        ("TP1305", 88.0,  63.0, 180),  # VCC_1V8
        ("TP1306", 88.25, 54.0, 90),  # LED_P
    ],
    # ------------------------------------------------ page 14: M1421
    "M1421": [
        ("U1401",  35.0, 35.0,   0),     # m1421, under can SH1401 (RF column, left edge)
        ("SH1401", 35.0, 35.0, 180),
        ("D1403",   8.0, 32.0,  90),     # ESD7351XV2T1G
        ("U1405",  12.0, 32.0, 270),     # SCN-2-11+
        ("R1408",  20.0, 32.0,  90),     # 100R
        # J1403: placed by EDGE_LEFT  (SMA 1090/978)

        ("U1402", 65.0, 45.0, 180),     # 74LVC1G97 (AND)
        ("R1401", 72.0, 45.0,   0),     # 100k
        ("R1409", 72.0, 40.0,   0),     # 100k

        ("U1403", 65.0, 25.0, 180),     # 74LVC1G32
        ("R1402", 72.0, 20.0, 180),     # 100k
        ("R1403", 72.0, 25.0, 180),     # 100k

        ("U1404", 65.0, 35.0, 180),     # 74LVC1G07
        ("R1404", 72.0, 30.0,   0),     # 100k
        ("R1405", 72.0, 35.0,   0),     # 100k

        ("D1401",  5.0, 20.0, 180),     # RED 1090
        ("R1406", 10.0, 20.0,   0),     # 287R
        ("D1402",  5.0, 15.0, 180),     # GREEN UAT
        ("R1407", 10.0, 15.0,   0),     # 115R

        ("J1401", 55.0, 25.0,   0),     # m1421 JTAG (below the m1421 can)
        ("J1402", 55.0, 35.0, 180),     # ADSBee Dev Kit header (1x6, vertical, next to the m1421)


        ("C1401", 28.88, 20.05, 180),    # 1uF
        ("C1402", 24.91, 29.02, 270),    # 100nF

        ("TP1401", 45.5, 32.0, 180),    # SD23
        ("TP1402", 45.5, 29.0, 180),    # SD24
        ("TP1403", 45.5, 26.0, 180),    # SD25
        ("TP1404", 45.5, 45.0, 180),    # LD11
        ("TP1405", 45.5, 42.0, 180),    # LD09
        ("TP1406", 45.5, 39.0, 180),    # LD08
        ("TP1407",  50.0,  36.0, 180),    # LRST

        ("TP1408",  17.0,  39.0, 180),    # CSMI
        ("TP1409",  17.0,  43.0, 180),    # CSMO
        ("TP1410",  17.0,  47.0, 180),    # CSCK
        ("TP1411",  17.0,  51.0, 180),    # LRCS
        ("TP1412",  17.0,  55.0, 180),    # LBSY
    ],
    # ------------------------------------------------ page 15: Storage Misc
    "Storage Misc": [
        # J1501: placed by EDGE_RIGHT  (microSD (push-pull, detect))
        ("Q1501",  180.0,  89.0, 180),    # AO3401A
        ("TP1501", 186.0,  90.0, 180),    # SD_VDD

        ("R1501",  200.0, 100.0,  90),    # 10k
        ("R1502",  196.0, 100.0,  90),    # 10k
        ("R1503",  192.0, 100.0,  90),    # 10k
        ("R1504",  188.0, 100.0,  90),    # 10k
        ("R1505",  184.0, 100.0,  90),    # 10k

        ("R1506",  195.0,  80.0,  90),    # 10k
        ("R1507",  190.0,  80.0,  90),    # 10k
        
        ("C1501",  185.0,  82.0,  90),    # 10uF
        ("C1502",  181.0,  82.0,  90),    # 100nF

        ("U1501",   59.0,  65.0, 180),    # TCA6408APW
        ("C1503",   59.0,  59.0, 180),    # 100nF

        ("R1508",   66.0,  57.0, 180),    # 10k
        ("R1509",   66.0,  61.0, 180),    # 10k
        ("R1510",   66.0,  65.0, 180),    # 100k
        ("R1511",   66.0,  69.0, 180),    # 100k

        ("R1513",   59.0,  54.0, 180),    # 100k
        ("R1512",   59.0,  72.0, 180),    # 100k
    ],
    # ------------------------------------------------ page 16: Test Debug
    "Test Debug": [
        ("J1601",  100.0, 133.0, 270),    # LA5016 2x20 header, horizontal along the bottom edge

        ("R1601",   96.0, 127.0, 270),    # 100R
        ("R1602",   92.0, 127.0, 270),    # 100R
        ("R1603",   88.0, 127.0, 270),    # 100R
        ("R1604",   84.0, 127.0, 270),    # 100R
        ("R1605",   80.0, 127.0, 270),    # 100R
        ("R1606",   76.0, 127.0, 270),    # 100R
        ("R1607",   72.0, 127.0, 270),    # 100R
        ("R1608",   68.0, 127.0, 270),    # 100R
        ("R1609",   64.0, 127.0, 270),    # 100R
        ("R1610",   60.0, 127.0, 270),    # 100R
        ("R1611",   56.0, 127.0, 270),    # 100R
        ("R1612",   52.0, 127.0, 270),    # 100R
        ("R1613", 55.87, 122.75, 90),    # 100R
        ("R1614", 51.87, 122.75, 90),    # 100R
        ("R1615",   48.0, 127.0, 270),    # 100R
        ("R1616",   44.0, 127.0, 270),    # 100R

        ("R1617",   44.0, 132.0,  90),    # 0R

        ("TP1601",  44.0, 136.0, 180),    # LA_PWM1
        ("TP1602",  41.0, 136.0, 180),    # LA_PWM2
        ("TP1603",  41.0, 132.0, 180),    # GND
        ("TP1604",  38.0, 132.0, 180),    # GND
        ("TP1605",  38.0, 136.0, 180),    # GND
        ("TP1606",  35.0, 132.0, 180),    # GND
        # H1601: corner mounting hole
        # H1602: corner mounting hole
        # H1603: corner mounting hole
        # H1604: corner mounting hole
    ],
    # ------------------------------------------------ page 17: Dev UARTs
    "Dev UARTs": [
        ("U1701",  105.0,  30.0, 270),  # FT2232HL
        ("U1702",  125.0,  30.0, 180),  # 93LC56B

        ("U1703",  105.0,  15.0,  90),  # 74LVC1G07
        ("C1708", 100.8, 13.65, 0),  # 100nF
        
        ("U1704",   85.0,  30.0, 180),  # 74LVC1G125
        ("C1709", 85.48, 26.71, 0),  # 100nF
        
        ("U1705",  100.0,  45.0, 270),  # 74LVC1G07
        ("C1710",  100.0,  50.0, 180),  # 100nF
        
        ("U1706",  110.0,  45.0,  90),  # 74LVC1G125
        ("C1711", 105.8, 43.65, 0),  # 100nF

        ("Q1701",   85.0,  22.0,   0),  # MMBT3904
        ("R1709",   92.0,  19.0 ,  0),  # 10k
        ("Q1702",   85.0,  15.0,   0),  # MMBT3904
        ("R1710",   92.0,  15.0,   0),  # 10k

        ("Q1703",   85.0,  37.0,   0),  # MMBT3904
        ("R1711",   92.0,  48.0,   0),  # 10k
        ("Q1704",   85.0,  44.0,   0),  # MMBT3904
        ("R1712",   92.0,  52.0,   0),  # 10k
        
        ("Y1701", 112.1, 20.65, 0),  # 12MHz
        ("C1706", 119.2, 20.65, 180),  # 27pF for Y1701
        ("C1707", 109.7, 16.16, 90),  # 27pF for Y1701
        
        ("J1701",   60.0,   5.0, 270),  # FT2232H ch A port (pins DNP), 2x10
        ("J1702",   95.0,   5.0, 270),  # FT2232H ch B port (pins DNP), 2x10
        
        ("R1701",  105.0,  20.0, 180),  # 12k 1%

        ("R1703",  118.0,  30.0,  90),  # 2.2k

        ("R1702",   92.0,  23.0, 180),  # 10k
        ("R1704",   92.0,  27.0, 180),  # 10k
        ("R1705",   92.0,  31.0, 180),  # 10k
        ("R1706",   92.0,  35.0, 180),  # 10k
        ("R1707",   92.0,  39.0, 180),  # 10k
        ("R1708",   92.0,  44.0, 180),  # 10k

        ("C1701", 114.17, 26.51, 180),  # 100nF
        ("C1702", 113.24, 34.74, 270),  # 100nF
        ("C1703", 114.18, 31.32, 180),  # 100nF
        ("C1704", 116.67, 33.86, 180),  # 100nF
        ("C1705",  118.0,  43.0, 180),  # 4.7uF
        
        ("TP1701",  97.0,  40.0, 180),  # FT_A_DTR
        ("TP1702", 100.0,  40.0, 180),  # FT_A_RTS
        ("TP1703", 103.0,  40.0, 180),  # FT_B_DTR
        ("TP1704", 106.0,  40.0, 180),  # FT_B_RTS
    ],
    # ------------------------------------------------ page 18: Dev m1421 Programmer
    "Dev m1421 Programmer": [
        ("U1801",  25.0, 75.0, 180),   # RP2040

        ("U1802",  25.0, 55.0, 270),   # W25Q16JVSS
        ("R1805",  25.0, 63.0, 180),   # 10k
        ("R1806",  25.0, 68.0, 180),   # 1k
        ("C1809", 30.4, 58.84, 180),   # 100nF

        ("U1803",  37.0, 55.0, 180),   # 74LVC1G125
        ("C1811",  42.0, 55.0, 270),   # 100nF

        ("U1804",  37.0, 63.0, 180),   # 74LVC1G125
        ("C1812",  42.0, 63.0, 270),   # 100nF

        ("U1805",  37.0, 71.0, 180),   # 74LVC1G125
        ("C1813",  42.0, 71.0, 270),   # 100nF

        ("U1806",  37.0, 78.0, 180),   # 74LVC1G125
        ("C1814",  42.0, 78.0, 270),   # 100nF

        ("Y1801", 21.12, 84.82, 270),   # 12MHz
        ("C1801", 16.48, 81.22, 0),   # 27pF
        ("C1802", 21.12, 91.92, 270),   # 27pF
        ("R1803", 24.8, 81.89, 90),   # 1k for Y1801

        ("J1801",   7.0,  90.0,   0),  # RP2040 GPIO header (DNP)
        ("J1802",  15.0,  90.0,   0),  # RP2040 SWD

        ("SW1801",  7.0,  95.0, 180),  # RP2040 BOOTSEL (Dev zone)
        ("D1802",   5.0,  48.0, 270),  # WS2812B
        ("D1801",  12.0,  48.0, 180),  # 1N4148W
        ("C1810",   5.0,  40.0,   0),  # 100nF
        ("R1807", 13.01, 50.73, 0),  # 330R

        ("R1801",  50.0,  55.0,   0),  # 27R
        ("R1802",  50.0,  59.0,   0),  # 27R

        ("R1808",  50.0,  64.0, 180),  # 0R
        ("R1809",  50.0,  68.0, 180),  # 0R
        ("R1812",  50.0,  72.0, 180),  # 0R
        ("R1813",  50.0,  76.0, 180),  # 0R

        ("R1804",  50.0,  81.0,   0),  # 10k
        ("R1810",  50.0,  85.0,   0),  # 10k
        ("R1811",  50.0,  90.0, 180),  # 100k

        ("C1803", 18.93, 77.61, 270),  # 1uF
        ("C1804", 20.71, 68.95, 0),  # 1uF
        ("C1805", 18.91, 72.9, 270),  # 100nF
        ("C1806", 15.36, 76.0, 0),  # 100nF
        ("C1807", 27.36, 84.5, 270),  # 100nF
        ("C1808", 28.38, 81.15, 180),  # 100nF

        ("TP1801", 45.0,  85.0, 180),  # RP_SWCLK
        ("TP1802", 38.0,  85.0, 180),  # RP_SWDIO
        ("TP1803", 31.0,  85.0, 180),  # RP_RUN
    ],
}
# <<< PLACE

# ================================================================ derived from the arrays
PANEL_BOTTOM = (H + PH) / 2  # bottom-view y of the panel's bottom edge
# (name, bottom-view x centre, length, bottom-view y centre, height)
SLOTS = [
    (n, W - (W - PW) / 2 - (a + b) / 2, b - a, PANEL_BOTTOM - (up + h / 2), h)
    for n, a, b, up, h in SLOTS_FRONT
]
# edge parts: ref -> (side, origin position along the edge)
EDGE = {
    **{r: ("L", v) for r, v in EDGE_LEFT},
    **{r: ("R", v) for r, v in EDGE_RIGHT},
    **{r: ("T", v) for r, v in EDGE_TOP},
}
PLACED_BY_PAGE = {e[0]: tuple(e[1:]) for page in PLACE.values() for e in page}


def mm(v):
    return pcbnew.FromMM(v)


def top(bx, by):
    """bottom-view (bx, by) -> KiCad top-view point (mirror in x)."""
    return pcbnew.VECTOR2I(mm(OX + W - bx), mm(OY + by))


# ---------------------------------------------------------------- netlist
def netlist():
    xml = KICAD / "_pcbgen_netlist.xml"
    subprocess.run(
        [
            CLI,
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadxml",
            "-o",
            str(xml),
            str(KICAD / "ADSB_Test.kicad_sch"),
        ],
        check=True,
        capture_output=True,
    )
    r = ET.parse(xml).getroot()
    xml.unlink()
    comps = []
    for c in r.find("components").findall("comp"):
        sp = c.find("sheetpath")
        comps.append(
            dict(
                ref=c.get("ref"),
                value=c.findtext("value"),
                fp=c.findtext("footprint") or "",
                path=sp.get("tstamps") + c.findtext("tstamps"),
                sheet=sp.get("names").strip("/") or "Top",
                dnp=any(p.get("name") == "dnp" for p in c.findall("property")),
                no_bom=any(
                    p.get("name") == "exclude_from_bom" for p in c.findall("property")
                ),
                fields={
                    f.get("name"): f.text or ""
                    for f in c.iterfind("fields/field")
                    if f.get("name") not in ("Footprint", "Datasheet", "Description")
                },
            )
        )
    pins = {}
    for n in r.find("nets").findall("net"):
        for node in n.findall("node"):
            name = n.get("name")
            if name.startswith(
                "unconnected-("
            ):  # KiCad escapes '/' in pin names inside these net names
                name = "unconnected-(" + name[len("unconnected-(") :].replace(
                    "/", "{slash}"
                )
            pins[(node.get("ref"), node.get("pin"))] = name
    return comps, pins


def load_fp(fpid):
    lib, name = fpid.split(":", 1)
    path = (
        KICAD / "lib/ADSB_Test.pretty" if lib == "ADSB_Test" else STD / f"{lib}.pretty"
    )
    fp = pcbnew.FootprintLoad(str(path), name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ---------------------------------------------------------------- geometry helpers
def pad_centroid(fp):
    ps = list(fp.Pads())
    return (
        sum(p.GetPosition().x for p in ps) / len(ps),
        sum(p.GetPosition().y for p in ps) / len(ps),
    )


def edge_marker(fp):
    """Midpoint of the footprint's 'PCB Edge' line (Dwgs.User), if it has one."""
    txt = [
        t
        for t in fp.GraphicalItems()
        if isinstance(t, pcbnew.PCB_TEXT) and "PCB Edge" in t.GetText()
    ]
    lines = [
        g
        for g in fp.GraphicalItems()
        if isinstance(g, pcbnew.PCB_SHAPE)
        and g.GetLayer() == pcbnew.Dwgs_User
        and g.GetShape() == pcbnew.SHAPE_T_SEGMENT
    ]
    if not txt or not lines:
        return None
    tp = txt[0].GetPosition()

    def mid(g):
        return (
            (g.GetStart().x + g.GetEnd().x) / 2,
            (g.GetStart().y + g.GetEnd().y) / 2,
        )

    return min(
        (mid(g) for g in lines), key=lambda m: (m[0] - tp.x) ** 2 + (m[1] - tp.y) ** 2
    )


def body_box(fp):
    return fp.GetBoundingBox(False)  # without text


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
    edge-mount (end-launch) connectors, whose barrel overhangs the edge; otherwise the body.
    """
    if "EdgeMount" in fp.GetFPID().GetLibItemName().wx_str():
        b = pcbnew.BOX2I()
        for p in fp.Pads():
            b.Merge(p.GetBoundingBox())
        b.Inflate(
            mm(0.5), mm(0.5)
        )  # pads 0.5 mm in from the edge (copper-to-edge clearance)
        return b
    return body_box(fp)


def place_on_edge(fp, side, along):
    """Turn the part to face out of its edge, snap it to the edge ('PCB Edge' marker, edge-mount pads or body front)
    and put its ORIGIN at `along`: y for 'L' (RF edge, x = 0) and 'R' (digital edge), x for 'T' (top edge).
    """
    if side == "T":
        turn_to(fp, (0, -1))
        em = edge_marker(fp)
        front = em[1] if em else front_box(fp).GetTop()
        fp.SetPosition(
            pcbnew.VECTOR2I(top(along, 0).x, fp.GetPosition().y + int(mm(OY) - front))
        )
        return
    turn_to(fp, (1, 0) if side == "L" else (-1, 0))
    target_x = mm(OX + W) if side == "L" else mm(OX)
    em = edge_marker(fp)
    if em:  # the marker line on the board edge
        front = em[0]
    else:  # body (or edge-mount pads) flush with the edge
        b = front_box(fp)
        front = b.GetRight() if side == "L" else b.GetLeft()
    fp.SetPosition(
        pcbnew.VECTOR2I(fp.GetPosition().x + int(target_x - front), mm(OY + along))
    )


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
        rect(
            cx - length / 2, OY + by - height / 2, cx + length / 2, OY + by + height / 2
        )
    t = pcbnew.PCB_TEXT(board)
    t.SetText(
        "ADSB_Test Rev A - ALL COMPONENTS ON THE BOTTOM SIDE (panel bonded to the top).\n"
        "Dwgs.User rectangle = panel outline. Slots = panel FPC pass-throughs (from the Waveshare board)."
    )
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
    text = re.sub(
        r'\(paper "[^"]*"\)', f'(paper "{PAPER[0]}")', text, count=1
    )  # page size (no Python API)
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
            zones[s] = (
                name,
                mm(OX + W - x1),
                mm(OY + y0),
                mm(OX + W - x0),
                mm(OY + y1),
            )
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
                        cand = pcbnew.BOX2I(
                            pcbnew.VECTOR2I(x, y), pcbnew.VECTOR2L(w, h)
                        )
                        if not any(cand.Intersects(o) for o in occupied):
                            fp.Move(
                                pcbnew.VECTOR2I(x + sp - b.GetX(), y + sp - b.GetY())
                            )
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


def board_keepouts():
    """Slots and corner holes as (x0, y0, x1, y1) in page mm, for the ground-via search."""
    out = []
    for _, bx, length, by, height in SLOTS:
        c = top(bx, by)
        cx, cy = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
        out.append((cx - length / 2 - 0.5, cy - height / 2 - 0.5, cx + length / 2 + 0.5, cy + height / 2 + 0.5))
    for hx, hy in ((HOLE_IN, HOLE_IN), (W - HOLE_IN, HOLE_IN), (HOLE_IN, H - HOLE_IN), (W - HOLE_IN, H - HOLE_IN)):
        c = top(hx, hy)
        cx, cy = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
        out.append((cx - 3.5, cy - 3.5, cx + 3.5, cy + 3.5))
    return out


def add_copper(board, nets, old, mode):
    import copper

    kept, dropped = copper.keep_routing(old, board, nets, mode)
    board.SetLayerType(board.GetLayerID(PLANE), pcbnew.LT_POWER)
    e = EDGE_PULLBACK
    pts = [(OX + e, OY + e), (OX + W - e, OY + e), (OX + W - e, OY + H - e), (OX + e, OY + H - e)]
    gnd = nets["GND"]
    copper.add_zone(board, gnd, PLANE, "AUTO_GND_PLANE", pts, ZONE_CLEARANCE)
    for layer in GND_FILLS:
        copper.add_zone(board, gnd, layer, "AUTO_GND_" + layer.split(".")[0], pts, ZONE_CLEARANCE)
    def inside(x, y):
        return OX + 1.0 < x < OX + W - 1.0 and OY + 1.0 < y < OY + H - 1.0

    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for net_name, layer, ics, radius in POWER_ISLANDS:
        net = nets[net_name]
        for ic in ics:
            c = fps[ic].GetPosition()
            pads = [p for f in board.GetFootprints() for p in f.Pads()
                    if p.GetNetname() == net_name and (p.GetPosition() - c).EuclideanNorm() < pcbnew.FromMM(radius)]
            pts = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for p in pads]
            cy = fps[ic].GetCourtyard(pcbnew.B_CrtYd).BBox()
            pts += [(pcbnew.ToMM(x), pcbnew.ToMM(y)) for x in (cy.GetLeft(), cy.GetRight())
                    for y in (cy.GetTop(), cy.GetBottom())]
            copper.add_zone(board, net, layer, f"AUTO_{net_name}_{ic}", copper.grow(copper.hull(pts), 3.0),
                            ZONE_CLEARANCE, priority=1)
            keys = {(p.GetParentFootprint().GetReference(), p.GetNumber()) for p in pads}
            n_v, nr = copper.pad_vias(board, net, inside, board_keepouts(), f"AUTO_{net_name}_VIAS_{ic}",
                                      only=lambda p, k=keys: (p.GetParentFootprint().GetReference(), p.GetNumber()) in k)
            print(f"  island {net_name} round {ic} on {layer}: {len(pads)} pads, {n_v} vias"
                  + (f", no via room: {' '.join(nr)}" if nr else ""))
    vias, no_room = 0, []
    if GND_VIAS:
        vias, no_room = copper.gnd_vias(board, gnd, inside, board_keepouts())
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"  copper: {kept} routing items kept ({mode}), {vias} ground vias, "
          f"{len(no_room)} ground pads with no room for a via")
    if no_room:
        print("    no via room:", " ".join(no_room))
    if dropped:
        print("    routing dropped (net no longer exists):", " ".join(sorted(dropped)))


def main():
    mode = "none" if "--clear-routing" in sys.argv else "locked" if "--keep-locked" in sys.argv else "all"
    old = pcbnew.LoadBoard(str(PCB)) if PCB.exists() and mode != "none" else None
    comps, pins = netlist()
    board = (
        pcbnew.CreateEmptyBoard()
        if hasattr(pcbnew, "CreateEmptyBoard")
        else pcbnew.BOARD()
    )
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    # PCBWay standard capabilities (docs/pcb-manufacturing.md): 0.127 mm track/space, 0.25 mm drill / 0.5 mm via
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_MinClearance = mm(0.127)
    ds.m_MinThroughDrill = mm(0.25)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_ViasMinAnnularWidth = mm(0.125)
    ds.SetGridOrigin(
        top(0, 0)
    )  # bottom-view board corner: KiCad X (relative) = -bx, Y = by
    ds.SetAuxOrigin(top(0, 0))
    outline(board)

    nets = {}
    for name in sorted(set(pins.values())):
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n

    corners = [
        (HOLE_IN, HOLE_IN),
        (W - HOLE_IN, HOLE_IN),
        (HOLE_IN, H - HOLE_IN),
        (W - HOLE_IN, H - HOLE_IN),
    ]
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
        for name, text in c[
            "fields"
        ].items():  # symbol fields (Check, Note, ...) as hidden footprint fields
            fp.SetField(name, text)
            fp.GetField(name).SetVisible(False)
        board.Add(fp)
        for pad in fp.Pads():
            net = pins.get((c["ref"], pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])
        fp.SetPosition(top(0, 0))
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)  # bottom side
        ref = c["ref"]
        if ref.startswith("H16"):  # corner mounting holes
            bx, by = next(holes)
            fp.SetPosition(top(bx, by))
            placed.append(ref)
        elif ref in EDGE:
            side, by = EDGE[ref]
            place_on_edge(fp, side, by)
            placed.append(ref)
        elif (
            ref in BIG or ref in PLACED_BY_PAGE
        ):  # BIG / PLACE: origin (x, y) + rotation
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
        occupied.append(
            pcbnew.BOX2I(
                pcbnew.VECTOR2I(c.x - mm(length / 2 + 1), c.y - mm(height / 2 + 1)),
                pcbnew.VECTOR2L(mm(length + 2), mm(height + 2)),
            )
        )
    for hx, hy in corners:
        c = top(hx, hy)
        occupied.append(
            pcbnew.BOX2I(
                pcbnew.VECTOR2I(c.x - mm(4), c.y - mm(4)), pcbnew.VECTOR2L(mm(8), mm(8))
            )
        )
    auto = collections.defaultdict(list)
    if AUTO_ZONES:
        for sheet, fps in parked.items():
            for f in fps:
                if is_auto(f.GetReference(), f.GetFPID().GetLibItemName().wx_str()):
                    auto[sheet].append(f)
        left = place_in_zones(board, auto, occupied)
        zoned = sum(len(v) for v in auto.values()) - len(left)
        for sheet in parked:
            parked[sheet] = [
                f
                for f in parked[sheet]
                if f not in auto[sheet] or f.GetReference() in left
            ]
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
            fp.SetPosition(
                pcbnew.VECTOR2I(
                    fp.GetPosition().x + int(mm(cx + w / 2) - b.GetCenter().x),
                    fp.GetPosition().y + int(mm(y + h / 2) - b.GetCenter().y),
                )
            )
            cx += w + 1.5
            row_h = max(row_h, h)
        y += row_h + 8
        if y > PAPER[2] - 60 and col + 1 < len(columns):
            col += 1
            col_x, y = columns[col], 15.0

    add_copper(board, nets, old, mode)

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
    print(
        f"wrote {PCB.name}: {len(comps)} parts, {len(placed)} placed ({len(PLACED_BY_PAGE)} from PLACE), "
        f"{zoned} by the zone packer, "
        f"{sum(len(v) for v in parked.values())} parked, "
        f"{len(nets)} nets"
    )


if __name__ == "__main__":
    main()
