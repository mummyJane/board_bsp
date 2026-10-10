#include "p4_board_common.h"
#include "esp_check.h"
#include "esp_ldo_regulator.h"
#include "esp_lcd_mipi_dsi.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_ek79007.h"

static const char *TAG = "p4c_disp";

static esp_ldo_channel_handle_t s_phy_ldo;

esp_err_t p4c_display_ek79007_new(const p4c_display_cfg_t *cfg, p4c_display_t *out)
{
    ESP_RETURN_ON_FALSE(cfg && out, ESP_ERR_INVALID_ARG, TAG, "bad args");
    esp_err_t ret = ESP_OK;
    *out = (p4c_display_t){0};

    if (cfg->phy_ldo_chan >= 0 && !s_phy_ldo) {
        const esp_ldo_channel_config_t ldo_cfg = {
            .chan_id = cfg->phy_ldo_chan,
            .voltage_mv = cfg->phy_ldo_mv,
        };
        ESP_RETURN_ON_ERROR(esp_ldo_acquire_channel(&ldo_cfg, &s_phy_ldo), TAG, "DSI PHY LDO");
    }

    esp_lcd_dsi_bus_config_t bus_cfg = EK79007_PANEL_BUS_DSI_2CH_CONFIG();
    bus_cfg.num_data_lanes = cfg->lane_num;
    ESP_GOTO_ON_ERROR(esp_lcd_new_dsi_bus(&bus_cfg, &out->dsi_bus), err, TAG, "DSI bus");

    const esp_lcd_dbi_io_config_t dbi_cfg = EK79007_PANEL_IO_DBI_CONFIG();
    ESP_GOTO_ON_ERROR(esp_lcd_new_panel_io_dbi(out->dsi_bus, &dbi_cfg, &out->io), err, TAG, "DBI IO");

    const lcd_color_format_t fmt = (cfg->bits_per_pixel == 24) ? LCD_COLOR_FMT_RGB888 : LCD_COLOR_FMT_RGB565;
    esp_lcd_dpi_panel_config_t dpi_cfg = EK79007_1024_600_PANEL_60HZ_CONFIG_CF(fmt);
    ek79007_vendor_config_t vendor_cfg = {
        .mipi_config = {
            .dsi_bus = out->dsi_bus,
            .dpi_config = &dpi_cfg,
            .lane_num = cfg->lane_num,
        },
    };
    const esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = cfg->reset_gpio,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = cfg->bits_per_pixel,
        .vendor_config = &vendor_cfg,
    };
    ESP_GOTO_ON_ERROR(esp_lcd_new_panel_ek79007(out->io, &panel_cfg, &out->panel), err, TAG, "panel");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_reset(out->panel), err, TAG, "reset");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_init(out->panel), err, TAG, "init");
    return ESP_OK;

err:
    if (out->panel) {
        esp_lcd_panel_del(out->panel);
    }
    if (out->io) {
        esp_lcd_panel_io_del(out->io);
    }
    if (out->dsi_bus) {
        esp_lcd_del_dsi_bus(out->dsi_bus);
    }
    *out = (p4c_display_t){0};
    return ret;
}
