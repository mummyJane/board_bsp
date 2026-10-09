#pragma once

#include "esp_err.h"
#include "bsp/board_pins.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialise board-level resources common to all applications.
 *
 * Safe to call more than once.
 */
esp_err_t bsp_init(void);

/** @brief Return the board name string. */
const char *bsp_board_name(void);

#ifdef __cplusplus
}
#endif
