# ADSB_Test block floorplan (fit check, 2026-10-12)

A quick check, before layout, that every block still fits now the MCU is the
OSPTEK ESP32-P4C5 module, the Dev port has the hub + FT2232H + RP2040, and the RF cans,
RTC, test pads and LA header are in. It is **not** a placement: it sizes zones
from the real footprints and checks them against the board, the edge
connectors, the mounting holes, the panel cables and the battery.

Re-run after schematic changes:

```powershell
python boards\adsb-test\hardware\floorplan\floorplan.py --compare        # gap 4..16 mm round the panel
python boards\adsb-test\hardware\floorplan\floorplan.py                  # 180.9 x 116 mm: table + floorplan.svg/png
python boards\adsb-test\hardware\floorplan\floorplan.py --size 196x97    # any other size
```

![Floorplan, 180.9 x 116 mm](../hardware/floorplan/floorplan.png)

_Component (bottom) side; the panel is on the other side. Left = RF edge,
right = digital edge (swapped 2026-10-20 so the digital connectors sit next to
the module). Orange box = where the 2 × 18650 cells sit behind the board (parts
there ≤ 4 mm). Purple = slots for the panel cables (measured on the Waveshare
board). Grey circles = corner mounting holes._

## Method

- Courtyard of every placed part from its KiCad footprint (480 parts,
  including the 1.5 mm test pads): **about 11,000 mm²**.
- Required zone area = 1.6 × small parts (spacing and 4-layer routing for hand
  assembly) + 1.15 × big parts (module, connectors, cans). RF can frames count as
  an envelope for the parts under them.
- Green < 75 %, yellow 75–90 %, red > 90 % of the zone. Above about 90 % hand
  assembly gets uncomfortable.

## Board outline: panel + an even gap all round

The panel is 164.9 × 100 mm (the AliExpress MIPI panel drawing; the Waveshare
lens is 164.28 × 99.17). Making the board bigger than the panel on **all four
sides** gives an even border in the case. The panel cables then fold through
**slots in the PCB** at the panel's bottom edge instead of round the board edge.

| Gap round the panel | Board | Overall | Fullest zone |
|---------------------|-------|---------|--------------|
| 4 mm | 172.9 × 108 | 75 % | 96 % (too tight) |
| 6 mm | 176.9 × 112 | 70 % | 89 % (borderline) |
| **8 mm** | **180.9 × 116** | **61 %** | **83 %** |
| 10 mm | 184.9 × 120 | 62 % | 77 % |
| 12 mm | 188.9 × 124 | 59 % | 72 % |

For comparison, the earlier plan (188 × 97, the panel flush with the long edges)
is 75 % overall but 100 % along the display strip.

**Recommended: 8 mm gap, board 180.9 × 116 mm** (Q28). Zones, left to right
(layout of 2026-10-20: RF edge left, digital edge right, module kept in place):

| Zone | Size (mm) | Fill |
|------|-----------|------|
| m1421 + RF (can 27.5 mm), left edge top | 34 × 58 | 63 % |
| GNSS (can 17.8 mm), left edge bottom | 34 × 58 | 25 % (keep it quiet) |
| Bucks + load switches + monitors (top band) | 58 × 36 | 51 % |
| Charger + RTC (top band) | 36 × 36 | 69 % |
| Power in + User USB-C (top band, digital end) | 27 × 36 | 57 % |
| Dev UARTs (FT2232H) + m1421 programmer (RP2040) | 58 × 41 | 86 % |
| Display supplies + LCD FPC | 58 × 25 | 82 % |
| MCU module (OSPTEK 25 × 25 mm) + touch FPC | 36 × 66 | 63 % |
| LA header (along the bottom) | 94 × 14 | 72 % |
| Dev hub + Ethernet + USB host (digital edge) | 27 × 60 | 78 % |
| Storage + expander (digital edge) | 27 × 20 | 54 % |

## Findings

1. **Board 180.9 × 116 mm**, panel centred with an 8 mm border. Shorter than the
   earlier 188 mm, 19 mm taller.
2. **Panel cable slots: measured on the Waveshare board (2026-10-20).** The tails fold back behind the panel
   and pass through the PCB past the wide section with the chip, into sockets 7 mm further in.
   - Measured (back view, from the Waveshare PCB's bottom edge and USB side): **LCD 22 × 3 mm**, bottom of the
     hole 41 mm up, near side 68 mm from the USB side; **touch 8 × 3 mm**, 48 mm up, 122 mm from the USB side.
   - In panel coordinates (front view from the panel's left edge, the USB side being its right edge; +1.58 mm
     because the Waveshare PCB edge is that far in from the lens edge):

     | Slot | Across (from left) | Up from the panel's bottom edge | Socket |
     |------|--------------------|---------------------------------|--------|
     | LCD 30-pin | 74–96 mm | 42.6–45.6 mm | J1301 |
     | Touch 6-pin | 34–42 mm | 49.6–52.6 mm | J1302 |

   - They agree with the panel drawings (touch tail from 37.5 mm; Midas LCD tail at ~73–90 mm).
   - The module sits **between the two sockets** (short MIPI run to J1301); the LA header runs along the
     bottom edge. Values live in `SLOTS_FRONT` in `gen_pcb.py`.
3. **Mounting holes move to the board corners** (4 mm in). The Waveshare
   156 × 89 mm pattern would now be under the panel.
4. **Digital edge (right, bottom view; since 2026-10-20):** User USB-C, Dev USB-C, USB-A,
   RJ45, microSD, **the POWER switch and the SLEEP/WAKE button** need 92.1 mm of the 101 mm
   between the corner holes (about 1.3 mm between parts). It is the edge nearer the
   module (about 30 mm from it instead of about 100 mm), so the USB, RMII and SD runs are
   short and the digital traffic stays on the far side of the board from the RF. If the
   case needs wider webs, the SLEEP/WAKE button can move to the top edge.
5. **RF edge (left):** the two SMAs, far apart (1090/978 at the top, GNSS at the bottom),
   with the m1421 and GNSS cans behind them.
   **Wi-Fi antenna:** J602 RP-SMA (bulkhead, 12.2 mm wide, pads 7.5 mm in, barrel over the edge) on the **top long edge**,
   96 mm from the RF end, so the 2.4/5 GHz transmitter is well away from the GNSS and
   1090/978 antennas. J601 U.FL just behind it takes a 100 mm jumper from the module's
   IPEX. Leave a case hole and room for the antenna above that edge.
6. **LA header** (2 × 20 shrouded, 59.5 × 10.9 mm, 9.1 mm tall) lies along the bottom
   edge, reachable with the back cover off.
7. **Battery:** two 18650 cells across the board over the MCU and power area.
   Tall parts stay out from under them: RJ45 (13.5 mm, at the edge), JST battery
   connector (9.8 mm), LA header (9.1 mm), USB-A (7 mm), the 150 µF electrolytic
   (6 mm), the RF cans (5.1 mm). The BOOT/RESET buttons (B3F-1000, 4.3 mm) now sit
   in the top band near the digital edge, and J301 at the top of the charger zone,
   both outside the cells. The USB-A bulk capacitor C1103 must also go outside them.
8. **RJ45:** the BOM's HR911105A is full-height (13.5 mm), not mid-mount. Fine as
   long as the battery isn't over it.
9. **GNSS corner** has room to spare (25 %): good for noise, and the place to move
   quiet, low-speed parts if something has to give later.
