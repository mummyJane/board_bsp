# Wi-Fi via the ESP32-C6

The P4 has no radio. Wi-Fi goes through the on-board **ESP32-C6-MINI-1** over
SDIO, using `esp_hosted`. On ESP-IDF 6.1 the standard `esp_wifi_*` API is
routed to the C6 by IDF's built-in `esp_wifi_remote`. Application code calls
`esp_wifi_init()` etc. as normal.

| Item | Setting |
|------|---------|
| Host component | `espressif/esp_hosted` ^3.0.9 (`test/main/idf_component.yml`) |
| Wi-Fi remote | Built into ESP-IDF 6.1 (`components/esp_wifi/remote`). **Don't** add `espressif/esp_wifi_remote` |
| Transport | SDIO slot 1, 4-bit: CLK 18, CMD 19, D0–D3 14–17. C6 reset on GPIO54 (`sdkconfig.defaults`) |
| Slave target | ESP32-C6 |

## Slave firmware version

The C6 ships with Waveshare's esp_hosted slave firmware. Waveshare's own
examples pin host esp_hosted 1.4.x, so the shipped slave firmware is likely
1.x. According to esp_hosted `docs/migration.md`, **host 3.x is back-compatible
with co-processor 1.x/2.x**, but upgrading the co-processor is recommended.

Waveshare's pinned host combination (`esp_wifi_remote` 1.2.5 + `esp_hosted`
1.4.x) doesn't build on ESP-IDF 6.1. That's why this project uses esp_hosted
3.x.

To upgrade the C6 later, either:
- **Host-driven OTA** (no wiring): `eh_host_cp_ota_begin/write/end/activate`.
  See esp_hosted `examples/ota`. This is also how ADSB_Test will update its C5.
- **Serial:** the C6 UART0 + IO9 (boot) are on header H4 (SH1.0 4-pin). Use a
  3.3 V USB-UART adapter and flash the esp_hosted slave image for esp32c6.

Test: `[wifi]` in the test app scans for access points.
