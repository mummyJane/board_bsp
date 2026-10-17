#include <stdio.h>
#include "unity.h"
#include "esp_sleep.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "bsp/bsp.h"

/* Manual: press SLEEP/WAKE within 10 s -> rails off + deep sleep; press again -> the board restarts and the
 * menu comes back (check the wake-up cause line). Measure VSYS current on PM1 CH3 / a meter while asleep. */
TEST_CASE("SLEEP/WAKE button: deep sleep and wake", "[sleep][manual]")
{
    printf("Woke by SLEEP/WAKE last time: %s\n",
           (esp_sleep_get_wakeup_causes() & (1u << ESP_SLEEP_WAKEUP_EXT1)) ? "yes" : "no");
    printf("Press SLEEP/WAKE within 10 s...\n");
    for (int i = 0; i < 500 && !bsp_sleep_button_pressed(); i++) {
        vTaskDelay(pdMS_TO_TICKS(20));
    }
    if (!bsp_sleep_button_pressed()) {
        TEST_IGNORE_MESSAGE("button not pressed");
    }
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sleep(false));       /* only returns on error */
}
