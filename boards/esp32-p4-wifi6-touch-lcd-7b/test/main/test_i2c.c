#include <stdio.h>
#include "unity.h"
#include "bsp/bsp.h"

TEST_CASE("I2C bus scan finds devices", "[i2c]")
{
    TEST_ASSERT_EQUAL(ESP_OK, bsp_i2c_init());
    i2c_master_bus_handle_t bus = bsp_i2c_get_handle();
    TEST_ASSERT_NOT_NULL(bus);

    int found = 0;
    printf("I2C devices:");
    for (uint8_t addr = 0x08; addr < 0x78; addr++) {
        if (p4c_i2c_probe(bus, addr) == ESP_OK) {
            printf(" 0x%02x", addr);
            found++;
        }
    }
    printf("\n");
    TEST_ASSERT_GREATER_THAN(0, found);
}
