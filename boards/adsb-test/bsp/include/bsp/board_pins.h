/*
 * Pin map for ADSB_Test Rev A.
 *
 * Blocks copied from the reference board keep the reference pins (from the
 * Waveshare schematic). New blocks use pins freed by dropping audio, CAN,
 * RS485 and battery ADC, following the ESP32-P4 EMAC IOMUX table and the
 * ESP-IDF Ethernet defaults. Full table: boards/adsb-test/docs/architecture.md.
 *
 * MCU = Wireless-Tag WT01P4C5-S1 module (ESP32-P4 + ESP32-C5, Q26). Module pads and
 * the P4<->C5 wiring inside it: WT01P4C5-S1 datasheet v1.3 sections 3.2 and 3.4.
 * GPIO5 is not brought out; GPIO12-19 are used inside the module.
 */
#pragma once

#define BSP_BOARD_NAME          "ADSB_Test"
#define BSP_BOARD_REV           "A"

/* ---- Same as reference board ---- */

/* 32.768 kHz RTC crystal on GPIO0 / GPIO1 */

/* I2C: touch, PD sink, charger, power monitors, GPIO expander */
#define BSP_I2C_NUM             0
#define BSP_I2C_SDA             (7)
#define BSP_I2C_SCL             (8)

/* LCD: EK79007, 2-lane MIPI-DSI, PHY on LDO ch3 = 2.5 V */
#define BSP_LCD_H_RES           1024
#define BSP_LCD_V_RES           600
#define BSP_LCD_DSI_LANES       2
#define BSP_LCD_DSI_PHY_LDO_CH  3
#define BSP_LCD_DSI_PHY_LDO_MV  2500
#define BSP_LCD_BITS_PER_PIXEL  24      /* RGB888, as the vendor example */
#define BSP_LCD_RST             (33)
#define BSP_LCD_BACKLIGHT_INVERTED 1    /* higher PWM duty = dimmer */
#define BSP_LCD_BACKLIGHT       (32)    /* PWM, RC-filtered into backlight driver FB */

/* Touch GT911 */
#define BSP_TOUCH_RST           (23)
#define BSP_TOUCH_INT           (26)    /* new: wired to the P4 (reference: test point only) */

/* microSD, SDMMC slot 0 */
#define BSP_SD_CLK              (43)
#define BSP_SD_CMD              (44)
#define BSP_SD_D0               (39)
#define BSP_SD_D1               (40)
#define BSP_SD_D2               (41)
#define BSP_SD_D3               (42)
#define BSP_SD_IO_LDO_CH        4       /* P4 internal LDO VO4 powers the SD I/O domain */
#define BSP_SD_PWR_EN           (45)    /* LOW = card powered */

/* ESP32-C5 co-processor over SDIO, inside the module (same P4 pins as the reference C6) */
#define BSP_COPRO_SDIO_CLK      (18)
#define BSP_COPRO_SDIO_CMD      (19)
#define BSP_COPRO_SDIO_D0       (14)
#define BSP_COPRO_SDIO_D1       (15)
#define BSP_COPRO_SDIO_D2       (16)
#define BSP_COPRO_SDIO_D3       (17)
#define BSP_COPRO_RESET         (13)    /* C5 CHIP_PU, inside the module (reference: GPIO54) */
#define BSP_COPRO_IO            (12)    /* C5 GPIO0 (wake), inside the module (reference: GPIO6) */

/* UART0 console -> Dev port FT2232H ch A */
#define BSP_CONSOLE_UART_NUM    0
#define BSP_CONSOLE_TX          (37)
#define BSP_CONSOLE_RX          (38)
#define BSP_BOOT_BUTTON         (35)    /* strap; shared with Ethernet TXD1 (as on Espressif P4 EV board) */

/* USB: GPIO24/25 = USB-Serial/JTAG -> Dev hub port 1; HS OTG (dedicated pins) -> USB-A */

/* ---- New on ADSB_Test ---- */

/* Ethernet RMII PHY LAN8720A (ESP-IDF ESP32-P4 pin defaults); REF_CLK = 50 MHz out of the PHY (REFCLKO) */
#define BSP_ETH_TX_EN           (49)
#define BSP_ETH_TXD0            (34)
#define BSP_ETH_TXD1            (35)    /* also BOOT strap: PHY must not pull it low at reset */
#define BSP_ETH_CRS_DV          (28)
#define BSP_ETH_RXD0            (29)
#define BSP_ETH_RXD1            (30)
#define BSP_ETH_REF_CLK         (50)    /* 50 MHz from PHY, input */
#define BSP_ETH_MDC             (31)
#define BSP_ETH_MDIO            (52)
#define BSP_ETH_PHY_RST         (51)
#define BSP_ETH_PHY_ADDR        1       /* LAN8720A PHYAD0 strap (RXER pulled up) */

/* User UART (CP2102N on User USB-C) */
#define BSP_USER_UART_NUM       1
#define BSP_USER_UART_TX        (21)
#define BSP_USER_UART_RX        (22)

/* GPS (MAX-M10S) */
#define BSP_GPS_UART_NUM        2
#define BSP_GPS_TX              (2)     /* P4 TX -> GPS RX */
#define BSP_GPS_RX              (3)     /* GPS TX -> P4 RX */
#define BSP_GPS_PPS             (4)

/* ADSBee m1421 console (AT commands + GDL90 / Beast / MAVLink / JSON output) */
#define BSP_M1421_UART_NUM      3
#define BSP_M1421_BAUD          1000000 /* module default; it sends "UU" at boot for autobaud */
#define BSP_M1421_TX            (46)    /* P4 TX -> mux -> m1421 SURX (pad 20) */
#define BSP_M1421_RX            (47)    /* m1421 SUTX (pad 21) -> P4 RX */
#define BSP_M1421_SYNC          (48)    /* P4 output -> m1421 SYNC (pad 28), active high:
                                         * high at reset = ROM bootloader, high at run time = sleep.
                                         * Keep LOW in normal operation and before any reset. */

/* USB-A host power (TPS2596 eFuse) */
#define BSP_USBA_FAULT          (27)

/* Interrupts */
#define BSP_CHG_PD_INT          (9)     /* BQ25798 INT + STUSB4500 ALERT, wired-OR */
#define BSP_PM_ALERT            (20)    /* PAC1954 ALERT, wired-OR (GPIO5 is not on a module pad) */
#define BSP_RTC_INT             (6)     /* DS3231M INT/SQW, open drain; LP GPIO for deep-sleep wake */
#define BSP_EXP_INT             (53)    /* TCA6408A INT */

/* Debug GPIOs on the LA5016 header (CH14, CH15) for firmware timing markers */
#define BSP_DBG_A               (10)
#define BSP_DBG_B               (11)

/* Spare (test pads): GPIO36 (strap - keep unloaded), GPIO54 */

/* TCA6408A I2C GPIO expander bit assignments */
#define BSP_EXP_EN_LCD          0
#define BSP_EXP_EN_ETH          1
#define BSP_EXP_EN_GPS          2
#define BSP_EXP_EN_M1421        3
#define BSP_EXP_USBA_EN         4
#define BSP_EXP_SD_DET          5       /* input: microSD card detect, low = card in (normally-open switch) */
#define BSP_EXP_GPS_RST         6
#define BSP_EXP_M1421_RESET     7       /* open-drain to ~SRST */

/* I2C addresses (7-bit) */
#define BSP_I2C_ADDR_PD         0x28    /* STUSB4500 default */
#define BSP_I2C_ADDR_CHG        0x6B    /* BQ25798 */
#define BSP_I2C_ADDR_EXP        0x20    /* TCA6408A, ADDR = GND */
#define BSP_I2C_ADDR_PM1        0x10    /* PAC1954, ADDRSEL 0R  */
#define BSP_I2C_ADDR_PM2        0x11    /* ADDRSEL 499R */
#define BSP_I2C_ADDR_PM3        0x12    /* ADDRSEL 806R */
#define BSP_I2C_ADDR_RTC        0x68    /* DS3231M (fixed) */
