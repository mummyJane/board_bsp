# ADSB_Test — Test plan

ADSB_Test hardware is weeks away, so testing runs in two phases.

## Phase 1 — on the reference board (now)

Use the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B-C, plus eval/dev boards wired
to its headers. **Wire each eval board to the same GPIO numbers as ADSB_Test**:
GPS 2/3/4, PM ALERT 5, m1421 46/47/48 and Ethernet 28–31/34/49–52 are all on
headers P1/P3, so Phase-1 firmware runs unchanged on ADSB_Test (see the
architecture pin table). Build `boards/adsb-test/test` (or the reference board's test
app) with the matching pin map. The reference board has **no Ethernet** and
uses a **C6**, not a C5. Those items use add-on boards.

| Step | Requirement(s) | Setup | Pass criteria |
|------|----------------|-------|---------------|
| 1.1 | CORE-01/03 | Reference board | Test app boots, Unity menu, `[bsp]` tests pass |
| 1.2 | DISP-01..03 | Reference board | Panel shows test pattern, touch coordinates reported, backlight 0–100 % |
| 1.3 | CORE-02, NET-02 | Reference board (C6) | esp_wifi_remote / esp_hosted joins AP, iperf ≥ TBC Mbit/s |
| 1.4 | CORE-02, NET-02 | ESP32-C5 DevKit running esp_hosted slave, SDIO wired to the reference board (short wires, low SDIO clock) | Same as 1.3 on 2.4 and 5 GHz |
| 1.5 | M14-01/04 | ADSBee 1421 Dev Kit: UART + SYNC + ~SRST + 3V3 wired to the reference board | Autobaud on `UU` at 1 Mbaud; `AT+LOG_LEVEL=SILENT`; GDL90 / Beast / JSON frames parsed on the P4; 1090 and 978 traffic seen; SD26/SD27 activity on the LA |
| 1.6 | M14-02 | Dev Kit + its RP2040 Programmer, ADSBee web console | AT terminal and firmware upload from the PC. Then rebuild the Programmer with auto-reflash off and confirm plugging it in no longer resets the module (Q16) |
| 1.6a | M14-05 | Dev Kit wired to the reference board | The P4 enters the ROM bootloader (SYNC high + reset), reads the CRC, flashes a release `.hex`, and boots the app with SYNC low |
| 1.6b | M14-04 | As 1.5 | SYNC sleep/wake: current drops on sleep, the aircraft table survives, and a reset with SYNC low always boots the app |
| 1.7 | USB-05 | Reference board **USB-A (J1, P4 HS OTG)** + external hub + 1 RTL-SDR, then 2 | Enumeration; sustained bulk rate at 2.0 / 2.4 MS/s with no drops |
| 1.8 | USB-05 | As 1.7 | AIS decode from one SDR: CPU % on the P4 |
| 1.9 | GPS-01/02 | MAX-M10S breakout on a UART + PPS GPIO | NMEA/UBX parsed, PPS interrupt jitter measured |
| 1.10 | PWR-03 | PAC1954 (or INA3221) breakout on I2C | Channels read, energy accumulator works, values match a multimeter |
| 1.11 | NET-01 | IP101 / LAN8720 RMII breakout | Link up, DHCP, iperf |
| 1.12 | USB-01/02, PWR-01 | STUSB4500 + BQ25798 eval boards, 2S pack | PD contract at 15 V, charge/discharge, input-current limit set from the PDO, I2C status read |
| 1.13 | PWR-02 | Reference board + all eval boards, USB power meter on each | Measured power budget replaces the estimate in architecture.md |
| 1.14 | KEEP-01 | Reference board microSD | Write/read throughput, logging while decoding |

## Phase 2 — on ADSB_Test Rev A

| Step | Check |
|------|-------|
| 2.1 | Visual inspection, rail-to-GND resistance on every rail before power |
| 2.2 | Dev USB only: hub, FT2232H and RP2040 enumerate, no voltage on target rails (back-power check, USB-04) |
| 2.3 | Bench supply on VSYS with current limit: bring up rails one at a time via the 0 Ω links. Check each rail at its test point |
| 2.4 | LA5016 plugged into the LA header: all 16 channels toggle (firmware walks each signal) |
| 2.5 | P4 USB-JTAG, both UARTs (C5 flashed over UART0 with auto-reset) and the m1421 probe over the single Dev cable |
| 2.6 | m1421 UART mux: P4 ↔ m1421 by default, probe takes over when selected |
| 2.7 | Repeat all Phase 1 steps on ADSB_Test |
| 2.8 | Battery-only run: display + Wi-Fi + Ethernet + GPS + m1421 + 1 SDR (then 2) for ≥ 1 h. All rails logged by the PAC1954s to microSD. Record temperatures |

Record the results in [bringup-log.md](bringup-log.md).
