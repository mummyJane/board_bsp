# <Board name>

Template for a new board. To start one:

1. Copy `boards/_template` to `boards/<board-name>`.
2. Copy `bsp/` and `test/` from the reference board
   (`boards/esp32-p4-wifi6-touch-lcd-7b`) and update `board_pins.h`,
   `BSP_BOARD_NAME`, and the test project name.
3. Create the KiCad project in `hardware/kicad/` (KiCad 10), set the title block
   (board name, `Rev A`, date).
4. Add the board to the table in the top-level `README.md` and add a
   CHANGELOG entry.

## Hardware revisions

| Rev | Date | Changes |
|-----|------|---------|
| A | | Initial |
