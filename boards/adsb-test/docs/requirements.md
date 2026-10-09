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
| CORE-01 | ESP32-P4 main processor, same flash/PSRAM configuration as the reference board | Yes |
| CORE-02 | ESP32-C6 _(proposed, same as reference)_ as Wi-Fi 6 / BLE co-processor over SDIO (esp_hosted) | Yes |
| CORE-03 | BSP and test firmware shared with the reference board where hardware is the same | Yes |

## Connectivity

| ID | Requirement | Ref board |
|----|-------------|-----------|
| NET-01 | 10/100 Ethernet from the ESP32-P4 EMAC (RMII PHY + RJ45 with magnetics) | Eval (PHY board) |
| NET-02 | Wi-Fi via the C6 | Yes |

## USB

| ID | Requirement | Ref board |
|----|-------------|-----------|
| USB-01 | **User** USB-C: USB-PD sink (main power input + battery charging) | Eval (PD sink board) |
| USB-02 | **User** USB-C data → USB-UART bridge → P4 "user" UART | Eval (USB-UART) |
| USB-03 | **Dev** USB-C: one cable gives all debug: P4 USB-Serial/JTAG, C6 USB-Serial/JTAG, P4 console UART, C6 UART, M1421 JTAG + debug UART | Partly (P4/C6 USB-JTAG) |
| USB-04 | Dev USB debug section is powered from the Dev port and must not back-power the target | No |
| USB-05 | USB-A host port on the P4 high-speed USB OTG, able to run up to 4 RTL-SDR type receivers (via a hub) | Yes, if the reference board's USB OTG port is usable as host |
| USB-06 | USB-A port has current-limited, switchable, measured 5 V (≥ 2.5 A target) | Eval |

## GPS

| ID | Requirement | Ref board |
|----|-------------|-----------|
| GPS-01 | GNSS module on a P4 UART | Eval (GPS breakout) |
| GPS-02 | GPS PPS (time pulse) to a P4 GPIO for message time-stamping | Eval |
| GPS-03 | Backup supply for fast hot start; active antenna connector with bias | Eval |

## Power

| ID | Requirement | Ref board |
|----|-------------|-----------|
| PWR-01 | Rechargeable battery _(proposed 2S Li-ion)_ with charger, power-path and protection | Eval (charger EVM) |
| PWR-02 | Runs from battery alone, including the SDRs on USB-A | No |
| PWR-03 | Voltage **and** current monitoring on every rail and every major load (see channel map in architecture.md) | Eval (monitor breakout) |
| PWR-04 | Each monitored load can be switched off by firmware where practical | No |
| PWR-05 | Battery temperature (NTC) monitoring by the charger | Eval |

## Display

| ID | Requirement | Ref board |
|----|-------------|-----------|
| DISP-01 | Same 7" 1024×600 MIPI-DSI panel and connector pin-out as the reference board, so the panel is interchangeable | Yes |
| DISP-02 | Same capacitive touch controller and I2C wiring as the reference board | Yes |
| DISP-03 | Firmware-controlled backlight (PWM) | Yes |

## M1421

| ID | Requirement | Ref board |
|----|-------------|-----------|
| M14-01 | Pads/footprint for an M1421 _(part to be confirmed)_ | No |
| M14-02 | M1421 JTAG and debug UART brought to the Dev USB-C port | No |
| M14-03 | M1421 supply measured by the power monitor | No |

## Kept from the reference board _(proposed)_

| ID | Requirement | Ref board |
|----|-------------|-----------|
| KEEP-01 | microSD card (logging captured ADS-B data) | Yes |
| KEEP-02 | BOOT and RESET buttons, status LED | Yes |

## Test and production

| ID | Requirement |
|----|-------------|
| TEST-01 | Test points on every power rail and on key signals (PPS, UARTs, I2C) |
| TEST-02 | Each block can be brought up independently (solder jumpers / 0 Ω links between blocks) |
| TEST-03 | Every requirement has a test in `boards/adsb-test/test` or a manual step in [test-plan.md](test-plan.md) |
