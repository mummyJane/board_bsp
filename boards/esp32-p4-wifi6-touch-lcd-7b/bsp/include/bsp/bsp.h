#pragma once

#include "esp_err.h"
#include "driver/i2c_master.h"
#include "esp_lcd_touch.h"
#include "p4_board_common.h"
#include "bsp/board_pins.h"

#ifdef __cplusplus
extern "C" {
#endif

#define BSP_SD_MOUNT_POINT      "/sdcard"

/** Initialise board-level resources common to all applications. Safe to call more than once. */
esp_err_t bsp_init(void);

/** Return the board name string. */
const char *bsp_board_name(void);

/** Shared I2C bus (touch, codec, ...). Created on first call. */
esp_err_t bsp_i2c_init(void);
i2c_master_bus_handle_t bsp_i2c_get_handle(void);

/** Display: EK79007 1024x600 over MIPI-DSI, plus backlight. Created once, then cached. */
esp_err_t bsp_display_new(p4c_display_t *out);
esp_err_t bsp_display_backlight_set(int percent);

/** GT911 touch on the shared I2C bus. */
esp_err_t bsp_touch_new(esp_lcd_touch_handle_t *out);

/** microSD (4-bit SDMMC slot 0) mounted at BSP_SD_MOUNT_POINT. */
esp_err_t bsp_sdcard_mount(void);
esp_err_t bsp_sdcard_unmount(void);

/** Format the microSD card as FAT32 (ERASES IT) and leave it mounted. */
esp_err_t bsp_sdcard_format(void);

#ifdef __cplusplus
}
#endif
