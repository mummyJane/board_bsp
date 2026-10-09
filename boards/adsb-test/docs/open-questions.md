# ADSB_Test — Open questions

Record each answer here, then update requirements.md / architecture.md and
the CHANGELOG.

## Open

| # | Question | Current assumption |
|---|----------|--------------------|
| Q2a | Does the esp_hosted release we use support the ESP32-C5 as an SDIO slave and host-driven slave OTA? | Yes, to be confirmed in Phase 1 step 1.4 |
| Q16 | Can the ADSBee 1421 Programmer firmware's power-up auto-reflash be turned off with a build option, or does it need a small patch? | Patch if needed (GPL-3.0 firmware on the RP2040, kept separate from this repo's MIT code) |
| Q17 | m1421 module revision we'll buy (Rev D+ has the external SYNC pull-down) | Rev D or later. Our 100 kΩ pull-down covers either |
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
| Q2b | Which C5 module? | **ESP32-C5-WROOM-1-N16R8**: WROOM for more memory, so OTA is possible (a nice-to-have) |
| Q12 | m1421 SYNC: output or input? | **Input, host-driven** (from the adsbee repo). High at reset = ROM bootloader; high at run time = sleep + LR2021 hand-off; weak pull-down keeps it awake. The official symbol says "output"; our copy is corrected. Activity outputs are SD26 (1090) / SD27 (UAT) |
| Q13 | m1421 programming | Over its **console UART via the CC1314 ROM bootloader** (SYNC high + reset), no debugger. The Dev Kit's RP2040-Zero runs the open-source ADSBee 1421 Programmer (USB-serial bridge, RTS→SYNC, DTR→~SRST). JTAG uses a Segger J-Link (CC1314R10) |
| Q14 | Licensing of the m1421 KiCad parts | Taken from **PantsForBirds/kicad-libs, MIT** (licence copied into `hardware/kicad/lib`). The module firmware/schematic are GPL-3.0; none of that code is in this repo |
| Q11 | LA5016 header | **2×20 keyed header (40-way cable)**. The key-side row is CH0–7, GND, CH8–15, GND, PWM1, PWM2. The other row is for the LA5032 (future) |
