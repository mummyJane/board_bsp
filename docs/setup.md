# Development setup

## Firmware — ESP-IDF v6.1

The project targets the **ESP-IDF v6.1 release** (ESP32-P4 needs v5.3 or newer).

Current install on the main dev PC:

| Item | Path |
|------|------|
| ESP-IDF v6.1 | `D:\wirkflow\esp_test\tools\esp-idf-6.1` |
| Tools | `%USERPROFILE%\.espressif\tools` |
| Python venv | `%USERPROFILE%\.espressif\python_env\idf6.1_py3.13_env` |

> `~/esp/master/esp-idf` is a `v6.1-dev` snapshot of master. Don't use it for
> project builds.

Load the environment in PowerShell, then build a board's test app:

```powershell
. .\tools\idf_env.ps1
cd boards\<board>\test
idf.py set-target esp32p4
idf.py build flash monitor
```

On another machine, set `IDF_PATH` (and optionally `IDF_PYTHON_ENV_PATH`) before
running `tools\idf_env.ps1`, or use that install's own `export.ps1` / `export.sh`.

The test app pulls in the board's BSP component through `EXTRA_COMPONENT_DIRS`
in its top-level `CMakeLists.txt`.

## Hardware — KiCad 10

| Item | Path |
|------|------|
| KiCad 10 program | `C:\Program Files\KiCad\10.0` (`bin\kicad-cli.exe` for scripted ERC/DRC/exports) |
| User libraries / config | `%USERPROFILE%\OneDrive\Documents\KiCad\10.0` |

- Each board's KiCad project lives in `boards/<board>/hardware/kicad/`.
- Project-specific symbol/footprint libraries go in
  `boards/<board>/hardware/kicad/lib/` and are referenced with
  `${KIPRJMOD}` paths so the project opens on any machine. Don't reference the
  OneDrive user library folder from a project. Copy any part you need into the
  project's `lib/` instead.
- Don't commit `*-backups/`, `*.kicad_prl` or `fp-info-cache` (already ignored).
