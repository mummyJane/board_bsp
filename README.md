# board_bsp

Board Support Packages (BSPs), test firmware, documentation and KiCad schematics
for a family of ESP32-P4 based boards.

Current version: see [VERSION](VERSION) · History: see [CHANGELOG.md](CHANGELOG.md)

## Boards

| Board | Folder | Status |
|-------|--------|--------|
| Waveshare ESP32-P4-WIFI6-Touch-LCD-7B-C (reference / test board) | [boards/esp32-p4-wifi6-touch-lcd-7b](boards/esp32-p4-wifi6-touch-lcd-7b/) | Bring-up |
| ADSB_Test — ESP32-P4 ADS-B test board derived from the above | [boards/adsb-test](boards/adsb-test/) | Rev A design (requirements / architecture) |

The Waveshare board is used to develop and validate the BSP and test code. The
next (custom) board reuses its design as a starting point, so everything proven
on the reference board should carry over with only pin/peripheral changes.

## Repository layout

```
board_bsp/
├── VERSION                 Project version (SemVer)
├── CHANGELOG.md            All notable changes, newest first
├── docs/                   Project-wide docs (setup, conventions)
├── common/components/      ESP-IDF components shared by all boards
└── boards/
    ├── _template/          Starting point for a new board
    └── <board>/
        ├── README.md       Board summary, pin map, status
        ├── bsp/            ESP-IDF BSP component for the board
        ├── test/           ESP-IDF test application (hardware bring-up tests)
        ├── docs/           Datasheets notes, bring-up logs, errata
        └── hardware/       KiCad project (schematic / PCB)
```

## Reference documents

Datasheets and links for every part: [docs/datasheets.md](docs/datasheets.md).
Run `python tools/fetch_datasheets.py` to download the PDFs into `datasheets/`
(git-ignored; vendor documents aren't redistributed in this public repo).

## Manufacturing

PCBs and assembly by PCBWay: capabilities, design rules and the hand-solder policy are in
[docs/pcb-manufacturing.md](docs/pcb-manufacturing.md).

## Toolchain

- **Firmware:** ESP-IDF v6.1 (ESP32-P4 target) — see [docs/setup.md](docs/setup.md)
- **Hardware:** KiCad 10

## Quick start (test app)

```powershell
. .\tools\idf_env.ps1     # load ESP-IDF v6.1
cd boards\esp32-p4-wifi6-touch-lcd-7b\test
idf.py set-target esp32p4
idf.py build flash monitor
```

## Versioning

See [docs/versioning.md](docs/versioning.md).
