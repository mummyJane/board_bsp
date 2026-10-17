# ADSB_Test — Architecture

Status: **Draft, Rev A**. Part numbers marked _(proposed)_ haven't been
reviewed yet. They were chosen for availability, ESP-IDF support or a vendor
evaluation board, so each circuit can be tried before ADSB_Test exists.

ADS-B reception (1090 MHz Mode S **and** 978 MHz UAT) is done by the **ADSBee
m1421** module, not by SDRs on the P4. The USB-A port is for **one** extra SDR
(AIS or similar), a second if needed, and up to 4 as a nice-to-have, all on an
external hub.

## Block diagram

```mermaid
flowchart LR
  subgraph USER["User USB-C"]
    PD[PD sink<br/>STUSB4500]
    UUART[USB-UART<br/>CP2102N]
  end
  subgraph DEV["Dev USB-C (Dev-powered)"]
    HUB[USB2.0 hub<br/>USB2514B]
    FT[Dual UART<br/>FT2232H]
    DP[RP2040<br/>ADSBee Programmer fw]
  end
  PD -->|5-20 V| CHG[Charger + power path<br/>BQ25798]
  BAT[(2S Li-ion<br/>2x 18650)] <--> CHG
  CHG -->|VSYS| RAILS[5V / 3V3 bucks<br/>+ load switches]
  RAILS -.->|shunts| PM[Power monitors<br/>3x PAC1954]

  P4[ESP32-P4<br/>OSPTEK P4C5 module]
  C5[ESP32-C5<br/>inside the module]
  P4 <-->|SDIO esp_hosted| C5
  P4 <-->|RMII| PHY[LAN8720A + RJ45]
  P4 <-->|USB HS OTG| USBA[USB-A host<br/>ext. hub, 1-2 SDR]
  P4 <-->|MIPI-DSI + I2C| LCD[7in LCD + touch]
  P4 <-->|UART + PPS| GPS[GNSS<br/>MAX-M10S]
  P4 <-->|UART3 + SYNC + RESET| M14[ADSBee m1421<br/>1090 + 978 MHz]
  P4 <-->|SDMMC| SD[microSD]
  P4 <-->|I2C| PM
  P4 <-->|I2C| CHG
  P4 <-->|I2C| PD
  P4 <-->|I2C| EXP[GPIO expander<br/>TCA6408A]
  UUART <-->|UART1| P4
  HUB -->|USB-JTAG| P4
  HUB --> FT
  HUB --> DP
  FT -->|ch A UART0| P4
  FT -->|ch B UART0| C5
  DP -->|UART + SYNC + RESET| M14
  M14 --> RF[SCN-2-11 combiner<br/>-> SMA 1090/978]
```

## Reuse from the reference board

Facts below are from the Waveshare schematic
(`boards/esp32-p4-wifi6-touch-lcd-7b/hardware/vendor/`).

| Block | Reference board | ADSB_Test |
|-------|-----------------|-----------|
| SoC | ESP32-P4NRW32 (32 MB in-package PSRAM) | **OSPTEK ESP32-P4C5 Core module** (P4 rev v3 + 32 MB PSRAM, Q26) |
| Flash | GD25Q256EYIGR (32 MB) | 16 MB inside the module |
| Core supplies | MP1605 / MP1658 bucks, RT9193 LDOs | **Inside the module** (5 V in) |
| Wireless co-processor | ESP32-C6-MINI-1 over SDIO | **ESP32-C5 inside the module** (dual-band Wi-Fi 6, IPEX antenna). Same SDIO wiring and esp_hosted host side |
| USB-UART | CH343P | Moves to the Dev port (FT2232H) and User port (CP2102N) |
| Battery | ETA6098 1S charger, RTC battery | Replaced by 2S BQ25798 power path. RTC battery kept if used |
| Display + touch | 7" EK79007 bare COG panel, 2-lane MIPI-DSI, GT911 touch. Panel supplies generated on the board | Same FPC connectors, pin-out and **panel supply circuits** (AVDD 9.6 V boost, VGH/VGL charge pumps, VCOM, 1V8 LDO, AP3032 backlight driver), same stack-up. Touch INT newly wired to the P4 |
| microSD | Yes | Same |
| Audio (ES8311, ES7210, NS4150B) | Yes | **Dropped** |
| CAN (TJA1051), RS485 | Yes | Dropped (not in requirements) |
| CSI camera | Yes | Dropped |
| Ethernet | **None** | New. Test on an RMII PHY breakout |

### ESP32-C5 instead of C6

- **The P4 firmware barely changes.** It talks to the co-processor through
  `esp_wifi_remote` / esp_hosted over the same SDIO bus. Only the slave
  firmware is rebuilt for the C5 target, and the host's slave-target setting
  changes. Check that the esp_hosted release in use supports C5 over SDIO
  (open question Q2a).
- **New on the C5:** 5 GHz Wi-Fi 6. Its pin numbers differ from the C6
  (USB-Serial/JTAG, UART0, strapping pins), so the C5 sheet uses the C5
  datasheet, not a copy of the C6 sheet.
- **Testing before hardware:** the reference board has a C6, so the Wi-Fi
  remote API is tested there. C5-specific behaviour (5 GHz) is tested with an
  ESP32-C5 DevKit running esp_hosted, wired to the reference board. The DevKit
  uses the same N16R8 module.
- **Memory and OTA:** 16 MB flash allows a factory image plus two OTA slots for
  the C5 slave firmware. OTA is a nice-to-have: the P4 can push new C5 firmware
  over SDIO (esp_hosted host-driven slave OTA) or the C5 can be reflashed over
  the Dev port. 8 MB PSRAM gives headroom for larger Wi-Fi buffers.
- **Antenna (since Q26):** IPEX on the OSPTEK module → 100 mm U.FL-U.FL jumper →
  J601 (U.FL on the board) → a few mm of 50 Ω CPW → **J602 RP-SMA** (Molex
  0732513152, bulkhead nut) on the **top long edge**, 96 mm from the digital end,
  well away from the 1090/978 and GNSS SMAs on the RF edge. RP-SMA so the Wi-Fi
  antenna can't be swapped with the other two. Needs a dual-band 2.4/5 GHz RP-SMA
  antenna and a hole in the case's top side. Wi-Fi is a backup and the unit
  normally runs offline.
- _This section was written for the C5-WROOM; the module's C5 has its own
  flash (C5 GPIO numbers below are unchanged; see the module section)._

### ESP32-C5 pins and straps (from the C5 datasheet)

| C5 GPIO | Use | Note |
|---------|-----|------|
| 9 / 10 | SDIO CLK / CMD | to P4 GPIO18 / 19 |
| 8 / 7 / 14 / 13 | SDIO D0 / D1 / D2 / D3 | to P4 GPIO14–17 |
| 11 / 12 | UART0 TX / RX | to Dev FT2232H ch B |
| 28 | BOOT strap (low = download, with 27 high) | FT2232H auto-reset + P4 optional |
| 26 / 27 | Boot-mode straps (27 pulled up internally) | **10 kΩ pull-up on GPIO26**: it floats by default, and 26 = 27 = 28 = 0 selects SDIO download |
| 25, MTDI | SDIO sampling/drive edge straps | defaults unless esp_hosted needs otherwise (check) |
| 7 | JTAG-source strap (= SDIO D1) | ignored with unburned eFuses |

**GPIO13/14 are both SDIO D3/D2 and the C5's USB D−/D+.** With 4-bit SDIO to
the P4, the C5's USB-Serial/JTAG port **can't be used**. So the C5 is flashed and
debugged over **UART0** (Dev FT2232H ch B, DTR/RTS auto-reset on CHIP_PU and
GPIO28), and Dev hub port 2 is spare. Field updates still go over SDIO
(esp_hosted host-driven OTA).

### ESP32-P4 strapping pins (from the P4 datasheet)

- **GPIO35–38:** boot mode. GPIO36 also controls ROM printing.
- **GPIO34:** JTAG source. With unburned eFuses (default) GPIO34 is
  **ignored** and JTAG comes from the USB-Serial/JTAG controller, so the
  P4's GPIO2–5 (an alternative JTAG pad set) are free for GPS/PM. **Never burn
  `EFUSE_JTAG_SEL_ENABLE`** on this board.

## P4 + C5 module (OSPTEK ESP32-P4C5 Core) _(adopted 2026-10-12, Q26)_

Hand-soldering the bare ESP32-P4 (QFN-104, 0.35 mm pitch) is the hardest job on
Rev 1. A module with the P4 **and** the Wi-Fi chip removes that job, the flash,
the P4 core supplies and the separate C5-WROOM. The Wireless-Tag WT01P4C5-S1 was
chosen first, then replaced the same day by the OSPTEK module (similar price,
about GBP 13, [AliExpress](https://www.aliexpress.com/item/1005012626312933.html)).

| | **OSPTEK ESP32-P4C5 Core** (chosen) | Wireless-Tag WT01P4C5-S1 (first choice) |
|---|---|---|
| Chips | ESP32-P4 **rev v3.x** + ESP32-C5HF4 (2.4 + 5 GHz Wi-Fi 6) | ESP32-P4 + ESP32-C5 |
| Memory | 16 MB flash, 32 MB PSRAM | 16 MB flash, 16/32 MB PSRAM |
| Package | **25 × 25 mm, 88 stamp holes, 1.0 mm pitch** (pads 0.7 × 1.3 mm) | 35 × 35 mm, 92 pads, 1.4 mm |
| Supply | **3.3 V** (3.0–3.6 V, about 1 A) | 5 V |
| P4 VBAT (RTC) | **RTC_VBAT pad 84** (must not float) | none |
| P4 ↔ C5 inside | SDIO GPIO14–19, C5 CHIP_PU = **GPIO54**, C5 GPIO2 = **GPIO6**: **same as the reference board's C6** | SDIO 14–19, reset GPIO13, wake GPIO12 |
| C5 pads | U0RXD/TXD, IO28 (BOOT), IO27/26 straps, IO23–25, IO4–6. **No C5_EN pad, no full C5 JTAG** | EN, UART, BOOT, JTAG |
| Docs | Pin table, connection diagram, dimension drawing, Altium SchLib/PcbLib, STEP (CC BY 4.0) | Datasheet only, no land pattern |

Why OSPTEK: the firmware wiring is the reference board's (no pin moves), the P4
RTC has its VBAT back, the module is smaller (the MCU floorplan zone drops from
82 % to 51 % full), it runs from the existing 3V3 rail, and there is a published
footprint. Costs: 1.0 mm pitch (iron-solderable, but finer) and no C5_EN pad.

**Programming the C5 without a C5_EN pad:** the C5 CHIP_PU is the P4 GPIO54 net,
which is also brought out on pad 82. The Dev port's FT2232H channel B pulls it low
through **R606 (330 Ω)**, and drives C5 BOOT (C5 IO28, pad 6), so esptool's
auto-reset still works. The P4 firmware must drive GPIO54 **open-drain** (or leave
it as an input) when the Dev port is used; R606 limits the current if it doesn't.
Field updates of the C5 still go over SDIO from the P4 (esp_hosted OTA).

`board_pins.h` is back to the reference-board values: C5 reset GPIO54, C5 IO
GPIO6, PM_ALERT GPIO5; the optional DS3231M INT is on GPIO13; SLEEP/WAKE button GPIO12; spares 20, 36.
The module uses **P4 rev v3.x**, so the test app builds for v3 by default;
`sdkconfig.rev1` is the overlay for the rev v1.3 Waveshare boards.

Schematic: sheet 6 **MCU Module** (U601, 3V3_MCU decoupling, RTC_VBAT from
VBACKUP, CHIP_PU 10k + 1 µF (the module has no reset RC), 32.768 kHz crystal, I2C
pull-ups, BOOT/RESET/SLEEP-WAKE buttons, R606 C5 reset path, C5 IO26 pull-up, test pads on
the spare pins) and sheet 7 **RTC** (DS3231M, now **DNP**: fit for ±5 ppm time).
Generated by `hardware/gen/gen_mcu.py`; symbol/footprint by
`hardware/gen/gen_osptek_p4c5.py` (cross-check the footprint against OSPTEK's PcbLib).

## ADSBee m1421 integration

Sources:
- The m1421 module docs (`docs/adsbee-1421/m1421.md`) and firmware README in
  [PantsForBirds/adsbee](https://github.com/PantsForBirds/adsbee).
- The [ADSBee 1421 carrier reference design](https://pantsforbirds.com/the-worlds-smallest-dual-band-ads-b-receiver-module/).
- The official symbol and footprint from
  [PantsForBirds/kicad-libs](https://github.com/PantsForBirds/kicad-libs) (MIT), in [`hardware/kicad/lib`](../hardware/kicad/lib/).

Key facts:
- **Chips:** CC1314R10 + LR2021.
- **Supply:** VCC 1.8–3.3 V (3.3 V here), about 19 mA (< 60 mW). Logic levels are 0–VCC.
- **Console:** UART at 1,000,000 baud by default (9600–3,000,000). The module
  sends `UU` at boot and after every rate change, so a host can autobaud.
- **Output protocols:** Raw, CSBee, MAVLink 1/2, GDL90, Mode S Beast,
  Aircraft JSON. Configured with AT commands and saved to flash.
- **No MLAT:** the module has no per-packet timestamps or RSSI in its
  high-throughput mode.

### SYNC (pad 28): a host-driven input, never an output

| When | SYNC high | SYNC low |
|------|-----------|----------|
| As the CC1314 leaves reset (ROM reads it once) | ROM serial **bootloader** on the console UART (the "backdoor", active high) | Application boots |
| While the application runs | **Sleep request**: the CC1314 enters STANDBY (keeps its aircraft table) and releases the LR2021 bus within ~25 µs | Wake. The CC1314 takes the LR2021 back |

- SYNC has a weak pull-down: an external one on module Rev D and later, an
  internal one before that. A floating SYNC keeps the module awake.
- **Any reset with SYNC high enters the bootloader**, including a watchdog
  reset. Before long host-driven sleeps, send `AT+WATCHDOG=0`.
- The official KiCad symbol types SYNC as an "output". **Our copy corrects it
  to "input".**

There's no "start of message" output. The closest things are the activity LED
outputs **SD26 (pad 15, 1090 MHz)** and **SD27 (pad 16, 978 MHz UAT)**. Both go
to LEDs and to the LA header (CH7, CH11), and they're good enough as rough
message-activity markers.

### Pad connections

| m1421 pad(s) | Signal | ADSB_Test connection |
|--------------|--------|----------------------|
| 1, 4, 19, 22 | VCC | `3V3_M1421`: switched branch, PM3 ch2 |
| 6, 18, 23, 25, 27, 34, 36, MP | GND | GND. **Filled and capped** thermal vias in both MP pads and under the GND pads next to the RF pins |
| 20 / 21 | SURX / SUTX (console) | P4 UART3 at 1 Mbaud (≥ 921600 recommended). TX also goes to the Dev probe. RX = P4 TX AND Dev TX (74LVC1G97 wired as AND; both idle high) |
| 28 | SYNC | `SYNC = P4_SYNC OR DEV_SYNC` (74LVC1G32, target-powered). DEV_SYNC is pulled low, so an unpowered Dev domain can't assert it. 100 kΩ pull-down on SYNC. LA CH6 |
| 17 | ~SRST | Open-drain wired-AND: TCA6408A bit 7, Dev probe (74LVC1G07, Ioff), 10-pin JTAG header pin 10 |
| 8–11 | JMSC / JCKC / JTDO / JTDI | 10-pin 1.27 mm Cortex debug header, as on the carrier: **Segger J-Link, target CC1314R10, JTAG 4 MHz** (the documented flow) |
| 15 / 16 | SD26 / SD27 | 1090 / UAT activity LEDs (red / green, as carrier) + LA CH7 / CH11 |
| 12–14 | SD23–25 | Test pads |
| 24 / 26 | SRF (978) / LRFL (1090) | SCN-2-11+ combiner (100 Ω across ports) → ESD7351 → SMA. Copy the carrier's RF layout. Keep the footprint's top-copper keep-outs |
| 2, 3, 5, 7, 29–33 | LR2021 DIO / reset / SPI / BUSY | Test pads only (normal use: not connected). Leaves room for an optional LR2021 hand-off later |
| 35 | LRFH (LR2021 2.4 GHz) | Not connected (test pad). Possible LoRa/mesh use later, but the module has no transmitter certification |

### Fit options for Rev A: module or Dev Kit

The m1421 is new, so Rev A supports **both**:

| Option | How | When |
|--------|-----|------|
| **(b) ADSBee 1421 Dev Kit** _(default for first boards)_ | Leave U1401 unfitted. Plug the Dev Kit's comms connector into **J1402** (1×6 2.54 mm) with the JST-GH-to-DuPont harness in the kit. Pinout matches the Dev Kit: 1 VIN, 2 UART RX (into module), 3 UART TX, 4 SYNC, 5 RESET, 6 GND. VIN = `3V3_M1421` (switched and measured; the Dev Kit's AP2112K then gives ≈ 3.0 V, inside the module's 1.8–3.3 V range). The Dev Kit uses its own U.FL antenna; the board's SMA path is unused | Proving the module, firmware and host code with known-good RF |
| **(a) Solder U1401** | Fit the module on the board; J1402 left empty. RF through the board's combiner to the edge SMA | Once the module is proven, and to test the board's own RF layout |

Both options share the same nets (UART, SYNC, RESET, power), so the RX combiner,
SYNC OR gate, reset buffer and Dev-port RP2040 work the same either way. **Never
fit U1401 and connect a Dev Kit at the same time.**

The RX combiner is a **74LVC1G97** wired as a 2-input AND (Nexperia function
table: C = 0 → Y = B, C = 1 → Y = A; with B = GND, Y = A AND C). A = Dev TX,
C = P4 TX, both pulled up with 100 kΩ. UART lines idle high, so whichever side
talks drives SURX; don't talk from both at once. _Changed 2026-10-12: the stock
ADSBee Programmer (its `board.hh`: GPIO26 ~SRST, 27 SYNC, 28 TX, 29 RX) has no
mux-select output, so the earlier select line is gone._

**Pogo pins to an unsoldered module?** Possible, but not recommended on
ADSB_Test:
- **Fixture:** the module has 36 bottom-side pads at 1.27 mm pitch plus two
  large ground/thermal pads underneath. A pogo fixture needs fine-pitch spring
  pins (about 38 of them), an alignment pocket for the 23.4 × 14.5 mm body, and
  a clamp lid. That's a separate jig board, not something to put on ADSB_Test.
- **RF:** pads 24/26 are 50 Ω coplanar feeds, and the MP pads are the RF/thermal
  ground. Spring pins add inductance and a weaker ground return, so receiver
  sensitivity measured that way would not represent a soldered module. It's
  fine for programming or a UART smoke test, not for judging 1090/978 MHz
  performance.
- **Simpler:** the Dev Kit header gives a known-good module + RF today. When
  ready, solder a module on a second board. The module tolerates two reflow
  passes, so hot-air/reflow fitting by hand is practical.

### Firmware updates and Dev-port access

The m1421 is normally updated over **its own console UART** through the
CC1314 ROM bootloader. No debugger is needed. The sequence:
1. Hold SYNC high.
2. Pulse ~SRST.
3. Autobaud with `0x55 0x55` (≤ 1.2 Mbaud).
4. Erase, program and verify.
5. Drive SYNC low, then reset.

That gives two update paths on ADSB_Test:

| Path | How | Use |
|------|-----|-----|
| **P4 (field update)** | The P4 drives SYNC (GPIO) and ~SRST (expander) and talks to the ROM bootloader on UART3. It needs a CC13x4 ROM bootloader client in the BSP. Write it from TI's protocol spec (CC13x4 TRM SWCU194, "ROM Serial Bootloader") to keep the BSP MIT. The ADSBee Programmer's client is GPL-3.0 | Firmware updates in the field, including over Wi-Fi/Ethernet via the P4 |
| **Dev USB-C (bench)** | RP2040 on Dev hub port 4 running the **stock ADSBee 1421 Programmer** firmware (open source, RP2040-Zero). Any changes go in a separate fork repo that links back to PantsForBirds/adsbee (Q16). It works as a USB-serial adapter with RTS → SYNC and DTR → ~SRST, so the ADSBee web console's firmware uploader and AT terminal work unchanged. Its TX reaches the module through the RX AND gate, so no select line is needed | Console, AT configuration, firmware upload, logs from the PC |
| **JTAG** | 10-pin Cortex header + Segger J-Link | Breakpoint debugging, and recovery if the bootloader backdoor was turned off (`AT+BOOTLOADER_PIN=0`) |

Living with the stock Programmer (Q16):
- At every power-up (that is, every time the Dev cable is plugged in) it
  resets the module into the bootloader, CRC-checks it against its baked-in
  image, reflashes any sectors that differ, then restarts the app. Reception
  stops for a moment.
- **Rule:** keep the Programmer's baked image the same as the m1421 firmware
  release in use. Update both together: re-flash the RP2040 `.uf2` from the same
  `adsbee_1421-<version>` release. A P4 field update to a newer version is
  reverted the next time the Dev cable is plugged in, unless the Programmer is
  updated too.
- **Hardware escape hatch:** 0 Ω links (fitted) in the RP2040 → DEV_SYNC and
  RP2040 → ~SRST paths. Removing them makes the Dev port a console-only UART
  that can't reset or reflash the module.

JTAG over the Dev USB port isn't provided. The CC1314 is flashed and debugged
with a J-Link (cJTAG/JTAG), and no documented RP2040/FTDI flow exists for it.
The UART bootloader covers everything except backdoor-off recovery and
breakpoint debugging.

## Power budget and battery

Target: **everything running for about 1 hour on battery** (PWR-02).

| Load | Typical (W) | Max (W) | Notes |
|------|-------------|---------|-------|
| ESP32-P4 + flash + PSRAM | 0.5 | 0.8 | |
| ESP32-C5 (Wi-Fi active) | 0.4 | 1.0 | TX peaks |
| 7" LCD + backlight | 2.0 | 3.0 | Backlight dominant. PWM-dimmable |
| Ethernet PHY | 0.3 | 0.4 | Switchable |
| GPS + active antenna | 0.1 | 0.15 | |
| ADSBee m1421 | 0.06 | 0.1 | |
| SDR #1 (AIS, RTL-SDR class) | 1.4 | 1.5 | |
| SDR #2 (optional) | — | 1.5 | |
| External hub | 0.2 | 0.5 | Bus-powered |
| Misc (PD, monitors, LEDs, microSD) | 0.2 | 0.5 | |
| **Subtotal** | **5.2** | **9.4** | |
| Conversion losses (~12 %) | 0.6 | 1.1 | |
| **Total from battery** | **≈ 5.8 W** | **≈ 10.5 W** | |

Battery: **2S1P Li-ion 18650, ≥ 3000 mAh cells** _(proposed)_, giving about
21.6 Wh nominal. Allowing 80 % usable capacity and 10 % ageing:

| Case | Runtime |
|------|---------|
| Typical (1 SDR) | ≈ 2.7 h |
| Worst case (2 SDRs, full backlight) | ≈ 1.5 h |

Both meet the 1 h target with margin. If 4 SDRs are ever run from battery
(+3 W), use **2S2P** (≈ 43 Wh).

Charging while running at the worst case needs about 10.5 W + 2 A × 8.4 V ≈
28 W at the input. So the PD sink requests **15 V / 3 A** first, and
firmware sets the BQ25798 input-current limit from the negotiated contract.
At 9 V the charge current is reduced automatically. At 5 V the board runs
but charges slowly.

## Power tree

```
User USB-C ──► STUSB4500 (PD sink: 15 V pref, 9 V, 5 V fallback)
                   │ VBUS_USER  [PM1 ch1]
                   ▼
              BQ25798 buck-boost charger, power path ◄──► 2S Li-ion + NTC  [PM1 ch2 VBAT, bidirectional]
                   │ VSYS 6.0–8.4 V  [PM1 ch3]
     ┌─────────────┴─────────────┐
     ▼                           ▼
  5V buck 3 A                 3V3 buck 3 A (TPS62933)
     ├► USB-A eFuse 1.5 A (TPS2596) [PM1 ch4 5V_SDR]
     ├► LCD + backlight (switch)     [PM2 ch1 5V_LCD]
                                 ├► 3V3_MCU    [PM2 ch2]  (OSPTEK P4+C5 module)

                                 ├► 3V3_SD     [PM2 ch3]  (microSD)
                                 ├► 3V3_ETH    [PM2 ch4]  (switch)
                                 ├► 3V3_GPS    [PM3 ch1]  (switch)
                                 ├► 3V3_M1421  [PM3 ch2]  (switch)
                                 └► 3V3_PERIPH [PM3 ch3]  (touch, microSD, PD, monitors, expander)

Dev USB-C VBUS ──► LDO 3V3_DEV ──► USB2514B hub + FT2232H + RP2040 (ADSBee Programmer fw)  (separate domain)
```

The USB-A eFuse limit drops to 1.5 A (1–2 SDRs + hub). Use a powered hub for
4 SDRs. The 5 V buck drops to 3 A.

## Power-monitor channel map _(proposed: 3 × PAC1954, 12 channels)_

| Device (I2C addr TBC) | Ch1 | Ch2 | Ch3 | Ch4 |
|-----------------------|-----|-----|-----|-----|
| PM1 — input/battery | VBUS_USER | VBAT (bidirectional) | VSYS | 5V_SDR (USB-A) |
| PM2 — main loads | 5V_LCD | 3V3_MCU | 3V3_SD | 3V3_ETH |
| PM3 — peripherals | 3V3_GPS | 3V3_M1421 | 3V3_PERIPH | spare (5V rail total) |

The BQ25798's built-in ADC also reports VBUS/VBAT/IBAT/IBUS, which gives a
second, independent measurement for checking.

## USB topology

| Port | Connector | Connected to |
|------|-----------|--------------|
| User | USB-C (sink) | CC → STUSB4500. D+/D- → CP2102N → P4 UART1 |
| Dev | USB-C (device) | USB2514B hub. Port 1: P4 USB-Serial/JTAG. Port 2: spare (the C5's USB pins are used by SDIO). Port 3: FT2232H (A = P4 UART0 + auto-reset, B = C5 UART0 + auto-reset). Port 4: RP2040 running the ADSBee 1421 Programmer firmware, auto-reflash off (m1421 console + RTS→SYNC / DTR→~SRST; RP2040 GPIO26 ~SRST, 27 SYNC, 28 TX, 29 RX, 16 WS2812 status) |
| Host | USB-A | P4 USB 2.0 HS OTG (host) → TPS2596 eFuse, ESD → external hub → SDR(s) |

Design rules for the Dev domain:
- The hub, FT2232H and RP2040 run from Dev VBUS, so debugging still works when
  the target is unpowered.
- No signal can back-power the other domain (USB-04): Dev → target UART lines
  use open-drain 74LVC1G07s (Dev-powered) with target-side pull-ups; target →
  Dev lines use 74LVC1G125s (Dev-powered, Ioff inputs); the m1421 lines use
  74LVC1G125s into the target's own LVC gates; EN/BOOT auto-reset uses
  open-collector MMBT3904 pairs.
- The P4 USB-Serial/JTAG lines get series resistors and ESD protection
  only.
- The BQ25798's BC1.2 detection is **disabled**, because the User D+/D- lines
  go to the CP2102N.

## Test points and logic-analyser header

- Every power rail gets a test point (and a 0 Ω link for staged bring-up).
- Every PAC1954 shunt gets Kelvin pads: footprint `ADSB_Test:R_Shunt_1206_Kelvin_HandSolder`
  (pads 1/4 current, small sense pads 2/3 on the inner corners, net-tied), matching the
  4-pin `Device:R_Shunt` symbol.
- Key digital signals go to **one 2×20 2.54 mm keyed box header** that the
  **Kingst LA5016** 40-way cable plugs straight into. The LA5016 uses only the
  row on the key side: CH0–7, GND, CH8–15, GND, PWM1, PWM2. The other row is
  NC on the LA5016 apart from 2 GND. It's reserved for the LA5032
  (CH16–31) as a future upgrade.
- **PWM1 / PWM2** are outputs from the analyser. They go to test pads, and
  PWM1 can be linked by a DNP 0 Ω to the GPS PPS net to simulate PPS without a
  GPS fix.
- Each signal is tapped through a 0 Ω/100 Ω series resistor at the header.
  That keeps stubs short and lets a misbehaving channel be cut.

Header pin-out. The signal row is the key-side row, using the odd pins. Check
pin 1 against the cable's triangle mark before layout.

| Pin | LA5016 | Pin | LA5016 (row 2) |
|-----|--------|-----|----------------|
| 1–15 (odd) | CH0–CH7 | 2–16 (even) | NC (LA5032 reserved) |
| 17 | GND | 18 | GND |
| 19–33 (odd) | CH8–CH15 | 20–34 (even) | NC (LA5032 reserved) |
| 35 | GND | 36 | GND |
| 37 | PWM1 (LA output) | 38 | NC |
| 39 | PWM2 (LA output) | 40 | NC |

Signal assignment:

| LA ch | Signal | LA ch | Signal |
|-------|--------|-------|--------|
| 0 | I2C SCL | 8 | P4 UART0 TX (console) |
| 1 | I2C SDA | 9 | C5 UART0 TX |
| 2 | GPS PPS | 10 | User UART TX (P4 → CP2102N) |
| 3 | GPS TX → P4 | 11 | m1421 SD27 (UAT activity) |
| 4 | m1421 UART TX | 12 | PM ALERT (wired-OR) |
| 5 | m1421 UART RX (after mux) | 13 | Charger INT / PD ALERT |
| 6 | m1421 SYNC | 14 | P4 debug GPIO A (firmware timing marker) |
| 7 | m1421 SD26 (1090 activity) | 15 | P4 debug GPIO B (firmware timing marker) |

## ESP32-P4 pin allocation

The source of truth is [`bsp/include/bsp/board_pins.h`](../bsp/include/bsp/board_pins.h).
- **Reused pins** come from the Waveshare schematic and are identical to the
  reference board.
- **New pins** use GPIOs freed by dropping audio, CAN, RS485 and the battery
  ADC. They follow the ESP32-P4 EMAC IOMUX table and the ESP-IDF Ethernet
  defaults (`esp_eth_mac_esp.h`; `examples/ethernet/basic`: MDC 31, MDIO 52,
  PHY_RST 51).
- MIPI-DSI, USB HS and the flash use dedicated pins and aren't listed.

| GPIO | ADSB_Test | Reference board | Ref header |
|------|-----------|-----------------|------------|
| 0, 1 | 32.768 kHz crystal (on our board) | same | |
| 2 / 3 | GPS UART2 TX / RX | free | P3 |
| 4 | GPS PPS | free | P3 |
| 5 | **not on a module pad** | free | P3 |
| 6 | **DS3231M RTC INT** (LP GPIO, wake) | C6 IO2 | |
| 7 / 8 | I2C SDA / SCL | same | |
| 9 | Charger INT + PD ALERT (wired-OR) | I2S DOUT | |
| 10 / 11 | DBG_A / DBG_B (LA CH14/15) | I2S LRCK / DIN | |
| 12 / 13 | C5 GPIO0 wake / C5 CHIP_PU (inside the module) | I2S SCLK / MCLK | |
| 14–17 | SDIO D0–D3 to C5 | same (C6) | |
| 18 / 19 | SDIO CLK / CMD to C5 | same (C6) | |
| 20 | PM ALERT (PAC1954, wired-OR) | battery sense | |
| 21 / 22 | User UART1 TX / RX (CP2102N) | CAN RX / TX | |
| 23 | Touch reset | same | |
| 24 / 25 | USB-Serial/JTAG → Dev hub | USB-C H2 | |
| 26 | Touch INT | RS485 TX | |
| 27 | USB-A eFuse FAULT | RS485 RX | |
| 28 / 29 / 30 | RMII CRS_DV / RXD0 / RXD1 | free | P3 |
| 31 | MDC | free | P3 |
| 32 | Backlight PWM | same | |
| 33 | LCD reset | same | |
| 34 | RMII TXD0 | free | P3 |
| 35 | **BOOT strap + RMII TXD1** | BOOT strap | (BOOT button) |
| 36 | spare (strap, keep unloaded) | free | P3 |
| 37 / 38 | UART0 TX / RX → Dev FT2232H A | → CH343P | |
| 39–42 | microSD D0–D3 | same | |
| 43 / 44 | microSD CLK / CMD | same | |
| 45 | microSD power enable (low = on) | same | |
| 46 / 47 | m1421 UART3 TX / RX | free | P1 |
| 48 | m1421 SYNC | free | P1 |
| 49 | RMII TX_EN | free | P1 |
| 50 | RMII REF_CLK in (50 MHz) | free | P1 |
| 51 | PHY reset | free | P1 |
| 52 | MDIO | free | P1 |
| 53 | Expander INT | PA_CTRL | |
| 54 | spare (test pad) | C6 CHIP_PU | |

**Spare: 36, 54 (test pads); GPIO5 not available on the module.** Slow outputs are on the
TCA6408A: EN_LCD, EN_ETH, EN_GPS, EN_M1421, USBA_EN, SD_DET (input),
GPS_RST, M1421_RESET.

**Phase 1 bonus:** GPS (2, 3, 4), PM ALERT (5), m1421 (46, 47, 48) and
Ethernet (28–31, 34, 49–52) are all on the reference board's P1/P3 headers.
Eval boards wired to the reference board therefore use **the same GPIOs as
ADSB_Test**. The exceptions are RMII TXD1 (GPIO35, only on the BOOT button
pad) and charger/PD INT (GPIO9, used by the codec on the reference board).
For those, use a spare header pin in Phase 1.

**Checks:**
- **GPIO35** is both the BOOT strap and RMII TXD1, as on Espressif's P4 EV
  board. The PHY's TXD1 input must not pull it low during reset (check the
  LAN8720A: TXD1 has no pull or strap). Keep the reference 4.7 kΩ pull-up.
- P4 strapping pins confirmed from the datasheet: GPIO34–38 (see above).
  GPIO36 is left unloaded on purpose.

## Mechanical and RF layout

Decided 2026-10-10 (Q8, Q10):
- **Board outline:** about the size of the 7" panel, slightly larger so the
  connectors reach through the case wall.
- **Panel mounting:** the panel mounts on the PCB, as the reference board does
  (stand-offs/adhesive frame on the top side, FPC to the display connector).
- **Connector edges:** digital/power connectors (User USB-C, Dev USB-C, USB-A,
  RJ45, microSD) go on one edge. The two RF SMA connectors (GNSS and m1421
  1090/978) go on the **opposite** edge, so RF and digital cables don't share a
  side.
- **Inside the case:** the LA5016 header and the 10-pin m1421 JTAG header
  don't need to reach the case wall, but stay reachable with the back cover
  off.

Outline and case (Q20, decided 2026-10-10):

| Item | Decision |
|------|----------|
| Board outline | ~~188 × 97 mm~~. **Proposed (Q28, floorplan check): 180.9 × 116 mm**, panel centred with an 8 mm gap all round, panel cables through PCB slots, mounting holes in the board corners. See [floorplan.md](floorplan.md) |
| Digital edge (one short edge) | User USB-C, Dev USB-C, USB-A, RJ45, microSD (mid-mount/sink-in parts, ≈ 70 mm of the 97 mm edge) |
| RF edge (other short edge) | GNSS SMA and m1421 SMA, spaced apart |
| C5 antenna | ~~In the digital-edge margin~~ (edge is full). **J602 RP-SMA on the top long edge** (96 mm from the digital end), U.FL jumper from the module |
| Case | **3D-printed plastic** for the prototypes (RF-friendly for the on-module Wi-Fi antenna). ≈ 2 mm walls on the **short edges** so the connectors reach through. **Thicker walls (≈ 3 mm, optionally ribbed) on the long edges** for stiffness, since nothing passes through them |
| Battery | 2 × 18650 (2S1P) in the case behind the board. Expected overall depth ≈ 33–35 mm. A 2S flat pouch pack (≈ 22–25 mm total) is a later option needing no PCB change |

Consequences:

| Topic | Rule |
|-------|------|
| Component side | The panel is bonded to the top side (≈ 1.4 mm tape gap), so **all components go on the bottom side**. See the panel stack-up below |
| Board zoning | RF zone (m1421 + combiner + SMA, GNSS + bias-T + SMA) along the RF edge. Digital zone (P4, PSRAM/flash, MIPI-DSI, USB, Ethernet) and power zone (bucks, charger) away from it. Continuous ground plane, stitched along the zone boundary |
| RF cans _(optional)_ | Two-piece shields (frame soldered, lid snaps on and off for probing), **frames DNP by default**: (1) **SH1401** Laird BMI-S-203-F frame (26.21 mm, 5.08 mm high) + BMI-S-203-C lid over the m1421 + SCN-2-11 combiner + ESD (on the M1421 sheet); (2) GNSS module + bias-T/LNA, size chosen with the GPS sheet (BMI-S-202-F 16.5 mm or BMI-S-209-F 29.4 × 18.5 mm); (3, optional) the switching regulators. Fit the frames, decide on lids after the first RF tests (Wi-Fi, screen, Ethernet noise). Stitch each frame's pad ring to GND; RF traces leave the can on an inner layer. Fit a frame only after the module under it is soldered and checked (the m1421 hand-solder pads need iron access) |
| RF feeds | 50 Ω CPW from each module to its edge SMA, as short as possible, ground-via fenced. m1421 RF routing copied from the ADSBee 1421 carrier |
| Wi-Fi antenna | **IPEX on the OSPTEK module** → U.FL-U.FL jumper → J601 → J602 **RP-SMA on the top long edge**, away from the RF-edge SMAs and the metal panel frame. Dual-band 2.4/5 GHz RP-SMA antenna through the case. Wi-Fi is a backup and the unit normally runs offline |
| Noise | MIPI-DSI and the bucks are the main digital noise sources near the 1090/978 and GNSS L1 inputs. Keep the switch-node copper small. The buck frequencies must not have harmonics landing on 978/1090/1575 MHz (check during part selection) |

### 7" panel: what we know (Q19)

There's no public datasheet for the bare panel. Panels with the EK79007 driver
vary by vendor in outline (about 164 × 97 mm up to 170 × 103 mm) and in lane
count. So **the authoritative source is Waveshare's own dimension drawing and
STEP model** of the ESP32-P4-WIFI6-Touch-LCD-7B (resources page →
"Drawing (3D ZIP)", 2025-11-08). The files are kept locally in
`boards/esp32-p4-wifi6-touch-lcd-7b/hardware/vendor/` (git-ignored).

| Item | Value | Source |
|------|-------|--------|
| Cover lens outline | 164.28 ± 0.1 × 99.17 ± 0.1 mm | Waveshare drawing |
| Viewing area | 154.58 × 86.42 mm (offsets from lens edge: 3.06 left, 6.64 right, 4.02 top) | Waveshare drawing |
| LCD module outline | 164 × 97.1 mm | Waveshare drawing |
| Lens front → LCD back | 5.7 mm | Waveshare drawing |
| LCD back → PCB top face | **≈ 1.4 mm** (scaled from the drawing; looks like a bonding tape/foam layer, no stand-offs) | Waveshare drawing, measured |
| Waveshare PCB | 164 × 97 × 1.6 mm, PCB edge 1.58 mm in from the lens bottom edge | Waveshare drawing |
| Overall depth (lens front → tallest back-side part) | 15.3 mm, so about **6.6 mm** component height behind the PCB | Waveshare drawing |
| Mounting | 4 × M2.5 threaded holes, **156 × 89 mm** pitch (4 mm in from the PCB edges) | Waveshare drawing |
| Driver IC / interface | EK79007, **2-lane MIPI-DSI**, 1024 × 600, RGB888/565. ESP-IDF component `esp_lcd_ek79007` | Waveshare `07_color_panel` example |
| DSI PHY supply | P4 internal LDO channel 3 at 2.5 V | Waveshare example |
| Touch | GT911 (I2C) | Waveshare examples |
| LCD reset | GPIO33 in the vendor example (check against the schematic before it goes into `board_pins.h`) | Waveshare example |

**Stack-up for ADSB_Test ("as short as we can get away with"):** copy the
Waveshare stack.
- The panel is bonded straight to the **top side of the PCB** with the same
  ≈ 1.4 mm tape layer. No stand-offs.
- The top side under the panel is **component-free**: only flat items such as
  test pads, fiducials and the panel FPC exit.
- All components go on the **bottom side** (single-sided assembly).
- The case depth is set by the tallest bottom-side part. Waveshare manages 6.6
  mm. Ethernet and USB-A make that hard, so use **mid-mount / sink-in RJ45 and
  USB-A** through cut-outs in the board margin, and edge-straddle SMAs.
- The 2S 18650 pack (18.6 mm diameter) goes in the case behind the board, off
  the PCB.
- **Board outline:** the 164 × 97 mm panel area plus margin strips on the
  connector edges (width TBC, to suit the case wall and the C5 antenna). The
  4 × M2.5 holes stay on the Waveshare 156 × 89 mm pitch.

## Risks to test early

| Risk | Why | Early test |
|------|-----|------------|
| AIS SDR decode load on the P4 | DDC + AIS demod of one 1.6–2.4 MS/s stream | Profile on the reference board with 1 RTL-SDR |
| esp_hosted with C5 over SDIO | Newer slave target | C5 DevKit + reference board |
| m1421 Dev-port and P4 update paths | Programmer firmware must run with auto-reflash off; the P4 needs a ROM bootloader client | Dev Kit: run the Programmer in pass-through, then flash the module from the reference board's P4 over UART |
| SYNC held high during a reset | Module boots into the bootloader instead of the app | P4 drives SYNC low before any reset. `AT+WATCHDOG=0` for long sleeps |
| RF: 1090/978 MHz vs GPS L1 vs Wi-Fi 2.4/5 GHz on one board | Desense | Keep the carrier's RF layout. Separate antennas, shielding/keep-outs |
| USB-A current | 1–2 SDRs + hub ≈ 0.5–0.8 A | Measure, set the eFuse limit |

## Power switch and always-on backup (added 2026-10-12)

| Item | Implementation |
|------|----------------|
| **POWER switch** | SW401, right-angle through-hole slide switch (C&K OS102011MA1Q) on the case edge. **OFF** pulls the shared enable `PWR_EN` of both TPS62933 bucks low, so 5 V, 3V3 and every rail after them are off. One UVLO divider (100k/28k, ≈ 5.5 V on VSYS) feeds `PWR_EN` |
| Still alive when OFF | VSYS (charger power path), the BQ25798 (**charges from USB while switched off**), the STUSB4500 (powered from VBUS) and the backup LDO |
| **VBACKUP** (3.0 V) | MCP1703 (16 V input, ≈ 2 µA quiescent) from VSYS → BAT43W diode → `VBACKUP` → **DS3231M VBAT** (RTC, Q27) and GPS **V_BCKP** (hot start). Present whenever a battery or USB is connected |
| Optional coin cell | BT301 CR1220 holder + diode, **not fitted** by default. Fit it to keep RTC/GPS alive with the main battery removed. A primary cell is safe here: it's diode-OR'd, with no charge path |
| Off-state drain (estimate) | MCP1703 ≈ 2 µA + BQ25798 battery-only quiescent + TPS62933 shutdown. Confirm from datasheets / measure in bring-up |
| **SLEEP/WAKE button** | SW603, right-angle tactile (C&K PTS645VL31-2 LFS) on the edge next to POWER → **GPIO12** (LP GPIO), 10k pull-up on 3V3_MCU, 470R + 100 nF. Firmware `bsp_sleep()`: expander turns 5V_LCD, 3V3_ETH, 3V3_GPS, 3V3_M1421 and USB-A off, the C5 is held in reset (GPIO54 hold), the P4 goes into deep sleep. A second press wakes it (ext1, low level; wake = reset); the DS3231M alarm (GPIO13) can wake it too |
| Still alive in sleep | Everything alive when OFF, plus both bucks (light load), 3V3_MCU (P4 LP domain, module), 3V3_PERIPH (expander keeps the rails off, PAC1954s - put them in sleep over I2C, STUSB4500 pull-ups), 3V3_SD with the card switched off. Measure in bring-up (test 1.17) |

## Power sheets: schematic status (generated 2026-10-12)

The four power sheets are generated by `hardware/gen/gen_power.py`. Values
come from the part datasheets where we have them.

| Block | Implementation | Source of values |
|-------|----------------|------------------|
| PD sink | STUSB4500 + **FDS9435A (SO-8)** P-FET power path (gate pulled up 100k, VBUS_EN_SNK pulls it on), SMAJ20A TVS, USBLC6-2 on D+/D- | Confirmed from ST DS12499: VSYS to GND when unused, VBUS_VS_DISCH from the receptacle VBUS, DISCH needs a series resistor (internal discharge, max 500 mA) |
| Charger | BQ25798, PROG 8.2k = **2S, 750 kHz**; L 2.2 µH; VBUS 2×10 µF, PMID 3×10 µF + 100 nF, SYS 5×10 µF + 100 nF, BAT 2×10 µF; REGN 4.7 µF; BTST1/2 47 nF; VAC1/VAC2 to VBUS, ACDRV1/2 to GND (single input); ILIM_HIZ to REGN; CE pulled low; SDRV 1 nF (no ship FET); BATP 100 Ω; TS 5.23k / 30.1k + 103AT NTC; D+/D- unused | BQ25798 datasheet (pin table, Table 7-1, §7.3.5.2) |
| Bucks | 2 × TPS62933: RT open = 500 kHz, L 4.7 µH, SS 33 nF, BST 100 nF, EN UVLO 100k/28k (~5.5 V), FB 52.3k/10k (5 V) and 31.6k/10k (3.33 V), 2×22 µF out | TPS62933 datasheet (Table 9-1, Typical Application) |
| Branches | Kelvin shunts per rail (20 mΩ … 1 Ω by current); TPS22917 switches for 5V_LCD, 3V3_ETH, 3V3_GPS, 3V3_M1421 (QOD via 100 Ω, CT 1 nF), enables from the TCA6408A | Shunts sized for ~50 mV at the expected current. Each shunt doubles as a removable bring-up link |
| Monitors | 3 × PAC1954; SLOW = GND, PWRDN = high, GPIO = PM_ALERT (open drain, 10k pull-up). ADDRSEL: PM1 0 Ω → 0x10, PM2 499 Ω → 0x11, PM3 806 Ω → 0x12 | Microchip DS20006539 Table 6-1. EP is not connected inside (tied to GND, harmless) |
| Battery | 3-pin JST-XH (BAT+, GND, NTC). The pack must have its own 2S protection + balancing (the BQ25798 doesn't balance) | Connector current rating to confirm vs. pack |

## Proposed parts (to review)

| Function | Proposed | Alternatives | Reason |
|----------|----------|--------------|--------|
| ADS-B receiver | ADSBee m1421 | — | User choice. Dual-band, < 60 mW, UART |
| ADS-B RF combiner | MiniCircuits SCN-2-11+ | — | As on the ADSBee 1421 carrier |
| MCU + Wi-Fi | OSPTEK ESP32-P4C5 Core | Wireless-Tag WT01P4C5-S1; Waveshare ESP32-P4-Module (C6) | P4 + C5 on one module, reference-board wiring, RTC_VBAT, published footprint. Q26 |
| RTC | DS3231M (SO-8) | RV-3028-C7, PCF8563T + crystal | No crystal, ±5 ppm, on VBACKUP. Q27 |
| PD sink | STUSB4500 | AP33772S, CH224K | Standalone (NVM), I2C status |
| Charger | BQ25798 | BQ25792 (TI pages 404 since 2026-10-10), MP2762A | 1–4 cell buck-boost, power path, ADC, MPPT. Same family as BQ25792: check pin compatibility (Q21) |
| Battery | 2S1P 18650 ≥ 3000 mAh, protected | 2S2P | ≈ 21.6 Wh, 1.5–2.7 h |
| Power monitor | PAC1954 | INA3221 | 4 ch + energy accumulators |
| 3V3 buck | TPS62933 | TPS62130 | 3.8–30 V in, 3 A |
| 5V buck | TPS62933 (same part as 3V3) | | 3 A, 3.8–30 V in, one part type for both rails |
| USB-A power | TPS2596 eFuse | TPS25200 (no KiCad symbol) | Adjustable limit, fault flag, KiCad symbol available |
| Ethernet PHY | LAN8720A (since 2026-10-12) | IP101GRI (no KiCad symbol) | KiCad symbol, ESP-IDF lan87xx driver, cheap breakouts for Phase 1, 25 MHz crystal → 50 MHz REFCLKO |
| Dev hub | USB2514B | CH334 | 4-port HS hub |
| Dev UART | FT2232H | CH342 | 2 × UART with DTR/RTS auto-reset |
| Dev m1421 access | RP2040 + ADSBee 1421 Programmer firmware (auto-reflash off) | FTDI channel with RTS→SYNC, DTR→~SRST | Same as the Dev Kit, works with the ADSBee web console |
| m1421 JTAG | 10-pin 1.27 mm Cortex header + Segger J-Link | — | Documented CC1314R10 flow |
| User UART | CP2102N | CH343P (reference) | |
| GNSS | u-blox MAX-M10S | NEO-M9N | Low power, time pulse |
| GPIO expander | TCA6408A | TCA9535 | I2C, INT output |
