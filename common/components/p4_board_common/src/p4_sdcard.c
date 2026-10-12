#include "p4_board_common.h"
#include "driver/gpio.h"
#include "driver/sdmmc_host.h"
#include "esp_check.h"
#include "esp_vfs_fat.h"
#include "sd_pwr_ctrl_by_on_chip_ldo.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "p4c_sd";

static sdmmc_card_t *s_card;
static sd_pwr_ctrl_handle_t s_pwr;
static const char *s_mount_point;

static esp_err_t sdcard_mount(const p4c_sdcard_cfg_t *cfg, bool format_if_failed, sdmmc_card_t **out_card)
{
    ESP_RETURN_ON_FALSE(cfg && cfg->mount_point, ESP_ERR_INVALID_ARG, TAG, "bad args");
    ESP_RETURN_ON_FALSE(!s_card, ESP_ERR_INVALID_STATE, TAG, "already mounted");

    static bool s_power_configured;
    if (cfg->power_en_gpio >= 0 && !s_power_configured) {
        s_power_configured = true;
        const gpio_config_t io = {
            .pin_bit_mask = 1ULL << cfg->power_en_gpio,
            .mode = GPIO_MODE_OUTPUT,
        };
        ESP_RETURN_ON_ERROR(gpio_config(&io), TAG, "power enable gpio");
        gpio_set_level(cfg->power_en_gpio, cfg->power_en_active_low ? 0 : 1);
        vTaskDelay(pdMS_TO_TICKS(10));
    }

    sdmmc_host_t host = SDMMC_HOST_DEFAULT();
    host.slot = SDMMC_HOST_SLOT_0;
    host.max_freq_khz = SDMMC_FREQ_HIGHSPEED;

    if (cfg->io_ldo_chan >= 0 && !s_pwr) {
        const sd_pwr_ctrl_ldo_config_t ldo_cfg = {
            .ldo_chan_id = cfg->io_ldo_chan,
        };
        ESP_RETURN_ON_ERROR(sd_pwr_ctrl_new_on_chip_ldo(&ldo_cfg, &s_pwr), TAG, "SD I/O LDO");
    }
    host.pwr_ctrl_handle = s_pwr;

    sdmmc_slot_config_t slot = SDMMC_SLOT_CONFIG_DEFAULT();
    slot.width = cfg->bus_width;
    if (cfg->bus_width < 8) {
        /* The P4 slot-0 defaults list D4-D7 (GPIO45-48); GPIO45 is the card power
         * enable on these boards, so keep the driver off the unused data lines. */
        slot.d4 = GPIO_NUM_NC;
        slot.d5 = GPIO_NUM_NC;
        slot.d6 = GPIO_NUM_NC;
        slot.d7 = GPIO_NUM_NC;
    }
    slot.flags |= SDMMC_SLOT_FLAG_INTERNAL_PULLUP;

    const esp_vfs_fat_sdmmc_mount_config_t mount_cfg = {
        .format_if_mount_failed = format_if_failed,
        .max_files = 5,
        .allocation_unit_size = 32 * 1024,
    };
    ESP_RETURN_ON_ERROR(esp_vfs_fat_sdmmc_mount(cfg->mount_point, &host, &slot, &mount_cfg, &s_card),
                        TAG, "mount");
    s_mount_point = cfg->mount_point;
    sdmmc_card_print_info(stdout, s_card);
    if (out_card) {
        *out_card = s_card;
    }
    return ESP_OK;
}

esp_err_t p4c_sdcard_mount(const p4c_sdcard_cfg_t *cfg, sdmmc_card_t **out_card)
{
    return sdcard_mount(cfg, false, out_card);
}

esp_err_t p4c_sdcard_format(const p4c_sdcard_cfg_t *cfg)
{
    /* Card already has a FAT volume: mount it and reformat. Otherwise (e.g. exFAT)
     * mounting with format_if_mount_failed formats it once - don't format twice. */
    if (sdcard_mount(cfg, false, NULL) == ESP_OK) {
        return esp_vfs_fat_sdcard_format(s_mount_point, s_card);
    }
    return sdcard_mount(cfg, true, NULL);
}

esp_err_t p4c_sdcard_unmount(void)
{
    ESP_RETURN_ON_FALSE(s_card, ESP_ERR_INVALID_STATE, TAG, "not mounted");
    /* SDMMC slot 1 may be held by esp_hosted (Wi-Fi co-processor), so the shared
     * host controller stays up; IDF then logs "host controller with slot
     * registered" from sd_host_del_controller(). That is expected and harmless. */
    esp_err_t ret = esp_vfs_fat_sdcard_unmount(s_mount_point, s_card);
    s_card = NULL;
    s_mount_point = NULL;
    return ret;
}
