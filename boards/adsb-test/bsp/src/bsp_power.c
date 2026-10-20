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

/* PAC1954: CTRL (0x01, 16 bit) SAMPLE_MODE[15:12] = 0b1111 sleep (5 uA instead of ~0.4 mA); ALERT pin bits
 * [11:8] kept at their power-on value 0b0111. A CTRL change takes effect after a REFRESH (0x00) command. */
#define PAC_REG_REFRESH 0x00
#define PAC_REG_CTRL    0x01
#define PAC_CTRL_ACTIVE 0x07    /* high byte: 1024 sps adaptive (power-on default) */
#define PAC_CTRL_SLEEP  0xF7

/* GT911: command register 0x8040, 0x05 = screen off / sleep. INT must be low while the command is sent and
 * stay low while asleep (a high pulse on INT wakes it). Address 0x5D or 0x14, latched at its reset. */
#define GT911_REG_CMD   0x8040
#define GT911_CMD_SLEEP 0x05

static esp_err_t i2c_write(uint8_t addr, const uint8_t *buf, size_t len)
{
    ESP_RETURN_ON_ERROR(bsp_i2c_init(), TAG, "i2c");
    i2c_master_dev_handle_t dev;
    const i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = addr,
        .scl_speed_hz = 100000,
    };
    ESP_RETURN_ON_ERROR(i2c_master_bus_add_device(bsp_i2c_get_handle(), &cfg, &dev), TAG, "add 0x%02x", addr);
    esp_err_t err = i2c_master_transmit(dev, buf, len, 100);
    i2c_master_bus_rm_device(dev);
    return err;
}

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
    const uint8_t out[] = { EXP_REG_OUTPUT, 0x00 };
    const uint8_t dir[] = { EXP_REG_CONFIG, (uint8_t)((1u << BSP_EXP_SD_DET) | (1u << BSP_EXP_GPS_RST) |
                                                      (1u << BSP_EXP_M1421_RESET)) };
    ESP_RETURN_ON_ERROR(i2c_write(BSP_I2C_ADDR_EXP, out, sizeof(out)), TAG, "expander out");
    return i2c_write(BSP_I2C_ADDR_EXP, dir, sizeof(dir));
}

esp_err_t bsp_power_monitors_sleep(bool sleep)
{
    static const uint8_t addrs[] = { BSP_I2C_ADDR_PM1, BSP_I2C_ADDR_PM2, BSP_I2C_ADDR_PM3 };
    const uint8_t ctrl[] = { PAC_REG_CTRL, sleep ? PAC_CTRL_SLEEP : PAC_CTRL_ACTIVE, 0x00 };
    const uint8_t refresh[] = { PAC_REG_REFRESH };
    esp_err_t ret = ESP_OK;
    for (int i = 0; i < 3; i++) {
        esp_err_t err = i2c_write(addrs[i], ctrl, sizeof(ctrl));
        if (err == ESP_OK) {
            err = i2c_write(addrs[i], refresh, sizeof(refresh));
        }
        if (err != ESP_OK) {
            ESP_LOGW(TAG, "PAC1954 0x%02x: %s", addrs[i], esp_err_to_name(err));
            ret = err;
        }
    }
    return ret;
}

/* GT911 to sleep: INT low (held through deep sleep), then the sleep command at whichever address answers.
 * It is powered from 3V3, which stays on: switching it off would let it clamp the shared I2C bus. */
static void touch_sleep(void)
{
    gpio_set_direction(BSP_TOUCH_INT, GPIO_MODE_OUTPUT);
    gpio_set_level(BSP_TOUCH_INT, 0);
    vTaskDelay(pdMS_TO_TICKS(1));
    const uint8_t cmd[] = { GT911_REG_CMD >> 8, GT911_REG_CMD & 0xFF, GT911_CMD_SLEEP };
    if (i2c_write(0x5D, cmd, sizeof(cmd)) != ESP_OK && i2c_write(0x14, cmd, sizeof(cmd)) != ESP_OK) {
        ESP_LOGW(TAG, "GT911 not answering");
    }
    gpio_hold_en(BSP_TOUCH_INT);
}

void bsp_sleep_release_holds(void)
{
    gpio_hold_dis(BSP_COPRO_RESET);
    gpio_hold_dis(BSP_TOUCH_INT);       /* the touch driver's reset sequence wakes the GT911 */
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
    bsp_power_monitors_sleep(true);
    touch_sleep();

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

void bsp_power_after_wake(void)
{
    bsp_sleep_release_holds();
    if (esp_sleep_get_wakeup_causes() & (1u << ESP_SLEEP_WAKEUP_EXT1)) {
        bsp_power_monitors_sleep(false);                   /* the PAC1954s stay asleep until told otherwise */
    }
}
