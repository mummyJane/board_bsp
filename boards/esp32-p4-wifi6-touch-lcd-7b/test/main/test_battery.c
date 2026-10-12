/*
 * Batteries on the reference board (two different ones):
 *   "BAT"     - main 1S Li-ion on J4, charged by the ETA6098, measured on GPIO20 (1/3 divider)
 *   "RTC BAT" - CR1220-size coin cell BAT1 on the P4 VDD_BAT pin (RTC / LP domain backup);
 *               it has no ADC, so the test checks whether RTC memory and the clock survive
 *               a full power-off (needs CONFIG_ESP_VBAT_INIT_AUTO).
 */
#include <stdio.h>
#include <sys/time.h>
#include <time.h>
#include "unity.h"
#include "esp_attr.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "sdkconfig.h"
#include "bsp/bsp.h"
#if CONFIG_ESP_VBAT_INIT_AUTO
#include "esp_vbat.h"
#endif

TEST_CASE("Main battery voltage (BAT on GPIO20)", "[battery]")
{
    /* Sample for 2 s: with no battery fitted the ETA6098 keeps probing the empty
     * connector, so the BAT net pulses between ~0 and ~4.2 V. A real cell is steady. */
    int mn = 100000, mx = 0, sum = 0;
    const int n = 20;
    for (int i = 0; i < n; i++) {
        int v = 0;
        TEST_ASSERT_EQUAL(ESP_OK, bsp_battery_voltage_mv(&v));
        mn = v < mn ? v : mn;
        mx = v > mx ? v : mx;
        sum += v;
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    int mv = sum / n;
    printf("BAT = %d mV average (min %d, max %d over 2 s)\n", mv, mn, mx);
    if (mx - mn > 500) {
        printf("-> unstable: NO battery fitted (charger output cycling on the empty connector)\n");
    } else if (mv < 1000) {
        printf("-> no battery connected (BAT net near 0 V)\n");
    } else if (mv < 3000) {
        printf("-> battery very low / deeply discharged, or no battery with the charger idle\n");
    } else if (mv <= 4350) {
        printf("-> battery present, or charger output with no battery (about 4.2 V) - unplug USB to tell\n");
    } else {
        printf("-> above a Li-ion maximum: check the divider / ADC calibration\n");
    }
    TEST_ASSERT_INT_WITHIN(5000, 2500, mv);   /* sane range 0..7.5 V */
}

#define RTC_MAGIC   0x52544342u   /* "RTCB" */

typedef struct {
    uint32_t magic;
    int64_t epoch;      /* wall-clock seconds when the marker was written */
    uint32_t runs;
} rtc_marker_t;

static RTC_NOINIT_ATTR rtc_marker_t s_marker;

static const char *vbat_state(void)
{
#if CONFIG_ESP_VBAT_INIT_AUTO
    switch (esp_vbat_get_battery_state()) {
    case ESP_VBAT_STATE_NORMAL: return "NORMAL";
    case ESP_VBAT_STATE_CHARGING: return "CHARGING";
    case ESP_VBAT_STATE_LOWBATTERY: return "LOW BATTERY (replace the coin cell)";
    }
    return "?";
#else
    return "unknown (CONFIG_ESP_VBAT_INIT_AUTO is off)";
#endif
}

TEST_CASE("RTC coin cell: RTC memory + clock survive power-off", "[rtc_battery]")
{
    printf("Reset reason: %d, VBAT state: %s\n", esp_reset_reason(), vbat_state());
    time_t now = time(NULL);

    if (s_marker.magic == RTC_MAGIC) {
        long long elapsed = (long long)now - s_marker.epoch;
        printf("RTC memory SURVIVED (marker from run %lu).\n", (unsigned long)s_marker.runs);
        if (now >= 1735689600) {   /* 2025-01-01 */
            printf("Clock SURVIVED: %lld s since the marker was written.\n", elapsed);
            printf("VERDICT: RTC backup works (if the board was fully powered off in between).\n");
        } else {
            printf("Clock was reset (time is before 2025) but RTC memory survived.\n");
            printf("VERDICT: LP memory kept, RTC time not restored.\n");
        }
        s_marker.runs++;
    } else {
        printf("No marker in RTC memory: first run, or the RTC domain lost power.\n");
        if (now < 1735689600) {
            const struct timeval tv = {.tv_sec = 1767225600};   /* 2026-01-01 00:00:00 UTC */
            settimeofday(&tv, NULL);
            now = time(NULL);
            printf("Clock set to 2026-01-01 00:00:00 UTC as a reference point.\n");
        }
        s_marker.magic = RTC_MAGIC;
        s_marker.runs = 1;
        printf("VERDICT: if this follows a power-off with a coin cell fitted, the backup did NOT hold.\n");
    }
    s_marker.epoch = now;
    printf("Marker written. Now: remove ALL power (both USB-C cables and the main battery), wait\n"
           "about 30 s, power up and run [rtc_battery] again.\n");
}
