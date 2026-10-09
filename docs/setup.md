# Development setup

## Firmware — ESP-IDF

1. Install ESP-IDF **v5.5** using the Espressif installer (Windows) or
   `install.sh esp32p4` (Linux/macOS). ESP32-P4 requires ESP-IDF v5.3 or newer;
   v5.5 is the version this project targets.
2. Open an "ESP-IDF PowerShell" / export the environment (`export.ps1` / `. export.sh`).
3. Build a board's test app:
   ```sh
   cd boards/<board>/test
   idf.py set-target esp32p4
   idf.py build flash monitor
   ```

The test app pulls in the board's BSP component through `EXTRA_COMPONENT_DIRS`
in its top-level `CMakeLists.txt`.

## Hardware — KiCad

- Install **KiCad 9**.
- Each board's KiCad project lives in `boards/<board>/hardware/kicad/`.
- Project-specific symbol/footprint libraries go in
  `boards/<board>/hardware/kicad/lib/` and are referenced with
  `${KIPRJMOD}` paths so the project opens on any machine.
- Do not commit `*-backups/`, `*.kicad_prl` or `fp-info-cache` (already ignored).
