/*
 * GPS (u-blox MAX-M10S class) on the board's GPS UART + PPS.
 * Reference board: wire the module to header P3 (see the board README).
 * The baud rate is detected: M10 modules usually default to 38400, older ones 9600.
 */
#include <stdio.h>
#include <string.h>
#include "unity.h"
#include "driver/uart.h"
#include "driver/gpio.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "bsp/bsp.h"

#define GPS_BUF     1024

static volatile int s_pps_count;
static volatile int64_t s_pps_last_us;
static volatile int64_t s_pps_min_us = INT64_MAX;
static volatile int64_t s_pps_max_us;

static void IRAM_ATTR pps_isr(void *arg)
{
    int64_t now = esp_timer_get_time();
    if (s_pps_count > 0) {
        int64_t dt = now - s_pps_last_us;
        if (dt < s_pps_min_us) {
            s_pps_min_us = dt;
        }
        if (dt > s_pps_max_us) {
            s_pps_max_us = dt;
        }
    }
    s_pps_last_us = now;
    s_pps_count++;
}

static bool saw_nmea(int baud)
{
    uart_set_baudrate(BSP_GPS_UART_NUM, baud);
    uart_flush_input(BSP_GPS_UART_NUM);
    char buf[256] = {0};
    int n = uart_read_bytes(BSP_GPS_UART_NUM, buf, sizeof(buf) - 1, pdMS_TO_TICKS(2500));
    return n > 0 && (strstr(buf, "$GP") || strstr(buf, "$GN") || strstr(buf, "$GL") || strstr(buf, "$GA"));
}

TEST_CASE("GPS: detect baud, read NMEA, measure PPS for 30 s", "[gps]")
{
    printf("GPS UART%d TX(P4)=GPIO%d RX(P4)=GPIO%d PPS=GPIO%d\n",
           BSP_GPS_UART_NUM, BSP_GPS_TX, BSP_GPS_RX, BSP_GPS_PPS);

    const uart_config_t cfg = {
        .baud_rate = 38400,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    TEST_ASSERT_EQUAL(ESP_OK, uart_driver_install(BSP_GPS_UART_NUM, GPS_BUF * 2, 0, 0, NULL, 0));
    TEST_ASSERT_EQUAL(ESP_OK, uart_param_config(BSP_GPS_UART_NUM, &cfg));
    TEST_ASSERT_EQUAL(ESP_OK, uart_set_pin(BSP_GPS_UART_NUM, BSP_GPS_TX, BSP_GPS_RX, -1, -1));

    static const int bauds[] = {38400, 9600, 115200, 57600, 230400};
    int baud = 0;
    for (int i = 0; i < sizeof(bauds) / sizeof(bauds[0]) && !baud; i++) {
        if (saw_nmea(bauds[i])) {
            baud = bauds[i];
        }
    }
    printf("GPS baud: %d\n", baud);

    s_pps_count = 0;
    s_pps_min_us = INT64_MAX;
    s_pps_max_us = 0;
    if (BSP_GPS_PPS >= 0) {
        const gpio_config_t io = {
            .pin_bit_mask = 1ULL << BSP_GPS_PPS,
            .mode = GPIO_MODE_INPUT,
            .intr_type = GPIO_INTR_POSEDGE,
        };
        TEST_ASSERT_EQUAL(ESP_OK, gpio_config(&io));
        esp_err_t err = gpio_install_isr_service(0);
        TEST_ASSERT_TRUE(err == ESP_OK || err == ESP_ERR_INVALID_STATE);
        TEST_ASSERT_EQUAL(ESP_OK, gpio_isr_handler_add(BSP_GPS_PPS, pps_isr, NULL));
    }

    int sentences = 0;
    if (baud) {
        char line[128];
        int len = 0;
        int64_t end = esp_timer_get_time() + 30 * 1000000LL;
        while (esp_timer_get_time() < end) {
            uint8_t c;
            if (uart_read_bytes(BSP_GPS_UART_NUM, &c, 1, pdMS_TO_TICKS(100)) != 1) {
                continue;
            }
            if (c == '\n') {
                line[len] = 0;
                if (line[0] == '$') {
                    sentences++;
                    if (strstr(line, "GGA") || strstr(line, "RMC")) {
                        printf("%s\n", line);
                    }
                }
                len = 0;
            } else if (c != '\r' && len < (int)sizeof(line) - 1) {
                line[len++] = c;
            }
        }
    }

    printf("NMEA sentences: %d\n", sentences);
    if (s_pps_count > 1) {
        printf("PPS pulses: %d, interval min %lld us, max %lld us (jitter %lld us)\n",
               s_pps_count, s_pps_min_us, s_pps_max_us, s_pps_max_us - s_pps_min_us);
    } else {
        printf("PPS pulses: %d (PPS only pulses once the receiver has a time fix)\n", s_pps_count);
    }

    if (BSP_GPS_PPS >= 0) {
        gpio_isr_handler_remove(BSP_GPS_PPS);
    }
    uart_driver_delete(BSP_GPS_UART_NUM);
    TEST_ASSERT_NOT_EQUAL_MESSAGE(0, baud, "no NMEA seen: check wiring, power and that GPS TX goes to P4 RX");
    TEST_ASSERT_GREATER_THAN(10, sentences);
}
