#!/usr/bin/env python3
"""Generate the ADSB_Test 'MCU Module' (page 6) and 'RTC' (page 7) sheets.

MCU: OSPTEK ESP32-P4C5 Core (ESP32-P4 rev v3.x + ESP32-C5HF4 over SDIO inside the module), Q26.
     Inside the module: SDIO on P4 GPIO14-19, C5 CHIP_PU on P4 GPIO54, C5 GPIO2 on P4 GPIO6 -
     the same wiring as the Waveshare reference board's C6.
RTC: DS3231M on VBACKUP, now optional (DNP): the module has RTC_VBAT, so the P4 RTC keeps time (Q27).

Run from the repo root:  python boards/adsb-test/hardware/gen/gen_mcu.py
Needs the module symbol/footprint from gen_osptek_p4c5.py. Pins: bsp/include/bsp/board_pins.h.
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
s = Sheet(libs, "ADSB_Test", root_uuid, sheets["mcu_module.kicad_sch"], pwr_base=6000)
s.locals |= {"XTAL32_P", "XTAL32_N", "C5_IO26", "C5_IO27", "C5_IO25", "C5_IO24", "C5_IO23", "C5_IO6",
             "C5_IO5", "C5_IO4", "SLEEP_WAKE", "SLEEP_BTN", "P4_GPIO20", "P4_GPIO36", "C5_PU"}
u = s.add("ADSB_Test:OSPTEK_ESP32-P4C5_Core", "U601", "ESP32-P4C5 Core (OSPTEK)", (203.2, 142.24),
          footprint="ADSB_Test:OSPTEK_ESP32-P4C5_Core_HandSolder",
          props={"Source": "OSPTEK AliExpress 1005012626312933; docs github.com/osptek/esp32-p4c5-core-board",
                 "Antenna": "IPEX (U.FL) on the module: pigtail to a 2.4/5 GHz antenna"})
s.connect(u, ["85", "86"], "3V3_MCU")
s.connect(u, ["1", "3", "15", "33", "40", "47", "52", "83"], "GND")
for p in ("2", "21", "41", "42", "43", "44", "45", "46"):   # LAN_OUT (use the IPEX), GPIO6 = C5 IO2 inside, CSI unused
    s.nc(u, p)
nets = {
    # P4 side (module pad: net). GPIO numbers in board_pins.h (same as the reference board where reused).
    "87": "P4_EN", "88": "XTAL32_N", "16": "XTAL32_P", "17": "P4_GPS_TX", "18": "GPS_TX", "19": "GPS_PPS",
    "20": "PM_ALERT", "22": "I2C_SDA", "23": "I2C_SCL", "24": "CHG_PD_INT", "25": "DBG_A", "26": "DBG_B",
    "27": "SLEEP_WAKE", "28": "RTC_INT", "29": "P4_GPIO20", "30": "P4_USER_TX", "31": "P4_USER_RX", "32": "TOUCH_RST",
    "34": "DSI_D1_P", "35": "DSI_D1_N", "36": "DSI_CLK_N", "37": "DSI_CLK_P", "38": "DSI_D0_P", "39": "DSI_D0_N",
    "48": "USB_HS_D_N", "49": "USB_HS_D_P", "50": "P4_USJ_D_N", "51": "P4_USJ_D_P", "53": "TOUCH_INT",
    "54": "USBA_FAULT", "55": "ETH_CRS_DV", "56": "ETH_RXD0", "57": "ETH_RXD1", "58": "ETH_MDC",
    "59": "LCD_BL_PWM", "60": "LCD_RST", "61": "ETH_TXD0", "62": "ETH_TXD1_BOOT", "63": "P4_GPIO36",
    "64": "P4_CON_TX", "65": "P4_CON_RX", "66": "SD_VIO", "67": "SD_D0", "68": "SD_D1", "69": "SD_D2",
    "70": "SD_D3", "71": "SD_CLK", "72": "SD_CMD", "73": "SD_PWR_EN",
    "74": "P4_M1421_TX", "75": "M1421_SUTX", "76": "P4_M1421_SYNC", "77": "ETH_TX_EN", "78": "ETH_REF_CLK",
    "79": "ETH_PHY_RST", "80": "ETH_MDIO", "81": "EXP_INT", "82": "C5_PU", "84": "VBACKUP",
    # C5 side
    "4": "C5_CON_RX", "5": "C5_CON_TX", "6": "C5_BOOT", "7": "C5_IO27", "8": "C5_IO26", "9": "C5_IO25",
    "10": "C5_IO24", "11": "C5_IO23", "12": "C5_IO6", "13": "C5_IO5", "14": "C5_IO4",
}
for pin, net in nets.items():
    s.connect(u, pin, net)

# 3.3 V supply decoupling (module: 3.0-3.6 V, about 1 A)
s.two_pin("Device:C", "C601", "22uF 10V", (38.1, 33.02), "3V3_MCU", "GND", C1206)
s.two_pin("Device:C", "C602", "22uF 10V", (50.8, 33.02), "3V3_MCU", "GND", C1206)
s.two_pin("Device:C", "C603", "100nF", (63.5, 33.02), "3V3_MCU", "GND", C0805)
s.two_pin("Device:C", "C604", "1uF", (76.2, 33.02), "SD_VIO", "GND", C0805)     # ESP_LDO_VO4 output (SD I/O)
s.two_pin("Device:C", "C608", "100nF", (88.9, 33.02), "VBACKUP", "GND", C0805)  # RTC_VBAT (must not float)

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

# Reset / BOOT. The module has no reset RC on CHIP_PU, so 10k + 1uF here. Dev FT2232H ch A drives the
# same nets for auto-reset. GPIO35 has no pull-up inside the module: 4.7k here.
s.two_pin("Device:R", "R607", "10k", (25.4, 157.48), "3V3_MCU", "P4_EN", R0805)
s.two_pin("Device:R", "R604", "4.7k", (38.1, 157.48), "3V3", "ETH_TXD1_BOOT", R0805)
s.two_pin("Device:C", "C607", "1uF", (50.8, 157.48), "P4_EN", "GND", C0805)
for ref, name, net, x in (("SW601", "BOOT", "ETH_TXD1_BOOT", 38.1), ("SW602", "RESET", "P4_EN", 63.5)):
    b = s.add("Switch:SW_Push", ref, name, (x, 190.5), footprint="Button_Switch_THT:SW_PUSH_6mm")
    s.connect(b, "1", net)
    s.connect(b, "2", "GND")

# SLEEP/WAKE button on GPIO12 (LP GPIO, so it can wake the P4 from deep sleep: ext1, low level). Pull-up on
# 3V3_MCU (stays on in sleep), 470R series + 100nF against ESD and bounce (edge-mounted button).
b = s.add("Switch:SW_Push", "SW603", "SLEEP/WAKE", (101.6, 190.5),
          footprint="Button_Switch_THT:SW_Tactile_SPST_Angled_PTS645Vx31-2LFS",
          props={"Note": "Right-angle tactile on the digital edge next to the POWER switch"})
s.connect(b, "1", "SLEEP_BTN")
s.connect(b, "2", "GND")
s.two_pin("Device:R", "R608", "10k", (88.9, 157.48), "3V3_MCU", "SLEEP_BTN", R0805)
s.two_pin("Device:R", "R609", "470R", (101.6, 157.48), "SLEEP_BTN", "SLEEP_WAKE", R0805)
s.two_pin("Device:C", "C609", "100nF", (114.3, 157.48), "SLEEP_WAKE", "GND", C0805)

# C5 reset from the Dev port: C5 CHIP_PU is the P4 GPIO54 net inside the module (pad 82). 330R limits the
# current if the P4 is driving it high; firmware drives GPIO54 open-drain so the Dev port can pull it low.
s.two_pin("Device:R", "R606", "330R", (330.2, 76.2), "C5_PU", "C5_EN", R0805)
# C5 straps: GPIO26 floats by default and 26 = 27 = 28 = 0 selects SDIO download, so pull it up
s.two_pin("Device:R", "R605", "10k", (330.2, 50.8), "3V3", "C5_IO26", R0805)

# spare pins to test pads
for i, net in enumerate(("C5_IO27", "C5_IO25", "C5_IO24", "C5_IO23", "C5_IO6", "C5_IO5", "C5_IO4",
                         "SLEEP_WAKE", "P4_GPIO20", "P4_GPIO36", "C5_PU")):
    tp(s, f"TP{601 + i}", net, (309.88 + (i % 4) * 15.24, 152.4 + (i // 4) * 25.4))

s.text("MCU MODULE: OSPTEK ESP32-P4C5 Core (ESP32-P4 rev v3.x + ESP32-C5HF4, 16 MB flash, 32 MB PSRAM).\n"
       "Inside the module: SDIO on P4 GPIO14-19, C5 CHIP_PU = P4 GPIO54 (pad 82), C5 GPIO2 = P4 GPIO6 (pad 21, NC here)\n"
       "- the same wiring as the Waveshare reference board. Pins: bsp/include/bsp/board_pins.h.\n"
       "3.3 V supply (3V3_MCU, shunt RS404 / PM2 CH2). RTC_VBAT from VBACKUP (always on): P4 RTC keeps time when off.\n"
       "CHIP_PU has no RC inside the module: R607/C607 here. C5 reset from the Dev port via R606 onto the GPIO54 net.\n"
       "Wi-Fi: IPEX on the module -> U.FL pigtail -> antenna (case must be plastic there). LAN_OUT pad unused.\n"
       "Hand solder: 1.0 mm stamp holes; no exposed copper/untented vias under the module.\n"
       "GPIO35 = BOOT strap + RMII TXD1 (4.7k pull-up, PHY must not pull it low at reset).\n"
       "SW603 SLEEP/WAKE -> GPIO12 (LP GPIO): press = expander rails off + P4 deep sleep; press again = wake (ext1).",
       (25.4, 233.68))
s.write(KICAD / "mcu_module.kicad_sch", "ADSB_Test - MCU Module", "Requirements: boards/adsb-test/docs/requirements.md")
print("wrote mcu_module.kicad_sch")
missing = s.missing_footprints({"ADSB_Test": KICAD / "lib/ADSB_Test.pretty"})

# =================================================================== RTC (page 7)
r = Sheet(libs, "ADSB_Test", root_uuid, sheets["rtc.kicad_sch"], pwr_base=7000)
rtc = r.add("Timer_RTC:DS3231MZ", "U701", "DS3231M", (127.0, 101.6),
            footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", dnp=True,
            props={"I2C": "0x68", "MPN": "DS3231MZ+", "DNP": "Optional: fit for +/-5 ppm time keeping"})
r.connect(rtc, "2", "3V3")
r.connect(rtc, "6", "VBACKUP")
r.connect(rtc, "5", "GND")
r.connect(rtc, "7", "I2C_SDA")
r.connect(rtc, "8", "I2C_SCL")
r.connect(rtc, "3", "RTC_INT")
r.nc(rtc, "1")       # 32KHZ not used
r.nc(rtc, "4")       # ~RST: internal pull-up, not used
r.two_pin("Device:C", "C701", "100nF", (76.2, 76.2), "3V3", "GND", C0805, dnp=True)
r.two_pin("Device:C", "C702", "100nF", (88.9, 76.2), "VBACKUP", "GND", C0805, dnp=True)
r.two_pin("Device:R", "R701", "10k", (177.8, 76.2), "3V3", "RTC_INT", R0805)
tp(r, "TP701", "RTC_INT", (190.5, 101.6), local=False)
r.text("RTC: DS3231M (+/-5 ppm, MEMS resonator, no crystal) at I2C 0x68.\n"
       "VCC from 3V3 when on; VBAT from VBACKUP (always-on 3.0 V LDO, optional CR1220) when off.\n"
       "INT/SQW (open drain) -> P4 GPIO13 (LP GPIO: alarm wake-up from deep sleep).\n"
       "OPTIONAL (DNP): the OSPTEK module has RTC_VBAT on VBACKUP, so the P4 RTC keeps time. Fit U701/C701/C702\n"
       "for a +/-5 ppm clock (Q27). R701 stays fitted (RTC_INT pull-up).",
       (25.4, 165.1))
r.write(KICAD / "rtc.kicad_sch", "ADSB_Test - RTC", "Requirements: boards/adsb-test/docs/requirements.md")
print("wrote rtc.kicad_sch")
missing.update(r.missing_footprints({"ADSB_Test": KICAD / "lib/ADSB_Test.pretty"}))
if missing:
    print("  MISSING FOOTPRINTS:", missing)
