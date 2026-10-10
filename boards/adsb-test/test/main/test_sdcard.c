#include <stdio.h>
#include <string.h>
#include "unity.h"
#include "bsp/bsp.h"

TEST_CASE("microSD mount, write, read back, unmount", "[sdcard]")
{
    printf("Needs a FAT-formatted microSD card inserted\n");
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_mount());

    const char *path = BSP_SD_MOUNT_POINT "/bsptest.txt";
    const char *msg = "board_bsp sdcard test\n";

    FILE *f = fopen(path, "w");
    TEST_ASSERT_NOT_NULL(f);
    TEST_ASSERT_EQUAL(strlen(msg), fwrite(msg, 1, strlen(msg), f));
    fclose(f);

    char buf[64] = {0};
    f = fopen(path, "r");
    TEST_ASSERT_NOT_NULL(f);
    fread(buf, 1, sizeof(buf) - 1, f);
    fclose(f);
    TEST_ASSERT_EQUAL_STRING(msg, buf);

    remove(path);
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_unmount());
}
