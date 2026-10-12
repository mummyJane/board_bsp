#!/usr/bin/env python3
"""Generate the ADSB_Test 'MCU Module' (page 6) and 'RTC' (page 7) sheets.

MCU: Wireless-Tag WT01P4C5-S1 (ESP32-P4 + ESP32-C5 over SDIO, inside the module), Q26.
RTC: DS3231M on VBACKUP, because the module has no P4 VBAT pin (Q27).

Run from the repo root:  python boards/adsb-test/hardware/gen/gen_mcu.py
Needs the module symbol/footprint from gen_wt01p4c5.py. Pins: bsp/include/bsp/board_pins.h.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from kicad_sch_gen import SymbolLibs, Sheet, sheet_uuids  # noqa: E402

KICAD = ROOT / "boards/adsb-test/hardware/kicad"
R0805 = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
C0805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
C1206 = "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
TPFP = "TestPoint:TestPoint_Pad_D1.5mm"

libs = SymbolLibs({"ADSB_Test": KICAD / "lib/ADSB_Test.kicad_sym"})
root_uuid, sheets = sheet_uuids(KICAD / "ADSB_Test.kicad_sch")


def tp(s, ref, net, at, local=True):
    t = s.add("Connector:TestPoint", ref, net, at, footprint=TPFP)
    s.connect(t, "1", net, kind="label" if local else None)


# =================================================================== MCU Module (page 6)
s = Sheet(libs, "ADSB_Test", root_uuid, sheets["mcu_module.kicad_sch"])
s.locals |= {"XTAL32_P", "XTAL32_N", "C5_TMS", "C5_TDI", "C5_TCK", "C5_TDO", "C5_IO26", "MCU_PWR_CTRL",
             "C5_IO1", "C5_IO6", "C5_IO23", "C5_IO24", "C5_IO25", "C5_IO27", "P4_GPIO36", "P4_GPIO54"}
u = s.add("ADSB_Test:Wireless-Tag_WT01P4C5-S1", "U601", "WT01P4C5-S1-N16R32", (203.2, 142.24),
          footprint="ADSB_Test:Wireless-Tag_WT01P4C5-S1_HandSolder",
          props={"Check": "Land pattern derived from datasheet v1.3 drawing: measure a real module before ordering PCBs",
                 "Antenna": "IPEX (U.FL) on the module: pigtail to a 2.4/5 GHz antenna at the digital edge"})
s.connect(u, ["68", "69"], "5V_MCU")
s.connect(u, ["10", "29", "36", "43", "46", "47", "70", "71", "92"], "GND")
for p in ("17", "23", "72", "37", "38", "39", "40", "41", "42"):   # NC1/NC2, VBAT (no internal connection), CSI unused
    s.nc(u, p)
nets = {
    # P4 side (module pad: net). GPIO numbers in board_pins.h.
    "11": "P4_EN", "12": "XTAL32_N", "13": "XTAL32_P", "14": "P4_GPS_TX", "15": "GPS_TX", "16": "GPS_PPS",
    "18": "RTC_INT", "19": "I2C_SDA", "20": "I2C_SCL", "21": "CHG_PD_INT", "22": "DBG_A", "24": "DBG_B",
    "25": "PM_ALERT", "26": "P4_USER_TX", "27": "P4_USER_RX", "28": "TOUCH_RST",
    "30": "DSI_D1_P", "31": "DSI_D1_N", "32": "DSI_CLK_N", "33": "DSI_CLK_P", "34": "DSI_D0_P", "35": "DSI_D0_N",
    "44": "USB_HS_DM", "45": "USB_HS_DP", "48": "P4_USJ_DM", "49": "P4_USJ_DP", "50": "TOUCH_INT",
    "51": "USBA_FAULT", "52": "ETH_CRS_DV", "53": "ETH_RXD0", "54": "ETH_RXD1", "55": "ETH_MDC",
    "56": "LCD_BL_PWM", "57": "LCD_RST", "58": "ETH_TXD0", "59": "ETH_TXD1_BOOT", "60": "P4_GPIO36",
    "61": "P4_CON_TX", "62": "P4_CON_RX", "63": "SD_VIO", "64": "SD_D0", "65": "SD_D1", "66": "SD_D2",
    "67": "MCU_PWR_CTRL", "73": "SD_D3", "74": "SD_CLK", "75": "SD_CMD", "76": "SD_PWR_EN",
    "77": "P4_M1421_TX", "78": "M1421_SUTX", "79": "P4_M1421_SYNC", "80": "ETH_TX_EN", "81": "ETH_REF_CLK",
    "82": "ETH_PHY_RST", "83": "ETH_MDIO", "84": "EXP_INT", "85": "P4_GPIO54",
    # C5 side
    "1": "C5_EN", "2": "C5_IO1", "3": "C5_TMS", "4": "C5_TDI", "5": "C5_TCK", "6": "C5_TDO", "7": "C5_IO6",
    "8": "C5_CON_TX", "9": "C5_CON_RX", "86": "C5_IO23", "87": "C5_IO24", "88": "C5_IO25", "89": "C5_IO26",
    "90": "C5_IO27", "91": "C5_BOOT",
}
for pin, net in nets.items():
    s.connect(u, pin, net)

# 5 V supply decoupling (module regulates internally; up to 1.5 A)
s.two_pin("Device:C", "C601", "22uF 10V", (38.1, 33.02), "5V_MCU", "GND", C1206)
s.two_pin("Device:C", "C602", "22uF 10V", (50.8, 33.02), "5V_MCU", "GND", C1206)
s.two_pin("Device:C", "C603", "100nF", (63.5, 33.02), "5V_MCU", "GND", C0805)
s.two_pin("Device:C", "C604", "1uF", (76.2, 33.02), "SD_VIO", "GND", C0805)     # ESP_LDO_VO4 output (SD I/O)

# 32.768 kHz crystal on GPIO0/1 (as the reference board)
y = s.add("Device:Crystal", "Y601", "32.768kHz", (50.8, 68.58),
          footprint="Crystal:Crystal_C26-LF_D2.1mm_L6.5mm_Horizontal", props={"Note": "Through-hole tuning fork, hand-solder"})
s.connect(y, "1", "XTAL32_P")
s.connect(y, "2", "XTAL32_N")
s.two_pin("Device:C", "C605", "22pF", (38.1, 86.36), "XTAL32_P", "GND", C0805)
s.two_pin("Device:C", "C606", "22pF", (63.5, 86.36), "XTAL32_N", "GND", C0805)
s.two_pin("Device:R", "R601", "10M", (76.2, 68.58), "XTAL32_P", "XTAL32_N", R0805)

# I2C pull-ups (bus master here)
s.two_pin("Device:R", "R602", "2.2k", (38.1, 116.84), "3V3", "I2C_SDA", R0805)
s.two_pin("Device:R", "R603", "2.2k", (50.8, 116.84), "3V3", "I2C_SCL", R0805)

# Reset / BOOT (Dev FT2232H ch A drives the same nets for auto-reset)
s.two_pin("Device:R", "R604", "4.7k", (38.1, 157.48), "3V3", "ETH_TXD1_BOOT", R0805)
s.two_pin("Device:C", "C607", "1uF", (50.8, 157.48), "P4_EN", "GND", C0805)
for ref, name, net, x in (("SW601", "BOOT", "ETH_TXD1_BOOT", 38.1), ("SW602", "RESET", "P4_EN", 63.5)):
    b = s.add("Switch:SW_Push", ref, name, (x, 190.5), footprint="Button_Switch_THT:SW_PUSH_6mm")
    s.connect(b, "1", net)
    s.connect(b, "2", "GND")

# C5 straps: GPIO26 floats by default and 26 = 27 = 28 = 0 selects SDIO download, so pull it up
s.two_pin("Device:R", "R605", "10k", (330.2, 50.8), "3V3", "C5_IO26", R0805)

# C5 JTAG (not fitted by default; the C5 is normally flashed over UART0 from the Dev port)
j = s.add("Connector:Conn_ARM_JTAG_SWD_10", "J601", "C5 JTAG (DNP)", (350.52, 101.6), dnp=True,
          footprint="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD")
s.connect(j, "1", "3V3")
s.connect(j, ["3", "5", "9"], "GND")
s.connect(j, "2", "C5_TMS")
s.connect(j, "4", "C5_TCK")
s.connect(j, "6", "C5_TDO")
s.connect(j, "8", "C5_TDI")
s.connect(j, "10", "C5_EN")
s.nc(j, "7")

# spare pins to test pads
for i, net in enumerate(("C5_IO1", "C5_IO6", "C5_IO23", "C5_IO24", "C5_IO25", "C5_IO27",
                         "P4_GPIO36", "P4_GPIO54", "MCU_PWR_CTRL")):
    tp(s, f"TP{601 + i}", net, (309.88 + (i % 3) * 15.24, 167.64 + (i // 3) * 25.4))

s.text("MCU MODULE: Wireless-Tag WT01P4C5-S1 (ESP32-P4 + ESP32-C5, SDIO inside: P4 GPIO14-19,\n"
       "C5 CHIP_PU = P4 GPIO13, C5 GPIO0 = P4 GPIO12). Pins: bsp/include/bsp/board_pins.h.\n"
       "5 V supply only (5V_MCU, shunt RS404 / PM2 CH2); PWR_CTRL left to its internal pull-up (TP).\n"
       "No P4 VBAT on this module: wall-clock time is kept by the DS3231M (RTC sheet).\n"
       "Wi-Fi: IPEX on the module -> U.FL pigtail -> antenna at the digital edge (case must be plastic there).\n"
       "Hand solder: 1.4 mm castellated pads; no exposed copper/untented vias under the module.\n"
       "GPIO35 = BOOT strap + RMII TXD1 (4.7k pull-up, PHY must not pull it low at reset).",
       (25.4, 233.68))
s.write(KICAD / "mcu_module.kicad_sch", "ADSB_Test - MCU Module", "Requirements: boards/adsb-test/docs/requirements.md")
print("wrote mcu_module.kicad_sch")
missing = s.missing_footprints({"ADSB_Test": KICAD / "lib/ADSB_Test.pretty"})

# =================================================================== RTC (page 7)
r = Sheet(libs, "ADSB_Test", root_uuid, sheets["rtc.kicad_sch"])
rtc = r.add("Timer_RTC:DS3231MZ", "U701", "DS3231M", (127.0, 101.6),
            footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", props={"I2C": "0x68", "MPN": "DS3231MZ+"})
r.connect(rtc, "2", "3V3")
r.connect(rtc, "6", "VBACKUP")
r.connect(rtc, "5", "GND")
r.connect(rtc, "7", "I2C_SDA")
r.connect(rtc, "8", "I2C_SCL")
r.connect(rtc, "3", "RTC_INT")
r.nc(rtc, "1")       # 32KHZ not used
r.nc(rtc, "4")       # ~RST: internal pull-up, not used
r.two_pin("Device:C", "C701", "100nF", (76.2, 76.2), "3V3", "GND", C0805)
r.two_pin("Device:C", "C702", "100nF", (88.9, 76.2), "VBACKUP", "GND", C0805)
r.two_pin("Device:R", "R701", "10k", (177.8, 76.2), "3V3", "RTC_INT", R0805)
tp(r, "TP701", "RTC_INT", (190.5, 101.6), local=False)
r.text("RTC: DS3231M (+/-5 ppm, MEMS resonator, no crystal) at I2C 0x68.\n"
       "VCC from 3V3 when on; VBAT from VBACKUP (always-on 3.0 V LDO, optional CR1220) when off.\n"
       "INT/SQW (open drain) -> P4 GPIO6 (LP GPIO: alarm wake-up from deep sleep).\n"
       "Replaces the P4's own RTC backup: the WT01P4C5-S1 has no VBAT pin (Q27).",
       (25.4, 165.1))
r.write(KICAD / "rtc.kicad_sch", "ADSB_Test - RTC", "Requirements: boards/adsb-test/docs/requirements.md")
print("wrote rtc.kicad_sch")
missing.update(r.missing_footprints({"ADSB_Test": KICAD / "lib/ADSB_Test.pretty"}))
if missing:
    print("  MISSING FOOTPRINTS:", missing)
