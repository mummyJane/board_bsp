#include <stdio.h>
#include <string.h>
#include "unity.h"
#include "bsp/bsp.h"

TEST_CASE("microSD mount, write, read back, unmount", "[sdcard]")
{
    printf("Needs a FAT/FAT32-formatted microSD card inserted\n");
    esp_err_t err = bsp_sdcard_mount();
    if (err != ESP_OK) {
        printf("Mount failed (%s). Cards over 32 GB usually ship as exFAT, which ESP-IDF 6.1's\n"
               "FatFs doesn't support. Reformat as FAT32, or run the [sdcard_format] test\n"
               "(ERASES THE CARD).\n", esp_err_to_name(err));
    }
    TEST_ASSERT_EQUAL(ESP_OK, err);

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

/* [ignore] keeps this out of "run all" ('*'). Run it only by name or tag. */
TEST_CASE("microSD FORMAT as FAT32 - ERASES THE CARD", "[sdcard_format][ignore]")
{
    printf("Formatting the microSD card as FAT32. All data on it will be lost.\n");
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_format());
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_unmount());
}
