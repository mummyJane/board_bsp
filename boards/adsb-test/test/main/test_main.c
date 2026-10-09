/*
 * Bring-up test app: presents the Unity test menu on the serial console.
 * Add a new test_<feature>.c file per peripheral using TEST_CASE().
 */
#include "unity.h"
#include "bsp/bsp.h"

void app_main(void)
{
    bsp_init();
    unity_run_menu();
}
