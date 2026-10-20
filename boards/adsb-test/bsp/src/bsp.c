#include <stdbool.h>
#include "esp_check.h"
#include "esp_log.h"
#include "esp_chip_info.h"
#include "bsp/bsp.h"

static const char *TAG = "bsp";
static bool s_initialised;
static i2c_master_bus_handle_t s_i2c;
static p4c_display_t s_display;
static bool s_backlight_ready;

esp_err_t bsp_init(void)
{
    if (s_initialised) {
        return ESP_OK;
    }

    bsp_power_after_wake();         /* pin holds from bsp_sleep(), monitors back on */

    esp_chip_info_t info;
    esp_chip_info(&info);
    ESP_LOGI(TAG, "%s: %d core(s), silicon rev v%d.%d",
             BSP_BOARD_NAME, info.cores, info.revision / 100, info.revision % 100);

    s_initialised = true;
    return ESP_OK;
}

const char *bsp_board_name(void)
{
    return BSP_BOARD_NAME;
}

esp_err_t bsp_i2c_init(void)
{
    if (s_i2c) {
        return ESP_OK;
    }
    return p4c_i2c_init(BSP_I2C_NUM, BSP_I2C_SDA, BSP_I2C_SCL, &s_i2c);
}

i2c_master_bus_handle_t bsp_i2c_get_handle(void)
{
    return s_i2c;
}

esp_err_t bsp_display_backlight_set(int percent)
{
    if (!s_backlight_ready) {
        const p4c_backlight_cfg_t bl = {
            .gpio = BSP_LCD_BACKLIGHT,
            .inverted = BSP_LCD_BACKLIGHT_INVERTED,
        };
        ESP_RETURN_ON_ERROR(p4c_backlight_init(&bl), TAG, "backlight");
        s_backlight_ready = true;
    }
    return p4c_backlight_set(percent);
}

esp_err_t bsp_display_new(p4c_display_t *out)
{
    if (!s_display.panel) {
        const p4c_display_cfg_t cfg = {
            .reset_gpio = BSP_LCD_RST,
            .lane_num = BSP_LCD_DSI_LANES,
            .phy_ldo_chan = BSP_LCD_DSI_PHY_LDO_CH,
            .phy_ldo_mv = BSP_LCD_DSI_PHY_LDO_MV,
            .bits_per_pixel = BSP_LCD_BITS_PER_PIXEL,
        };
        ESP_RETURN_ON_ERROR(p4c_display_ek79007_new(&cfg, &s_display), TAG, "display");
        ESP_RETURN_ON_ERROR(bsp_display_backlight_set(100), TAG, "backlight on");
    }
    if (out) {
        *out = s_display;
    }
    return ESP_OK;
}

esp_err_t bsp_touch_new(esp_lcd_touch_handle_t *out)
{
    ESP_RETURN_ON_ERROR(bsp_i2c_init(), TAG, "i2c");
    const p4c_touch_cfg_t cfg = {
        .bus = s_i2c,
        .reset_gpio = BSP_TOUCH_RST,
        .int_gpio = BSP_TOUCH_INT,
        .x_max = BSP_LCD_H_RES,
        .y_max = BSP_LCD_V_RES,
    };
    return p4c_touch_gt911_new(&cfg, out);
}

static const p4c_sdcard_cfg_t s_sd_cfg = {
    .power_en_gpio = BSP_SD_PWR_EN,
    .power_en_active_low = true,
    .io_ldo_chan = BSP_SD_IO_LDO_CH,
    .bus_width = 4,
    .mount_point = BSP_SD_MOUNT_POINT,
};

esp_err_t bsp_sdcard_mount(void)
{
    return p4c_sdcard_mount(&s_sd_cfg, NULL);
}

esp_err_t bsp_sdcard_format(void)
{
    return p4c_sdcard_format(&s_sd_cfg);
}

esp_err_t bsp_sdcard_unmount(void)
{
    return p4c_sdcard_unmount();
}
