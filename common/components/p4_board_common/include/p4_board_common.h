/*
 * Shared ESP32-P4 board helpers.
 *
 * Board BSPs (boards/<board>/bsp) fill these config structs from their
 * board_pins.h and call the helpers, so the same driver code runs on the
 * Waveshare reference board and on ADSB_Test.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"
#include "driver/i2c_master.h"
#include "esp_lcd_types.h"
#include "esp_lcd_mipi_dsi.h"
#include "esp_lcd_touch.h"
#include "sdmmc_cmd.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---------- I2C ---------- */

esp_err_t p4c_i2c_init(int port, int sda, int scl, i2c_master_bus_handle_t *out_bus);

/** Probe 7-bit address; returns ESP_OK if a device ACKs. */
esp_err_t p4c_i2c_probe(i2c_master_bus_handle_t bus, uint8_t addr);

/* ---------- Backlight (LEDC PWM) ---------- */

typedef struct {
    int gpio;
    bool inverted;          /* true: higher duty = dimmer (PWM fed into the LED driver FB) */
    uint32_t freq_hz;       /* 0 = default 20 kHz */
} p4c_backlight_cfg_t;

esp_err_t p4c_backlight_init(const p4c_backlight_cfg_t *cfg);
esp_err_t p4c_backlight_set(int percent);

/* ---------- Display: EK79007 1024x600, MIPI-DSI ---------- */

typedef struct {
    int reset_gpio;
    int lane_num;           /* 2 for EK79007 */
    int phy_ldo_chan;       /* P4 internal LDO channel powering the DSI PHY, -1 = none */
    int phy_ldo_mv;
    int bits_per_pixel;     /* 16 (RGB565) or 24 (RGB888) */
} p4c_display_cfg_t;

typedef struct {
    esp_lcd_panel_handle_t panel;
    esp_lcd_panel_io_handle_t io;
    esp_lcd_dsi_bus_handle_t dsi_bus;
} p4c_display_t;

esp_err_t p4c_display_ek79007_new(const p4c_display_cfg_t *cfg, p4c_display_t *out);

/* ---------- Touch: GT911 on I2C ---------- */

typedef struct {
    i2c_master_bus_handle_t bus;
    int reset_gpio;
    int int_gpio;           /* -1 if not connected */
    uint16_t x_max;
    uint16_t y_max;
} p4c_touch_cfg_t;

esp_err_t p4c_touch_gt911_new(const p4c_touch_cfg_t *cfg, esp_lcd_touch_handle_t *out);

/* ---------- microSD on SDMMC slot 0 ---------- */

typedef struct {
    int power_en_gpio;      /* -1 if none */
    bool power_en_active_low;
    int io_ldo_chan;        /* P4 internal LDO channel for the SD I/O domain, -1 = none */
    int bus_width;          /* 1 or 4 */
    const char *mount_point;
} p4c_sdcard_cfg_t;

esp_err_t p4c_sdcard_mount(const p4c_sdcard_cfg_t *cfg, sdmmc_card_t **out_card);
esp_err_t p4c_sdcard_unmount(void);

#ifdef __cplusplus
}
#endif
