# ADSB_Test — Open questions

Record each answer here, then update requirements.md / architecture.md and
the CHANGELOG.

## Open

| # | Question | Current assumption |
|---|----------|--------------------|
| Q2a | Does the esp_hosted release we use support the ESP32-C5 as an SDIO slave? Which C5 module (WROOM vs MINI footprint)? | Yes. Module TBC |
| Q11 | LA5016 cable pin order for the 2×10 header | Odd pins = CH0–CH15 in order, even pins = GND (to be checked against the cable) |
| Q12 | m1421 SYNC: module output or host input? (symbol says output, article says host can sleep the CC1314 with it) | Wire to a P4 GPIO that can be either, plus the LA header |
| Q13 | m1421 programming: what probe/firmware does the ADSBee 1421 Dev Kit's RP2040 Zero run (debugprobe / CMSIS-DAP)? Can the m1421 also be updated over its UART? | RP2040 debugprobe on Dev hub port 4 |
| Q14 | Licensing: ADSBee design files are GPL-3.0. OK to keep the copied m1421 symbol/footprint in this MIT repo with attribution? | Kept, attribution in `hardware/kicad/lib/README.md` |
| Q15 | Commit the Waveshare schematic PDF to this **public** repo? | Not committed. Kept locally (ignored) |
| Q8 | GPS antenna: on-board patch or SMA for an external active antenna? | SMA, active antenna with bias |
| Q10 | Board size / enclosure / mounting to the 7" panel? | Mounts behind the panel, same holes as the reference board |

## Answered

| # | Question | Answer (2026-10-09) |
|---|----------|---------------------|
| Q1 | What is the M1421? | **ADSBee m1421**: dual-band (1090 + 978 MHz) ADS-B receiver module from Pants for Birds. CC1314 + LR2021, 36 pads, 3.3 V, < 60 mW, UART host interface, SWD/JTAG debug |
| Q2 | Which C-series co-processor? | **ESP32-C5**: mainly used as the Wi-Fi remote. Same as the C6 for the host firmware |
| Q3 | Battery | **Li-ion**. Must run everything for about 1 hour, so 2S1P 18650 ≥ 3000 mAh is proposed (≈ 1.5–2.7 h) |
| Q4 | USB-A | **External hub**. Usually 1 SDR (AIS or similar), 2 possible, 4 nice-to-have. The m1421 replaces 2 of the original 4 ADS-B SDRs |
| Q5 | microSD | **Keep** (required) |
| Q6 | Audio | **Drop** |
| Q7 | Dev USB powers the board? | Solder jumper, default open (unchanged) |
| Q9 | 1090 MHz front end | Done by the m1421 (1090 + 978 MHz) |
