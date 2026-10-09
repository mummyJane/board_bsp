# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/) (see
[docs/versioning.md](docs/versioning.md)).

## [Unreleased]

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

[Unreleased]: https://github.com/mummyJane/board_bsp/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/mummyJane/board_bsp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/mummyJane/board_bsp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mummyJane/board_bsp/releases/tag/v0.1.0
