/* DS3231M real-time clock on the shared I2C bus (ADSB_Test Q27: the WT01P4C5-S1 module has no P4 VBAT,
 * so wall-clock time is kept here, on VBACKUP). Register map: DS3231M datasheet, "Timekeeping registers". */
#include "esp_check.h"
#include "bsp/bsp.h"

static const char *TAG = "bsp_rtc";
static i2c_master_dev_handle_t s_rtc;

#define REG_SECONDS 0x00
#define REG_STATUS  0x0F
#define REG_TEMP    0x11
#define STATUS_OSF  0x80    /* oscillator stopped: time not valid */

static uint8_t bcd2bin(uint8_t v) { return (v >> 4) * 10 + (v & 0x0F); }
static uint8_t bin2bcd(int v) { return (uint8_t)(((v / 10) << 4) | (v % 10)); }

static esp_err_t rd(uint8_t reg, uint8_t *buf, size_t len)
{
    return i2c_master_transmit_receive(s_rtc, &reg, 1, buf, len, 100);
}

esp_err_t bsp_rtc_init(void)
{
    if (s_rtc) {
        return ESP_OK;
    }
    ESP_RETURN_ON_ERROR(bsp_i2c_init(), TAG, "i2c");
    i2c_master_bus_handle_t bus = bsp_i2c_get_handle();
    if (p4c_i2c_probe(bus, BSP_I2C_ADDR_RTC) != ESP_OK) {
        return ESP_ERR_NOT_FOUND;
    }
    const i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = BSP_I2C_ADDR_RTC,
        .scl_speed_hz = 400000,
    };
    return i2c_master_bus_add_device(bus, &cfg, &s_rtc);
}

esp_err_t bsp_rtc_get_time(struct tm *t, bool *valid)
{
    ESP_RETURN_ON_FALSE(s_rtc && t, ESP_ERR_INVALID_STATE, TAG, "not initialised");
    uint8_t r[7], st;
    ESP_RETURN_ON_ERROR(rd(REG_SECONDS, r, sizeof(r)), TAG, "read time");
    ESP_RETURN_ON_ERROR(rd(REG_STATUS, &st, 1), TAG, "read status");
    *t = (struct tm) {
        .tm_sec = bcd2bin(r[0] & 0x7F),
        .tm_min = bcd2bin(r[1] & 0x7F),
        .tm_hour = (r[2] & 0x40) ? (bcd2bin(r[2] & 0x1F) % 12 + ((r[2] & 0x20) ? 12 : 0)) : bcd2bin(r[2] & 0x3F),
        .tm_wday = (r[3] & 0x07) - 1,
        .tm_mday = bcd2bin(r[4] & 0x3F),
        .tm_mon = bcd2bin(r[5] & 0x1F) - 1,
        .tm_year = 100 + bcd2bin(r[6]) + ((r[5] & 0x80) ? 100 : 0),
    };
    if (valid) {
        *valid = !(st & STATUS_OSF);
    }
    return ESP_OK;
}

esp_err_t bsp_rtc_set_time(const struct tm *t)
{
    ESP_RETURN_ON_FALSE(s_rtc && t, ESP_ERR_INVALID_STATE, TAG, "not initialised");
    int year = t->tm_year - 100;    /* 2000-based; bit 7 of the month register = century */
    ESP_RETURN_ON_FALSE(year >= 0 && year < 200, ESP_ERR_INVALID_ARG, TAG, "year out of range");
    uint8_t w[8] = {
        REG_SECONDS, bin2bcd(t->tm_sec), bin2bcd(t->tm_min), bin2bcd(t->tm_hour),   /* 24-hour mode */
        (uint8_t)(t->tm_wday + 1), bin2bcd(t->tm_mday),
        (uint8_t)(bin2bcd(t->tm_mon + 1) | (year >= 100 ? 0x80 : 0)), bin2bcd(year % 100),
    };
    ESP_RETURN_ON_ERROR(i2c_master_transmit(s_rtc, w, sizeof(w), 100), TAG, "write time");
    uint8_t st;
    ESP_RETURN_ON_ERROR(rd(REG_STATUS, &st, 1), TAG, "read status");
    uint8_t clr[2] = { REG_STATUS, (uint8_t)(st & ~STATUS_OSF) };
    return i2c_master_transmit(s_rtc, clr, sizeof(clr), 100);
}

esp_err_t bsp_rtc_get_temperature(float *celsius)
{
    ESP_RETURN_ON_FALSE(s_rtc && celsius, ESP_ERR_INVALID_STATE, TAG, "not initialised");
    uint8_t r[2];
    ESP_RETURN_ON_ERROR(rd(REG_TEMP, r, sizeof(r)), TAG, "read temp");
    *celsius = (int8_t)r[0] + (r[1] >> 6) * 0.25f;
    return ESP_OK;
}
