# Waveshare ESP32-P4-WIFI6-Touch-LCD-7B-C (reference board)

Commercial development board used to develop and validate the BSP and test
code. The next custom board in this repo is derived from this design.

## Hardware summary

Vendor docs: https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B

> Verify every item below against the Waveshare docs / schematic before relying
> on it, then replace "TBC" with the confirmed value.

| Block | Part | Interface | Status |
|-------|------|-----------|--------|
| Main SoC | ESP32-P4NRW32 (dual-core RISC-V, 32 MB in-package PSRAM) | — | From schematic |
| Flash | GD25Q256EYIGR (32 MB) | QSPI | From schematic |
| Wireless | ESP32-C6-MINI-1 co-processor (Wi-Fi 6 / BLE 5) | SDIO (esp_hosted) | From schematic |
| Display | 7" 1024×600 LCD | MIPI-DSI | TBC |
| Touch | Capacitive touch controller | I2C | TBC part |
| Audio | Codec + speaker / mic | I2S + I2C | TBC |
| Storage | microSD | SDMMC | TBC |
| USB | USB-C (USB-Serial/JTAG / USB OTG) | USB | TBC |

## Pin map

The authoritative pin assignments live in
[`bsp/include/bsp/board_pins.h`](bsp/include/bsp/board_pins.h). All entries are
`-1` (unassigned) until confirmed from the Waveshare schematic.

## Folders

| Folder | Content |
|--------|---------|
| [bsp/](bsp/) | ESP-IDF BSP component (`bsp_init()`, pin map, peripheral init) |
| [test/](test/) | Bring-up test app (Unity menu over serial) |
| [docs/](docs/) | Bring-up log, notes, links to vendor docs |
| [hardware/](hardware/) | Vendor schematic PDF / notes (no KiCad — vendor board) |

## Bring-up status

| Feature | BSP | Test | Notes |
|---------|-----|------|-------|
| Boot / chip info | ✅ skeleton | ✅ | |
| Display | ☐ | ☐ | |
| Touch | ☐ | ☐ | |
| Wi-Fi (C6 via esp_hosted) | ☐ | ☐ | |
| Audio | ☐ | ☐ | |
| microSD | ☐ | ☐ | |
| USB | ☐ | ☐ | |
