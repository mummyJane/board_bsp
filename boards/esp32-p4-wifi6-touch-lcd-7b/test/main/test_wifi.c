/*
 * Wi-Fi through the ESP32-C6 co-processor (esp_wifi_remote + esp_hosted over SDIO).
 * The esp_hosted version must match the slave firmware on the C6; see idf_component.yml.
 */
#include <stdio.h>
#include "unity.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "nvs_flash.h"

TEST_CASE("Wi-Fi via C6: scan access points", "[wifi]")
{
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        TEST_ASSERT_EQUAL(ESP_OK, nvs_flash_erase());
        err = nvs_flash_init();
    }
    TEST_ASSERT_EQUAL(ESP_OK, err);
    TEST_ASSERT_EQUAL(ESP_OK, esp_netif_init());
    err = esp_event_loop_create_default();
    TEST_ASSERT_TRUE(err == ESP_OK || err == ESP_ERR_INVALID_STATE);
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    TEST_ASSERT_EQUAL(ESP_OK, esp_wifi_init(&cfg));
    TEST_ASSERT_EQUAL(ESP_OK, esp_wifi_set_mode(WIFI_MODE_STA));
    TEST_ASSERT_EQUAL(ESP_OK, esp_wifi_start());

    TEST_ASSERT_EQUAL(ESP_OK, esp_wifi_scan_start(NULL, true));
    uint16_t n = 20;
    wifi_ap_record_t aps[20];
    TEST_ASSERT_EQUAL(ESP_OK, esp_wifi_scan_get_ap_records(&n, aps));
    printf("%u access points:\n", n);
    for (int i = 0; i < n; i++) {
        printf("  %-32s ch %2d  %d dBm\n", (const char *)aps[i].ssid, aps[i].primary, aps[i].rssi);
    }
    TEST_ASSERT_GREATER_THAN(0, n);

    esp_wifi_stop();
    esp_wifi_deinit();
}
