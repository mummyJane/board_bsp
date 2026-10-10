#include "p4_board_common.h"
#include "esp_check.h"

static const char *TAG = "p4c_i2c";

esp_err_t p4c_i2c_init(int port, int sda, int scl, i2c_master_bus_handle_t *out_bus)
{
    ESP_RETURN_ON_FALSE(out_bus && sda >= 0 && scl >= 0, ESP_ERR_INVALID_ARG, TAG, "bad args");

    const i2c_master_bus_config_t cfg = {
        .i2c_port = port,
        .sda_io_num = sda,
        .scl_io_num = scl,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    return i2c_new_master_bus(&cfg, out_bus);
}

esp_err_t p4c_i2c_probe(i2c_master_bus_handle_t bus, uint8_t addr)
{
    return i2c_master_probe(bus, addr, 50);
}
