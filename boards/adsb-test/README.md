# ADSB_Test

ESP32-P4 based ADS-B test board, derived from the Waveshare
ESP32-P4-WIFI6-Touch-LCD-7B-C reference board. It is kept as close to the
reference board as possible, so firmware and circuits can be proven on the
reference board while ADSB_Test is designed.

**Hardware revision:** Rev A (design started 2026-10-09). **Status:** requirements / architecture draft.

## Features

- ESP32-P4 + ESP32-C6 (Wi-Fi 6 / BLE over SDIO), copied from the reference board
- 10/100 Ethernet (IP101GRI RMII PHY, RJ45)
- **User USB-C:** USB-PD sink (main power + charging) and a USB-UART to the P4 user UART
- **Dev USB-C:** one cable for all debug: P4 + C6 USB-Serial/JTAG, P4 + C6 UARTs, M1421 JTAG + UART
- **USB-A host** (P4 USB 2.0 HS) for up to 4 SDR receivers
- GNSS module with PPS
- 2S Li-ion battery, buck-boost charger with power path
- Voltage + current monitoring on every rail (3 × PAC1954, 12 channels)
- Same 7" 1024×600 MIPI-DSI display and touch as the reference board
- Pads for the M1421 (part TBC), with its debug and JTAG on the Dev port

## Documents

| Doc | Content |
|-----|---------|
| [docs/requirements.md](docs/requirements.md) | Numbered requirements and how each is tested before hardware exists |
| [docs/architecture.md](docs/architecture.md) | Block diagram, power tree, monitor channel map, USB topology, GPIO budget, risks, proposed parts |
| [docs/open-questions.md](docs/open-questions.md) | Decisions waiting on an answer |
| [docs/test-plan.md](docs/test-plan.md) | Phase 1 (reference board + eval boards) and Phase 2 (ADSB_Test) tests |
| [docs/bringup-log.md](docs/bringup-log.md) | Test results |

## Folders

| Folder | Content |
|--------|---------|
| [bsp/](bsp/) | ESP-IDF BSP component. Pin map in [board_pins.h](bsp/include/bsp/board_pins.h) |
| [test/](test/) | Test app (Unity menu) |
| [hardware/kicad/](hardware/kicad/) | KiCad 10 project `ADSB_Test.kicad_pro`. One hierarchical sheet per block, each holding its design notes |

## KiCad sheets

| Page | Sheet | Source |
|------|-------|--------|
| 1 | Top level | — |
| 2 | Power Input (User USB-C, PD sink) | New |
| 3 | Charger Battery | New |
| 4 | Power Rails | New |
| 5 | Power Monitor | New |
| 6 | ESP32-P4 | Copy of reference board |
| 7 | ESP32-C6 | Copy of reference board |
| 8 | Ethernet | New (per Espressif P4 Function EV board) |
| 9 | USB User | New |
| 10 | USB Dev | New |
| 11 | USB Host | New |
| 12 | GPS | New |
| 13 | Display Touch | Copy of reference board connector |
| 14 | M1421 | New, part TBC |
| 15 | Storage Misc (microSD, buttons, LEDs) | Copy of reference board |

## Hardware revisions

| Rev | Date | Changes |
|-----|------|---------|
| A | — | In design |
