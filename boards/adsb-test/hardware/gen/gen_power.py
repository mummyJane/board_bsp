#!/usr/bin/env python3
"""Generate the ADSB_Test power sheets: Power Input (2xx), Charger Battery (3xx),
Power Rails (4xx) and Power Monitor (5xx).

Run from the repo root:  python boards/adsb-test/hardware/gen/gen_power.py
Values marked "TBC" in a part's 'Check' field still need confirming against the
part datasheet (several vendor sites block automated downloads).
Design: boards/adsb-test/docs/architecture.md (power tree, monitor channel map).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from kicad_sch_gen import SymbolLibs, Sheet, sheet_uuids, existing_notes  # noqa: E402

KICAD = ROOT / "boards/adsb-test/hardware/kicad"
libs = SymbolLibs({"ADSB_Test": KICAD / "lib/ADSB_Test.kicad_sym"})
root_uuid, sheets = sheet_uuids(KICAD / "ADSB_Test.kicad_sch")

R0402 = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"   # hand-solder size everywhere
R0603 = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
C0402 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
C0603 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
C0805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
C1206 = "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
RSHUNT = "Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder"   # 4-terminal Kelvin layout done on the PCB
TP = "TestPoint:TestPoint_Pad_D1.5mm"


def new_sheet(file):
    s = Sheet(libs, "ADSB_Test", root_uuid, sheets[file])
    return s, existing_notes(KICAD / file)


STALE = [("5V buck 3A (part TBC)", "5V buck TPS62933 3A"), ("TPS25200 eFuse", "TPS2596 eFuse"),
         ("TPS25200", "TPS2596"), ("BQ25792", "BQ25798"),
         # WT01P4C5-S1 module (Q26): 5 V module rail, no P4 core supplies on the board
         ("3V3_P4, 3V3_C5, 3V3_ETH (sw)", "3V3_SD, 3V3_ETH (sw)"),
         ("5V_LCD load switch.", "5V_LCD load switch, -> 5V_MCU (WT01P4C5-S1 module, shunt only)."),
         ("- P4 core supplies (VDD_HP buck etc.): COPY FROM REFERENCE BOARD (MP1605/MP1658/RT9193 circuit).",
          "- No P4 core supplies: they are inside the WT01P4C5-S1 module."),
         ("5V_LCD, 3V3_P4, 3V3_C5, 3V3_ETH", "5V_LCD, 5V_MCU, 3V3_SD, 3V3_ETH"),
         ("5V total", "3V3 total"), ("addresses set by ADDRSEL resistor (TBC)", "addresses 0x10/0x11/0x12 by ADDRSEL resistor")]


def finish(s, notes, file, title):
    if notes is not None:
        for old, new in STALE:
            notes[1] = notes[1].replace(old, new)
        for k in notes:
            if isinstance(k, list) and k[0] == "at":
                k[1:4] = ["322.58", "17.78", "0"]
            if isinstance(k, list) and k[0] == "size":
                k[1:3] = ["88.9", "248.92"]
            if isinstance(k, list) and k[0] == "effects":
                k[1] = ["font", ["size", "1.27", "1.27"]]
    s.write(KICAD / file, title, "Requirements: boards/adsb-test/docs/requirements.md", keep_notes=notes)
    missing = s.missing_footprints({"ADSB_Test": KICAD / "lib/ADSB_Test.pretty"})
    if missing:
        print("  MISSING FOOTPRINTS:", missing)
    print("wrote", file)


def cap(s, ref, val, at, n1, n2, fp=C0402):
    return s.two_pin("Device:C", ref, val, at, n1, n2, fp)


def res(s, ref, val, at, n1, n2, fp=R0402):
    return s.two_pin("Device:R", ref, val, at, n1, n2, fp)


def testpoint(s, ref, net, at):
    tp = s.add("Connector:TestPoint", ref, net, at, footprint=TP)
    s.connect(tp, "1", net)


def shunt(s, ref, val, at, src, load, sense_p, sense_n):
    """4-terminal shunt: current src (pin 1) -> load (pin 4); Kelvin sense pins 2 (+) and 3 (-)."""
    r = s.add("Device:R_Shunt", ref, val, at, footprint=RSHUNT, props={"Check": "Kelvin-route pins 2/3 to the PAC1954"})
    s.connect(r, "1", src)
    s.connect(r, "4", load)
    s.connect(r, "2", sense_p)
    s.connect(r, "3", sense_n)
    return r


# =================================================================== Power Input (page 2)
s, notes = new_sheet("power_input.kicad_sch")
s.locals |= {"USER_CC1", "USER_CC2", "VBUS_USER_RAW", "PD_GATE", "PD_VREG12", "PD_VREG27", "PD_ATTACH",
             "PD_DISCH", "PD_RESET", "DEV_VBUS_JP"}
j = s.add("Connector:USB_C_Receptacle_USB2.0_16P", "J201", "User USB-C (PD sink)", (38.1, 88.9),
          footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal")
s.connect(j, ["A4", "A9", "B4", "B9"], "VBUS_USER_RAW")
s.connect(j, ["A1", "A12", "B1", "B12", "SH"], "GND")
s.connect(j, "A5", "USER_CC1")
s.connect(j, "B5", "USER_CC2")
s.connect(j, ["A6", "B6"], "USER_DP")
s.connect(j, ["A7", "B7"], "USER_DM")
s.nc(j, "A8")
s.nc(j, "B8")

d = s.add("Device:D_Zener", "D201", "SMAJ20A", (78.74, 50.8), footprint="Diode_SMD:D_SMA",
          props={"Check": "VBUS TVS for up to 15 V PD (20 V stand-off)"})
s.connect(d, "1", "VBUS_USER_RAW")
s.connect(d, "2", "GND")
cap(s, "C201", "10uF 25V", (96.52, 50.8), "VBUS_USER_RAW", "GND", C0805)

e = s.add("Power_Protection:USBLC6-2SC6", "U202", "USBLC6-2SC6", (78.74, 152.4), footprint="Package_TO_SOT_SMD:SOT-23-6_Handsoldering")
s.connect(e, ["1", "6"], "USER_DP")
s.connect(e, ["3", "4"], "USER_DM")
s.connect(e, "5", "3V3_PERIPH")
s.connect(e, "2", "GND")

u = s.add("Interface_USB:STUSB4500QTR", "U201", "STUSB4500QTR", (152.4, 101.6),
          footprint="ADSB_Test:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_HandSolder",
          props={"Check": "VSYS to GND (unused), VBUS_VS_DISCH to receptacle VBUS, DISCH via series R: per DS12499 pin table",
                 "NVM": "PDO1 5V/3A, PDO2 9V/3A, PDO3 15V/3A"})
s.connect(u, ["2", "1"], "USER_CC1")       # CC1 + CC1DB (dead-battery Rd)
s.connect(u, ["4", "5"], "USER_CC2")
s.nc(u, "3")
s.connect(u, "24", "VBUS_USER_RAW")         # VDD
s.connect(u, "18", "VBUS_USER_RAW")         # VBUS_VS_DISCH (sense, source side)
s.connect(u, "22", "GND")                   # VSYS unused
s.connect(u, "21", "PD_VREG12")
s.connect(u, "23", "PD_VREG27")
s.connect(u, ["12", "13"], "GND")           # ADDR = 0x28
s.connect(u, "7", "I2C_SCL")
s.connect(u, "8", "I2C_SDA")
s.connect(u, "19", "CHG_PD_INT")            # ALERT (open drain, wired-OR with charger INT)
s.connect(u, "16", "PD_GATE")               # VBUS_EN_SNK
s.connect(u, "11", "PD_ATTACH")
s.connect(u, ["10", "25"], "GND")
for pin in ("14", "15", "17", "20"):        # POWER_OK3, GPIO, A_B_SIDE, POWER_OK2
    s.nc(u, pin)
res(s, "R201", "1k", (200.66, 66.04), "VBUS_USER", "PD_DISCH")
s.connect(u, "9", "PD_DISCH")
res(s, "R202", "10k", (213.36, 66.04), "PD_RESET", "GND")
s.connect(u, "6", "PD_RESET")
cap(s, "C202", "1uF", (124.46, 152.4), "PD_VREG12", "GND")
cap(s, "C203", "1uF", (137.16, 152.4), "PD_VREG27", "GND")
cap(s, "C204", "1uF 25V", (149.86, 152.4), "VBUS_USER_RAW", "GND", C0603)
testpoint(s, "TP201", "PD_ATTACH", (175.26, 152.4))

q = s.add("Transistor_FET:FDS9435A", "Q201", "FDS9435A", (254.0, 101.6),
          footprint="", props={"Why": "SO-8 for hand soldering; -30 V, 5.3 A, 50 mOhm"})
s.connect(q, ["1", "2", "3"], "VBUS_USER_RAW")
s.connect(q, ["5", "6", "7", "8"], "VBUS_USER")
s.connect(q, "4", "PD_GATE")
res(s, "R203", "100k", (231.14, 132.08), "VBUS_USER_RAW", "PD_GATE")
cap(s, "C205", "10uF 25V", (279.4, 132.08), "VBUS_USER", "GND", C0805)
shunt(s, "RS201", "20m", (279.4, 76.2), "VBUS_USER", "VBUS_CHG", "PM1_CH1_P", "PM1_CH1_N")
testpoint(s, "TP202", "VBUS_USER", (292.1, 132.08))

res(s, "R204", "10k", (231.14, 190.5), "3V3_PERIPH", "CHG_PD_INT")

# Dev VBUS can feed the charger input for bench work: solder jumper, default OPEN
jp = s.add("Jumper:SolderJumper_2_Open", "JP201", "Dev VBUS -> charger (default open)", (63.5, 223.52),
           footprint="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm")
s.connect(jp, "1", "VBUS_DEV")
s.connect(jp, "2", "DEV_VBUS_JP")
ds = s.add("Device:D_Schottky", "D202", "SS34", (91.44, 223.52), footprint="Diode_SMD:D_SMA")
s.connect(ds, "2", "DEV_VBUS_JP")
s.connect(ds, "1", "VBUS_CHG")

s.pwr_flag("GND", (292.1, 25.4))
s.pwr_flag("VBUS_USER_RAW", (304.8, 25.4))
finish(s, notes, "power_input.kicad_sch", "ADSB_Test - Power Input")

# =================================================================== Charger Battery (page 3)
s, notes = new_sheet("charger_battery.kicad_sch")
s.locals |= {"CHG_PMID", "CHG_REGN", "CHG_SW1", "CHG_SW2", "CHG_BTST1", "CHG_BTST2", "CHG_TS", "CHG_PROG",
             "CHG_CE", "CHG_SDRV", "CHG_STAT", "CHG_LED_A", "VBAT_CHG", "VSYS_CHG", "BAT_NTC", "CHG_BATP", "CHG_QON"}
u = s.add("Battery_Management:BQ25798", "U301", "BQ25798", (127.0, 101.6),
          footprint="",
          props={"Config": "PROG 8.2k = 2S, 750 kHz (VREG 8.4 V, VSYSMIN 7 V, ICHG 1 A defaults)",
                 "Check": "Land pattern per TI RQM0029A; thermal vias"})
s.connect(u, ["2", "3", "9", "8"], "VBUS_CHG")      # VBUS, VAC1, VAC2 (single input, no ACFETs)
s.connect(u, ["10", "11"], "GND")                  # ACDRV1/2 to GND (no ACFET/RBFET)
s.connect(u, "29", "CHG_PMID")
s.connect(u, "5", "CHG_REGN")
s.connect(u, "28", "CHG_SW1")
s.connect(u, "26", "CHG_SW2")
s.connect(u, "4", "CHG_BTST1")
s.connect(u, "19", "CHG_BTST2")
s.connect(u, "25", "VSYS_CHG")
s.connect(u, ["22", "23"], "VBAT_CHG")
s.connect(u, "18", "CHG_BATP")
s.connect(u, "16", "CHG_TS")
s.connect(u, "17", "CHG_REGN")                     # ILIM_HIZ to REGN: limit set by IINDPM register
s.connect(u, "20", "CHG_PROG")
s.connect(u, "13", "CHG_CE")
s.connect(u, "24", "CHG_SDRV")
s.connect(u, "1", "CHG_STAT")
s.connect(u, "21", "CHG_PD_INT")
s.connect(u, "14", "I2C_SCL")
s.connect(u, "15", "I2C_SDA")
s.connect(u, "12", "CHG_QON")
s.connect(u, "27", "GND")
s.nc(u, "6")    # D+  (BC1.2 detection not used; User D+/D- go to the CP2102N)
s.nc(u, "7")    # D-

L = s.add("Device:L", "L301", "2.2uH", (127.0, 38.1), footprint="Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm",
          props={"Check": "Isat >= 6 A, e.g. TI eval uses WE 2.2 uH; footprint TBC"})
s.connect(L, "1", "CHG_SW1")
s.connect(L, "2", "CHG_SW2")
cap(s, "C301", "47nF", (175.26, 38.1), "CHG_BTST1", "CHG_SW1")
cap(s, "C302", "47nF", (187.96, 38.1), "CHG_BTST2", "CHG_SW2")
for i in range(2):
    cap(s, f"C30{3 + i}", "10uF 25V", (25.4 + 12.7 * i, 50.8), "VBUS_CHG", "GND", C0805)
for i in range(3):
    cap(s, f"C30{5 + i}", "10uF 25V", (25.4 + 12.7 * i, 88.9), "CHG_PMID", "GND", C0805)
cap(s, "C308", "100nF 25V", (63.5, 88.9), "CHG_PMID", "GND")
cap(s, "C309", "4.7uF 10V", (25.4, 127.0), "CHG_REGN", "GND", C0603)
for i in range(5):
    cap(s, f"C31{i}", "10uF 25V", (215.9 + 12.7 * i, 50.8), "VSYS_CHG", "GND", C0805)
cap(s, "C315", "100nF 25V", (279.4, 50.8), "VSYS_CHG", "GND")
for i in range(2):
    cap(s, f"C31{6 + i}", "10uF 25V", (215.9 + 12.7 * i, 101.6), "VBAT_CHG", "GND", C0805)
res(s, "R301", "8.2k 1%", (50.8, 165.1), "CHG_PROG", "GND")
res(s, "R302", "10k", (63.5, 165.1), "CHG_CE", "GND")
cap(s, "C318", "1nF 50V", (76.2, 165.1), "CHG_SDRV", "GND")
res(s, "R303", "5.23k 1%", (101.6, 165.1), "CHG_REGN", "CHG_TS")
res(s, "R304", "30.1k 1%", (114.3, 165.1), "CHG_TS", "GND")
res(s, "R305", "100R", (139.7, 165.1), "CHG_BATP", "BAT_PACK")
res(s, "R306", "2.2k", (165.1, 165.1), "CHG_REGN", "CHG_LED_A")
led = s.add("Device:LED", "D301", "CHG (amber)", (182.88, 165.1), footprint="LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder")
s.connect(led, "2", "CHG_LED_A")
s.connect(led, "1", "CHG_STAT")
testpoint(s, "TP301", "CHG_QON", (88.9, 190.5))

bat = s.add("Connector_Generic:Conn_01x03", "J301", "2S Li-ion pack (BAT+, GND, NTC)", (279.4, 165.1),
            footprint="Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
            props={"Check": "Pack must have 2S protection + balancing BMS; 10k 103AT NTC to GND; connector rating >= 3 A"})
s.connect(bat, "1", "BAT_PACK")
s.connect(bat, "2", "GND")
s.connect(bat, "3", "CHG_TS")

# Always-on backup supply (VBACKUP, 3.0 V) for the DS3231M RTC VBAT and the GPS V_BCKP.
# Fed from VSYS, which is up whenever a battery or USB is present, regardless of the
# POWER switch. Optional CR1220 holder (not fitted) keeps it alive with the battery removed.
s.locals |= {"VBACKUP_LDO", "BKP_CELL"}
ldo = s.add("Regulator_Linear:MCP1703Ax-300xxTT", "U302", "MCP1703 3.0V (2 uA Iq)", (152.4, 226.06),
            footprint="Package_TO_SOT_SMD:SOT-23_Handsoldering")
s.connect(ldo, "3", "VSYS")
s.connect(ldo, "2", "VBACKUP_LDO")
s.connect(ldo, "1", "GND")
cap(s, "C319", "1uF 25V", (127.0, 226.06), "VSYS", "GND", C0805)
cap(s, "C320", "1uF", (177.8, 241.3), "VBACKUP_LDO", "GND")
dl = s.add("Device:D_Schottky", "D302", "BAT43W", (190.5, 226.06), footprint="Diode_SMD:D_SOD-123")
s.connect(dl, "2", "VBACKUP_LDO")
s.connect(dl, "1", "VBACKUP")
cell = s.add("Device:Battery_Cell", "BT301", "CR1220 (optional)", (215.9, 243.84), dnp=True,
             footprint="Battery:Battery_Panasonic_CR1220-VCN_Vertical_CircularHoles",
             props={"Fit": "DNP by default; fit to keep RTC/GPS alive with the main battery removed"})
s.connect(cell, "1", "BKP_CELL")
s.connect(cell, "2", "GND")
dc = s.add("Device:D_Schottky", "D303", "BAT43W", (228.6, 226.06), footprint="Diode_SMD:D_SOD-123", dnp=True)
s.connect(dc, "2", "BKP_CELL")
s.connect(dc, "1", "VBACKUP")
cap(s, "C321", "1uF", (254.0, 241.3), "VBACKUP", "GND")
testpoint(s, "TP305", "VBACKUP", (266.7, 226.06))
s.pwr_flag("VBACKUP", (279.4, 226.06))

shunt(s, "RS301", "10m", (254.0, 101.6), "VBAT_CHG", "BAT_PACK", "PM1_CH2_P", "PM1_CH2_N")
shunt(s, "RS302", "10m", (304.8, 101.6), "VSYS_CHG", "VSYS", "PM1_CH3_P", "PM1_CH3_N")
testpoint(s, "TP302", "BAT_PACK", (241.3, 190.5))
testpoint(s, "TP303", "VSYS", (254.0, 190.5))
testpoint(s, "TP304", "VBUS_CHG", (266.7, 190.5))
s.pwr_flag("VBUS_CHG", (304.8, 25.4))
finish(s, notes, "charger_battery.kicad_sch", "ADSB_Test - Charger Battery")

# =================================================================== Power Rails (page 4)
s, notes = new_sheet("power_rails.kicad_sch")


def buck(s, n, name, out_net, rfbt, at):
    """TPS62933 from VSYS: RT open = 500 kHz, L 4.7 uH, SS 33 nF, BST 100 nF, EN UVLO ~5.5 V."""
    x, y = at
    loc = {f"{name}_SW", f"{name}_BST", f"{name}_FB", f"{name}_SS", "PWR_EN"}
    s.locals |= loc
    u = s.add("Regulator_Switching:TPS62933", f"U4{n}1", "TPS62933", (x, y),
              footprint="ADSB_Test:SOT-583-8_HandSolder", props={"Out": out_net})
    s.connect(u, "3", "VSYS")
    s.connect(u, "4", "GND")
    s.connect(u, "5", f"{name}_SW")
    s.connect(u, "6", f"{name}_BST")
    s.connect(u, "8", f"{name}_FB")
    s.connect(u, "7", f"{name}_SS")
    s.connect(u, "2", "PWR_EN")              # shared enable: power switch + UVLO divider
    s.nc(u, "1")                                   # RT open -> 500 kHz
    cap(s, f"C4{n}1", "10uF 25V", (x - 38.1, y - 25.4), "VSYS", "GND", C0805)
    cap(s, f"C4{n}2", "10uF 25V", (x - 25.4, y - 25.4), "VSYS", "GND", C0805)
    cap(s, f"C4{n}3", "100nF", (x - 12.7, y - 25.4), "VSYS", "GND")
    if n == 1:   # one UVLO divider (~5.5 V on VSYS) for both bucks
        res(s, "R411", "100k", (x - 38.1, y + 25.4), "VSYS", "PWR_EN")
        res(s, "R412", "28k", (x - 25.4, y + 25.4), "PWR_EN", "GND")
    cap(s, f"C4{n}4", "33nF", (x - 12.7, y + 25.4), f"{name}_SS", "GND")
    cap(s, f"C4{n}5", "100nF", (x + 25.4, y - 25.4), f"{name}_BST", f"{name}_SW")
    L = s.add("Device:L", f"L4{n}1", "4.7uH", (x + 38.1, y - 25.4), footprint="Inductor_SMD:L_Bourns_SRP5030T",
              props={"Check": "Isat >= 4 A"})
    s.connect(L, "1", f"{name}_SW")
    s.connect(L, "2", out_net)
    res(s, f"R4{n}3", rfbt, (x + 25.4, y + 25.4), out_net, f"{name}_FB")
    res(s, f"R4{n}4", "10k 1%", (x + 38.1, y + 25.4), f"{name}_FB", "GND")
    cap(s, f"C4{n}6", "22uF 10V", (x + 50.8, y - 25.4), out_net, "GND", C1206)
    cap(s, f"C4{n}7", "22uF 10V", (x + 63.5, y - 25.4), out_net, "GND", C1206)
    s.pwr_flag(out_net, (x + 63.5, y + 22.86))


buck(s, 1, "B5V", "5V", "52.3k 1%", (63.5, 63.5))
buck(s, 2, "B3V3", "3V3_BUCK", "31.6k 1%", (63.5, 157.48))

# POWER switch: OFF pulls the shared buck enable low, so 5 V and 3V3 (and everything after them)
# are off. VSYS stays up, so the charger still charges from USB and the always-on backup LDO
# (Charger sheet, VBACKUP for the DS3231M RTC + GPS) keeps running.
sw = s.add("Switch:SW_SPDT", "SW401", "POWER (slide)", (38.1, 228.6),
           footprint="Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q",
           props={"Positions": "B-C = OFF (enable to GND), B-A = ON"})
s.connect(sw, "2", "PWR_EN")
s.connect(sw, "3", "GND")
s.nc(sw, "1")
s.text("POWER: SW401 OFF = PWR_EN low = both bucks off.\nVSYS, charger and VBACKUP stay alive.", (25.4, 241.3))


def switch(s, ref, at, vin, vout, en):
    ct, qd = f"CT{ref[2:]}", f"QD{ref[2:]}"
    s.locals |= {ct, qd}
    u = s.add("Power_Management:TPS22917DBV", ref, "TPS22917", at, footprint="Package_TO_SOT_SMD:SOT-23-6_Handsoldering")
    s.connect(u, "1", vin)
    s.connect(u, "6", vout)
    s.connect(u, "5", qd)    # QOD via 100R to VOUT: quick output discharge when off
    res(s, f"R{ref[1:]}", "100R", (at[0] + 10.16, at[1] + 22.86), qd, vout)
    s.connect(u, "3", en)
    s.connect(u, "2", "GND")
    s.connect(u, "4", ct)
    cap(s, f"C{ref[1:]}", "1nF", (at[0] - 5.08, at[1] + 22.86), ct, "GND")
    s.pwr_flag(vin, (at[0] - 15.24, at[1] - 17.78))   # shunt (passive) feeds the switch


# 3V3 total (PM3 ch4), then the branches. Each shunt doubles as the staged bring-up link.
shunt(s, "RS401", "10m", (152.4, 30.48), "3V3_BUCK", "3V3", "PM3_CH4_P", "PM3_CH4_N")
rails = [  # ref, value, src, mid/load, pm channel, switch enable or None, final rail
    ("RS402", "20m", "5V", "5V_SDR", "PM1_CH4", None, None),
    ("RS403", "50m", "5V", "5V_LCD_SH", "PM2_CH1", "EXP_EN_LCD", "5V_LCD"),
    ("RS404", "20m", "5V", "5V_MCU", "PM2_CH2", None, None),        # WT01P4C5-S1 module (5 V in, <= 1.5 A)
    ("RS405", "100m", "3V3", "3V3_SD", "PM2_CH3", None, None),      # microSD card supply
    ("RS406", "100m", "3V3", "3V3_ETH_SH", "PM2_CH4", "EXP_EN_ETH", "3V3_ETH"),
    ("RS407", "1R", "3V3", "3V3_GPS_SH", "PM3_CH1", "EXP_EN_GPS", "3V3_GPS"),
    ("RS408", "1R", "3V3", "3V3_M1421_SH", "PM3_CH2", "EXP_EN_M1421", "3V3_M1421"),
    ("RS409", "100m", "3V3", "3V3_PERIPH", "PM3_CH3", None, None),
]
plain = [r for r in rails if not r[5]]
switched = [r for r in rails if r[5]]
for i, (ref, val, src, mid, pm, en, final) in enumerate(plain):        # top row: shunt only
    x, y = 152.4 + i * 43.18, 76.2
    shunt(s, ref, val, (x, y), src, mid, f"{pm}_P", f"{pm}_N")
    s.pwr_flag(mid, (x + 12.7, y + 20.32))
    testpoint(s, f"TP4{10 + rails.index((ref, val, src, mid, pm, en, final))}", mid, (x - 12.7, y + 25.4))
for i, (ref, val, src, mid, pm, en, final) in enumerate(switched):     # 2x2 grid: shunt -> load switch
    x, y = 165.1 + (i % 2) * 88.9, 124.46 + (i // 2) * 83.82
    s.locals.add(mid)
    shunt(s, ref, val, (x, y), src, mid, f"{pm}_P", f"{pm}_N")
    switch(s, f"U4{30 + i}", (x, y + 33.02), mid, final, en)
    testpoint(s, f"TP4{10 + rails.index((ref, val, src, mid, pm, en, final))}", final, (x + 30.48, y + 50.8))
testpoint(s, "TP401", "5V", (25.4, 254.0))
testpoint(s, "TP402", "3V3", (38.1, 254.0))
testpoint(s, "TP403", "VSYS", (50.8, 254.0))
s.pwr_flag("3V3", (182.88, 20.32))
s.pwr_flag("VSYS", (198.12, 20.32))   # VSYS comes through shunt RS302 (passive)
finish(s, notes, "power_rails.kicad_sch", "ADSB_Test - Power Rails")

# =================================================================== Power Monitor (page 5)
s, notes = new_sheet("power_monitor.kicad_sch")
addr = {"1": "0R (0x10)", "2": "499R 1% (0x11)", "3": "806R 1% (0x12)"}
for n in ("1", "2", "3"):
    x = 76.2 + (int(n) - 1) * 88.9
    y = 101.6
    u = s.add("Sensor_Energy:PAC1954x-x4MX", f"U50{n}", f"PAC1954 (PM{n})", (x, y),
              footprint="ADSB_Test:VQFN-16-1EP_3x3mm_P0.5mm_EP1.1x1.1mm_HandSolder",
              props={"I2C": {"1": "0x10", "2": "0x11", "3": "0x12"}[n] + " (ADDRSEL, DS20006539 Table 6-1)"})
    for ch in range(1, 5):
        s.connect(u, f"SENSE{ch}+", f"PM{n}_CH{ch}_P")
        s.connect(u, f"SENSE{ch}-", f"PM{n}_CH{ch}_N")
    s.connect(u, "2", "3V3_PERIPH")
    s.connect(u, ["3", "17"], "GND")
    s.connect(u, "4", "I2C_SCL")
    s.connect(u, "5", "I2C_SDA")
    s.connect(u, "15", "PM_ALERT")                 # GPIO configured as ALERT (open drain)
    s.connect(u, "1", "GND")                       # SLOW: normal sample rate
    s.locals.add(f"PM{n}_ADDR")
    s.connect(u, "6", f"PM{n}_ADDR")
    s.connect(u, "16", "3V3_PERIPH")               # PWRDN high = active
    res(s, f"R50{n}", addr[n], (x + 25.4, y + 38.1), f"PM{n}_ADDR", "GND")
    cap(s, f"C50{n}", "100nF", (x, y - 50.8), "3V3_PERIPH", "GND")
res(s, "R504", "10k", (304.8, 50.8), "3V3_PERIPH", "PM_ALERT")
s.text("PM1: CH1 VBUS_USER, CH2 VBAT (bidirectional), CH3 VSYS, CH4 5V_SDR\n"
       "PM2: CH1 5V_LCD, CH2 5V_MCU (P4+C5 module), CH3 3V3_SD, CH4 3V3_ETH\n"
       "PM3: CH1 3V3_GPS, CH2 3V3_M1421, CH3 3V3_PERIPH, CH4 3V3 total\n"
       "Sense lines: Kelvin from each shunt (pins 2/3), routed as pairs.", (25.4, 190.5))
finish(s, notes, "power_monitor.kicad_sch", "ADSB_Test - Power Monitor")
