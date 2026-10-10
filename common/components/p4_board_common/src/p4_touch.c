#include "p4_board_common.h"
#include "esp_check.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_touch_gt911.h"

static const char *TAG = "p4c_touch";

esp_err_t p4c_touch_gt911_new(const p4c_touch_cfg_t *cfg, esp_lcd_touch_handle_t *out)
{
    ESP_RETURN_ON_FALSE(cfg && cfg->bus && out, ESP_ERR_INVALID_ARG, TAG, "bad args");

    /* The GT911 address (0x5D or 0x14) is latched from INT during reset. When
     * INT isn't wired to the host we can't steer it, so probe for both. */
    uint8_t addr = ESP_LCD_TOUCH_IO_I2C_GT911_ADDRESS;
    if (p4c_i2c_probe(cfg->bus, addr) != ESP_OK) {
        addr = ESP_LCD_TOUCH_IO_I2C_GT911_ADDRESS_BACKUP;
    }
    ESP_LOGI(TAG, "GT911 at 0x%02x", addr);

    esp_lcd_panel_io_i2c_config_t io_cfg = ESP_LCD_TOUCH_IO_I2C_GT911_CONFIG();
    io_cfg.dev_addr = addr;
    io_cfg.scl_speed_hz = 400000;
    esp_lcd_panel_io_handle_t io = NULL;
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_io_i2c(cfg->bus, &io_cfg, &io), TAG, "panel IO");

    esp_lcd_touch_io_gt911_config_t gt911_cfg = {
        .dev_addr = addr,
    };
    const esp_lcd_touch_config_t tp_cfg = {
        .x_max = cfg->x_max,
        .y_max = cfg->y_max,
        .rst_gpio_num = cfg->reset_gpio,
        .int_gpio_num = cfg->int_gpio,
        .levels = {
            .reset = 0,
            .interrupt = 0,
        },
        .driver_data = &gt911_cfg,
    };
    return esp_lcd_touch_new_i2c_gt911(io, &tp_cfg, out);
}
