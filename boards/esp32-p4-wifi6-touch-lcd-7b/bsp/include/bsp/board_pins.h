/*
 * Pin map for Waveshare ESP32-P4-WIFI6-Touch-LCD-7B-C.
 *
 * -1 = not yet confirmed. Fill in from the Waveshare schematic and record the
 * change in CHANGELOG.md.
 */
#pragma once

#define BSP_BOARD_NAME          "ESP32-P4-WIFI6-Touch-LCD-7B-C"

/* I2C (touch, audio codec, misc.) */
#define BSP_I2C_NUM             0
#define BSP_I2C_SDA             (-1)
#define BSP_I2C_SCL             (-1)

/* LCD (MIPI-DSI) */
#define BSP_LCD_H_RES           1024
#define BSP_LCD_V_RES           600
#define BSP_LCD_BACKLIGHT       (-1)
#define BSP_LCD_RST             (-1)

/* Touch */
#define BSP_TOUCH_INT           (-1)
#define BSP_TOUCH_RST           (-1)

/* I2S audio */
#define BSP_I2S_MCLK            (-1)
#define BSP_I2S_BCLK            (-1)
#define BSP_I2S_WS              (-1)
#define BSP_I2S_DOUT            (-1)
#define BSP_I2S_DIN             (-1)
#define BSP_POWER_AMP           (-1)

/* microSD (SDMMC) */
#define BSP_SD_CLK              (-1)
#define BSP_SD_CMD              (-1)
#define BSP_SD_D0               (-1)
#define BSP_SD_D1               (-1)
#define BSP_SD_D2               (-1)
#define BSP_SD_D3               (-1)
