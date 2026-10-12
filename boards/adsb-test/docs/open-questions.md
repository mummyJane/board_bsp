# ADSB_Test — Open questions

Record each answer here, then update requirements.md / architecture.md and
the CHANGELOG.

## Open

| # | Question | Current assumption |
|---|----------|--------------------|
| Q21 | Charger: TI's BQ25792 product page and datasheet return 404 (checked 2026-10-10), while the BQ25798 (same family, adds solar MPPT) is live. Switch to BQ25798? Confirm pin/register compatibility and I2C address from its datasheet | **BQ25798** proposed (datasheet downloaded) |

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
| Q2b | Which C5 module? | **WROOM, N16R8** (16 MB flash / 8 MB PSRAM) for more memory, so OTA is possible (a nice-to-have). On-module antenna (Q18) |
| Q12 | m1421 SYNC: output or input? | **Input, host-driven** (from the adsbee repo). High at reset = ROM bootloader; high at run time = sleep + LR2021 hand-off; weak pull-down keeps it awake. The official symbol says "output"; our copy is corrected. Activity outputs are SD26 (1090) / SD27 (UAT) |
| Q13 | m1421 programming | Over its **console UART via the CC1314 ROM bootloader** (SYNC high + reset), no debugger. The Dev Kit's RP2040-Zero runs the open-source ADSBee 1421 Programmer (USB-serial bridge, RTS→SYNC, DTR→~SRST). JTAG uses a Segger J-Link (CC1314R10) |
| Q14 | Licensing of the m1421 KiCad parts | Taken from **PantsForBirds/kicad-libs, MIT** (licence copied into `hardware/kicad/lib`). The module firmware/schematic are GPL-3.0; none of that code is in this repo |
| Q2a | esp_hosted with C5 over SDIO + slave OTA? | **Likely yes**. Confirm in Phase 1 step 1.4 |
| Q16 | ADSBee 1421 Programmer auto-reflash | **Keep their stock firmware** where possible. Any changes go in a separate fork repo that links back to PantsForBirds/adsbee. Operating rule: Programmer baked image = module firmware version; 0 Ω links can isolate the RP2040 from SYNC/~SRST |
| Q17 | m1421 module revision | **Latest available** (Rev D or later: external SYNC pull-down) |
| Q15 | Waveshare schematic | Not committed (public repo). Linked instead: https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B |
| Q8 | Antennas | **SMA for both GNSS and the m1421**, on the edge opposite the digital ports. Optional RF cans to keep digital/screen noise out |
| Q10 | Size / mounting | **About the size of the screen, slightly bigger** so connectors go through the case. **Screen mounted on the PCB** |
| Q18 | C5 antenna | **On-module PCB antenna (WROOM-1-N16R8)**: Wi-Fi is a backup and the unit normally runs offline. Antenna in a board margin outside the panel |
| Q19 | Panel stand-off / outline | **As short as possible.** No bare-panel datasheet is public. Use Waveshare's dimension drawing + STEP: lens 164.28 × 99.17 mm, panel 5.7 mm deep, ≈ 1.4 mm tape to the PCB, all parts on the bottom side, M2.5 holes at 156 × 89 mm |
| Q20 | Margins and case | **≈ 12 mm margins on both short edges** (board ≈ 188 × 97 mm): digital connectors on one, RF SMAs on the other, C5 antenna at the digital edge away from RJ45/USB-A. **3D-printed plastic** case, ≈ 2 mm walls on the short edges, **thicker (≈ 3 mm) on the long edges** for strength. 2 × 18650 behind the board |
| Q22 | m1421 fit for Rev A? | **Both supported**: footprint U1401 (solder later) + Dev Kit header J1402 (default for first boards). Pogo pins not recommended on the board (RF/ground; would need a separate jig) |
| Q23 | RTC / GPS backup when off | **VBACKUP 3.0 V always-on LDO from VSYS** (MCP1703, ~2 µA) feeds the P4 VDD_BAT and GPS V_BCKP. Optional CR1220 holder (DNP), diode-OR'd, for battery-removed backup |
| Q25 | On/off switch? | **Yes**: slide switch SW401 disables both bucks. The charger keeps charging from USB while off |
| Q24 | Assembly | **Rev 1: all hand-soldered; PCBWay makes the PCB only** (+ stencil). Rev 2 may be PCBWay-assembled depending on Rev 1 errors. Hand-solder footprints everywhere (docs/pcb-manufacturing.md) |
| Q26 | P4 + C5 module instead of the bare P4 + C5-WROOM? | **Yes (2026-10-12): Wireless-Tag WT01P4C5-S1-N16R32.** 1.4 mm castellated pads (hand-solderable), C5 dual-band kept, IPEX antenna accepted. 5 V supply (5V_MCU). Land pattern derived from the datasheet drawing: measure a real module before ordering PCBs |
| Q27 | RTC with no P4 VBAT on the module | **DS3231M** (SO-8, I2C 0x68) on VBACKUP, INT → GPIO6. `bsp_rtc_*` + test `[rtc_ext]` |
| Q11 | LA5016 header | **2×20 keyed header (40-way cable)**. The key-side row is CH0–7, GND, CH8–15, GND, PWM1, PWM2. The other row is for the LA5032 (future) |
