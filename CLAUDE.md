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

- Firmware: ESP-IDF v5.5, target `esp32p4`. One BSP component per board in
  `boards/<board>/bsp`, test app in `boards/<board>/test` (Unity menu).
- Pin assignments only in `bsp/include/bsp/board_pins.h`; `-1` = unconfirmed.
  Never guess pins — confirm from the vendor/our schematic.
- Hardware: KiCad 9, project in `boards/<board>/hardware/kicad/`, local libs via `${KIPRJMOD}`.
- Shared code goes in `common/components/`.
