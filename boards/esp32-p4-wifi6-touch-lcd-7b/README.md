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
| Boot / chip info | ✅ | `[bsp]` | ✅ PASS 2026-10-12 (silicon **rev v1.3**) |
| Pin map | ✅ from schematic | — | |
| I2C bus scan | ✅ `bsp_i2c_init()` | `[i2c]` | ✅ PASS: 0x18, 0x36 (?), 0x40, 0x5D |
| Display (EK79007, MIPI-DSI) | ✅ `bsp_display_new()` | `[display]` colour bars | ✅ init PASS, picture not yet checked by eye |
| Backlight (inverted PWM) | ✅ `bsp_display_backlight_set()` | `[display]` sweep | ✅ runs, direction not yet checked by eye |
| Touch (GT911) | ✅ `bsp_touch_new()` | `[touch]` | GT911 seen at 0x5D; touch not yet tried |
| microSD | ✅ `bsp_sdcard_mount()`, `bsp_sdcard_format()` | `[sdcard]`; `[sdcard_format]` (erases, not in `*`) | ❌ card detected, FAT mount fails (likely exFAT) |
| Wi-Fi (C6 via esp_hosted) | IDF `esp_wifi_*` | `[wifi]` AP scan, see [docs/wifi.md](docs/wifi.md) | ✅ PASS: 11 APs (C6 fw old, upgrade recommended) |
| USB host on USB-A (hub, RTL-SDR) | `espressif/usb` | `[usb]` lists devices, flags RTL-SDRs | ❌ 0 devices: check what's plugged in |
| GPS (eval module on P3) | UART2 + PPS | `[gps]` baud detect, NMEA, PPS jitter | not wired yet |
| Audio / CAN / RS485 | ☐ (not needed for ADSB_Test) | | |

Details: [docs/bringup-log.md](docs/bringup-log.md).

### Chip revision

This unit is **ESP32-P4 rev v1.3**. Builds for rev < 3 and rev ≥ 3 aren't
interchangeable, so `sdkconfig.defaults` selects rev < 3
(`CONFIG_ESP32P4_SELECTS_REV_LESS_V3`). For a newer rev v3.x board, build with
`idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.rev3" ...`.

### Running the tests

| Port on the dev PC | Board USB-C | What it is |
|--------------------|-------------|------------|
| **COM4** | upper, "UART" (H1) | CH343P on UART0: **primary console**, reliable auto-reset for flashing |
| COM3 | lower, "USB1.1" (H2) | P4 USB-Serial/JTAG: mirrors the console output |

```powershell
. .\tools\idf_env.ps1
cd boards\esp32-p4-wifi6-touch-lcd-7b\test
idf.py -p COM4 flash monitor
```

Write port names in **capitals** (`COM3`, not `com3`). esptool matches them
case-sensitively. With lower case it can't recognise the Espressif USB port,
falls back to the wrong reset method, and reports "Wrong boot mode detected".

The Unity menu appears on the console. Enter a test number, `[tag]` (e.g.
`[display]`), or `*` for everything. `*` skips `[ignore]` tests, which
includes the SD format. Tests marked CHECK need you to look at the screen or
touch it. Record results in [docs/bringup-log.md](docs/bringup-log.md).

To run tests unattended over the serial port:

```powershell
python tools\unity_run.py -p COM4 "[bsp]" "[i2c]" "[wifi]"
```

### microSD cards over 32 GB

Large cards ship formatted **exFAT**, and ESP-IDF 6.1's FatFs is built without
exFAT. So they won't mount until reformatted as **FAT32**. Either:
- format it on the PC with a FAT32 tool (Windows' own format dialog refuses
  FAT32 above 32 GB), or
- run the `[sdcard_format]` test, which **erases the card** and formats it
  FAT32 (32 KB clusters).

### GPS module wiring (Phase 1)

The GPS goes on header **P3** (PH2.0 12-pin), on the same GPIOs ADSB_Test
uses:

| GPS module | P3 pin | P4 GPIO |
|------------|--------|---------|
| TX (data out) | 9 | GPIO3 (P4 RX) |
| RX (data in) | 10 | GPIO2 (P4 TX) |
| PPS / TIMEPULSE | 8 | GPIO4 |
| GND | 11 | — |
| VCC | 12 (ESP_3V3, 3.3 V) | — |

Check the module's supply first: some MAX-M10S breakouts are 5 V boards with
a regulator, and P3 only provides 3.3 V. The test detects the baud rate
(38400, 9600, 115200, ...). PPS only starts pulsing once the receiver has a
time fix, so put the antenna where it can see the sky.
