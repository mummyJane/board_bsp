/*
 * USB host on the P4 high-speed OTG port (USB-A J1): enumerate everything,
 * including devices behind a hub, and flag RTL-SDR dongles.
 */
#include <stdio.h>
#include "unity.h"
#include "usb/usb_host.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define SCAN_SECONDS    8

static volatile bool s_lib_running;

static void usb_lib_task(void *arg)
{
    while (s_lib_running) {
        uint32_t flags = 0;
        usb_host_lib_handle_events(pdMS_TO_TICKS(100), &flags);
    }
    vTaskDelete(NULL);
}

static void client_cb(const usb_host_client_event_msg_t *msg, void *arg)
{
    if (msg->event == USB_HOST_CLIENT_EVENT_NEW_DEV) {
        printf("new device at address %u\n", msg->new_dev.address);
    }
}

static const char *speed_name(usb_speed_t s)
{
    switch (s) {
    case USB_SPEED_LOW: return "low";
    case USB_SPEED_FULL: return "full";
    case USB_SPEED_HIGH: return "high";
    default: return "?";
    }
}

static bool is_rtl_sdr(uint16_t vid, uint16_t pid)
{
    return vid == 0x0BDA && (pid == 0x2838 || pid == 0x2832);
}

TEST_CASE("USB host: list devices on USB-A (hub, RTL-SDR)", "[usb]")
{
    const usb_host_config_t host_cfg = {
        .intr_flags = 0,
        .peripheral_map = 0,    /* default = high-speed OTG on the P4 */
    };
    TEST_ASSERT_EQUAL(ESP_OK, usb_host_install(&host_cfg));
    s_lib_running = true;
    xTaskCreate(usb_lib_task, "usb_lib", 4096, NULL, 5, NULL);

    usb_host_client_handle_t client = NULL;
    const usb_host_client_config_t client_cfg = {
        .is_synchronous = false,
        .max_num_event_msg = 8,
        .async = {
            .client_event_callback = client_cb,
            .callback_arg = NULL,
        },
    };
    TEST_ASSERT_EQUAL(ESP_OK, usb_host_client_register(&client_cfg, &client));

    printf("Waiting %d s for enumeration...\n", SCAN_SECONDS);
    for (int i = 0; i < SCAN_SECONDS * 10; i++) {
        usb_host_client_handle_events(client, pdMS_TO_TICKS(100));
    }

    uint8_t addrs[16];
    int n = 0;
    TEST_ASSERT_EQUAL(ESP_OK, usb_host_device_addr_list_fill(sizeof(addrs), addrs, &n));
    printf("%d USB device(s):\n", n);
    int sdrs = 0;
    for (int i = 0; i < n; i++) {
        usb_device_handle_t dev = NULL;
        if (usb_host_device_open(client, addrs[i], &dev) != ESP_OK) {
            continue;
        }
        const usb_device_desc_t *desc = NULL;
        usb_device_info_t info = {0};
        usb_host_get_device_descriptor(dev, &desc);
        usb_host_device_info(dev, &info);
        printf("  addr %u: %04x:%04x class 0x%02x, %s speed%s%s\n", addrs[i],
               desc->idVendor, desc->idProduct, desc->bDeviceClass, speed_name(info.speed),
               desc->bDeviceClass == USB_CLASS_HUB ? "  <- hub" : "",
               is_rtl_sdr(desc->idVendor, desc->idProduct) ? "  <- RTL-SDR" : "");
        if (is_rtl_sdr(desc->idVendor, desc->idProduct)) {
            sdrs++;
        }
        usb_host_device_close(client, dev);
    }
    printf("RTL-SDR dongles found: %d\n", sdrs);

    usb_host_client_deregister(client);
    s_lib_running = false;
    usb_host_lib_unblock();
    vTaskDelay(pdMS_TO_TICKS(200));
    usb_host_device_free_all();
    vTaskDelay(pdMS_TO_TICKS(200));
    usb_host_uninstall();

    TEST_ASSERT_GREATER_THAN_MESSAGE(0, n, "nothing enumerated on USB-A");
}
