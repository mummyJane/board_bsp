#!/usr/bin/env python3
"""Generate the ADSB_Test 'M1421' sheet (ADSBee m1421 + Dev Kit header + RF).

Run from the repo root:  python boards/adsb-test/hardware/gen/gen_m1421.py
then: kicad-cli sch upgrade + erc (see build_sheets.ps1 / the README).

Design notes: boards/adsb-test/docs/architecture.md "ADSBee m1421 integration".
Ref-des block 14xx (sheet page 14).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from kicad_sch_gen import SymbolLibs, Sheet, sheet_uuids, existing_notes  # noqa: E402

KICAD = ROOT / "boards/adsb-test/hardware/kicad"
SHEET = KICAD / "m1421.kicad_sch"

libs = SymbolLibs({"ADSB_Test": KICAD / "lib/ADSB_Test.kicad_sym"})
root_uuid, sheets = sheet_uuids(KICAD / "ADSB_Test.kicad_sch")
notes = existing_notes(SHEET)
s = Sheet(libs, "ADSB_Test", root_uuid, sheets["m1421.kicad_sch"])
# Nets that never leave this sheet (everything else is a global label).
s.locals |= {"M1421_TMSC", "M1421_TCKC", "M1421_TDO", "M1421_TDI", "M1421_RF_978", "M1421_RF_1090",
             "RF_ADSB_ANT", "LED_SD26_A", "LED_SD27_A", "M1421_SD23", "M1421_SD24", "M1421_SD25",
             "M1421_LD11", "M1421_LD09", "M1421_LD08", "M1421_LRST", "M1421_CSMI", "M1421_CSMO",
             "M1421_CSCK", "M1421_LRCS", "M1421_LBSY"}

R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
SC70_5 = "Package_TO_SOT_SMD:SOT-353_SC-70-5"
SC70_6 = "Package_TO_SOT_SMD:SOT-363_SC-70-6"
VCC = "3V3_M1421"

# ------------------------------------------------------------------ module
u = s.add("ADSB_Test:PantsForBirds_ADSBee_m1421", "U1401", "ADSBee m1421", (101.6, 111.76),
          footprint="ADSB_Test:PantsForBirds_ADSBee_m1421_Module",
          props={"Fit": "Fit EITHER U1401 OR use J1402 with the ADSBee 1421 Dev Kit"})
s.connect(u, ["1", "4", "19", "22"], VCC)
s.connect(u, ["6", "18", "23", "25", "27", "34", "36", "MP"], "GND")
s.connect(u, "20", "M1421_SURX")
s.connect(u, "21", "M1421_SUTX")
s.connect(u, "28", "M1421_SYNC")
s.connect(u, "17", "M1421_NRST")
for pin, net in (("8", "M1421_TMSC"), ("9", "M1421_TCKC"), ("10", "M1421_TDO"), ("11", "M1421_TDI")):
    s.connect(u, pin, net, kind="label")
s.connect(u, "15", "M1421_SD26")
s.connect(u, "16", "M1421_SD27")
s.connect(u, "24", "M1421_RF_978", kind="label")
s.connect(u, "26", "M1421_RF_1090", kind="label")
s.nc(u, "35")                                   # LR_RF_HF (2.4 GHz) not used
tp_nets = {"12": "M1421_SD23", "13": "M1421_SD24", "14": "M1421_SD25", "2": "M1421_LD11", "3": "M1421_LD09",
           "5": "M1421_LD08", "7": "M1421_LRST", "29": "M1421_CSMI", "30": "M1421_CSMO", "31": "M1421_CSCK",
           "32": "M1421_LRCS", "33": "M1421_LBSY"}
for pin, net in tp_nets.items():
    s.connect(u, pin, net, kind="label")

s.two_pin("Device:C", "C1401", "1uF", (60.96, 63.5), VCC, "GND", C0402)
s.two_pin("Device:C", "C1402", "100nF", (71.12, 63.5), VCC, "GND", C0402)

# ------------------------------------------------------------------ test pads
for i, (pin, net) in enumerate(tp_nets.items()):
    tp = s.add("Connector:TestPoint", f"TP{1401 + i}", net.replace("M1421_", ""),
               (25.4 + (i % 6) * 15.24, 236.22 + (i // 6) * 30.48),
               footprint="TestPoint:TestPoint_Pad_D1.0mm")
    s.connect(tp, "1", net, kind="label")

# ------------------------------------------------------------------ JTAG (Segger J-Link, as the carrier)
j = s.add("Connector:Conn_ARM_JTAG_SWD_10", "J1401", "m1421 JTAG (J-Link)", (50.8, 190.5),
          footprint="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD")
s.connect(j, "1", VCC)
s.connect(j, ["3", "5", "9"], "GND")
s.connect(j, "2", "M1421_TMSC", kind="label")
s.connect(j, "4", "M1421_TCKC", kind="label")
s.connect(j, "6", "M1421_TDO", kind="label")
s.connect(j, "8", "M1421_TDI", kind="label")
s.connect(j, "10", "M1421_NRST")
s.nc(j, "7")

# ------------------------------------------------------------------ Dev Kit comms header
h = s.add("Connector_Generic:Conn_01x06", "J1402", "ADSBee 1421 Dev Kit", (50.8, 152.4),
          footprint="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
          props={"Pinout": "1 VIN, 2 UART RX (into module), 3 UART TX, 4 SYNC, 5 RESET, 6 GND (Dev Kit JST-GH harness)"})
s.connect(h, "1", VCC)
s.connect(h, "2", "M1421_SURX")
s.connect(h, "3", "M1421_SUTX")
s.connect(h, "4", "M1421_SYNC")
s.connect(h, "5", "M1421_NRST")
s.connect(h, "6", "GND")

# ------------------------------------------------------------------ RX mux: 74LVC1G97 as 2:1 mux
# Nexperia function table: C=L -> Y=B (pin 1), C=H -> Y=A (pin 3). Select C = pin 6.
m = s.add("74xGxx:74LVC1G97", "U1402", "74LVC1G97 (2:1 mux)", (203.2, 50.8), footprint=SC70_6,
          props={"Function": "C(6)=0: Y=B(1)=P4 TX; C(6)=1: Y=A(3)=Dev TX"})
s.connect(m, "1", "P4_M1421_TX")
s.connect(m, "3", "DEV_M1421_TX")
s.connect(m, "6", "DEV_M1421_SEL")
s.connect(m, "4", "M1421_SURX")
s.connect(m, "5", VCC)
s.connect(m, "2", "GND")
s.two_pin("Device:R", "R1401", "100k", (241.3, 30.48), "DEV_M1421_SEL", "GND", R0402)

# ------------------------------------------------------------------ SYNC = P4 OR Dev
g = s.add("74xGxx:74LVC1G32", "U1403", "74LVC1G32", (203.2, 106.68), footprint=SC70_5)
s.connect(g, "1", "P4_M1421_SYNC")
s.connect(g, "2", "DEV_M1421_SYNC")
s.connect(g, "4", "M1421_SYNC")
s.connect(g, "5", VCC)
s.connect(g, "3", "GND")
s.two_pin("Device:R", "R1402", "100k", (241.3, 96.52), "M1421_SYNC", "GND", R0402)
s.two_pin("Device:R", "R1403", "100k", (165.1, 96.52), "DEV_M1421_SYNC", "GND", R0402)

# ------------------------------------------------------------------ Dev reset: open-drain buffer
b = s.add("74xGxx:74LVC1G07", "U1404", "74LVC1G07", (203.2, 157.48), footprint=SC70_5)
s.connect(b, "2", "DEV_M1421_NRST")
s.connect(b, "4", "M1421_NRST")
s.connect(b, "5", VCC)
s.connect(b, "3", "GND")
s.nc(b, "1")
s.two_pin("Device:R", "R1404", "100k", (165.1, 147.32), VCC, "DEV_M1421_NRST", R0402)
s.two_pin("Device:R", "R1405", "100k", (241.3, 147.32), VCC, "M1421_NRST", R0402)

# ------------------------------------------------------------------ activity LEDs (as carrier)
for i, (net, col, rv) in enumerate((("M1421_SD26", "RED 1090", "287R"), ("M1421_SD27", "GREEN UAT", "115R"))):
    y = 195.58 + i * 27.94
    s.two_pin("Device:R", f"R{1406 + i}", rv, (165.1, y), net, f"LED_{net[6:]}_A", R0402)
    d = s.add("Device:LED", f"D{1401 + i}", col, (182.88, y), footprint="LED_SMD:LED_0603_1608Metric")
    s.connect(d, "2", f"LED_{net[6:]}_A", kind="label")
    s.connect(d, "1", "GND")

# ------------------------------------------------------------------ RF: combiner -> ESD -> SMA
c = s.add("ADSB_Test:MiniCircuits_SCN-2-11", "U1405", "SCN-2-11+", (254.0, 213.36),
          footprint="ADSB_Test:MiniCircuits_SCN")
s.connect(c, "6", "M1421_RF_978", kind="label")
s.connect(c, "4", "M1421_RF_1090", kind="label")
s.connect(c, "2", "RF_ADSB_ANT", kind="label")
s.connect(c, ["1", "3", "5"], "GND")
s.two_pin("Device:R", "R1408", "100R", (228.6, 236.22), "M1421_RF_1090", "M1421_RF_978", R0402)
e = s.add("Device:D_TVS", "D1403", "ESD7351XV2T1G", (287.02, 233.68), footprint="Diode_SMD:D_SOD-523")
s.connect(e, "1", "RF_ADSB_ANT", kind="label")
s.connect(e, "2", "GND")
a = s.add("Connector:Conn_Coaxial", "J1403", "SMA 1090/978", (304.8, 213.36),
          footprint="Connector_Coaxial:SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount")
s.connect(a, "1", "RF_ADSB_ANT", kind="label")
s.connect(a, "2", "GND")

# ------------------------------------------------------------------ staging
# Until the Power Rails sheet drives 3V3_M1421 and GND, flag them here so ERC
# checks the rest. REMOVE when the power sheets are generated.
s.pwr_flag(VCC, (279.4, 35.56))
s.pwr_flag("GND", (292.1, 35.56))

# ------------------------------------------------------------------ notes
s.text("FIT OPTIONS: (a) solder U1401 m1421, or (b) leave U1401 off and plug the ADSBee 1421 Dev Kit\n"
       "into J1402 with its JST-GH-to-DuPont harness (Dev Kit uses its own U.FL antenna).\n"
       "SYNC (pad 28) is an INPUT: high at reset = ROM bootloader, high at run time = sleep.\n"
       "M1421_NRST: TCA6408A bit 7 drives it open-drain style (output-low = reset, input = release),\n"
       "U1404 for the Dev-port RP2040, J1401 pin 10 for a J-Link.\n"
       "RF: copy the ADSBee 1421 carrier CPW layout; keep the footprint keep-outs; filled+capped vias.",
       (127.0, 241.3))

if notes is not None:
    # keep the design notes, smaller, down the right-hand side
    for k in notes:
        if isinstance(k, list) and k[0] == "at":
            k[1:4] = ["322.58", "17.78", "0"]
        if isinstance(k, list) and k[0] == "size":
            k[1:3] = ["88.9", "248.92"]
        if isinstance(k, list) and k[0] == "effects":
            k[1] = ["font", ["size", "1.27", "1.27"]]

s.write(SHEET, "ADSB_Test - M1421", "Requirements: boards/adsb-test/docs/requirements.md", keep_notes=notes)
print("wrote", SHEET)
