#include <stdio.h>
#include <stdlib.h>
#include "unity.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_ops.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "bsp/bsp.h"

#define BYTES_PER_PIXEL     (BSP_LCD_BITS_PER_PIXEL / 8)

/* Fill the screen with 8 vertical colour bars, one band of rows at a time. */
static void draw_colour_bars(esp_lcd_panel_handle_t panel)
{
    static const uint8_t bars[8][3] = {
        {255, 255, 255}, {255, 255, 0}, {0, 255, 255}, {0, 255, 0},
        {255, 0, 255}, {255, 0, 0}, {0, 0, 255}, {0, 0, 0},
    };
    const int rows = 50;
    uint8_t *buf = heap_caps_malloc(BSP_LCD_H_RES * rows * BYTES_PER_PIXEL, MALLOC_CAP_DMA | MALLOC_CAP_SPIRAM);
    TEST_ASSERT_NOT_NULL(buf);

    for (int x = 0; x < BSP_LCD_H_RES; x++) {
        const uint8_t *c = bars[x * 8 / BSP_LCD_H_RES];
        for (int y = 0; y < rows; y++) {
            uint8_t *p = buf + (y * BSP_LCD_H_RES + x) * BYTES_PER_PIXEL;
#if BYTES_PER_PIXEL == 3
            p[0] = c[2];
            p[1] = c[1];
            p[2] = c[0];
#else
            uint16_t v = ((c[0] & 0xF8) << 8) | ((c[1] & 0xFC) << 3) | (c[2] >> 3);
            p[0] = v & 0xFF;
            p[1] = v >> 8;
#endif
        }
    }
    for (int y = 0; y < BSP_LCD_V_RES; y += rows) {
        TEST_ASSERT_EQUAL(ESP_OK, esp_lcd_panel_draw_bitmap(panel, 0, y, BSP_LCD_H_RES, y + rows, buf));
    }
    vTaskDelay(pdMS_TO_TICKS(100));
    free(buf);
}

TEST_CASE("display shows colour bars", "[display]")
{
    p4c_display_t disp;
    TEST_ASSERT_EQUAL(ESP_OK, bsp_display_new(&disp));
    draw_colour_bars(disp.panel);
    printf("CHECK: 8 vertical bars, white -> black, left to right\n");
    vTaskDelay(pdMS_TO_TICKS(3000));
}

TEST_CASE("backlight sweeps 100 -> 0 -> 100 %", "[display]")
{
    p4c_display_t disp;
    TEST_ASSERT_EQUAL(ESP_OK, bsp_display_new(&disp));
    printf("CHECK: backlight fades out then back in\n");
    for (int pct = 100; pct >= 0; pct -= 5) {
        TEST_ASSERT_EQUAL(ESP_OK, bsp_display_backlight_set(pct));
        vTaskDelay(pdMS_TO_TICKS(60));
    }
    for (int pct = 0; pct <= 100; pct += 5) {
        TEST_ASSERT_EQUAL(ESP_OK, bsp_display_backlight_set(pct));
        vTaskDelay(pdMS_TO_TICKS(60));
    }
}
