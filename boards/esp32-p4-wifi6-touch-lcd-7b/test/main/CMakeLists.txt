idf_component_register(
    SRCS "test_main.c" "test_bsp.c" "test_i2c.c" "test_display.c" "test_touch.c" "test_sdcard.c"
         "test_wifi.c" "test_gps.c" "test_gps_ubx.c" "test_usb_host.c"
    INCLUDE_DIRS "."
    REQUIRES bsp unity esp_lcd nvs_flash esp_netif esp_event esp_wifi esp_driver_uart esp_driver_gpio esp_timer
    WHOLE_ARCHIVE
)
