cmake_minimum_required(VERSION 3.16)

set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_LIST_DIR}/../bsp"
    "${CMAKE_CURRENT_LIST_DIR}/../../../common/components"
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(bsp_test_p4_lcd_7b)
