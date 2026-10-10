idf_component_register(
    SRCS "src/p4_i2c.c" "src/p4_backlight.c" "src/p4_display.c" "src/p4_touch.c" "src/p4_sdcard.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_driver_i2c esp_driver_ledc esp_driver_gpio esp_lcd esp_driver_sdmmc sdmmc fatfs esp_hw_support
)
