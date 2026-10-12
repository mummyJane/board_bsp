# Bring-up log — ESP32-P4-WIFI6-Touch-LCD-7B-C

Record each test session: date, BSP version, what was tested, result, notes.

| Date | Version | Feature | Result | Notes |
|------|---------|---------|--------|-------|
| | 0.1.0 | Project created | — | |
| 2026-10-10 | 0.11.0 | Setup | Info | Board connected to the dev PC on COM3 = P4 USB-Serial/JTAG (VID 303A PID 1001, USB-C "USB1.1"). USB hub + RTL-SDR may be on USB-A; SD card (maybe 128 GB) to be fitted; GPS "A99E-MAX-M10S" breakout to be wired to P3 on 2026-10-11. Tests not run yet. |
| 2026-10-12 | 0.12.0 | Flash | Fixed | Chip is **ESP32-P4 rev v1.3**: builds required rev ≥ v3.0 (copied from Waveshare's examples) and were rejected. Now built with `ESP32P4_SELECTS_REV_LESS_V3`. Flashed over COM4 (CH343, upper USB-C). COM3 (USB-Serial/JTAG) failed only because esptool was given `com3` in lower case (it matches port names case-sensitively). |
| 2026-10-12 | 0.12.0 | `[bsp]` | PASS | Boots, 2 cores, silicon rev v1.3 |
| 2026-10-12 | 0.12.0 | `[i2c]` | PASS | Devices at 0x18 (ES8311), 0x36 (unidentified), 0x40 (ES7210), 0x5D (GT911 touch at primary address) |
| 2026-10-12 | 0.12.0 | `[wifi]` | PASS | C6 link up over SDIO; scan found 11 APs, strongest −35 dBm. C6 reports esp_hosted fw 0.0.0 ("major version mismatch, OTA coprocessor"), but host 3.0.9 still works. C6 firmware upgrade recommended |
| 2026-10-12 | 0.12.0 | `[display]` | PASS (init) | EK79007 init + colour bars + backlight sweep ran without error. Picture not checked (board remote) |
| 2026-10-12 | 0.12.0 | `[sdcard]` | FAIL (expected) | Card detected and initialised; FAT mount failed (ESP_FAIL), consistent with an exFAT (>32 GB) card. Not formatted; needs FAT32 or `[sdcard_format]` with the owner's OK |
| 2026-10-12 | 0.12.0 | `[usb]` | FAIL | 0 devices enumerated, no connection event. USB-A J1 confirmed on P4 HS DP/DM (schematic). Check what is plugged into USB-A / hub power |
| 2026-10-12 | 0.12.0 | `[gps]` | FAIL (expected) | No NMEA: GPS not wired yet |
| 2026-10-12 | 0.13.0 | `[sdcard_format]` | PASS | Run by the owner: 128 GB card (LX128, 119850 MB, 4-bit, 40 MHz) reformatted FAT32. Old code formatted twice (fixed) |
| 2026-10-12 | 0.13.0 | `[sdcard]` ×2 | PASS | Mount/write/read/unmount repeatable. GPIO45 (card power) conflict fixed. Remaining log noise: "host controller with slot registered" (esp_hosted holds SDMMC slot 1, expected) and a GPIO42 (D3) re-config warning from the IDF driver on later mounts |
| 2026-10-12 | 0.13.0 | `[gps]` | FAIL (expected) | New UBX comms test: no bytes received; GPS not connected yet |
| 2026-10-12 | 0.14.0 | `[display]` / `[touch]` | PASS | Owner confirmed by eye: colour bars correct, touch OK (25 touch reports in a 10 s run) |
| 2026-10-12 | 0.14.0 | `[wifi]` ×2 | PASS | Second run used to crash (duplicate default STA netif assert); fixed. 14 APs each run |
| 2026-10-12 | 0.14.0 | `[sdcard]` ×2 | PASS | New 4 MiB write + read-back verify: 0 bad words, write ≈ 9.8 MB/s, read+verify ≈ 13 MB/s; FAT32 volume 119820 MB. Persistence counter 0 → 1 across runs (power-cycle check still to do) |
| 2026-10-12 | 0.14.0 | `[usb]` ×3 | PASS | Hub 05e3:0610 (Genesys, HS) + RTL-SDR 0bda:2838 (HS) enumerated. Repeat runs used to fail (install returned 0x103: previous uninstall incomplete); teardown fixed |
| 2026-10-12 | 0.14.0 | `[gps]` ×2 | PASS | u-blox MAX-M10S: ROM SPG 5.10, PROTVER 34.10, GPS/GLO/GAL/BDS + SBAS/QZSS, 38400 baud. Antenna status DONTKNOW (breakout has no antenna supervision), no fix (no antenna fitted) |
| 2026-10-12 | 0.14.0 | `[gps_pps]` | PASS (no PPS) | ~360 NMEA sentences in 30 s; 0 PPS pulses (no fix without an antenna) |
| 2026-10-12 | 0.14.0 | `*` ×2 | PASS | Full suite twice in one boot: 14 tests, 0 failures each time |
