#include "p4_board_common.h"
#include "driver/ledc.h"
#include "esp_check.h"

static const char *TAG = "p4c_bl";

#define BL_LEDC_MODE        LEDC_LOW_SPEED_MODE
#define BL_LEDC_TIMER       LEDC_TIMER_0
#define BL_LEDC_CHANNEL     LEDC_CHANNEL_0
#define BL_LEDC_RES         LEDC_TIMER_10_BIT
#define BL_DUTY_MAX         ((1 << 10) - 1)

static bool s_inverted;
static bool s_ready;

esp_err_t p4c_backlight_init(const p4c_backlight_cfg_t *cfg)
{
    ESP_RETURN_ON_FALSE(cfg && cfg->gpio >= 0, ESP_ERR_INVALID_ARG, TAG, "bad args");

    const ledc_timer_config_t timer = {
        .speed_mode = BL_LEDC_MODE,
        .timer_num = BL_LEDC_TIMER,
        .duty_resolution = BL_LEDC_RES,
        .freq_hz = cfg->freq_hz ? cfg->freq_hz : 20000,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), TAG, "timer");

    const ledc_channel_config_t channel = {
        .gpio_num = cfg->gpio,
        .speed_mode = BL_LEDC_MODE,
        .channel = BL_LEDC_CHANNEL,
        .timer_sel = BL_LEDC_TIMER,
        .duty = 0,
    };
    ESP_RETURN_ON_ERROR(ledc_channel_config(&channel), TAG, "channel");

    s_inverted = cfg->inverted;
    s_ready = true;
    return p4c_backlight_set(100);
}

esp_err_t p4c_backlight_set(int percent)
{
    ESP_RETURN_ON_FALSE(s_ready, ESP_ERR_INVALID_STATE, TAG, "not initialised");
    if (percent < 0) {
        percent = 0;
    } else if (percent > 100) {
        percent = 100;
    }
    uint32_t duty = (uint32_t)percent * BL_DUTY_MAX / 100;
    if (s_inverted) {
        duty = BL_DUTY_MAX - duty;
    }
    ESP_RETURN_ON_ERROR(ledc_set_duty(BL_LEDC_MODE, BL_LEDC_CHANNEL, duty), TAG, "duty");
    return ledc_update_duty(BL_LEDC_MODE, BL_LEDC_CHANNEL);
}
