idf_component_register(
    SRCS "test_main.c" "test_bsp.c"
    INCLUDE_DIRS "."
    REQUIRES bsp unity
    WHOLE_ARCHIVE
)
