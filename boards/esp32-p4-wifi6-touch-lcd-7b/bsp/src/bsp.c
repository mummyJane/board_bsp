#include <stdbool.h>
#include "esp_log.h"
#include "esp_chip_info.h"
#include "bsp/bsp.h"

static const char *TAG = "bsp";
static bool s_initialised;

esp_err_t bsp_init(void)
{
    if (s_initialised) {
        return ESP_OK;
    }

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
