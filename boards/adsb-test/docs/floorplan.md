# ADSB_Test block floorplan (fit check, 2026-10-12)

A quick check, before layout, that every block still fits now the MCU is the
WT01P4C5-S1 module, the Dev port has the hub + FT2232H + RP2040, and the RF cans,
RTC, test pads and LA header are in. It is **not** a placement: it sizes zones
from the real footprints and checks them against the board, the edge
connectors, the mounting holes, the panel cables and the battery.

Re-run after schematic changes:

```powershell
python boards\adsb-test\hardware\floorplan\floorplan.py --compare        # several board sizes
python boards\adsb-test\hardware\floorplan\floorplan.py --size 196x97    # table + floorplan.svg/png
```

![Floorplan, 196 x 97 mm](../hardware/floorplan/floorplan.png)

_Component (bottom) side; the panel is on the other side. Left = digital
edge, right = RF edge. Orange box = where the 2 × 18650 cells sit behind the
board (parts there ≤ 4 mm). Purple = where the panel cables fold over (Waveshare
panel, approximate)._

## Method

- Courtyard of every placed part from its KiCad footprint (480 parts,
  including the 1.5 mm test pads): **about 11,000 mm²**.
- Required zone area = 1.6 × small parts (spacing and 4-layer routing for hand
  assembly) + 1.15 × big parts (module, connectors, cans). RF can frames count as
  an envelope for the parts under them.
- Green < 75 %, yellow 75–90 %, red > 90 % of the zone. Above about 90 % hand
  assembly gets uncomfortable.

## Result

| Board | Overall fill | Fullest zone | Verdict |
|-------|-------------|--------------|---------|
| 188 × 97 mm (12 mm margins, current plan) | 75 % | Display supplies + LCD FPC **100 %** | Fits on paper, too tight in the middle and along the display edge |
| **196 × 97 mm (16 mm margins)** | **72 %** | LA header column 88 % | **Recommended**: every zone under 90 % |
| 204 × 97 mm | 69 % | 88 % | More room, longer case |
| 188 × 105 mm (8 mm strip on the top long edge) | 70 % | 100 % | Doesn't help the crowded zones |

Zones at 196 × 97 mm:

| Zone | Size (mm) | Fill |
|------|-----------|------|
| Power in + User UART | 28 × 30 | 64 % |
| Charger + RTC | 38 × 30 | 78 % |
| Bucks + load switches + monitors | 70 × 30 | 48 % |
| m1421 + RF (can 27.5 mm) | 34 × 48 | 76 % |
| GNSS (can 17.8 mm) | 34 × 48 | 30 % (keep it quiet) |
| Dev USB (hub, FT2232H, RP2040) | 60 × 44 | 85 % |
| LA header (vertical) | 16 × 67 | 88 % |
| MCU module | 60 × 44 | 85 % |
| Ethernet + USB host | 40 × 23 | 80 % |
| Storage + expander + touch FPC | 20 × 23 | 64 % |
| Display supplies + LCD FPC | 60 × 23 | 87 % |

## Findings

1. **Make the board 196 × 97 mm** (16 mm margins on the short edges instead of
   12). It adds 8 mm to the length of the case; nothing else changes. (Q28)
2. **Digital edge:** User USB-C, Dev USB-C, USB-A, RJ45 and microSD need 71 mm of
   the 82 mm between the mounting-hole keep-outs (about 2.7 mm gaps). It fits, but
   nothing more can go on that edge. The **POWER switch moves to the RF edge**
   (between the two SMAs: it only switches the PWR_EN signal).
3. **Panel cables decide where the display block goes.** With the Waveshare panel
   the right way round, the LCD cable folds over the bottom long edge about 135 mm
   from the digital edge and the touch cable about 67 mm from it. So the display
   supplies + 30-pin connector sit bottom-right next to the MCU (short MIPI run),
   and the 6-pin touch connector sits in the storage zone. Measure both tail
   positions on a spare Waveshare board before layout.
4. **LA header** (2 × 20 shrouded, 59.5 × 10.9 mm, 9.1 mm tall) goes vertically
   between the Dev USB and MCU zones, reachable with the back cover off.
5. **Battery:** place the two 18650 cells across the board over the MCU and power
   area. Keep the tall parts out from under them: RJ45 (13.5 mm, at the edge),
   JST battery connector (9.8 mm), LA header (9.1 mm), USB-A (7 mm), the 150 µF
   electrolytic (6 mm), the RF cans (5.1 mm). The BOOT/RESET buttons (B3F-1000,
   4.3 mm) are in the MCU zone: use a low-profile tactile switch or place them
   at the zone edge.
6. **RJ45:** the BOM's HR911105A is full-height (13.5 mm), not the mid-mount part
   the architecture assumed. That's fine as long as the battery isn't over it;
   a mid-mount MagJack would only matter for a thinner case.
7. **RF column:** 34 mm is enough for the m1421 can (27.5 mm) and keeps the
   GNSS corner mostly empty, which is good for noise. The GNSS zone has room
   to spare if something has to move later (only low-speed, quiet parts).
