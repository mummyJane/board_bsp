# PCB manufacturing and assembly

Fab and assembly house: **PCBWay**. The numbers below come from PCBWay's
published capabilities (<https://www.pcbway.com/capabilities.html>, read
2026-10-12). Turn them into KiCad board-setup / DRC rules when layout starts,
and recheck them against PCBWay's page at that point.

## PCBWay capabilities that matter here

| Item | PCBWay standard | Notes |
|------|-----------------|-------|
| Layers | 1–14 | ADSB_Test: **4 layers** (signal / GND / power / signal) |
| Thickness | 0.2–3.2 mm | **1.6 mm** |
| Min trace / space | 0.1 mm (4 mil) | Advanced outer 1 oz: 5/6 mil |
| Min drill | 0.15 mm | Advanced 0.20 mm |
| Annular ring | ≥ 0.15 mm (6 mil) | |
| Via plugging / fill | 0.20–0.40 mm holes, 70 % fill; 0.40–0.70 mm 100 % | The m1421 asks for **filled + capped** vias under its pads: order via-in-pad filling (POFV) for those |
| Castellated holes | ≥ 0.5 mm, spacing ≥ 0.3 mm (advanced) | Not needed on our board |
| Solder-mask bridge | 4 mil (< 2 oz copper) | |
| Silkscreen | line ≥ 0.15 mm, height ≥ 0.8 mm | Use 1.0 mm text for readability |
| Edge clearance | copper ≥ 0.25 mm from a routed edge | |
| Impedance control | ±10 % (±5 Ω at ≤ 50 Ω) | Needed: RF 50 Ω CPW (m1421, GNSS), USB 90 Ω diff, MIPI-DSI 100 Ω diff, RMII ~50 Ω |
| Finish | HASL, ENIG, … | **ENIG**: flat pads for the fine-pitch QFNs and the m1421 |

## Our design rules (start values, slightly conservative)

| Rule | Value |
|------|-------|
| Default track / clearance | 0.15 mm / 0.15 mm (fine-pitch escape down to 0.1 / 0.1) |
| Power tracks | sized for current; copper pours for VSYS / 5V / 3V3 |
| Vias | 0.3 mm drill / 0.6 mm pad (0.25 / 0.5 for the P4 fan-out if needed) |
| Silkscreen | 0.15 mm line, 1.0 mm text |
| Board edge to copper | 0.3 mm |

## Build plan: Rev 1 hand-assembled, PCBWay makes the bare PCB

**Rev 1:** PCBWay fabricates the **PCB only** (plus a solder-paste **stencil**,
recommended). Everything is assembled by hand, block by block, so each block can
be checked as it goes on (see the ADSB_Test test plan). **Rev 2** may be PCBWay
assembled, depending on how many fixes Rev 1 needs.

### Footprint rules for hand assembly

| Part type | Footprint choice |
|-----------|------------------|
| Resistors, capacitors, LEDs | **0805 HandSolder** (1206 HandSolder for bulk caps and shunts) |
| Test points | 1.5 mm pads |
| SOT-23 parts | KiCad `*_HandSoldering` variants; logic gates in SOT-23 (DBV), not SC-70 |
| QFN / short-lead ICs | `_HandSolder` copies in the board's project library (made by `tools/kicad_fp_handsolder.py` via `hardware/gen/gen_footprints.py`): edge pads lengthened 0.4–0.5 mm past the body; exposed pads get a plated hole so they can be soldered or heated from the back |
| Modules with bottom (LGA-style) pads (ADSBee m1421, newer ESP32 modules) | `_HandSolder` copy with edge pads lengthened **1.5 mm** (≈ 1.1 mm visible past the body for the iron) and plated holes in the large bottom ground pads (solder from the back). Slightly worse RF ground than filled vias, accepted for Rev 1 |
| Power FETs | Leaded packages (SO-8) instead of PowerDI / DFN |
| Switch, coin-cell holder, headers | Through-hole where possible |
| Castellated modules (WT01P4C5-S1) | Pads run 1.2 mm under the module and **1.3 mm past its edge** for the iron (`Wireless-Tag_WT01P4C5-S1_HandSolder`). No exposed copper or untented vias under the module (it has RF test pads underneath) |
| RF can frames (optional, DNP) | Laird BMI-S-2xx-F two-piece frames; fit after the parts underneath are soldered and tested |

### Parts that still need hot air or a hot plate + stencil

| Part | Why |
|------|-----|
| BQ25798 (VQFN-HR-29, 0.4 mm) | Power pads under the chip, not just around the edge: an iron can't reach them |
| ESP32-P4NRW32 (QFN-104, 0.35 mm) | Very fine pitch + large exposed pad. **Not used on ADSB_Test**: replaced by the WT01P4C5-S1 module (Q26), 1.4 mm castellated pads, iron-solderable |
| RP2040 (QFN-56, 0.4 mm), USB2514B, FT2232H, CP2102N, IP101GRI | Fine-pitch QFNs; `_HandSolder` variants will be made when their sheets are generated |
| MiniCircuits SCN-2-11+ (RF combiner), ESD7351 (SOD-523) | Small parts only made in these packages |

Suggested kit: stencil from PCBWay, solder paste, a small hot plate or hot-air
station, flux, and a microscope/magnifier for inspection.

