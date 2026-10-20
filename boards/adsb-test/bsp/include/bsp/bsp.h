#pragma once

#include <stdbool.h>
#include <time.h>
#include "esp_err.h"
#include "driver/i2c_master.h"
#include "esp_lcd_touch.h"
#include "p4_board_common.h"
#include "bsp/board_pins.h"

#ifdef __cplusplus
extern "C" {
#endif

#define BSP_SD_MOUNT_POINT      "/sdcard"

/** Initialise board-level resources common to all applications. Safe to call more than once. */
esp_err_t bsp_init(void);

/** Return the board name string. */
const char *bsp_board_name(void);

/** Shared I2C bus (touch, PD sink, charger, power monitors, expander). Created on first call. */
esp_err_t bsp_i2c_init(void);
i2c_master_bus_handle_t bsp_i2c_get_handle(void);

/** Display: EK79007 1024x600 over MIPI-DSI, plus backlight. Created once, then cached. */
esp_err_t bsp_display_new(p4c_display_t *out);
esp_err_t bsp_display_backlight_set(int percent);

/** GT911 touch on the shared I2C bus. */
esp_err_t bsp_touch_new(esp_lcd_touch_handle_t *out);

/** microSD (4-bit SDMMC slot 0) mounted at BSP_SD_MOUNT_POINT. */
esp_err_t bsp_sdcard_mount(void);
esp_err_t bsp_sdcard_unmount(void);

/** Format the microSD card as FAT32 (ERASES IT) and leave it mounted. */
esp_err_t bsp_sdcard_format(void);

/** DS3231M RTC on the shared I2C bus (on VBACKUP, keeps time with the power switch off).
 *  bsp_rtc_init() returns ESP_ERR_NOT_FOUND if nothing answers at BSP_I2C_ADDR_RTC. */
esp_err_t bsp_rtc_init(void);
/** Read the time (24 h, local as stored). *valid is false if the oscillator stopped since the last set. */
esp_err_t bsp_rtc_get_time(struct tm *t, bool *valid);
/** Set the time (tm_year 100..299 = 2000..2199) and clear the oscillator-stop flag. */
esp_err_t bsp_rtc_set_time(const struct tm *t);
/** DS3231M die temperature, 0.25 C steps. */
esp_err_t bsp_rtc_get_temperature(float *celsius);

/** SLEEP/WAKE button (SW603, GPIO12): true while pressed. */
bool bsp_sleep_button_pressed(void);
/** Sleep: switched rails off (LCD, Ethernet, GPS, m1421, USB-A via the expander), PAC1954 monitors and GT911
 *  touch to sleep over I2C, C5 held in reset, P4 into deep sleep. Waits for the button to be released first.
 *  SLEEP/WAKE wakes it (also the DS3231M alarm if wake_on_rtc); waking is a reset. Only returns on error.
 *  VSYS, charger, bucks, 3V3/3V3_PERIPH and the P4 LP domain stay on; the POWER switch is the full off. */
esp_err_t bsp_sleep(bool wake_on_rtc);
/** PAC1954 monitors into (true) or out of (false) their 5 uA sleep mode. */
esp_err_t bsp_power_monitors_sleep(bool sleep);
/** Release the pin holds left by bsp_sleep() (C5 reset, touch INT). */
void bsp_sleep_release_holds(void);
/** After a SLEEP/WAKE wake-up: release the holds and wake the monitors (called by bsp_init()). */
void bsp_power_after_wake(void);

#ifdef __cplusplus
}
#endif
