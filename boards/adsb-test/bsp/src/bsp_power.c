#include "esp_check.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "bsp/bsp.h"

static const char *TAG = "bsp_power";

/* TCA6408A registers */
#define EXP_REG_OUTPUT  0x01
#define EXP_REG_CONFIG  0x03    /* 1 = input */

static void sleep_button_init(void)
{
    const gpio_config_t io = {
        .pin_bit_mask = 1ULL << BSP_SLEEP_BUTTON,
        .mode = GPIO_MODE_INPUT,            /* 10k pull-up + 100nF on the board */
    };
    gpio_config(&io);
}

bool bsp_sleep_button_pressed(void)
{
    static bool ready;
    if (!ready) {
        sleep_button_init();
        ready = true;
    }
    return gpio_get_level(BSP_SLEEP_BUTTON) == 0;
}

/* All switched rails off: EN_LCD, EN_ETH, EN_GPS, EN_M1421, USBA_EN low (outputs); SD_DET, GPS reset and
 * m1421 reset as inputs (released). The expander is on 3V3_PERIPH, so it keeps this state while the P4 sleeps. */
static esp_err_t rails_off(void)
{
    ESP_RETURN_ON_ERROR(bsp_i2c_init(), TAG, "i2c");
    i2c_master_dev_handle_t dev;
    const i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = BSP_I2C_ADDR_EXP,
        .scl_speed_hz = 100000,
    };
    ESP_RETURN_ON_ERROR(i2c_master_bus_add_device(bsp_i2c_get_handle(), &cfg, &dev), TAG, "expander");
    const uint8_t out[] = { EXP_REG_OUTPUT, 0x00 };
    const uint8_t dir[] = { EXP_REG_CONFIG, (uint8_t)((1u << BSP_EXP_SD_DET) | (1u << BSP_EXP_GPS_RST) |
                                                      (1u << BSP_EXP_M1421_RESET)) };
    esp_err_t err = i2c_master_transmit(dev, out, sizeof(out), 100);
    if (err == ESP_OK) {
        err = i2c_master_transmit(dev, dir, sizeof(dir), 100);
    }
    i2c_master_bus_rm_device(dev);
    return err;
}

void bsp_sleep_release_holds(void)
{
    gpio_hold_dis(BSP_COPRO_RESET);
}

esp_err_t bsp_sleep(bool wake_on_rtc)
{
    sleep_button_init();
    while (gpio_get_level(BSP_SLEEP_BUTTON) == 0) {     /* level wake-up: wait for release first */
        vTaskDelay(pdMS_TO_TICKS(20));
    }
    vTaskDelay(pdMS_TO_TICKS(50));                         /* debounce */

    if (rails_off() != ESP_OK) {
        ESP_LOGW(TAG, "expander not answering: switched rails left as they are");
    }

    /* C5: hold CHIP_PU low (open drain) through deep sleep; bsp_sleep_release_holds() after wake-up */
    gpio_set_direction(BSP_COPRO_RESET, GPIO_MODE_OUTPUT_OD);
    gpio_set_level(BSP_COPRO_RESET, 0);
    gpio_hold_en(BSP_COPRO_RESET);

    uint64_t mask = 1ULL << BSP_SLEEP_BUTTON;
    if (wake_on_rtc) {
        mask |= 1ULL << BSP_RTC_INT;                       /* DS3231M INT/SQW, open drain, active low */
    }
    ESP_RETURN_ON_ERROR(esp_sleep_enable_ext1_wakeup_io(mask, ESP_EXT1_WAKEUP_ANY_LOW), TAG, "ext1");
    ESP_LOGI(TAG, "deep sleep: press SLEEP/WAKE to wake");
    esp_deep_sleep_start();
    return ESP_FAIL;                                       /* not reached */
}
