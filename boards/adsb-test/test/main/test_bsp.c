#include <string.h>
#include "unity.h"
#include "bsp/bsp.h"

TEST_CASE("bsp_init succeeds and is idempotent", "[bsp]")
{
    TEST_ASSERT_EQUAL(ESP_OK, bsp_init());
    TEST_ASSERT_EQUAL(ESP_OK, bsp_init());
}

TEST_CASE("board name is set", "[bsp]")
{
    TEST_ASSERT_EQUAL_STRING(BSP_BOARD_NAME, bsp_board_name());
}
