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
| Display | 7" 1024×600 LCD, EK79007 driver | 2-lane MIPI-DSI (`esp_lcd_ek79007`), PHY on P4 LDO ch3 2.5 V | From vendor example |
| Touch | GT911 capacitive touch | I2C | From vendor examples |
| Audio | Codec + speaker / mic | I2S + I2C | TBC |
| Storage | microSD | SDMMC | TBC |
| USB | USB-C (USB-Serial/JTAG / USB OTG) | USB | TBC |

## Pin map

Confirmed from the Waveshare schematic. The full list with notes is in
[`bsp/include/bsp/board_pins.h`](bsp/include/bsp/board_pins.h).

| Function | GPIO |
|----------|------|
| I2C SDA / SCL (GT911, ES8311, ES7210; 2.2k pull-ups) | 7 / 8 |
| LCD reset / backlight PWM | 33 / 32 |
| Touch reset (INT only on test point TP1) | 23 |
| SDIO to C6: CLK / CMD / D0–D3 | 18 / 19 / 14–17 |
| C6 CHIP_PU / C6 IO2 | 54 / 6 |
| microSD CLK / CMD / D0–D3 / power enable (low = on) | 43 / 44 / 39–42 / 45 |
| UART0 TX / RX (CH343P, header H8) / BOOT strap | 37 / 38 / 35 |
| USB-Serial/JTAG (USB-C H2) | 24 / 25 |
| I2S MCLK / SCLK / LRCK / DOUT / DIN, amp enable | 13 / 12 / 10 / 9 / 11, 53 |
| CAN TX / RX, RS485 TX / RX | 22 / 21, 26 / 27 |
| Battery sense (1/3 divider) | 20 |
| 32.768 kHz crystal | 0 / 1 |
| **Free on headers** P1: 46–52; P3: 2, 3, 4, 5, 28, 29, 30, 31, 34, 36 | |

Other hardware notes:
- **USB-A host socket (J1)** on the P4 USB 2.0 HS OTG port, VBUS via a DIO7003 load switch.
- Two USB-C ports: H1 = CH343P UART, H2 = P4 USB-Serial/JTAG.
- The panel is a bare COG panel. Its supplies (AVDD 9.6 V, VGH/VGL, VCOM,
  1V8, LED backlight boost) are generated on this board.

## Folders

| Folder | Content |
|--------|---------|
| [bsp/](bsp/) | ESP-IDF BSP component (`bsp_init()`, pin map, peripheral init) |
| [test/](test/) | Bring-up test app (Unity menu over serial) |
| [docs/](docs/) | Bring-up log, notes, links to vendor docs |
| [hardware/](hardware/) | Vendor schematic PDF / notes (no KiCad — vendor board) |

## Bring-up status

BSP API: [`bsp/include/bsp/bsp.h`](bsp/include/bsp/bsp.h). Shared driver code is in
[`common/components/p4_board_common`](../../common/components/p4_board_common/).

| Feature | BSP | Test (Unity tag) | Hardware result |
|---------|-----|------------------|-----------------|
| Boot / chip info | ✅ | `[bsp]` | not run yet |
| Pin map | ✅ from schematic | — | |
| I2C bus scan | ✅ `bsp_i2c_init()` | `[i2c]` | not run yet |
| Display (EK79007, MIPI-DSI) | ✅ `bsp_display_new()` | `[display]` colour bars | not run yet |
| Backlight (inverted PWM) | ✅ `bsp_display_backlight_set()` | `[display]` sweep | not run yet |
| Touch (GT911) | ✅ `bsp_touch_new()` | `[touch]` | not run yet |
| microSD | ✅ `bsp_sdcard_mount()` | `[sdcard]` | not run yet |
| Wi-Fi (C6 via esp_hosted) | IDF `esp_wifi_*` | `[wifi]` AP scan, see [docs/wifi.md](docs/wifi.md) | not run yet |
| Audio / CAN / RS485 | ☐ (not needed for ADSB_Test) | | |

### Running the tests

```powershell
. .\tools\idf_env.ps1
cd boards\esp32-p4-wifi6-touch-lcd-7b\test
idf.py -p COMx flash monitor      # COMx = the CH343P port (USB-C "UART")
```

The Unity menu appears on the console. Enter a test number, `[tag]` (e.g.
`[display]`), or `*` for everything. Tests marked CHECK need you to look at
the screen or touch it. Record results in [docs/bringup-log.md](docs/bringup-log.md).
