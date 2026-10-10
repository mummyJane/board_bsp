/*
 * Pin map for Waveshare ESP32-P4-WIFI6-Touch-LCD-7B-C.
 *
 * Source: Waveshare schematic ESP32-P4-WIFI6-Touch-LCD-7B.pdf
 * (https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B), read 2026-10-10.
 * -1 = not connected to the P4.
 */
#pragma once

#define BSP_BOARD_NAME          "ESP32-P4-WIFI6-Touch-LCD-7B-C"

/* 32.768 kHz RTC crystal on GPIO0 / GPIO1 */

/* I2C (touch GT911, codec ES8311, ADC ES7210), 2.2k pull-ups */
#define BSP_I2C_NUM             0
#define BSP_I2C_SDA             (7)
#define BSP_I2C_SCL             (8)

/* LCD: EK79007 panel, 2-lane MIPI-DSI on dedicated pins, PHY on LDO ch3 = 2.5 V */
#define BSP_LCD_H_RES           1024
#define BSP_LCD_V_RES           600
#define BSP_LCD_DSI_LANES       2
#define BSP_LCD_DSI_PHY_LDO_CH  3
#define BSP_LCD_DSI_PHY_LDO_MV  2500
#define BSP_LCD_BITS_PER_PIXEL  24      /* RGB888, as the vendor example */
#define BSP_LCD_RST             (33)    /* via R42 0R, 10k pull-down */
#define BSP_LCD_BACKLIGHT_INVERTED 1    /* higher PWM duty = dimmer */
#define BSP_LCD_BACKLIGHT       (32)    /* BL_CTRL: RC-filtered PWM into AP3032 FB (higher = dimmer) */

/* Touch GT911 (connector J3) */
#define BSP_TOUCH_RST           (23)    /* via R54 0R */
#define BSP_TOUCH_INT           (-1)    /* INT_TP only goes to test point TP1 */

/* microSD, SDMMC slot 0, pull-ups to LDO VO4 */
#define BSP_SD_CLK              (43)
#define BSP_SD_CMD              (44)
#define BSP_SD_D0               (39)
#define BSP_SD_D1               (40)
#define BSP_SD_D2               (41)
#define BSP_SD_D3               (42)
#define BSP_SD_IO_LDO_CH        4       /* P4 internal LDO VO4 powers the SD I/O domain */
#define BSP_SD_PWR_EN           (45)    /* AO3401 gate: LOW = card powered (10k pull-down) */
#define BSP_SD_DET              (-1)

/* ESP32-C6-MINI-1 co-processor over SDIO (esp_hosted) */
#define BSP_COPRO_SDIO_CLK      (18)    /* C6 IO19 */
#define BSP_COPRO_SDIO_CMD      (19)    /* C6 IO18 */
#define BSP_COPRO_SDIO_D0       (14)    /* C6 IO20 */
#define BSP_COPRO_SDIO_D1       (15)    /* C6 IO21 */
#define BSP_COPRO_SDIO_D2       (16)    /* C6 IO22 */
#define BSP_COPRO_SDIO_D3       (17)    /* C6 IO23 */
#define BSP_COPRO_RESET         (54)    /* C6 CHIP_PU via R33 0R */
#define BSP_COPRO_IO            (6)     /* C6 IO2 via R31 0R */

/* UART0 console -> CH343P (USB-C H1) and header H8; DTR/RTS auto-program */
#define BSP_CONSOLE_UART_NUM    0
#define BSP_CONSOLE_TX          (37)
#define BSP_CONSOLE_RX          (38)
#define BSP_BOOT_BUTTON         (35)    /* strap, 4.7k pull-up */

/* USB: GPIO24/25 = USB 1.1 FS (USB-Serial/JTAG) on USB-C H2; HS OTG (dedicated pins) on USB-A J1 */

/* Battery voltage sense: BAT through 200k/100k divider (V_BAT = 3 x V_pin) */
#define BSP_BAT_ADC             (20)

/* Audio (ES8311 DAC, ES7210 ADC, NS4150B amp) */
#define BSP_I2S_MCLK            (13)
#define BSP_I2S_SCLK            (12)
#define BSP_I2S_LRCK            (10)
#define BSP_I2S_DOUT            (9)     /* to ES8311 DSDIN */
#define BSP_I2S_DIN             (11)    /* from ES7210 ASDOUT */
#define BSP_POWER_AMP           (53)    /* PA_CTRL */

/* CAN (TJA1051) and RS485 */
#define BSP_CAN_TX              (22)
#define BSP_CAN_RX              (21)
#define BSP_RS485_TX            (26)
#define BSP_RS485_RX            (27)

/* Free GPIOs on headers: P1 = 46..52, P3 = 2, 3, 4, 5, 28, 29, 30, 31, 34, 36 */
