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

/* I2C (touch, PD sink, charger, power monitors, GPIO expander) */
#define BSP_I2C_NUM             0
#define BSP_I2C_SDA             (-1)
#define BSP_I2C_SCL             (-1)

/* LCD (MIPI-DSI) */
#define BSP_LCD_H_RES           1024
#define BSP_LCD_V_RES           600
#define BSP_LCD_BACKLIGHT       (-1)

/* Touch */
#define BSP_TOUCH_INT           (-1)

/* microSD (SDMMC slot 0) */
#define BSP_SD_CLK              (-1)
#define BSP_SD_CMD              (-1)
#define BSP_SD_D0               (-1)
#define BSP_SD_D1               (-1)
#define BSP_SD_D2               (-1)
#define BSP_SD_D3               (-1)

/* ESP32-C5 co-processor (same P4 pins as the reference board's C6) */
#define BSP_COPRO_EN            (-1)
#define BSP_COPRO_BOOT          (-1)

/* ---- New on ADSB_Test ---- */

/* Ethernet RMII PHY (IP101GRI) */
#define BSP_ETH_MDC             (-1)
#define BSP_ETH_MDIO            (-1)
#define BSP_ETH_PHY_ADDR        1

/* Console UART0 -> Dev port FT2232H ch A */
#define BSP_CONSOLE_UART_NUM    0

/* User UART (CP2102N on User USB-C) */
#define BSP_USER_UART_NUM       1
#define BSP_USER_UART_TX        (-1)
#define BSP_USER_UART_RX        (-1)

/* GPS (MAX-M10S) */
#define BSP_GPS_UART_NUM        2
#define BSP_GPS_TX              (-1)    /* P4 TX -> GPS RX */
#define BSP_GPS_RX              (-1)    /* GPS TX -> P4 RX */
#define BSP_GPS_PPS             (-1)

/* ADSBee m1421 (GDL90 / MAVLink / CSBee over UART) */
#define BSP_M1421_UART_NUM      3
#define BSP_M1421_TX            (-1)    /* P4 TX -> mux -> m1421 SUBG_UART_RX (pad 20) */
#define BSP_M1421_RX            (-1)    /* m1421 SUBG_UART_TX (pad 21) -> P4 RX */
#define BSP_M1421_SYNC          (-1)    /* m1421 SYNC (pad 28), direction TBC */

/* USB-A host power (TPS25200 eFuse) */
#define BSP_USBA_FAULT          (-1)

/* Interrupts */
#define BSP_CHG_PD_INT          (-1)    /* BQ25792 INT + STUSB4500 ALERT, wired-OR */
#define BSP_PM_ALERT            (-1)    /* PAC1954 ALERT, wired-OR */
#define BSP_EXP_INT             (-1)    /* TCA6408A INT */

/* Debug GPIOs on the LA5016 header (CH14, CH15) for firmware timing markers */
#define BSP_DBG_A               (-1)
#define BSP_DBG_B               (-1)

/* TCA6408A I2C GPIO expander bit assignments */
#define BSP_EXP_EN_LCD          0
#define BSP_EXP_EN_ETH          1
#define BSP_EXP_EN_GPS          2
#define BSP_EXP_EN_M1421        3
#define BSP_EXP_USBA_EN         4
#define BSP_EXP_PHY_RST         5
#define BSP_EXP_GPS_RST         6
#define BSP_EXP_M1421_RESET     7       /* open-drain to ~SUBG_RESET */

/* I2C addresses (7-bit) */
#define BSP_I2C_ADDR_PD         0x28    /* STUSB4500 default */
#define BSP_I2C_ADDR_CHG        0x6B    /* BQ25792 */
#define BSP_I2C_ADDR_EXP        0x20    /* TCA6408A, ADDR = GND */
#define BSP_I2C_ADDR_PM1        (-1)    /* PAC1954, set by ADDRSEL resistor */
#define BSP_I2C_ADDR_PM2        (-1)
#define BSP_I2C_ADDR_PM3        (-1)
