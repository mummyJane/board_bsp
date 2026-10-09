# ADSB_Test — Test plan

ADSB_Test hardware is weeks away, so testing runs in two phases.

## Phase 1 — on the reference board (now)

Use the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B-C, plus eval/breakout boards
wired to its headers. Build `boards/adsb-test/test` (or the reference board's
test app) with the matching pin map.

| Step | Requirement(s) | Setup | Pass criteria |
|------|----------------|-------|---------------|
| 1.1 | CORE-01/03 | Reference board | Test app boots, Unity menu, `[bsp]` tests pass |
| 1.2 | DISP-01..03 | Reference board | Panel shows test pattern, touch coordinates reported, backlight 0–100 % |
| 1.3 | NET-02 | Reference board | C6 via esp_hosted joins AP, iperf ≥ TBC Mbit/s |
| 1.4 | USB-05 | Reference board USB OTG + hub + 1→4 RTL-SDR | Device enumeration; sustained bulk rate per SDR at 2.0/2.4 MS/s with no drops |
| 1.5 | USB-05 (risk) | As 1.4 | ADS-B decode of 1 stream: CPU % per stream. Decide feasible SDR count |
| 1.6 | GPS-01/02 | MAX-M10S breakout on a UART + PPS GPIO | NMEA/UBX parsed, PPS interrupt jitter measured |
| 1.7 | PWR-03 | PAC1954 (or INA3221) breakout on I2C | Channels read, energy accumulator works, values match a multimeter |
| 1.8 | NET-01 | IP101 / LAN8720 RMII breakout | Link up, DHCP, iperf |
| 1.9 | USB-01/02, PWR-01 | STUSB4500 + BQ25792 eval boards | PD contract at 15 V, charge/discharge, I2C status read |
| 1.10 | KEEP-01 | Reference board microSD | Write/read throughput |

## Phase 2 — on ADSB_Test Rev A

| Step | Check |
|------|-------|
| 2.1 | Visual inspection, rail-to-GND resistance on every rail before power |
| 2.2 | Dev USB only: hub + FT4232H enumerate, no voltage on target rails (back-power check, USB-04) |
| 2.3 | Bench supply on VSYS with current limit: bring up rails one at a time via jumpers |
| 2.4 | P4 USB-JTAG, C6 USB-JTAG and all 4 UARTs over the single Dev cable |
| 2.5 | Repeat all Phase 1 steps on ADSB_Test |
| 2.6 | Battery-only run with 4 SDRs + display: runtime, temperatures, all rails logged by the power monitors |
| 2.7 | M1421 JTAG chain detected via the FT4232H (OpenOCD) |

Record the results in [bringup-log.md](bringup-log.md).
