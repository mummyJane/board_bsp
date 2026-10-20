#!/usr/bin/env python3
"""Generate the ADSB_Test peripheral sheets:

  page 8  Ethernet      LAN8720A RMII PHY + HR911105A MagJack
  page 9  User USB-C    User USB-C receptacle (PD sink + UART), TVS, ESD, CP2102N -> P4 UART1
  page 10 Dev USB Hub   Dev USB-C -> USB2514B hub, 3V3_DEV regulator
  page 17 Dev UARTs     FT2232H (P4 + C5 consoles, esptool auto-reset), Ioff/open-drain buffers
  page 18 Dev m1421 Programmer  RP2040 + W25Q16 (stock ADSBee 1421 Programmer), m1421 buffers, GPIO header
  page 11 USB Host      USB-A on the P4 HS OTG port, TPS259621 eFuse
  page 12 GPS           MAX-M10S, active-antenna bias, SMA, optional RF can
  page 13 Display Touch EK79007 panel FPC + panel supplies copied from the reference board, GT911 touch FPC
  page 15 Storage Misc  microSD (+ power switch), TCA6408A expander
  page 16 Test Debug    Kingst LA5016 header, PWM pads, mounting holes

Run from the repo root:  python boards/adsb-test/hardware/gen/gen_periph.py
Pins: bsp/include/bsp/board_pins.h. Design notes: docs/architecture.md.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from kicad_sch_gen import SymbolLibs, Sheet, sheet_uuids  # noqa: E402

KICAD = ROOT / "boards/adsb-test/hardware/kicad"
R0805 = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
R1206 = "Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder"
C0805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
C1206 = "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
L0805 = "Inductor_SMD:L_0805_2012Metric_Pad1.05x1.20mm_HandSolder"
LED0805 = "LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder"
SOT23 = "Package_TO_SOT_SMD:SOT-23_Handsoldering"
SOT23_5 = "Package_TO_SOT_SMD:SOT-23-5_HandSoldering"
SOT23_6 = "Package_TO_SOT_SMD:SOT-23-6_Handsoldering"
SOD123 = "Diode_SMD:D_SOD-123"
TPFP = "TestPoint:TestPoint_Pad_D1.5mm"
XTAL5032 = "Crystal:Crystal_SMD_5032-2Pin_5.0x3.2mm_HandSoldering"
HS = "ADSB_Test:"

libs = SymbolLibs({"ADSB_Test": KICAD / "lib/ADSB_Test.kicad_sym"})
root_uuid, SHEETS = sheet_uuids(KICAD / "ADSB_Test.kicad_sch")
missing = {}


PAGES = {"ethernet.kicad_sch": 8, "usb_user.kicad_sch": 9, "usb_dev.kicad_sch": 10, "usb_host.kicad_sch": 11,
         "dev_uart.kicad_sch": 17, "dev_prog.kicad_sch": 18,
         "gps.kicad_sch": 12, "display_touch.kicad_sch": 13, "storage_misc.kicad_sch": 15, "test_debug.kicad_sch": 16}


def new(file):
    return Sheet(libs, "ADSB_Test", root_uuid, SHEETS[file], pwr_base=PAGES[file] * 1000)


def done(s, file, title, paper="A3"):
    s.write(KICAD / file, title, "Requirements: boards/adsb-test/docs/requirements.md", paper=paper)
    missing.update(s.missing_footprints({"ADSB_Test": KICAD / "lib/ADSB_Test.pretty"}))
    print("wrote", file)


def R(s, ref, val, at, n1, n2, fp=R0805, **kw):
    return s.two_pin("Device:R", ref, val, at, n1, n2, fp, **kw)


def C(s, ref, val, at, n1, n2="GND", fp=C0805, **kw):
    return s.two_pin("Device:C", ref, val, at, n1, n2, fp, **kw)


def TP(s, ref, net, at):
    t = s.add("Connector:TestPoint", ref, net, at, footprint=TPFP)
    s.connect(t, "1", net)


def gate(s, kind, ref, at, a, y, vcc, oe_gnd=True):
    """74LVC1G125 (buffer, OE# to GND) or 74LVC1G07 (open-drain buffer), SOT-23-5."""
    g = s.add(f"74xGxx:74LVC1G{kind}", ref, f"74LVC1G{kind}", at, footprint=SOT23_5)
    s.connect(g, "2", a)
    s.connect(g, "4", y)
    s.connect(g, "5", vcc)
    s.connect(g, "3", "GND")
    if kind == "125":
        s.connect(g, "1", "GND")
    else:
        s.nc(g, "1")
    return g


# =================================================================== Ethernet (page 8)
s = new("ethernet.kicad_sch")
s.locals |= {"ETH_AVDD", "ETH_1V2", "ETH_XI", "ETH_XO", "ETH_RBIAS", "ETH_LED1", "ETH_LED2", "ETH_RXER",
             "ETH_TX_P", "ETH_TX_N", "ETH_RX_P", "ETH_RX_N", "ETH_REFCLKO", "ETH_LED1_K", "ETH_LED2_K"}
u = s.add("Interface_Ethernet:LAN8720A", "U801", "LAN8720A", (165.1, 127.0),
          footprint=HS + "VQFN-24-1EP_4x4mm_P0.5mm_EP2.5x2.5mm_HandSolder",
          props={"MDIO address": "1 (RXER/PHYAD0 pulled up)", "REF_CLK": "nINTSEL=0: pin 14 outputs 50 MHz to the P4"})
s.connect(u, ["1", "19"], "ETH_AVDD")
s.connect(u, "9", "3V3_ETH")
s.connect(u, "6", "ETH_1V2")
s.connect(u, "25", "GND")
s.connect(u, "5", "ETH_XI")
s.connect(u, "4", "ETH_XO")
s.connect(u, "24", "ETH_RBIAS")
s.connect(u, "2", "ETH_LED2")
s.connect(u, "3", "ETH_LED1")
s.connect(u, "7", "ETH_RXD1")
s.connect(u, "8", "ETH_RXD0")
s.connect(u, "11", "ETH_CRS_DV")
s.connect(u, "10", "ETH_RXER")
s.connect(u, "12", "ETH_MDIO")
s.connect(u, "13", "ETH_MDC")
s.connect(u, "14", "ETH_REFCLKO")
s.connect(u, "15", "ETH_PHY_RST")
s.connect(u, "16", "ETH_TX_EN")
s.connect(u, "17", "ETH_TXD0")
s.connect(u, "18", "ETH_TXD1_BOOT")
s.connect(u, "21", "ETH_TX_P")
s.connect(u, "20", "ETH_TX_N")
s.connect(u, "23", "ETH_RX_P")
s.connect(u, "22", "ETH_RX_N")
fb = s.add("Device:FerriteBead_Small", "FB801", "600R@100MHz", (63.5, 76.2), footprint="Inductor_SMD:L_0805_2012Metric_Pad1.05x1.20mm_HandSolder")
s.connect(fb, "1", "3V3_ETH")
s.connect(fb, "2", "ETH_AVDD")
C(s, "C801", "10uF", (25.4, 48.26), "3V3_ETH", fp=C1206)
C(s, "C802", "100nF", (38.1, 48.26), "3V3_ETH")
C(s, "C803", "10uF", (88.9, 48.26), "ETH_AVDD", fp=C1206)
C(s, "C804", "100nF", (101.6, 48.26), "ETH_AVDD")
C(s, "C805", "100nF", (114.3, 48.26), "ETH_AVDD")
C(s, "C806", "1uF", (127.0, 48.26), "ETH_1V2")
C(s, "C807", "470pF", (139.7, 48.26), "ETH_1V2")
y = s.add("Device:Crystal", "Y801", "25MHz", (50.8, 101.6), footprint=XTAL5032)
s.connect(y, "1", "ETH_XI")
s.connect(y, "2", "ETH_XO")
C(s, "C808", "27pF", (38.1, 124.46), "ETH_XI")
C(s, "C809", "27pF", (63.5, 124.46), "ETH_XO")
R(s, "R801", "12.1k 1%", (76.2, 154.94), "ETH_RBIAS", "GND")
R(s, "R802", "10k", (38.1, 165.1), "ETH_LED1", "GND")          # REGOFF = 0: internal 1.2 V regulator on
R(s, "R803", "10k", (50.8, 165.1), "ETH_LED2", "GND")          # nINTSEL = 0: REFCLKO mode
R(s, "R804", "10k", (63.5, 190.5), "3V3_ETH", "ETH_RXER")      # PHYAD0 = 1
R(s, "R805", "1.5k", (76.2, 190.5), "3V3_ETH", "ETH_MDIO")
R(s, "R806", "10k", (88.9, 190.5), "3V3_ETH", "ETH_PHY_RST")
R(s, "R807", "33R", (241.3, 177.8), "ETH_REFCLKO", "ETH_REF_CLK")
for i, n in enumerate(("ETH_RXD0", "ETH_RXD1", "ETH_CRS_DV")):   # MODE[2:0] = 111: the P4 pins load the straps (DS00002165 3.7)
    R(s, f"R{814 + i}", "10k", (101.6 + i * 12.7, 190.5), "3V3_ETH", n)
for i, n in enumerate(("ETH_TX_P", "ETH_TX_N", "ETH_RX_P", "ETH_RX_N")):
    R(s, f"R{808 + i}", "49.9R 1%", (241.3 + i * 12.7, 63.5), "ETH_AVDD", n)
C(s, "C810", "22nF", (304.8, 63.5), "ETH_AVDD")              # transformer centre taps
j = s.add("Connector:RJ45_Hanrun_HR911105A_Horizontal", "J801", "HR911105A", (330.2, 127.0),
          props={"Check": "LED pins 9-12 polarity against the HR911105A drawing before layout"})
s.connect(j, "1", "ETH_TX_P")
s.connect(j, "2", "ETH_TX_N")
s.connect(j, "3", "ETH_RX_P")
s.connect(j, "6", "ETH_RX_N")
s.connect(j, ["4", "5"], "ETH_AVDD")
s.connect(j, ["8", "SH"], "GND")
s.nc(j, "7")
R(s, "R812", "270R", (279.4, 177.8), "ETH_LED1", "ETH_LED1_K")   # LED1 = link/activity (active high with strap 0)
R(s, "R813", "270R", (292.1, 177.8), "ETH_LED2", "ETH_LED2_K")
s.connect(j, "12", "ETH_LED1_K")
s.connect(j, ["11", "10"], "GND")
s.connect(j, "9", "ETH_LED2_K")
s.pwr_flag("ETH_AVDD", (76.2, 88.9))
s.pwr_flag("ETH_1V2", (152.4, 33.02))      # VDDCR: internal regulator output
TP(s, "TP801", "ETH_REF_CLK", (266.7, 203.2))
TP(s, "TP802", "ETH_1V2", (279.4, 203.2))
s.text("ETHERNET: LAN8720A 10/100 RMII PHY (replaces the IP101GRI: KiCad symbol, ESP-IDF lan87xx driver, cheap\n"
       "breakouts for Phase 1). 25 MHz crystal; REFCLKO (pin 14) feeds the P4 REF_CLK in (GPIO50) through 33R.\n"
       "Straps: REGOFF=0 (int. 1V2 on), nINTSEL=0 (REFCLKO, 10k pull-down), PHYAD0=1 (address 1), MODE=111 (10k\n"
       "pull-ups: the P4 pins load the straps). LEDs active high via 270R. DS00002165: REFCLKO-mode timing is outside\n"
       "the RMII spec - verify with the P4 in Phase 1 (fallback: 50 MHz oscillator into XTAL1, nINTSEL=1).\n"
       "3V3_ETH is switched (EXP_EN_ETH): firmware keeps the RMII/MDIO/reset pins low or hi-Z while it is off.\n"
       "TXD1 = GPIO35 = P4 BOOT strap: the PHY TXD1 input has no pull, the 4.7k pull-up on the MCU sheet wins.",
       (25.4, 233.68))
done(s, "ethernet.kicad_sch", "ADSB_Test - Ethernet")

# =================================================================== USB User (page 9)
s = new("usb_user.kicad_sch")
s.locals |= {"CP_VBUS", "CP_RST", "CP_TXLED", "CP_RXLED", "USER_D_P", "USER_D_N"}
# User USB-C receptacle (PD sink + user UART). VBUS/CC go to the STUSB4500 on the Power Input sheet.
j = s.add("Connector:USB_C_Receptacle_USB2.0_16P", "J901", "User USB-C (PD sink + UART)", (50.8, 165.1),
          footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal")
s.connect(j, ["A4", "A9", "B4", "B9"], "VBUS_USER_RAW")
s.connect(j, ["A1", "A12", "B1", "B12", "SH"], "GND")
s.connect(j, "A5", "USER_CC1")
s.connect(j, "B5", "USER_CC2")
s.connect(j, ["A6", "B6"], "USER_D_P")
s.connect(j, ["A7", "B7"], "USER_D_N")
s.nc(j, "A8")
s.nc(j, "B8")
d = s.add("Device:D_Zener", "D903", "SMAJ20A", (114.3, 190.5), footprint="Diode_SMD:D_SMA",
          props={"Check": "VBUS TVS for up to 15 V PD (20 V stand-off)"})
s.connect(d, "1", "VBUS_USER_RAW")
s.connect(d, "2", "GND")
C(s, "C903", "10uF 25V", (139.7, 190.5), "VBUS_USER_RAW")
e = s.add("Power_Protection:USBLC6-2SC6", "U902", "USBLC6-2SC6", (127.0, 152.4), footprint=SOT23_6)
s.connect(e, ["1", "6"], "USER_D_P")
s.connect(e, ["3", "4"], "USER_D_N")
s.connect(e, "5", "3V3_PERIPH")
s.connect(e, "2", "GND")
s.pwr_flag("VBUS_USER_RAW", (157.48, 177.8))          # arrives through the connector (passive)
u = s.add("Interface_USB:CP2102N-Axx-xQFN24", "U901", "CP2102N-A02-GQFN24", (165.1, 114.3),
          footprint=HS + "QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm_HandSolder")
s.connect(u, "3", "USER_D_P")
s.connect(u, "4", "USER_D_N")
s.connect(u, ["5", "6", "7"], "3V3_PERIPH")       # self-powered: VREGIN = VDD = 3.3 V
s.connect(u, "8", "CP_VBUS")
s.connect(u, "9", "CP_RST")
s.connect(u, ["2", "25"], "GND")
s.connect(u, "20", "P4_USER_TX")                  # RXD <- P4 TX
s.connect(u, "21", "P4_USER_RX")                  # TXD -> P4 RX
s.connect(u, "14", "CP_TXLED")
s.connect(u, "13", "CP_RXLED")
for p in ("1", "10", "11", "12", "15", "16", "17", "18", "19", "22", "23", "24"):
    s.nc(u, p)
R(s, "R901", "22.1k", (76.2, 76.2), "VBUS_USER", "CP_VBUS")
R(s, "R902", "47.5k", (76.2, 101.6), "CP_VBUS", "GND")
R(s, "R903", "10k", (88.9, 152.4), "3V3_PERIPH", "CP_RST")
C(s, "C901", "1uF", (50.8, 50.8), "3V3_PERIPH")
C(s, "C902", "100nF", (63.5, 50.8), "3V3_PERIPH")
for i, (net, col) in enumerate((("CP_TXLED", "TX green"), ("CP_RXLED", "RX yellow"))):
    x = 254.0 + i * 25.4
    s.locals.add(f"{net}_A")
    R(s, f"R{904 + i}", "1k", (x, 76.2), "3V3_PERIPH", f"{net}_A")
    d = s.add("Device:LED", f"D{901 + i}", col, (x, 109.22), footprint=LED0805)
    s.connect(d, "2", f"{net}_A")
    s.connect(d, "1", net)
s.text("USER USB-C: receptacle J901 (16-pin USB 2.0), VBUS TVS D903, data-line ESD U902. VBUS_USER_RAW and CC1/CC2\n"
       "go to the STUSB4500 PD sink on the Power Input sheet. D+/D- (USB_90R pair) -> CP2102N (self-powered from\n"
       "3V3_PERIPH), VBUS sense from VBUS_USER through 22.1k/47.5k. TXD/RXD to P4 UART1 (GPIO22/21).\n"
       "GPIO.0/GPIO.1 = TX/RX activity LEDs (default CP2102N configuration). The UART is only live when the board is on.",
       (177.8, 233.68))
done(s, "usb_user.kicad_sch", "ADSB_Test - User USB-C")

# =================================================================== USB Host (page 11)
s = new("usb_host.kicad_sch")
s.locals |= {"USBA_DVDT", "USBA_ILM", "USBA_OVC"}
u = s.add("Power_Management:TPS2596xx", "U1101", "TPS259621DDA", (152.4, 101.6),
          props={"Variant": "TPS25962x: OVCSEL 400k = 5.7 V output clamp", "Limit": "RILM 604R ~ 1.5 A (1.0 A at 909R, 2.0 A at 453R)"})
s.connect(u, "4", "5V_SDR")
s.connect(u, "5", "VBUS_HOST")
s.connect(u, ["1", "9"], "GND")
s.connect(u, "3", "EXP_USBA_EN")
s.connect(u, "6", "USBA_FAULT")
s.connect(u, "7", "USBA_ILM")
s.connect(u, "2", "USBA_DVDT")
s.connect(u, "8", "USBA_OVC")
R(s, "R1101", "604R 1%", (127.0, 152.4), "USBA_ILM", "GND")
C(s, "C1101", "10nF", (152.4, 152.4), "USBA_DVDT")
R(s, "R1102", "402k 1%", (177.8, 152.4), "USBA_OVC", "GND")
R(s, "R1103", "10k", (203.2, 152.4), "3V3", "USBA_FAULT")
R(s, "R1104", "100k", (101.6, 152.4), "EXP_USBA_EN", "GND")     # off until the expander enables it
C(s, "C1102", "1uF", (88.9, 76.2), "5V_SDR")
cp = s.add("Device:C_Polarized", "C1103", "150uF 10V", (228.6, 76.2), footprint="Capacitor_SMD:CP_Elec_6.3x5.8")
s.connect(cp, "1", "VBUS_HOST")
s.connect(cp, "2", "GND")
C(s, "C1104", "100nF", (241.3, 76.2), "VBUS_HOST")
e = s.add("Power_Protection:USBLC6-2SC6", "U1102", "USBLC6-2SC6", (279.4, 152.4), footprint=SOT23_6)
s.connect(e, ["1", "6"], "USB_HS_D_P")
s.connect(e, ["3", "4"], "USB_HS_D_N")
s.connect(e, "5", "VBUS_HOST")
s.connect(e, "2", "GND")
j = s.add("Connector:USB_A", "J1101", "USB-A (SDR hub)", (330.2, 101.6), footprint="Connector_USB:USB_A_Molex_67643_Horizontal")
s.connect(j, "1", "VBUS_HOST")
s.connect(j, "2", "USB_HS_D_N")
s.connect(j, "3", "USB_HS_D_P")
s.connect(j, ["4", "SH"], "GND")
TP(s, "TP1101", "VBUS_HOST", (254.0, 203.2))
TP(s, "TP1102", "USBA_FAULT", (266.7, 203.2))
s.text("USB HOST: P4 HS OTG (module pads 44/45) -> USBLC6 -> USB-A, 90R differential, short.\n"
       "VBUS: 5V_SDR (shunt RS402, PM1 CH4) -> TPS259621 eFuse (~1.5 A, 5.7 V clamp, dV/dt 10 nF) -> 150 uF.\n"
       "EN from the expander (EXP_USBA_EN, 100k pull-down: off at reset), FAULT (open drain) -> P4 GPIO27.\n"
       "PowerPAD: thermal vias let it be soldered from the back. External powered hub for 2+ SDRs.",
       (25.4, 233.68))
done(s, "usb_host.kicad_sch", "ADSB_Test - USB Host")

# =================================================================== GPS (page 12)
s = new("gps.kicad_sch")
s.locals |= {"GPS_RF", "GPS_VCC_RF", "GPS_BIAS", "GPS_EXTINT", "GPS_SAFEBOOT", "GPS_PPS_LED"}
u = s.add("RF_GPS:MAX-M10S", "U1201", "MAX-M10S", (152.4, 114.3))
s.connect(u, ["1", "10", "12"], "GND")
s.connect(u, "2", "GPS_TX")
s.connect(u, "3", "P4_GPS_TX")
s.connect(u, "4", "GPS_PPS")
s.connect(u, "5", "GPS_EXTINT")
s.connect(u, "6", "VBACKUP")
s.connect(u, ["7", "8"], "3V3_GPS")
s.connect(u, "9", "GPS_RESET_N")
s.connect(u, "11", "GPS_RF")
s.connect(u, "14", "GPS_VCC_RF")
s.connect(u, "18", "GPS_SAFEBOOT")
for p in ("13", "15", "16", "17"):     # LNA_EN, VIO_SEL open = 3.3 V I/O, I2C unused
    s.nc(u, p)
C(s, "C1201", "10uF", (76.2, 63.5), "3V3_GPS", fp=C1206)
C(s, "C1202", "100nF", (88.9, 63.5), "3V3_GPS")
C(s, "C1203", "100nF", (101.6, 63.5), "VBACKUP")
# active antenna bias: VCC_RF -> 10R -> 47 nH -> RF line (RF_IN is DC-blocked inside the module)
R(s, "R1201", "10R", (228.6, 63.5), "GPS_VCC_RF", "GPS_BIAS")
C(s, "C1204", "10nF", (241.3, 88.9), "GPS_BIAS")
L = s.add("Device:L", "L1201", "47nH", (254.0, 63.5), footprint=L0805, props={"Note": "High-Q RF inductor, SRF > 1.6 GHz"})
s.connect(L, "1", "GPS_BIAS")
s.connect(L, "2", "GPS_RF")
e = s.add("Device:D_TVS", "D1201", "ESD7351XV2T1G", (279.4, 101.6), footprint="Diode_SMD:D_SOD-523")
s.connect(e, "1", "GPS_RF")
s.connect(e, "2", "GND")
a = s.add("Connector:Conn_Coaxial", "J1201", "SMA GNSS (active antenna)", (304.8, 76.2),
          footprint="Connector_Coaxial:SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount")
s.connect(a, "1", "GPS_RF")
s.connect(a, "2", "GND")
R(s, "R1202", "1k", (228.6, 152.4), "GPS_PPS", "GPS_PPS_LED")
d = s.add("Device:LED", "D1202", "PPS green", (254.0, 152.4), footprint=LED0805)
s.connect(d, "2", "GPS_PPS_LED")
s.connect(d, "1", "GND")
for i, net in enumerate(("GPS_EXTINT", "GPS_SAFEBOOT", "GPS_RESET_N", "GPS_PPS")):
    TP(s, f"TP{1201 + i}", net, (63.5 + i * 25.4, 203.2))
sh = s.add("Mechanical:Housing_Pad", "SH1201", "RF can frame (DNP)", (330.2, 152.4), dnp=True,
           footprint="RF_Shielding:Laird_Technologies_BMI-S-202-F_16.50x16.50mm",
           props={"MPN": "Laird BMI-S-202-F frame + BMI-S-202-C lid", "DNP": "Fit if RF noise"})
s.connect(sh, "1", "GND")
s.text("GNSS: u-blox MAX-M10S, UART2 to the P4 (38400 baud default), PPS -> P4 GPIO4 + LED + LA CH2.\n"
       "V_BCKP from VBACKUP (always on) for hot starts; RESET_N from the expander (bit 6, released = input).\n"
       "Active antenna fed from VCC_RF through 10R + 47 nH; RF_IN is DC-blocked inside. 50R CPW to the edge SMA.\n"
       "SH1201: optional RF can over the module + bias parts (fit after soldering/testing; RF trace leaves on an inner layer).",
       (25.4, 233.68))
done(s, "gps.kicad_sch", "ADSB_Test - GPS")

# =================================================================== Display Touch (page 13)
s = new("display_touch.kicad_sch")
s.locals |= {"AVDD", "AVDD_SW", "AVDD_FB", "AVDD_SHDN", "VGH", "VGH_RAW", "VGH_PUMP", "VGL", "VGL_RAW",
             "VGL_PUMP", "VCOM", "VCC_1V8", "LED_P", "LED_N", "BL_SW", "BL_FB", "BL_EN", "BL_OV", "BL_CTRL",
             "BL_RC", "LCD_RESET", "TP_RESET", "LCD_STRAP5", "LCD_STRAP6", "LCD_STRAP26"}
# AVDD 9.6 V boost (AP3012)
b = s.add("Regulator_Switching:AP3012", "U1301", "AP3012KTR-E1", (63.5, 50.8), footprint=SOT23_5)
s.connect(b, "5", "5V_LCD")
s.connect(b, "4", "AVDD_SHDN")
s.connect(b, "2", "GND")
s.connect(b, "1", "AVDD_SW")
s.connect(b, "3", "AVDD_FB")
R(s, "R1301", "10k", (38.1, 76.2), "5V_LCD", "AVDD_SHDN")
L = s.add("Device:L", "L1301", "10uH", (88.9, 25.4), footprint="Inductor_SMD:L_Bourns-SRN4018", props={"Check": "Isat >= 0.5 A"})
s.connect(L, "1", "5V_LCD")
s.connect(L, "2", "AVDD_SW")
d = s.add("Device:D_Schottky", "D1301", "1N5819HW", (114.3, 25.4), footprint=SOD123)
s.connect(d, "2", "AVDD_SW")
s.connect(d, "1", "AVDD")
R(s, "R1302", "22k 1%", (127.0, 63.5), "AVDD", "AVDD_FB")
R(s, "R1303", "3.3k 1%", (127.0, 88.9), "AVDD_FB", "GND")
C(s, "C1301", "10uF", (25.4, 50.8), "5V_LCD", fp=C1206)
C(s, "C1302", "1uF", (38.1, 50.8), "5V_LCD")
C(s, "C1303", "1uF 25V", (139.7, 50.8), "AVDD")
C(s, "C1304", "100nF 25V", (152.4, 50.8), "AVDD")
C(s, "C1305", "10uF 25V", (165.1, 50.8), "AVDD", fp=C1206)
# VGL -6..-7.5 V charge pump
C(s, "C1306", "100nF 50V", (190.5, 25.4), "AVDD_SW", "VGL_PUMP")
dp = s.add("Diode:BAT54S", "D1302", "BAT54S", (228.6, 25.4), footprint=SOT23)
s.connect(dp, "3", "VGL_PUMP")
s.connect(dp, "1", "VGL_RAW")
s.connect(dp, "2", "GND")
C(s, "C1307", "1uF 25V", (254.0, 25.4), "VGL_RAW")
R(s, "R1304", "220R 1%", (266.7, 50.8), "VGL_RAW", "VGL")
z = s.add("Diode:BZT52Bxx", "D1303", "BZT52C7V5S", (292.1, 38.1), footprint="Diode_SMD:D_SOD-123F")
s.connect(z, "1", "GND")
s.connect(z, "2", "VGL")
R(s, "R1305", "51k 1%", (304.8, 50.8), "VGL", "GND")
C(s, "C1308", "100nF 25V", (317.5, 50.8), "VGL")
C(s, "C1309", "10uF 25V", (330.2, 50.8), "VGL", fp=C1206)
# VGH +18 V charge pump
C(s, "C1310", "100nF 50V", (190.5, 88.9), "AVDD_SW", "VGH_PUMP")
dp = s.add("Diode:BAT54S", "D1304", "BAT54S", (228.6, 88.9), footprint=SOT23)
s.connect(dp, "3", "VGH_PUMP")
s.connect(dp, "1", "AVDD")
s.connect(dp, "2", "VGH_RAW")
C(s, "C1311", "1uF 50V", (254.0, 88.9), "VGH_RAW")
R(s, "R1306", "220R 1%", (266.7, 114.3), "VGH_RAW", "VGH")
z = s.add("Diode:BZT52Bxx", "D1305", "BZT52C18S", (292.1, 101.6), footprint="Diode_SMD:D_SOD-123F")
s.connect(z, "1", "VGH")
s.connect(z, "2", "GND")
R(s, "R1307", "51k 1%", (304.8, 114.3), "VGH", "GND")
C(s, "C1312", "100nF 50V", (317.5, 114.3), "VGH")
C(s, "C1313", "10uF 25V", (330.2, 114.3), "VGH", fp=C1206)
# VCOM = AVDD / 3
R(s, "R1308", "2k 1%", (190.5, 139.7), "AVDD", "VCOM")
R(s, "R1309", "1k 1%", (190.5, 165.1), "VCOM", "GND")
C(s, "C1314", "10uF", (203.2, 165.1), "VCOM", fp=C1206)
C(s, "C1315", "100nF", (215.9, 165.1), "VCOM")
# 1V8 LDO (reference: RT9193-18; AP2112K-1.8 is pin-compatible except BP, which is NC here)
ld = s.add("Regulator_Linear:AP2112K-1.8", "U1302", "AP2112K-1.8", (63.5, 127.0), footprint=SOT23_5)
s.connect(ld, ["1", "3"], "5V_LCD")
s.connect(ld, "2", "GND")
s.connect(ld, "5", "VCC_1V8")
C(s, "C1316", "1uF", (38.1, 139.7), "5V_LCD")
C(s, "C1317", "1uF", (101.6, 139.7), "VCC_1V8")
# Backlight LED boost (AP3032)
bl = s.add("ADSB_Test:AP3032", "U1303", "AP3032KTR-G1", (63.5, 190.5))
s.connect(bl, "6", "5V_LCD")
s.connect(bl, "4", "BL_EN")
s.connect(bl, "2", "GND")
s.connect(bl, "1", "BL_SW")
s.connect(bl, "5", "BL_OV")
s.connect(bl, "3", "BL_FB")
C(s, "C1318", "10uF", (25.4, 177.8), "5V_LCD", fp=C1206)
R(s, "R1310", "100k", (25.4, 203.2), "5V_LCD", "BL_EN")
C(s, "C1319", "1uF 50V", (38.1, 215.9), "BL_EN", fp=C1206)
L = s.add("Device:L", "L1302", "10uH 0.55A", (101.6, 165.1), footprint="Inductor_SMD:L_Bourns-SRN4018")
s.connect(L, "1", "5V_LCD")
s.connect(L, "2", "BL_SW")
d = s.add("Device:D_Schottky", "D1306", "1N5819HW", (127.0, 165.1), footprint=SOD123)
s.connect(d, "2", "BL_SW")
s.connect(d, "1", "LED_P")
R(s, "R1311", "0R", (139.7, 190.5), "LED_P", "BL_OV")
C(s, "C1320", "1uF 50V", (152.4, 190.5), "LED_P", fp=C1206)
R(s, "R1312", "5.1k 1%", (114.3, 215.9), "BL_FB", "LED_N")
R(s, "R1313", "1.3R 1%", (139.7, 228.6), "LED_N", "GND", fp=R1206)   # ~150 mA LED string
R(s, "R1314", "68k", (101.6, 228.6), "BL_RC", "BL_FB")
C(s, "C1321", "100nF", (88.9, 241.3), "BL_RC")
R(s, "R1315", "10k", (76.2, 228.6), "BL_CTRL", "BL_RC")
R(s, "R1316", "0R", (50.8, 241.3), "LCD_BL_PWM", "BL_CTRL")
# Panel FPC (30-pin 0.5 mm, same pin-out as the reference board)
j = s.add("Connector_Generic_MountingPin:Conn_01x30_MountingPin", "J1301", "LCD FPC 30p 0.5mm", (368.3, 127.0),
          footprint="Connector_FFC-FPC:Hirose_FH12-30S-0.5SH_1x30-1MP_P0.50mm_Horizontal",
          props={"Check": "Bottom-contact flip-lock, 2.0 mm high, as the reference board P2; confirm the contact side for the FPC wrap"})
fpc = {"1": "LED_P", "2": "LED_P", "3": "VGH", "4": "VGL", "5": "LCD_STRAP5", "6": "LCD_STRAP6", "7": "LED_N", "8": "LED_N",
       "9": "AVDD", "17": "DSI_CLK_P", "18": "DSI_CLK_N", "20": "DSI_D1_P", "21": "DSI_D1_N", "23": "DSI_D0_P",
       "24": "DSI_D0_N", "26": "LCD_STRAP26", "27": "LCD_RESET", "28": "VCC_1V8", "29": "VCC_1V8", "30": "VCOM"}
for p, n in fpc.items():
    s.connect(j, p, n)
s.connect(j, ["10", "13", "16", "19", "22", "25", "MP"], "GND")
for p in ("11", "12", "14", "15"):
    s.nc(j, p)
R(s, "R1317", "10k", (279.4, 165.1), "VCC_1V8", "LCD_STRAP5")
R(s, "R1318", "10k", (292.1, 165.1), "VCC_1V8", "LCD_STRAP26")
# Pins 5/6 are UPDN/SHLR (scan direction) on some EK79007 panels, pin 6 is GND on the Waveshare panel.
# Default = Waveshare: pin 5 high, pin 6 low. Swap the fitted/DNP parts to flip a mirrored panel.
R(s, "R1322", "0R", (304.8, 165.1), "LCD_STRAP5", "GND", dnp=True, props={"Option": "UPDN low (flip vertical)"})
R(s, "R1323", "0R", (317.5, 165.1), "LCD_STRAP6", "GND", props={"Option": "Waveshare panel: pin 6 = GND / SHLR low"})
R(s, "R1324", "10k", (330.2, 165.1), "VCC_1V8", "LCD_STRAP6", dnp=True, props={"Option": "SHLR high (fit instead of R1323)"})
R(s, "R1319", "0R", (304.8, 203.2), "LCD_RST", "LCD_RESET")
R(s, "R1320", "10k", (317.5, 203.2), "LCD_RESET", "GND")
# Touch FPC (6-pin 0.5 mm)
t = s.add("Connector_Generic_MountingPin:Conn_01x06_MountingPin", "J1302", "Touch FPC 6p 0.5mm", (368.3, 203.2),
          footprint="Connector_FFC-FPC:Hirose_FH12-6S-0.5SH_1x06-1MP_P0.50mm_Horizontal")
s.connect(t, "1", "TP_RESET")
s.connect(t, "2", "3V3")
s.connect(t, ["3", "MP"], "GND")
s.connect(t, "4", "TOUCH_INT")
s.connect(t, "5", "I2C_SDA")
s.connect(t, "6", "I2C_SCL")
R(s, "R1321", "0R", (304.8, 241.3), "TOUCH_RST", "TP_RESET")
C(s, "C1322", "100nF", (330.2, 241.3), "3V3")
for i, net in enumerate(("AVDD", "VGH", "VGL", "VCOM", "VCC_1V8", "LED_P")):
    TP(s, f"TP{1301 + i}", net, (190.5 + i * 12.7, 203.2))
s.text("DISPLAY: 7in 1024x600 EK79007 bare COG panel, 2-lane MIPI-DSI from the module; same FPC pin-out and panel\n"
       "supplies as the Waveshare reference board (all from 5V_LCD, switched by EXP_EN_LCD, PM2 CH1):\n"
       "AVDD 9.6 V (AP3012 boost), VGH +18 V / VGL -7.5 V (charge pumps off the AVDD switch node, zener clamps),\n"
       "VCOM = AVDD/3, VCC_1V8 (AP2112K-1.8 instead of RT9193-18), backlight AP3032 (1.3R sense ~150 mA).\n"
       "Backlight dimming: LCD_BL_PWM (GPIO32) -> 10k/100nF -> 68k into FB: higher duty = dimmer (as reference).\n"
       "DSI pairs 100R differential, length-matched. Touch: GT911 on the shared I2C, RST GPIO23, INT GPIO26.",
       (25.4, 266.7))
done(s, "display_touch.kicad_sch", "ADSB_Test - Display Touch")

# =================================================================== Storage Misc (page 15)
s = new("storage_misc.kicad_sch")
s.locals |= {"SD_VDD", "EXP_RESET", "SD_DET"}
j = s.add("Connector:Micro_SD_Card_Det2", "J1501", "microSD (push-pull, detect)", (101.6, 101.6),
          footprint="Connector_Card:microSD_HC_Molex_104031-0811",
          props={"Detect": "Normally-open switch (Molex 104031 spec): closes with a card -> SD_DET low"})
for p, n in {"1": "SD_D2", "2": "SD_D3", "3": "SD_CMD", "4": "SD_VDD", "5": "SD_CLK", "7": "SD_D0", "8": "SD_D1",
             "9": "SD_DET"}.items():
    s.connect(j, p, n)
s.connect(j, ["6", "10", "SH"], "GND")
for i, n in enumerate(("SD_CMD", "SD_D0", "SD_D1", "SD_D2", "SD_D3")):
    R(s, f"R{1501 + i}", "10k", (25.4 + i * 12.7, 38.1), "SD_VIO", n)
q = s.add("Transistor_FET:AO3401A", "Q1501", "AO3401A", (50.8, 152.4), footprint=SOT23,
          props={"Function": "microSD power switch: SD_PWR_EN (GPIO45) low = card powered"})
s.connect(q, "2", "3V3_SD")
s.connect(q, "3", "SD_VDD")
s.connect(q, "1", "SD_PWR_EN")
R(s, "R1506", "10k", (25.4, 152.4), "3V3_SD", "SD_PWR_EN")
C(s, "C1501", "10uF", (76.2, 177.8), "SD_VDD", fp=C1206)
C(s, "C1502", "100nF", (88.9, 177.8), "SD_VDD")
R(s, "R1507", "10k", (139.7, 152.4), "3V3_PERIPH", "SD_DET")
TP(s, "TP1501", "SD_VDD", (101.6, 203.2))
s.pwr_flag("SD_VDD", (63.5, 177.8))
# TCA6408A I2C expander (0x20)
x = s.add("Interface_Expansion:TCA6408APW", "U1501", "TCA6408APW", (254.0, 101.6), props={"I2C": "0x20 (ADDR = GND)"})
s.connect(x, ["1", "16"], "3V3_PERIPH")
s.connect(x, "2", "GND")
s.connect(x, "8", "GND")
s.connect(x, "3", "EXP_RESET")
s.connect(x, "13", "EXP_INT")
s.connect(x, "14", "I2C_SCL")
s.connect(x, "15", "I2C_SDA")
bits = {"4": "EXP_EN_LCD", "5": "EXP_EN_ETH", "6": "EXP_EN_GPS", "7": "EXP_EN_M1421", "9": "EXP_USBA_EN",
        "10": "SD_DET", "11": "GPS_RESET_N", "12": "M1421_NRST"}
for p, n in bits.items():
    s.connect(x, p, n)
R(s, "R1508", "10k", (203.2, 50.8), "3V3_PERIPH", "EXP_RESET")
R(s, "R1509", "10k", (215.9, 50.8), "3V3_PERIPH", "EXP_INT")
C(s, "C1503", "100nF", (228.6, 50.8), "3V3_PERIPH")
for i, n in enumerate(("EXP_EN_LCD", "EXP_EN_ETH", "EXP_EN_GPS", "EXP_EN_M1421")):   # off until enabled
    R(s, f"R{1510 + i}", "100k", (304.8 + i * 12.7, 152.4), n, "GND")
s.text("microSD: P4 SDMMC slot 0, 4-bit (GPIO39-44), I/O from the module's ESP_LDO_VO4 (SD_VIO), 10k pull-ups.\n"
       "Card power: 3V3_SD (shunt RS405, PM2 CH3) -> AO3401A, GPIO45 low = on (as reference). Detect -> expander P5.\n"
       "TCA6408A (0x20): P0 EN_LCD, P1 EN_ETH, P2 EN_GPS, P3 EN_M1421, P4 USBA_EN (100k pull-downs: all off at reset),\n"
       "P5 SD_DET (input), P6 GPS_RESET_N, P7 M1421_NRST (both: output low = reset, input = released). INT -> GPIO53.",
       (25.4, 233.68))
done(s, "storage_misc.kicad_sch", "ADSB_Test - Storage Misc")

# =================================================================== Test Debug (page 16)
s = new("test_debug.kicad_sch")
la = ["I2C_SCL", "I2C_SDA", "GPS_PPS", "GPS_TX", "M1421_SUTX", "M1421_SURX", "M1421_SYNC", "M1421_SD26",
      "P4_CON_TX", "C5_CON_TX", "P4_USER_TX", "M1421_SD27", "PM_ALERT", "CHG_PD_INT", "DBG_A", "DBG_B"]
s.locals |= {f"LA_CH{i}" for i in range(16)} | {"LA_PWM1", "LA_PWM2"}
h = s.add("Connector_Generic:Conn_02x20_Odd_Even", "J1601", "Kingst LA5016 (2x20 keyed)", (254.0, 127.0),
          footprint="Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical",
          props={"Check": "Pin 1 against the LA5016 cable triangle; key-side row = odd pins"})
for ch in range(16):
    pin = 1 + 2 * ch if ch < 8 else 19 + 2 * (ch - 8)
    s.connect(h, str(pin), f"LA_CH{ch}")
    R(s, f"R{1601 + ch}", "100R", (63.5 + (ch % 8) * 15.24, 63.5 + (ch // 8) * 50.8), la[ch], f"LA_CH{ch}")
s.connect(h, ["17", "35", "18", "36"], "GND")
s.connect(h, "37", "LA_PWM1")
s.connect(h, "39", "LA_PWM2")
for p in range(2, 41, 2):
    if p not in (18, 36):
        s.nc(h, str(p))
TP(s, "TP1601", "LA_PWM1", (342.9, 63.5))
TP(s, "TP1602", "LA_PWM2", (355.6, 63.5))
R(s, "R1617", "0R", (342.9, 101.6), "LA_PWM1", "GPS_PPS", dnp=True,
  props={"DNP": "Fit to drive GPS_PPS from the analyser PWM1 (simulate PPS without a fix)"})
for i in range(4):
    TP(s, f"TP{1603 + i}", "GND", (330.2 + i * 12.7, 190.5))
for i in range(4):
    mh = s.add("Mechanical:MountingHole_Pad", f"H{1601 + i}", "M2.5", (63.5 + i * 15.24, 203.2),
               footprint="MountingHole:MountingHole_2.7mm_M2.5_Pad_Via")
    s.connect(mh, "1", "GND")
s.text("LOGIC ANALYSER: Kingst LA5016 40-way cable into J1601. Key-side row (odd pins): 1-15 CH0-7, 17 GND,\n"
       "19-33 CH8-15, 35 GND, 37 PWM1, 39 PWM2 (LA outputs). Even row reserved for the LA5032 (18/36 GND).\n"
       "CH: 0 SCL, 1 SDA, 2 GPS PPS, 3 GPS TX, 4 m1421 SUTX, 5 m1421 SURX, 6 SYNC, 7 SD26 | 8 P4 console TX,\n"
       "9 C5 console TX, 10 user UART TX, 11 SD27, 12 PM ALERT, 13 CHG/PD INT, 14 DBG_A, 15 DBG_B. 100R series each.\n"
       "H1601-H1604: M2.5 panel holes at 156 x 89 mm (Waveshare drawing). Rail test points are on each power sheet.",
       (25.4, 233.68))
done(s, "test_debug.kicad_sch", "ADSB_Test - Test Debug")

# =================================================================== Dev USB Hub (page 10)
# The Dev domain is split over three A3 pages: 10 hub, 17 UARTs, 18 m1421 programmer. 3V3_DEV, VBUS_DEV and the
# hub's downstream USB pairs (FT_D_*, RP_HUB_D_*) cross between them as global labels.
s = new("usb_dev.kicad_sch")
s.locals |= {"DEV_D_P", "DEV_D_N", "DEV_CC1", "DEV_CC2", "HUB_XI", "HUB_XO", "HUB_RBIAS", "HUB_CRFILT",
             "HUB_PLLFILT", "HUB_RESET", "HUB_VBUS_DET", "HUB_CFG0", "HUB_CFG1", "HUB_NONREM0", "HUB_NONREM1",
             "HUB_DN2_N", "HUB_DN2_P"}
j = s.add("Connector:USB_C_Receptacle_USB2.0_16P", "J1001", "Dev USB-C", (38.1, 88.9),
          footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal")
s.connect(j, ["A4", "A9", "B4", "B9"], "VBUS_DEV")
s.connect(j, ["A6", "B6"], "DEV_D_P")
s.connect(j, ["A7", "B7"], "DEV_D_N")
s.connect(j, "A5", "DEV_CC1")
s.connect(j, "B5", "DEV_CC2")
s.connect(j, ["A1", "A12", "B1", "B12", "SH"], "GND")
s.nc(j, "A8")
s.nc(j, "B8")
R(s, "R1001", "5.1k", (88.9, 139.7), "DEV_CC1", "GND")
R(s, "R1002", "5.1k", (101.6, 139.7), "DEV_CC2", "GND")
e = s.add("Power_Protection:USBLC6-2SC6", "U1001", "USBLC6-2SC6", (38.1, 165.1), footprint=SOT23_6)
s.connect(e, ["1", "6"], "DEV_D_P")
s.connect(e, ["3", "4"], "DEV_D_N")
s.connect(e, "5", "VBUS_DEV")
s.connect(e, "2", "GND")
ld = s.add("Regulator_Linear:AP2112K-3.3", "U1002", "AP2112K-3.3", (38.1, 215.9), footprint=SOT23_5)
s.connect(ld, ["1", "3"], "VBUS_DEV")
s.connect(ld, "2", "GND")
s.connect(ld, "5", "3V3_DEV")
C(s, "C1001", "1uF", (25.4, 241.3), "VBUS_DEV")
C(s, "C1002", "10uF", (63.5, 241.3), "3V3_DEV", fp=C1206)
s.pwr_flag("VBUS_DEV", (88.9, 190.5))     # arrives through the connector (passive)
TP(s, "TP1001", "VBUS_DEV", (88.9, 228.6))
TP(s, "TP1002", "3V3_DEV", (101.6, 228.6))
hub = s.add("Interface_USB:USB2514B_Bi", "U1003", "USB2514B", (190.5, 114.3),
            footprint=HS + "QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm_HandSolder",
            props={"Ports": "DN1 P4 USB-Serial/JTAG, DN2 disabled, DN3 FT2232H, DN4 RP2040"})
s.connect(hub, "31", "DEV_D_P")
s.connect(hub, "30", "DEV_D_N")
s.connect(hub, "2", "P4_USJ_D_P")
s.connect(hub, "1", "P4_USJ_D_N")
s.connect(hub, "4", "HUB_DN2_P")
s.connect(hub, "3", "HUB_DN2_N")
s.connect(hub, "7", "FT_D_P")
s.connect(hub, "6", "FT_D_N")
s.connect(hub, "9", "RP_HUB_D_P")
s.connect(hub, "8", "RP_HUB_D_N")
s.connect(hub, ["5", "10", "29", "36", "15", "23"], "3V3_DEV")
s.connect(hub, ["11", "37"], "GND")
s.connect(hub, "14", "HUB_CRFILT")
s.connect(hub, "34", "HUB_PLLFILT")
s.connect(hub, "35", "HUB_RBIAS")
s.connect(hub, "33", "HUB_XI")
s.connect(hub, "32", "HUB_XO")
s.connect(hub, "26", "HUB_RESET")
s.connect(hub, "27", "HUB_VBUS_DET")
s.connect(hub, "24", "HUB_CFG0")
s.connect(hub, "25", "HUB_CFG1")
s.connect(hub, "28", "HUB_NONREM0")
s.connect(hub, "22", "HUB_NONREM1")
for p in ("12", "13", "16", "17", "18", "19", "20", "21"):
    s.nc(hub, p)
R(s, "R1003", "10k", (279.4, 38.1), "3V3_DEV", "HUB_DN2_P")     # both D+/D- high = port 2 disabled
R(s, "R1004", "10k", (292.1, 38.1), "3V3_DEV", "HUB_DN2_N")
for i, n in enumerate(("HUB_CFG0", "HUB_CFG1", "HUB_NONREM0", "HUB_NONREM1")):   # strap: default config, bus powered
    R(s, f"R{1005 + i}", "10k", (317.5 + i * 12.7, 38.1), n, "GND")
R(s, "R1009", "12k 1%", (279.4, 101.6), "HUB_RBIAS", "GND")
C(s, "C1003", "1uF", (292.1, 101.6), "HUB_CRFILT")
C(s, "C1004", "1uF", (304.8, 101.6), "HUB_PLLFILT")
R(s, "R1010", "10k", (330.2, 88.9), "3V3_DEV", "HUB_RESET")
C(s, "C1005", "100nF", (330.2, 127.0), "HUB_RESET")
R(s, "R1011", "100k", (355.6, 88.9), "VBUS_DEV", "HUB_VBUS_DET")
R(s, "R1012", "100k", (355.6, 127.0), "HUB_VBUS_DET", "GND")
y = s.add("Device:Crystal", "Y1001", "24MHz", (292.1, 165.1), footprint=XTAL5032)
s.connect(y, "1", "HUB_XI")
s.connect(y, "2", "HUB_XO")
C(s, "C1006", "27pF", (279.4, 190.5), "HUB_XI")
C(s, "C1007", "27pF", (304.8, 190.5), "HUB_XO")
R(s, "R1013", "1M", (330.2, 165.1), "HUB_XI", "HUB_XO")
for i in range(4):
    C(s, f"C{1008 + i}", "100nF", (152.4 + i * 12.7, 203.2), "3V3_DEV")
C(s, "C1012", "4.7uF", (203.2, 203.2), "3V3_DEV")
s.text("DEV PORT, page 1 of 3: Dev USB-C -> USBLC6 -> USB2514B hub (strap defaults, bus powered). Own 3V3_DEV\n"
       "domain from Dev VBUS (AP2112K), so the Dev port works with the target unpowered.\n"
       "Downstream: DN1 P4 USB-Serial/JTAG | DN2 disabled (the C5 USB pins are its SDIO bus) |\n"
       "DN3 FT2232H -> page 'Dev UARTs' | DN4 RP2040 -> page 'Dev m1421 Programmer'.",
       (25.4, 266.7))
done(s, "usb_dev.kicad_sch", "ADSB_Test - Dev USB Hub")

# =================================================================== Dev UARTs (page 17)
s = new("dev_uart.kicad_sch")
s.locals |= {"FT_1V8", "FT_XI", "FT_XO", "FT_REF", "FT_RESET", "FT_EECS", "FT_EECLK", "FT_EEDATA", "FT_EEDO",
             "FT_A_TXD", "FT_A_RXD", "FT_A_RTS", "FT_A_DTR", "FT_B_TXD", "FT_B_RXD", "FT_B_RTS", "FT_B_DTR",
             "QA1_B", "QA2_B", "QB1_B", "QB2_B"}
ft = s.add("Interface_USB:FT2232HL", "U1701", "FT2232HL", (114.3, 114.3),
           props={"Package": "LQFP-64 0.5 mm (leaded, iron-solderable)"})
s.connect(ft, "8", "FT_D_P")
s.connect(ft, "7", "FT_D_N")
s.connect(ft, "50", "3V3_DEV")                     # VREGIN
s.connect(ft, "49", "FT_1V8")                      # VREGOUT -> VCORE
s.connect(ft, ["12", "37", "64"], "FT_1V8")
s.connect(ft, ["4", "9", "20", "31", "42", "56"], "3V3_DEV")   # VPHY, VPLL, VCCIO
s.connect(ft, ["1", "5", "10", "11", "15", "25", "35", "47", "51", "13"], "GND")   # GND, AGND, TEST
s.connect(ft, "14", "FT_RESET")
s.connect(ft, "2", "FT_XI")
s.connect(ft, "3", "FT_XO")
s.connect(ft, "6", "FT_REF")
s.connect(ft, "63", "FT_EECS")
s.connect(ft, "62", "FT_EECLK")
s.connect(ft, "61", "FT_EEDATA")
for p, n in {"16": "FT_A_TXD", "17": "FT_A_RXD", "18": "FT_A_RTS", "21": "FT_A_DTR",
             "38": "FT_B_TXD", "39": "FT_B_RXD", "40": "FT_B_RTS", "43": "FT_B_DTR"}.items():
    s.connect(ft, p, n)
for p in ("19", "22", "23", "24", "26", "27", "28", "29", "30", "32", "33", "34", "36", "41", "44", "45", "46",
          "48", "52", "53", "54", "55", "57", "58", "59", "60"):
    s.nc(ft, p)
y = s.add("Device:Crystal", "Y1701", "12MHz", (38.1, 38.1), footprint=XTAL5032)
s.connect(y, "1", "FT_XI")
s.connect(y, "2", "FT_XO")
C(s, "C1706", "27pF", (25.4, 63.5), "FT_XI")
C(s, "C1707", "27pF", (50.8, 63.5), "FT_XO")
R(s, "R1701", "12k 1%", (25.4, 203.2), "FT_REF", "GND")
R(s, "R1702", "10k", (38.1, 203.2), "3V3_DEV", "FT_RESET")
for i in range(4):
    C(s, f"C{1701 + i}", "100nF", (63.5 + i * 12.7, 203.2), "FT_1V8" if i < 2 else "3V3_DEV")
C(s, "C1705", "4.7uF", (114.3, 203.2), "FT_1V8")
ee = s.add("Memory_EEPROM:93LCxxB", "U1702", "93LC56B", (190.5, 203.2), footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
           props={"Note": "FT2232H config EEPROM (optional: blank/absent = FTDI defaults)"})
s.connect(ee, "1", "FT_EECS")
s.connect(ee, "2", "FT_EECLK")
s.connect(ee, "3", "FT_EEDATA")
s.connect(ee, "4", "FT_EEDO")
s.connect(ee, "5", "GND")
s.connect(ee, "8", "3V3_DEV")
s.nc(ee, "6")
s.nc(ee, "7")
R(s, "R1703", "2.2k", (228.6, 215.9), "FT_EEDO", "FT_EEDATA")
for i, n in enumerate(("FT_EECS", "FT_EECLK", "FT_EEDATA")):
    R(s, f"R{1704 + i}", "10k", (139.7 + i * 12.7, 241.3), "3V3_DEV", n)
# target-side buffers (Dev-powered, Ioff: no back-powering either way)
gate(s, "07", "U1703", (254.0, 38.1), "FT_A_TXD", "P4_CON_RX", "3V3_DEV")
gate(s, "125", "U1704", (254.0, 76.2), "P4_CON_TX", "FT_A_RXD", "3V3_DEV")
gate(s, "07", "U1705", (254.0, 114.3), "FT_B_TXD", "C5_CON_RX", "3V3_DEV")
gate(s, "125", "U1706", (254.0, 152.4), "C5_CON_TX", "FT_B_RXD", "3V3_DEV")
for i in range(4):     # one 100 nF per buffer
    C(s, f"C{1708 + i}", "100nF", (292.1, 38.1 + i * 38.1), "3V3_DEV")
R(s, "R1707", "10k", (241.3, 177.8), "3V3", "P4_CON_RX")      # target-side pull-ups for the open-drain buffers
R(s, "R1708", "10k", (254.0, 177.8), "3V3", "C5_CON_RX")
# esptool auto-reset (open collector into the target EN / BOOT nets)
for k, (ch, en, boot, b1, b2, x0) in enumerate((("A", "P4_EN", "ETH_TXD1_BOOT", "QA1_B", "QA2_B", 342.9),
                                                ("B", "C5_EN", "C5_BOOT", "QB1_B", "QB2_B", 393.7))):
    q1 = s.add("Transistor_BJT:MMBT3904", f"Q{1701 + 2 * k}", "MMBT3904", (x0, 38.1), footprint=SOT23)
    s.connect(q1, "1", b1)
    s.connect(q1, "2", f"FT_{ch}_RTS")
    s.connect(q1, "3", en)
    R(s, f"R{1709 + 2 * k}", "10k", (x0 - 12.7, 63.5), f"FT_{ch}_DTR", b1)
    q2 = s.add("Transistor_BJT:MMBT3904", f"Q{1702 + 2 * k}", "MMBT3904", (x0, 101.6), footprint=SOT23)
    s.connect(q2, "1", b2)
    s.connect(q2, "2", f"FT_{ch}_DTR")
    s.connect(q2, "3", boot)
    R(s, f"R{1710 + 2 * k}", "10k", (x0 - 12.7, 127.0), f"FT_{ch}_RTS", b2)
for i, n in enumerate(("FT_A_DTR", "FT_A_RTS", "FT_B_DTR", "FT_B_RTS")):
    TP(s, f"TP{1701 + i}", n, (330.2 + i * 15.24, 165.1))
s.text("DEV PORT, page 2 of 3: FT2232HL on hub port DN3. Channel A = P4 UART0 (console), channel B = C5 UART0.\n"
       "DTR/RTS -> MMBT3904 pairs = esptool auto-reset on P4_EN/BOOT (GPIO35) and C5_EN/C5_BOOT. C5_EN reaches the C5\n"
       "CHIP_PU through R606 (330R) onto module pad 82 (P4 GPIO54 net): P4 firmware drives GPIO54 open-drain.\n"
       "No back-powering: Dev->target TX through open-drain 74LVC1G07 (target pull-ups R1707/R1708),\n"
       "target->Dev TX through 74LVC1G125 (Ioff inputs). 93LC56B: optional FTDI config EEPROM.",
       (25.4, 266.7))
done(s, "dev_uart.kicad_sch", "ADSB_Test - Dev UARTs")

# =================================================================== Dev m1421 Programmer (page 18)
s = new("dev_prog.kicad_sch")
s.locals |= {"RP_D_N", "RP_D_P", "RP_1V1", "RP_XI", "RP_XO", "RP_XO_R", "RP_SWCLK", "RP_SWDIO", "RP_RUN", "RP_QSS",
             "RP_QSCK", "RP_QD0", "RP_QD1", "RP_QD2", "RP_QD3", "RP_BOOTSEL", "RP_LED", "RP_LED_D", "LED_VDD",
             "RP_NRST", "RP_SYNC", "RP_TX", "RP_RX", "RP_NRST_L", "RP_SYNC_L"}
# RP2040 running the stock ADSBee 1421 Programmer (pins from its board.hh: 26 ~SRST, 27 SYNC, 28 TX, 29 RX)
rp = s.add("MCU_RaspberryPi:RP2040", "U1801", "RP2040", (114.3, 114.3),
           footprint=HS + "QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm_HandSolder",
           props={"Firmware": "Stock ADSBee 1421 Programmer (PantsForBirds/adsbee firmware/adsbee_1421/programmer)"})
s.connect(rp, ["1", "10", "22", "33", "42", "49", "43", "44", "48"], "3V3_DEV")
s.connect(rp, "45", "RP_1V1")
s.connect(rp, ["23", "50"], "RP_1V1")
s.connect(rp, ["57", "19"], "GND")
s.connect(rp, "20", "RP_XI")
s.connect(rp, "21", "RP_XO")
s.connect(rp, "24", "RP_SWCLK")
s.connect(rp, "25", "RP_SWDIO")
s.connect(rp, "26", "RP_RUN")
s.connect(rp, "46", "RP_D_N")
s.connect(rp, "47", "RP_D_P")
for p, n in {"56": "RP_QSS", "52": "RP_QSCK", "53": "RP_QD0", "55": "RP_QD1", "54": "RP_QD2", "51": "RP_QD3",
             "27": "RP_LED", "38": "RP_NRST", "39": "RP_SYNC", "40": "RP_TX", "41": "RP_RX"}.items():
    s.connect(rp, p, n)
# Spare RP2040 GPIOs (not used by the stock Programmer) to a 2 x 14 header J1801 (pins not fitted: the holes are
# test points). GPIO0/1 = RP2040 I2C0 SDA/SCL: DNP 0R links onto the board I2C bus so the P4 can talk to it if
# custom RP2040 firmware is used. Fit them only when both domains are powered (the bus pull-ups are on 3V3).
RP_SPARE = [(g, str(2 + g)) for g in range(0, 8)] + [(g, str(3 + g)) for g in range(8, 16)] + \
           [(g, str(11 + g)) for g in range(17, 22)] + [(g, str(12 + g)) for g in range(22, 26)]
for g, pin in RP_SPARE:
    s.locals.add(f"RP_GPIO{g}")
    s.connect(rp, pin, f"RP_GPIO{g}", kind="label")
hdr = s.add("Connector_Generic:Conn_02x14_Odd_Even", "J1801", "RP2040 GPIO (pins DNP)", (355.6, 203.2), dnp=True,
            footprint="Connector_PinHeader_2.54mm:PinHeader_2x14_P2.54mm_Vertical",
            props={"Note": "Holes are test points; fit a 2x14 header only if needed"})
s.connect(hdr, "1", "3V3_DEV")
for i, (g, _) in enumerate(RP_SPARE):           # GPIOs on pins 2-26
    s.connect(hdr, str(2 + i), f"RP_GPIO{g}", kind="label")
s.connect(hdr, ["27", "28"], "GND")             # grounds on the bottom row
R(s, "R1812", "0R", (292.1, 165.1), "RP_GPIO0", "I2C_SDA", dnp=True,
  props={"Option": "RP2040 I2C0 SDA on the board I2C bus (custom RP2040 firmware)"})
R(s, "R1813", "0R", (304.8, 165.1), "RP_GPIO1", "I2C_SCL", dnp=True,
  props={"Option": "RP2040 I2C0 SCL on the board I2C bus (custom RP2040 firmware)"})
R(s, "R1801", "27R", (190.5, 165.1), "RP_HUB_D_P", "RP_D_P")
R(s, "R1802", "27R", (203.2, 165.1), "RP_HUB_D_N", "RP_D_N")
y = s.add("Device:Crystal", "Y1801", "12MHz", (38.1, 38.1), footprint=XTAL5032)
s.connect(y, "1", "RP_XI")
s.connect(y, "2", "RP_XO_R")
R(s, "R1803", "1k", (63.5, 38.1), "RP_XO_R", "RP_XO")
C(s, "C1801", "27pF", (25.4, 63.5), "RP_XI")
C(s, "C1802", "27pF", (50.8, 63.5), "RP_XO_R")
C(s, "C1803", "1uF", (25.4, 215.9), "3V3_DEV")
C(s, "C1804", "1uF", (38.1, 215.9), "RP_1V1")
for i in range(3):
    C(s, f"C{1805 + i}", "100nF", (50.8 + i * 12.7, 215.9), "3V3_DEV")
C(s, "C1808", "100nF", (88.9, 215.9), "RP_1V1")
R(s, "R1804", "10k", (101.6, 215.9), "3V3_DEV", "RP_RUN")
fl = s.add("Memory_Flash:W25Q16JVSS", "U1802", "W25Q16JVSS", (215.9, 63.5))
s.connect(fl, "1", "RP_QSS")
s.connect(fl, "2", "RP_QD1")
s.connect(fl, "3", "RP_QD2")
s.connect(fl, "4", "GND")
s.connect(fl, "5", "RP_QD0")
s.connect(fl, "6", "RP_QSCK")
s.connect(fl, "7", "RP_QD3")
s.connect(fl, "8", "3V3_DEV")
C(s, "C1809", "100nF", (254.0, 38.1), "3V3_DEV")
R(s, "R1805", "10k", (177.8, 25.4), "3V3_DEV", "RP_QSS")
R(s, "R1806", "1k", (177.8, 101.6), "RP_QSS", "RP_BOOTSEL")
bt = s.add("Switch:SW_Push", "SW1801", "BOOTSEL (programmer)", (190.5, 127.0), footprint="Button_Switch_THT:SW_PUSH_6mm")
s.connect(bt, "1", "RP_BOOTSEL")
s.connect(bt, "2", "GND")
# status LED (WS2812 on GPIO16 as the RP2040-Zero), from VBUS_DEV minus a diode so 3.3 V data is valid
dl = s.add("Device:D", "D1801", "1N4148W", (215.9, 203.2), footprint=SOD123)
s.connect(dl, "2", "VBUS_DEV")
s.connect(dl, "1", "LED_VDD")
w = s.add("LED:WS2812B", "D1802", "WS2812B", (254.0, 215.9))
s.connect(w, "1", "LED_VDD")
s.connect(w, "3", "GND")
s.connect(w, "4", "RP_LED_D")
s.nc(w, "2")
R(s, "R1807", "330R", (215.9, 241.3), "RP_LED", "RP_LED_D")
C(s, "C1810", "100nF", (279.4, 203.2), "LED_VDD")
s.pwr_flag("LED_VDD", (190.5, 190.5))
# m1421 path: 0R escape-hatch links, then Dev-powered buffers (pins of the target logic are Ioff LVC inputs)
R(s, "R1808", "0R", (266.7, 88.9), "RP_NRST", "RP_NRST_L", props={"Note": "Remove = console-only (no reset)"})
R(s, "R1809", "0R", (279.4, 88.9), "RP_SYNC", "RP_SYNC_L", props={"Note": "Remove = console-only (no bootloader entry)"})
R(s, "R1810", "10k", (292.1, 88.9), "3V3_DEV", "RP_NRST_L")    # RP2040 releases ~SRST as hi-Z
R(s, "R1811", "100k", (304.8, 88.9), "RP_SYNC_L", "GND")
gate(s, "125", "U1803", (342.9, 25.4), "RP_NRST_L", "DEV_M1421_NRST", "3V3_DEV")
gate(s, "125", "U1804", (342.9, 63.5), "RP_SYNC_L", "DEV_M1421_SYNC", "3V3_DEV")
gate(s, "125", "U1805", (342.9, 101.6), "RP_TX", "DEV_M1421_TX", "3V3_DEV")
gate(s, "125", "U1806", (342.9, 139.7), "M1421_SUTX", "RP_RX", "3V3_DEV")
for i in range(4):     # one 100 nF per buffer
    C(s, f"C{1811 + i}", "100nF", (393.7, 25.4 + i * 38.1), "3V3_DEV")
for i, n in enumerate(("RP_SWCLK", "RP_SWDIO", "RP_RUN")):
    TP(s, f"TP{1801 + i}", n, (139.7 + i * 15.24, 228.6))
# SWD header in the Raspberry Pi Pico order (SWCLK, GND, SWDIO): Raspberry Pi Debug Probe / Picoprobe plug straight on
sw = s.add("Connector_Generic:Conn_01x03", "J1802", "RP2040 SWD", (165.1, 248.92),
           footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
           props={"Pinout": "1 SWCLK, 2 GND, 3 SWDIO (Pico debug order); RUN on TP1803"})
s.connect(sw, "1", "RP_SWCLK", kind="label")
s.connect(sw, "3", "RP_SWDIO", kind="label")
_end, _ = s._stub(sw, "2")         # middle GND: run the wire out past the label text so the symbol clears them
s.wire(_end, (_end[0] - 20.32, _end[1]))
s.power("GND", (_end[0] - 20.32, _end[1]))
s.text("DEV PORT, page 3 of 3: RP2040 + W25Q16 on hub port DN4, running the STOCK ADSBee 1421 Programmer\n"
       "(RP2040-Zero pin-out: GPIO26 ~SRST, 27 SYNC, 28 TX, 29 RX, 16 WS2812 status). The m1421 lines go through\n"
       "Dev-powered 74LVC1G125s into the target's LVC logic (no back-powering). Remove R1808/R1809 for a console-only\n"
       "port. Spare GPIOs on J1801 (holes = test points); R1812/R1813 (DNP) put I2C0 on the board I2C bus.\n"
       "J1802 SWD (SWCLK, GND, SWDIO as on the Pico) for the Raspberry Pi Debug Probe; RUN on TP1803.",
       (25.4, 266.7))
done(s, "dev_prog.kicad_sch", "ADSB_Test - Dev m1421 Programmer")

if missing:
    print("  MISSING FOOTPRINTS:", missing)
