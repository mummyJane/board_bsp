# ADSB_Test — Open questions

Record each answer here, then update requirements.md / architecture.md and
the CHANGELOG.

| # | Question | Current assumption | Answer |
|---|----------|--------------------|--------|
| Q1 | What is the **M1421**? (part number, package, supply voltages, JTAG standard, does it have USB?) | Generic pads: VCC, VIO, GND, JTAG (TCK/TMS/TDI/TDO/nTRST/nSRST), UART TX/RX, RESET | |
| Q2 | Which C-series co-processor? | ESP32-C6, same as the reference board (Wi-Fi 6, 2.4 GHz). ESP32-C5 would add 5 GHz but differs from the reference board | |
| Q3 | Battery: chemistry, cell count, capacity, pack or holders? | 2S Li-ion (e.g. 2 × 18650), with protection PCB | |
| Q4 | USB-A: one port feeding an external hub, or an on-board 4-port hub with 4 × USB-A? | One USB-A, ≥ 2.5 A, external hub | |
| Q5 | Keep microSD from the reference board? | Yes (logging) | |
| Q6 | Keep audio (codec, speaker, mic) from the reference board? | No | |
| Q7 | Should Dev USB be able to power the board for bench work (no SDRs)? | Solder jumper, default open | |
| Q8 | GPS antenna: on-board patch or u.FL/SMA for an external active antenna? | SMA, active antenna with bias | |
| Q9 | 1090 MHz: SDRs only on USB, or a future on-board receiver front end? | SDRs only | |
| Q10 | Board size / enclosure / mounting to the 7" panel? | Mounts behind the panel, same holes as the reference board | |
