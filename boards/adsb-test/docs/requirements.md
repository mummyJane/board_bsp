# ADSB_Test — Requirements

Status: **Draft, Rev A**. Items marked _(proposed)_ are design choices made to
get started. Confirm or change them in [open-questions.md](open-questions.md).

Guiding rule: **stay as close as possible to the Waveshare
ESP32-P4-WIFI6-Touch-LCD-7B-C reference board** so firmware and circuits can be
proven on the reference board (plus eval boards) during the weeks before
ADSB_Test hardware exists.

The "Ref board" column says how each requirement can be tested before ADSB_Test
hardware exists:
- **Yes:** directly on the Waveshare board.
- **Eval:** using an evaluation/breakout board wired to the reference board.
- **No:** needs ADSB_Test hardware.

## Core

| ID | Requirement | Ref board |
|----|-------------|-----------|
| CORE-01 | ESP32-P4 main processor on a **Wireless-Tag WT01P4C5-S1** module (P4 + C5, 16 MB flash, 32 MB PSRAM; Q26), hand-solderable castellated pads | Yes (P4) |
| CORE-02 | ESP32-C5 dual-band Wi-Fi 6 co-processor **inside the WT01P4C5-S1** over SDIO (esp_hosted / esp_wifi_remote), same P4 SDIO pins as the reference board's C6. IPEX antenna on the module → U.FL pigtail (Wi-Fi is a backup, normally offline) | Yes (API on C6), Eval (C5 DevKit) |
| CORE-03 | BSP and test firmware shared with the reference board where hardware is the same | Yes |

## Connectivity

| ID | Requirement | Ref board |
|----|-------------|-----------|
| NET-01 | 10/100 Ethernet from the ESP32-P4 EMAC (RMII PHY + RJ45 with magnetics) | Eval (PHY board) |
| NET-02 | Wi-Fi (2.4 + 5 GHz) via the C5 | Yes (2.4 GHz on C6), Eval (C5 DevKit) |

## USB

| ID | Requirement | Ref board |
|----|-------------|-----------|
| USB-01 | **User** USB-C: USB-PD sink (main power input + battery charging) | Eval (PD sink board) |
| USB-02 | **User** USB-C data → USB-UART bridge → P4 "user" UART | Eval (USB-UART) |
| USB-03 | **Dev** USB-C: one cable gives all debug: P4 USB-Serial/JTAG, P4 console UART, C5 UART0 with auto-reset (the C5's USB pins are used by SDIO), m1421 console UART with SYNC/RESET control (firmware upload + AT terminal) | Partly (P4/C6 USB-JTAG) |
| USB-04 | Dev USB debug section is powered from the Dev port and must not back-power the target | No |
| USB-05 | USB-A host port on the P4 high-speed USB OTG, through an **external hub**: 1 SDR (AIS or similar) required, 2 supported, 4 nice-to-have (powered hub) | Yes, if the reference board's USB OTG port is usable as host |
| USB-06 | USB-A port has current-limited (≈ 1.5 A), switchable, measured 5 V | Eval |

## GPS

| ID | Requirement | Ref board |
|----|-------------|-----------|
| GPS-01 | GNSS module on a P4 UART | Eval (GPS breakout) |
| GPS-02 | GPS PPS (time pulse) to a P4 GPIO for message time-stamping | Eval |
| GPS-03 | Backup supply for fast hot start; active antenna connector with bias | Eval |

## Power

| ID | Requirement | Ref board |
|----|-------------|-----------|
| PWR-01 | Rechargeable Li-ion battery _(proposed 2S1P 18650, ≥ 3000 mAh)_ with charger, power path and protection | Eval (charger EVM) |
| PWR-02 | Runs **everything** (display, Wi-Fi, Ethernet, GPS, m1421, 1–2 SDRs) from battery for **≥ 1 hour** | No |
| PWR-03 | Voltage **and** current monitoring on every rail and every major load (see channel map in architecture.md) | Eval (monitor breakout) |
| PWR-04 | Each monitored load can be switched off by firmware where practical | No |
| PWR-05 | Battery temperature (NTC) monitoring by the charger | Eval |

## Display

| ID | Requirement | Ref board |
|----|-------------|-----------|
| DISP-01 | Same 7" 1024×600 MIPI-DSI panel and connector pin-out as the reference board, so the panel is interchangeable | Yes |
| DISP-02 | Same capacitive touch controller and I2C wiring as the reference board | Yes |
| DISP-03 | Firmware-controlled backlight (PWM) | Yes |
| DISP-04 | Panel supplies copied from the reference board (the panel is a bare COG panel): AVDD 9.6 V, VGH +18 V, VGL −6 V, VCOM, VCC_1V8, LED backlight boost (~150 mA) | Yes |

## ADSBee m1421

| ID | Requirement | Ref board |
|----|-------------|-----------|
| M14-01 | Footprint for the ADSBee m1421 dual-band (1090 MHz Mode S + 978 MHz UAT) ADS-B receiver module, RF front end copied from the ADSBee 1421 carrier | Eval (ADSBee 1421 Dev Kit) |
| M14-02 | m1421 console UART with SYNC/RESET control on the Dev USB-C port (ADSBee web console and firmware uploader work unchanged). JTAG on a 10-pin Cortex header for a Segger J-Link | Eval (Dev Kit) |
| M14-05 | The P4 can update the m1421 firmware in the field via the CC1314 ROM UART bootloader (SYNC + ~SRST + UART3) | Eval (Dev Kit wired to the reference board) |
| M14-04 | m1421 UART data link (GDL90 / MAVLink / CSBee) to the P4, plus SYNC and RESET | Eval (Dev Kit wired to the reference board) |
| M14-03 | m1421 supply switched and measured by the power monitor | No |

## Kept from the reference board

| ID | Requirement | Ref board |
|----|-------------|-----------|
| KEEP-01 | microSD card (logging), **required** | Yes |
| KEEP-02 | BOOT and RESET buttons, status LED | Yes |

Dropped from the reference board: audio, CAN, RS485, CSI camera.

## Mechanical and RF

| ID | Requirement | Ref board |
|----|-------------|-----------|
| MECH-01 | Board outline about the size of the 7" panel, slightly larger so connectors reach through the case | No |
| MECH-02 | Panel mounted on the PCB (as on the reference board) | Yes (reference concept) |
| MECH-03 | Digital/power connectors on one edge; GNSS and m1421 SMA connectors on the opposite edge | No |
| MECH-04 | Panel bonded straight to the PCB top side (≈ 1.4 mm tape, as on the reference board). Top side component-free under the panel; all parts on the bottom side | Yes (reference stack-up) |
| MECH-06 | Board ≈ 188 × 97 mm: ≈ 12 mm margins on both short edges (digital connectors one side, RF SMAs the other); C5 antenna in the digital margin away from RJ45/USB-A | No |
| MECH-07 | Prototype case: 3D-printed plastic, ≈ 2 mm walls on the short (connector) edges, ≈ 3 mm (optionally ribbed) on the long edges; 2 × 18650 behind the board | No |
| MECH-05 | Minimum overall depth: low-profile / mid-mount connectors; battery off-board in the case. 4 × M2.5 holes on the reference 156 × 89 mm pitch | No |
| RF-01 | SMA connectors for GNSS (active antenna, bias-T) and the m1421 (1090/978 dual-band) | Eval |
| RF-02 | Optional two-piece RF can footprints over the m1421 RF section, the GNSS section and (optionally) the switching regulators | No |
| RF-03 | C5 on-module PCB antenna placed in a board margin outside the panel outline, with keep-out, under a non-metallic part of the case | Eval (C5 DevKit) |

## Test and production

| ID | Requirement |
|----|-------------|
| TEST-01 | Test points on every power rail, Kelvin pads on every monitor shunt |
| TEST-04 | 16 key digital signals on a 2×20 keyed header that the Kingst LA5016 40-way cable plugs straight into. Second row reserved for an LA5032. LA PWM outputs to test pads (pin-out in architecture.md) |
| TEST-02 | Each block can be brought up independently (solder jumpers / 0 Ω links between blocks) |
| TEST-03 | Every requirement has a test in `boards/adsb-test/test` or a manual step in [test-plan.md](test-plan.md) |
