# ADSB_Test — Open questions

Record each answer here, then update requirements.md / architecture.md and
the CHANGELOG.

## Open

| # | Question | Current assumption |
|---|----------|--------------------|
| Q18 | C5 antenna: WROOM-1U (u.FL) with an external SMA/flex antenna (new default, because the panel's metal back covers the board), or WROOM-1 if a clear antenna edge is available? If external, a third SMA on the RF edge? | WROOM-1U-N16R8, u.FL pigtail to a third SMA on the RF edge |
| Q19 | Panel stand-off height, which sets the component height limit under the panel. Also the exact panel outline/holes (from the Waveshare 7B mechanical drawing) | TBC |

## Answered

| # | Question | Answer (2026-10-09 / 10) |
|---|----------|---------------------|
| Q1 | What is the M1421? | **ADSBee m1421**: dual-band (1090 + 978 MHz) ADS-B receiver module from Pants for Birds. CC1314 + LR2021, 36 pads, 3.3 V, < 60 mW, UART host interface, SWD/JTAG debug |
| Q2 | Which C-series co-processor? | **ESP32-C5**: mainly used as the Wi-Fi remote. Same as the C6 for the host firmware |
| Q3 | Battery | **Li-ion**. Must run everything for about 1 hour, so 2S1P 18650 ≥ 3000 mAh is proposed (≈ 1.5–2.7 h) |
| Q4 | USB-A | **External hub**. Usually 1 SDR (AIS or similar), 2 possible, 4 nice-to-have. The m1421 replaces 2 of the original 4 ADS-B SDRs |
| Q5 | microSD | **Keep** (required) |
| Q6 | Audio | **Drop** |
| Q7 | Dev USB powers the board? | Solder jumper, default open (unchanged) |
| Q9 | 1090 MHz front end | Done by the m1421 (1090 + 978 MHz) |
| Q2b | Which C5 module? | **WROOM, N16R8** (16 MB flash / 8 MB PSRAM) for more memory, so OTA is possible (a nice-to-have). Antenna variant (-1 vs -1U) in Q18 |
| Q12 | m1421 SYNC: output or input? | **Input, host-driven** (from the adsbee repo). High at reset = ROM bootloader; high at run time = sleep + LR2021 hand-off; weak pull-down keeps it awake. The official symbol says "output"; our copy is corrected. Activity outputs are SD26 (1090) / SD27 (UAT) |
| Q13 | m1421 programming | Over its **console UART via the CC1314 ROM bootloader** (SYNC high + reset), no debugger. The Dev Kit's RP2040-Zero runs the open-source ADSBee 1421 Programmer (USB-serial bridge, RTS→SYNC, DTR→~SRST). JTAG uses a Segger J-Link (CC1314R10) |
| Q14 | Licensing of the m1421 KiCad parts | Taken from **PantsForBirds/kicad-libs, MIT** (licence copied into `hardware/kicad/lib`). The module firmware/schematic are GPL-3.0; none of that code is in this repo |
| Q2a | esp_hosted with C5 over SDIO + slave OTA? | **Likely yes**. Confirm in Phase 1 step 1.4 |
| Q16 | ADSBee 1421 Programmer auto-reflash | **Keep their stock firmware** where possible. Any changes go in a separate fork repo that links back to PantsForBirds/adsbee. Operating rule: Programmer baked image = module firmware version; 0 Ω links can isolate the RP2040 from SYNC/~SRST |
| Q17 | m1421 module revision | **Latest available** (Rev D or later: external SYNC pull-down) |
| Q15 | Waveshare schematic | Not committed (public repo). Linked instead: https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B |
| Q8 | Antennas | **SMA for both GNSS and the m1421**, on the edge opposite the digital ports. Optional RF cans to keep digital/screen noise out |
| Q10 | Size / mounting | **About the size of the screen, slightly bigger** so connectors go through the case. **Screen mounted on the PCB** |
| Q11 | LA5016 header | **2×20 keyed header (40-way cable)**. The key-side row is CH0–7, GND, CH8–15, GND, PWM1, PWM2. The other row is for the LA5032 (future) |
