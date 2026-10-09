/*
 * Pin map for ADSB_Test Rev A.
 *
 * Blocks copied from the reference board (ESP32-P4-WIFI6-Touch-LCD-7B-C) must
 * keep the reference pin numbers so firmware runs on both boards.
 * -1 = not yet assigned. GPIO budget: boards/adsb-test/docs/architecture.md.
 */
#pragma once

#define BSP_BOARD_NAME          "ADSB_Test"
#define BSP_BOARD_REV           "A"

/* ---- Same as reference board ---- */

/* I2C (touch, PD sink, charger, power monitors) */
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

/* microSD (SDMMC slot 0) */
#define BSP_SD_CLK              (-1)
#define BSP_SD_CMD              (-1)
#define BSP_SD_D0               (-1)
#define BSP_SD_D1               (-1)
#define BSP_SD_D2               (-1)
#define BSP_SD_D3               (-1)

/* ESP32-C6 co-processor control (SDIO pins per esp_hosted config) */
#define BSP_C6_EN               (-1)
#define BSP_C6_BOOT             (-1)

/* ---- New on ADSB_Test ---- */

/* Ethernet RMII PHY (IP101GRI) */
#define BSP_ETH_MDC             (-1)
#define BSP_ETH_MDIO            (-1)
#define BSP_ETH_PHY_RST         (-1)
#define BSP_ETH_PHY_ADDR        1

/* GPS (MAX-M10S) */
#define BSP_GPS_UART_NUM        2
#define BSP_GPS_TX              (-1)    /* P4 TX -> GPS RX */
#define BSP_GPS_RX              (-1)    /* GPS TX -> P4 RX */
#define BSP_GPS_PPS             (-1)
#define BSP_GPS_RST             (-1)

/* User UART (CP2102N on User USB-C) */
#define BSP_USER_UART_NUM       1
#define BSP_USER_UART_TX        (-1)
#define BSP_USER_UART_RX        (-1)

/* USB-A host power (TPS25200 eFuse) */
#define BSP_USBA_PWR_EN         (-1)
#define BSP_USBA_FAULT          (-1)

/* Power: interrupts and load-switch enables */
#define BSP_CHG_INT             (-1)    /* BQ25792 INT */
#define BSP_PD_ALERT            (-1)    /* STUSB4500 ALERT */
#define BSP_PM_ALERT            (-1)    /* PAC1954 ALERT, wired-OR */
#define BSP_EN_LCD              (-1)
#define BSP_EN_ETH              (-1)
#define BSP_EN_GPS              (-1)
#define BSP_EN_M1421            (-1)

/* I2C addresses (7-bit) */
#define BSP_I2C_ADDR_PD         0x28    /* STUSB4500 default */
#define BSP_I2C_ADDR_CHG        0x6B    /* BQ25792 */
#define BSP_I2C_ADDR_PM1        (-1)    /* PAC1954, set by ADDRSEL resistor */
#define BSP_I2C_ADDR_PM2        (-1)
#define BSP_I2C_ADDR_PM3        (-1)
