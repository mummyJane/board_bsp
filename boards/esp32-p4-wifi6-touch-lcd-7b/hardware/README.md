# Hardware — reference board

This is a commercial Waveshare board, so there is no KiCad project here.
The vendor schematic is kept locally in `vendor/` (git-ignored, because the repo is
public). Notes on the circuits we intend to reuse in the custom board go in this file.

Key parts (from the schematic): ESP32-P4NRW32, GD25Q256EYIGR flash, ESP32-C6-MINI-1
(SDIO), CH343P USB-UART, ETA6098 1S charger, MP1605/MP1658 bucks, RT9193 LDOs,
ES8311 + ES7210 + NS4150B audio, TJA1051 CAN, RS485, CSI camera, microSD.
No Ethernet.

## Circuits to carry over to the custom board

| Block | Notes |
|-------|-------|
| Power | TBC |
| ESP32-P4 core + flash | TBC |
| ESP32-C6 (SDIO) | TBC |
| MIPI-DSI LCD connector | TBC |
| Touch | TBC |
| Audio | TBC |
| microSD | TBC |
| USB | TBC |
