#include <stdio.h>
#include "unity.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "bsp/bsp.h"

TEST_CASE("touch reports points for 10 s", "[touch]")
{
    esp_lcd_touch_handle_t tp = NULL;
    TEST_ASSERT_EQUAL(ESP_OK, bsp_touch_new(&tp));
    printf("CHECK: touch the screen; coordinates are printed for 10 s\n");

    int reports = 0;
    for (int i = 0; i < 200; i++) {
        esp_lcd_touch_read_data(tp);
        esp_lcd_touch_point_data_t pts[5];
        uint8_t n = 0;
        if (esp_lcd_touch_get_data(tp, pts, &n, 5) == ESP_OK && n > 0) {
            printf("touch: x=%u y=%u (points %u)\n", pts[0].x, pts[0].y, n);
            reports++;
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
    printf("%d touch reports\n", reports);
    esp_lcd_touch_del(tp);
}
