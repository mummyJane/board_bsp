#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "unity.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"
#include "esp_vfs_fat.h"
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

#define BIG_FILE_BYTES  (4 * 1024 * 1024)
#define CHUNK_BYTES     (32 * 1024)

static uint32_t pattern_word(uint32_t i)
{
    /* xorshift-style mix of the word index: deterministic, not repeating per chunk */
    uint32_t x = i * 2654435761u + 0x9E3779B9u;
    x ^= x >> 15;
    x *= 0x85EBCA6Bu;
    x ^= x >> 13;
    return x;
}

TEST_CASE("microSD 4 MiB write + read-back verify, speed, free space", "[sdcard]")
{
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_mount());

    uint64_t total = 0, free_bytes = 0;
    if (esp_vfs_fat_info(BSP_SD_MOUNT_POINT, &total, &free_bytes) == ESP_OK) {
        printf("FAT volume: %llu MB total, %llu MB free\n", total >> 20, free_bytes >> 20);
    }

    const char *path = BSP_SD_MOUNT_POINT "/bsp_big.bin";
    uint32_t *buf = heap_caps_malloc(CHUNK_BYTES, MALLOC_CAP_DMA);
    TEST_ASSERT_NOT_NULL(buf);
    const int words = CHUNK_BYTES / 4;

    FILE *f = fopen(path, "wb");
    TEST_ASSERT_NOT_NULL(f);
    int64_t t0 = esp_timer_get_time();
    for (int c = 0; c < BIG_FILE_BYTES / CHUNK_BYTES; c++) {
        for (int i = 0; i < words; i++) {
            buf[i] = pattern_word(c * words + i);
        }
        TEST_ASSERT_EQUAL(CHUNK_BYTES, fwrite(buf, 1, CHUNK_BYTES, f));
    }
    fclose(f);
    int64_t t1 = esp_timer_get_time();

    f = fopen(path, "rb");
    TEST_ASSERT_NOT_NULL(f);
    int bad = 0;
    for (int c = 0; c < BIG_FILE_BYTES / CHUNK_BYTES; c++) {
        TEST_ASSERT_EQUAL(CHUNK_BYTES, fread(buf, 1, CHUNK_BYTES, f));
        for (int i = 0; i < words; i++) {
            if (buf[i] != pattern_word(c * words + i) && bad++ < 5) {
                printf("MISMATCH at byte %d\n", (c * words + i) * 4);
            }
        }
    }
    fclose(f);
    int64_t t2 = esp_timer_get_time();
    free(buf);
    remove(path);

    printf("4 MiB: write %.2f MB/s, read+verify %.2f MB/s, %d bad words\n",
           BIG_FILE_BYTES / 1048576.0 / ((t1 - t0) / 1e6),
           BIG_FILE_BYTES / 1048576.0 / ((t2 - t1) / 1e6), bad);
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_unmount());
    TEST_ASSERT_EQUAL(0, bad);
}

TEST_CASE("microSD persistence counter (run, power-cycle, run again)", "[sdcard]")
{
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_mount());
    const char *path = BSP_SD_MOUNT_POINT "/bsp_persist.txt";
    int count = 0;
    FILE *f = fopen(path, "r");
    if (f) {
        fscanf(f, "%d", &count);
        fclose(f);
        printf("Previous counter value on the card: %d\n", count);
    } else {
        printf("No counter file yet (first run on this card)\n");
    }
    f = fopen(path, "w");
    TEST_ASSERT_NOT_NULL(f);
    fprintf(f, "%d\n", count + 1);
    fclose(f);
    printf("Counter now %d. Power-cycle the board and run this again: it should print %d.\n",
           count + 1, count + 1);
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_unmount());
}

/* [ignore] keeps this out of "run all" ('*'). Run it only by name or tag. */
TEST_CASE("microSD FORMAT as FAT32 - ERASES THE CARD", "[sdcard_format][ignore]")
{
    printf("Formatting the microSD card as FAT32. All data on it will be lost.\n");
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_format());
    TEST_ASSERT_EQUAL(ESP_OK, bsp_sdcard_unmount());
}
