idf_component_register(
    SRCS "test_main.c" "test_bsp.c" "test_i2c.c" "test_display.c" "test_touch.c" "test_sdcard.c" "test_wifi.c"
    INCLUDE_DIRS "."
    REQUIRES bsp unity esp_lcd nvs_flash esp_netif esp_event esp_wifi
    WHOLE_ARCHIVE
)
