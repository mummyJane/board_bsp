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

## Impedance-controlled nets (ADSB_Test)

Net classes are in `ADSB_Test.kicad_pro` and pair rules in `ADSB_Test.kicad_dru`, both written by
`boards/adsb-test/hardware/gen/gen_netclasses.py`. KiCad finds the pairs from the `_P`/`_N` suffix.

| Class | Nets | Target | Width / gap | In-pair skew | Other |
|-------|------|--------|-------------|--------------|-------|
| USB_90R | USB_HS, USER, DEV, P4_USJ, FT, RP, RP_HUB `_D_P/_D_N` | 90 Ω differential | 0.22 / 0.15 mm | 0.15 mm | uncoupled ≤ 3 mm |
| MIPI_100R | DSI_CLK, DSI_D0, DSI_D1 `_P/_N` | 100 Ω differential | 0.18 / 0.15 mm | 0.1 mm | lanes matched to 1 mm, uncoupled ≤ 2 mm |
| ETH_100R | ETH_TX_P/_N, ETH_RX_P/_N | 100 Ω differential | 0.18 / 0.15 mm | 0.5 mm | |
| RF_50R | RF_ADSB_ANT, M1421_RF_978/1090, GPS_RF, WIFI_ANT | 50 Ω CPWG | 0.32 mm, 0.20 mm gap to the ground pour | — | no vias; stitch the pour along both sides |
| (single-ended RMII, ~50 Ω) | ETH_TXD/RXD/REF_CLK… | 50 Ω | 0.29 mm if it matters; short runs at 0.15 mm are fine | | |

**Stack-up (PCBWay standard 4-layer 1.6 mm, <https://www.pcbway.com/multi-layer-laminated-structure.html>
entry #1, read 2026-10-20):** 1 oz outer copper (0.5 oz + plating), **7628 prepreg 0.1855 mm** (Dk 4.74),
1.1 mm core with 1 oz inner copper (Dk 4.6), 1 oz, 7628 0.1855 mm, 1 oz. Finished 1.61 mm. It is written into
the board by `gen_pcb.py`. The widths above come from `python tools/impedance.py` (IPC-2141 microstrip /
edge-coupled pair and Wadell CPWG closed forms, about ±10 %; solder mask takes off another 2–3 Ω). **Order
impedance control** and give PCBWay the targets: they adjust the widths to their process. The routing layer
is the bottom (B.Cu, component side) over In2.Cu, or the top over In1.Cu; both are the same geometry.

## Our design rules (start values, slightly conservative)

| Rule | Value |
|------|-------|
| Default track / clearance | 0.15 mm / 0.15 mm (fine-pitch escape down to the DRC minimum 0.127 / 0.127) |
| Power tracks | sized for current; copper pours for VSYS / 5V / 3V3 |
| Vias | 0.3 mm drill / 0.6 mm pad (0.25 / 0.5 for the P4 fan-out if needed; DRC minimum 0.25 / 0.5) |
| Silkscreen | 0.15 mm line, 1.0 mm text |
| Board edge to copper | 0.5 mm (DRC); 0.2 mm for the edge-mount RP-SMA J602 (custom rule) |

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
| Castellated / stamp-hole modules (OSPTEK ESP32-P4C5 Core, 1.0 mm) | 0.7 mm pads run 1.0 mm under the module and **1.3 mm past its edge** for the iron (`OSPTEK_ESP32-P4C5_Core_HandSolder`). Flux + fine tip; check for bridges. No exposed copper or untented vias under the module (it has RF test pads underneath) |
| RF can frames (optional, DNP) | Laird BMI-S-2xx-F two-piece frames; fit after the parts underneath are soldered and tested |

### Parts that still need hot air or a hot plate + stencil

| Part | Why |
|------|-----|
| BQ25798 (VQFN-HR-29, 0.4 mm) | Power pads under the chip, not just around the edge: an iron can't reach them |
| ESP32-P4NRW32 (QFN-104, 0.35 mm) | Very fine pitch + large exposed pad. **Not used on ADSB_Test**: replaced by the OSPTEK ESP32-P4C5 module (Q26), 1.0 mm stamp holes, iron-solderable |
| RP2040 (QFN-56, 0.4 mm), USB2514B (QFN-36), CP2102N (QFN-24), LAN8720A (VQFN-24) | Fine-pitch QFNs: `_HandSolder` variants (longer pads, hole in the EP) help, but use paste + hot air. FT2232H**L** is LQFP-64 (leads: iron + drag soldering) |
| FPC connectors (Hirose FH12, 0.5 mm) | Drag-solder with flux; check for bridges under magnification |
| MiniCircuits SCN-2-11+ (RF combiner), ESD7351 (SOD-523) | Small parts only made in these packages |

Suggested kit: stencil from PCBWay, solder paste, a small hot plate or hot-air
station, flux, and a microscope/magnifier for inspection.

