#include <stdio.h>
#include "unity.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "bsp/bsp.h"

/* DS3231M external RTC. On the reference board, wire a DS3231M breakout to the I2C header
 * (GPIO7 SDA / GPIO8 SCL, 3V3, GND); without one the test is skipped. */
TEST_CASE("DS3231M RTC keeps time", "[rtc_ext]")
{
    esp_err_t err = bsp_rtc_init();
    if (err == ESP_ERR_NOT_FOUND) {
        TEST_IGNORE_MESSAGE("no DS3231M at 0x68 (not fitted)");
    }
    TEST_ASSERT_EQUAL(ESP_OK, err);

    struct tm t;
    bool valid;
    TEST_ASSERT_EQUAL(ESP_OK, bsp_rtc_get_time(&t, &valid));
    printf("RTC: %04d-%02d-%02d %02d:%02d:%02d (%s)\n", t.tm_year + 1900, t.tm_mon + 1, t.tm_mday,
           t.tm_hour, t.tm_min, t.tm_sec, valid ? "valid" : "oscillator stopped since last set");
    if (!valid) {
        /* Lost power with no backup: set a known time so the next power-off test can check retention */
        struct tm set = { .tm_year = 126, .tm_mon = 0, .tm_mday = 1, .tm_hour = 0, .tm_min = 0, .tm_sec = 0, .tm_wday = 4 };
        TEST_ASSERT_EQUAL(ESP_OK, bsp_rtc_set_time(&set));
        printf("RTC set to 2026-01-01 00:00:00\n");
    }

    float temp;
    TEST_ASSERT_EQUAL(ESP_OK, bsp_rtc_get_temperature(&temp));
    printf("RTC temperature: %.2f C\n", temp);
    TEST_ASSERT_FLOAT_WITHIN(60.0f, 25.0f, temp);

    struct tm a, b;
    TEST_ASSERT_EQUAL(ESP_OK, bsp_rtc_get_time(&a, &valid));
    TEST_ASSERT_TRUE(valid);
    vTaskDelay(pdMS_TO_TICKS(2100));
    TEST_ASSERT_EQUAL(ESP_OK, bsp_rtc_get_time(&b, NULL));
    int dt = (int)difftime(mktime(&b), mktime(&a));
    printf("RTC advanced %d s in 2.1 s\n", dt);
    TEST_ASSERT_INT_WITHIN(1, 2, dt);
}
