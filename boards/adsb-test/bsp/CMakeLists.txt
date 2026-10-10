idf_component_register(
    SRCS "src/bsp.c"
    INCLUDE_DIRS "include"
    REQUIRES p4_board_common esp_driver_gpio esp_driver_i2c esp_lcd
)
