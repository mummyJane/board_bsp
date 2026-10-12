/*
 * GPS basic comms check over UBX (u-blox binary protocol): proves the UART
 * wiring and the module without needing a fix or PPS.
 *   UBX-MON-VER  (0x0A 0x04): firmware / hardware / module name
 *   UBX-MON-RF   (0x0A 0x38): antenna status + power, noise, jamming
 *   UBX-NAV-PVT  (0x01 0x07): fix type, satellites, time validity
 */
#include <stdio.h>
#include <string.h>
#include "unity.h"
#include "driver/uart.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "bsp/bsp.h"

#define UBX_MAX     1024

static void ubx_send_poll(uint8_t cls, uint8_t id)
{
    uint8_t f[8] = {0xB5, 0x62, cls, id, 0, 0, 0, 0};
    uint8_t a = 0, b = 0;
    for (int i = 2; i < 6; i++) {
        a += f[i];
        b += a;
    }
    f[6] = a;
    f[7] = b;
    uart_write_bytes(BSP_GPS_UART_NUM, f, sizeof(f));
}

/* Read the UART stream (NMEA is skipped) until a valid UBX frame with this
 * class/id arrives. Returns payload length, or -1 on timeout. */
static int ubx_wait(uint8_t cls, uint8_t id, uint8_t *payload, int max, int timeout_ms)
{
    int64_t end = esp_timer_get_time() + timeout_ms * 1000LL;
    int state = 0, len = 0, pos = 0;
    uint8_t hdr[4], a = 0, b = 0, ck_a = 0;
    while (esp_timer_get_time() < end) {
        uint8_t c;
        if (uart_read_bytes(BSP_GPS_UART_NUM, &c, 1, pdMS_TO_TICKS(20)) != 1) {
            continue;
        }
        switch (state) {
        case 0: state = (c == 0xB5) ? 1 : 0; break;
        case 1: state = (c == 0x62) ? 2 : 0; pos = 0; a = b = 0; break;
        case 2:
            hdr[pos++] = c;
            a += c;
            b += a;
            if (pos == 4) {
                len = hdr[2] | (hdr[3] << 8);
                pos = 0;
                state = (len > UBX_MAX) ? 0 : (len ? 3 : 4);
            }
            break;
        case 3:
            if (pos < max) {
                payload[pos] = c;
            }
            pos++;
            a += c;
            b += a;
            if (pos == len) {
                state = 4;
            }
            break;
        case 4: ck_a = c; state = 5; break;
        case 5:
            state = 0;
            if (ck_a == a && c == b && hdr[0] == cls && hdr[1] == id) {
                return len;
            }
            break;
        }
    }
    return -1;
}

static int detect_baud(void)
{
    static const int bauds[] = {38400, 9600, 115200, 57600, 230400};
    uint8_t buf[UBX_MAX];
    for (int i = 0; i < sizeof(bauds) / sizeof(bauds[0]); i++) {
        uart_set_baudrate(BSP_GPS_UART_NUM, bauds[i]);
        uart_flush_input(BSP_GPS_UART_NUM);
        ubx_send_poll(0x0A, 0x04);
        if (ubx_wait(0x0A, 0x04, buf, sizeof(buf), 1500) > 0) {
            return bauds[i];
        }
    }
    return 0;
}

static const char *ant_status(uint8_t s)
{
    static const char *n[] = {"INIT", "DONTKNOW", "OK", "SHORT", "OPEN"};
    return s < 5 ? n[s] : "?";
}

static const char *ant_power(uint8_t p)
{
    static const char *n[] = {"OFF", "ON", "DONTKNOW"};
    return p < 3 ? n[p] : "?";
}

static const char *fix_name(uint8_t f)
{
    static const char *n[] = {"no fix", "dead reckoning", "2D", "3D", "GNSS+DR", "time only"};
    return f < 6 ? n[f] : "?";
}

TEST_CASE("GPS: UBX comms check (version, antenna, fix status)", "[gps]")
{
    printf("GPS UART%d: P4 TX=GPIO%d -> GPS RX, GPS TX -> P4 RX=GPIO%d\n",
           BSP_GPS_UART_NUM, BSP_GPS_TX, BSP_GPS_RX);
    const uart_config_t cfg = {
        .baud_rate = 38400,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    TEST_ASSERT_EQUAL(ESP_OK, uart_driver_install(BSP_GPS_UART_NUM, 4096, 0, 0, NULL, 0));
    TEST_ASSERT_EQUAL(ESP_OK, uart_param_config(BSP_GPS_UART_NUM, &cfg));
    TEST_ASSERT_EQUAL(ESP_OK, uart_set_pin(BSP_GPS_UART_NUM, BSP_GPS_TX, BSP_GPS_RX, -1, -1));

    int baud = detect_baud();
    printf("UBX reply at baud: %d\n", baud);
    if (!baud) {
        /* Tell "no data at all" apart from "data but no UBX reply". */
        uint8_t raw[128] = {0};
        int got = 0;
        static const int bauds[] = {38400, 9600, 115200};
        for (int i = 0; i < 3 && got <= 0; i++) {
            uart_set_baudrate(BSP_GPS_UART_NUM, bauds[i]);
            uart_flush_input(BSP_GPS_UART_NUM);
            got = uart_read_bytes(BSP_GPS_UART_NUM, raw, sizeof(raw) - 1, pdMS_TO_TICKS(1500));
        }
        printf(got > 0 ? "Bytes are arriving on GPS TX -> P4 RX, but no UBX reply: check P4 TX -> GPS RX\n"
                       : "Nothing at all on GPS TX -> P4 RX: check power, GND and the TX/RX wiring\n");
        uart_driver_delete(BSP_GPS_UART_NUM);
        TEST_FAIL_MESSAGE("no UBX reply from the GPS");
    }

    uint8_t p[UBX_MAX];
    ubx_send_poll(0x0A, 0x04);
    int n = ubx_wait(0x0A, 0x04, p, sizeof(p), 1500);
    TEST_ASSERT_GREATER_OR_EQUAL(40, n);
    printf("MON-VER  software: %.30s\n", (char *)p);
    printf("MON-VER  hardware: %.10s\n", (char *)p + 30);
    for (int off = 40; off + 30 <= n; off += 30) {
        printf("MON-VER  ext     : %.30s\n", (char *)p + off);
    }

    ubx_send_poll(0x0A, 0x38);
    n = ubx_wait(0x0A, 0x38, p, sizeof(p), 1500);
    if (n >= 4 + 24) {
        int blocks = p[1];
        for (int i = 0; i < blocks && 4 + (i + 1) * 24 <= n; i++) {
            const uint8_t *blk = p + 4 + i * 24;
            uint16_t noise = blk[12] | (blk[13] << 8);
            uint16_t agc = blk[14] | (blk[15] << 8);
            printf("MON-RF   block %u: antenna %s, antenna power %s, jamming state %u, noise %u, AGC %u\n",
                   blk[0], ant_status(blk[2]), ant_power(blk[3]), blk[1] & 0x03, noise, agc);
        }
    } else {
        printf("MON-RF   no reply (older firmware may not support it)\n");
    }

    ubx_send_poll(0x01, 0x07);
    n = ubx_wait(0x01, 0x07, p, sizeof(p), 2500);
    if (n >= 92) {
        uint16_t year = p[4] | (p[5] << 8);
        printf("NAV-PVT  fix: %s, satellites used: %u, time %04u-%02u-%02u %02u:%02u:%02u UTC (valid flags 0x%02x)\n",
               fix_name(p[20]), p[23], year, p[6], p[7], p[8], p[9], p[10], p[11]);
    } else {
        printf("NAV-PVT  no reply\n");
    }

    uart_driver_delete(BSP_GPS_UART_NUM);
}
