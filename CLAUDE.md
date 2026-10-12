# CLAUDE.md

Project: BSPs, test firmware, docs and KiCad schematics for ESP32-P4 boards.
Reference board: Waveshare ESP32-P4-WIFI6-Touch-LCD-7B-C. The next custom board
is derived from it.

## Rules for every change

- Add an entry under `## [Unreleased]` in `CHANGELOG.md` (Added/Changed/Fixed/Removed).
- Bump `VERSION` (SemVer) when making a release; rules in `docs/versioning.md`.
  Keep `bsp/idf_component.yml` `version:` in step with `VERSION`.
- Commit to git after each logical change and push to `origin main`.
  Tag releases `vX.Y.Z`.

## Conventions

- Firmware: ESP-IDF v6.1, target `esp32p4`. One BSP component per board in
  `boards/<board>/bsp`, test app in `boards/<board>/test` (Unity menu).
- Pin assignments only in `bsp/include/bsp/board_pins.h`; `-1` = unconfirmed.
  Never guess pins — confirm from the vendor/our schematic.
- Hardware: KiCad 10, project in `boards/<board>/hardware/kicad/`, local libs via `${KIPRJMOD}`.
- Shared code goes in `common/components/`.
- Every board: test point on every power rail, Kelvin pads on current shunts, and key
  digital signals on a 2x20 keyed header for the user's Kingst LA5016 logic analyser
  (key-side row: CH0-7, GND, CH8-15, GND, PWM1, PWM2; other row reserved for LA5032).
- Vendor documents go in `boards/<board>/hardware/vendor/` (git-ignored, public repo).
- Third-party KiCad parts go in the board's `hardware/kicad/lib/` with source + licence in its README.
- Owner hand-solders: passives/LEDs **0805 HandSolder** footprints minimum (1206 HandSolder for
  big caps/shunts), 1.5 mm test pads, through-hole where it helps. Fine-pitch ICs/modules go to
  PCBWay assembly. Fab is **PCBWay**; rules in `docs/pcb-manufacturing.md`.
- Every part used on a board gets an entry in `docs/datasheets.json` (official URL; `link` if no
  direct PDF, `manual` if the site blocks scripts). Run `python tools/fetch_datasheets.py` to
  download into `datasheets/` (git-ignored) and regenerate `docs/datasheets.md`.

## Building

- Load ESP-IDF in PowerShell with `. .\tools\idf_env.ps1` (release v6.1 at
  `D:\wirkflow\esp_test\tools\esp-idf-6.1`, venv `idf6.1_py3.13_env`). Don't use
  `~/esp/master` (dev snapshot).
- KiCad CLI: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` (ERC/DRC/exports).
- Build the test app before committing firmware changes.
