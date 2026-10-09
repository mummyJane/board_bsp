# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/) (see
[docs/versioning.md](docs/versioning.md)).

## [Unreleased]

## [0.5.0] - 2026-10-09

### Changed
- ADSB_Test m1421 integration reworked from the PantsForBirds/adsbee repo docs and firmware:
  - **SYNC is a host-driven input**: high at reset = CC1314 ROM UART bootloader, high at run
    time = sleep + LR2021 hand-off. Driven as P4 OR Dev, with a pull-down. Not a message output.
    The activity outputs SD26 (1090) / SD27 (UAT) go to LEDs and LA CH7 / CH11.
  - Dev-port path is now the ADSBee 1421 Programmer firmware on the RP2040 (power-up auto-reflash
    disabled), so the ADSBee web console AT terminal and firmware uploader work unchanged.
    JTAG stays on the 10-pin header for a Segger J-Link. JTAG over Dev USB isn't provided.
  - New requirement M14-05: the P4 can update the m1421 firmware in the field via the ROM bootloader.
  - Layout rules from the module docs (filled/capped vias, keep-outs, paste on all pads).
- ADSB_Test KiCad library replaced with the official **PantsForBirds/kicad-libs (MIT)** m1421 and
  SCN-2-11 parts (3D models included). SYNC pin type corrected to input. Licence file added.
- LA header CH11 changed from P4->GPS TX to m1421 SD27 (UAT activity).

## [0.4.1] - 2026-10-09

### Changed
- ADSB_Test: C5 module fixed as **ESP32-C5-WROOM-1-N16R8** (16 MB flash / 8 MB PSRAM). Room for
  C5 OTA slots, same module as the C5 DevKit.
- ADSB_Test: LA header changed to a **2×20 keyed box header** matching the Kingst LA5016 40-way
  cable (key-side row: CH0–7, GND, CH8–15, GND, PWM1, PWM2). The second row is reserved for an LA5032.
  LA PWM1 can simulate GPS PPS via a DNP link.

## [0.4.0] - 2026-10-09

### Changed
- ADSB_Test: co-processor changed from ESP32-C6 to **ESP32-C5** (dual-band Wi-Fi remote,
  same SDIO/esp_hosted host side).
- ADSB_Test: "M1421" identified as the **ADSBee m1421** dual-band ADS-B module. Pad-level
  integration plan (UART + SYNC + RESET to the P4, SWD + UART to the Dev port via an RP2040
  debugprobe, RF combiner copied from the ADSBee 1421 carrier).
- ADSB_Test: USB-A now targets 1 SDR (AIS etc.), 2 supported, 4 nice-to-have via an external
  hub. eFuse limit 1.5 A, 5 V buck 3 A. Dev bridge FT4232H changed to FT2232H.
- ADSB_Test: battery 2S1P 18650 sized from a new power budget (≥ 1 h with everything running).
- ADSB_Test: slow control lines moved to a TCA6408A I2C GPIO expander (P4 GPIO use ≈ 44/55).
- ADSB_Test: audio confirmed dropped, microSD confirmed kept.

### Added
- ADSB_Test KiCad project library: ADSBee m1421 symbol + footprint and MiniCircuits SCN-2-11
  symbol + footprint, from the ADSBee 1421 carrier design (GPL-3.0, attribution in `lib/README.md`).
- ADSB_Test "Test Debug" sheet: 2×10 header for the Kingst LA5016 (16 signals) and test points
  on every rail. Board pin map updated to match.
- Reference board: key parts recorded from the Waveshare schematic.

### Changed (repository)
- `hardware/vendor/` folders are git-ignored (the repo is public).

## [0.3.0] - 2026-10-09

### Added
- New board **ADSB_Test** (`boards/adsb-test`), derived from the reference board:
  - Requirements, architecture (block diagram, power tree, power-monitor
    channel map, USB topology, GPIO budget, risks, proposed parts), open
    questions, two-phase test plan and bring-up log.
  - KiCad 10 project `ADSB_Test` with 14 hierarchical sheets, each holding
    its design notes. ERC clean (no components yet).
  - BSP component and test app. `board_pins.h` lists every planned signal
    (all unassigned). Test app builds with ESP-IDF v6.1.

### Changed
- Reference board BSP component version moved to 0.3.0, in step with the project.

## [0.2.0] - 2026-10-09

### Changed
- Toolchain moved to ESP-IDF v6.1 (BSP now requires `idf >= 6.1`) and KiCad 10.
- `docs/setup.md` documents the local ESP-IDF, Python venv and KiCad paths.

### Added
- `tools/idf_env.ps1` to load the ESP-IDF v6.1 environment in PowerShell.
- `.gitattributes` for consistent line endings (LF, CRLF for `.ps1`/`.bat`).

### Verified
- Reference board test app builds with ESP-IDF v6.1 for `esp32p4`.

## [0.1.0] - 2026-10-09

### Added
- Project structure for BSPs, test code, documents and KiCad hardware.
- `VERSION` file, this changelog, and versioning / setup docs.
- Board folder for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B-C reference board:
  BSP component skeleton, test application skeleton, board README.
- `boards/_template` as the starting point for the next (custom) board.
- `.gitignore` rules for ESP-IDF build output and KiCad backups/lock files.
- `CLAUDE.md` with project rules (changelog, versioning, commit workflow).

[Unreleased]: https://github.com/mummyJane/board_bsp/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/mummyJane/board_bsp/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/mummyJane/board_bsp/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/mummyJane/board_bsp/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/mummyJane/board_bsp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/mummyJane/board_bsp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mummyJane/board_bsp/releases/tag/v0.1.0
