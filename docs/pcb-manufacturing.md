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

## Hand soldering vs. PCBWay assembly

The owner hand-solders and wants larger parts where there's a choice. So:

- **Passives:** resistors, capacitors and LEDs are **0805 with KiCad
  "HandSolder" pads** (bigger caps and shunts are 1206 HandSolder). Test points
  are 1.5 mm pads. The schematic generators apply this automatically.
- **Through-hole** where it helps: the power switch, the coin-cell holder and
  the headers.
- **Fine-pitch parts can't be hand-soldered by eye.** Have PCBWay assemble at
  least these (partial PCBA), then hand-fit the rest:

| Part | Package | Pitch |
|------|---------|-------|
| ESP32-P4NRW32 | QFN-104 | 0.35 mm |
| RP2040 | QFN-56 | 0.4 mm |
| BQ25798 | VQFN-29 (RQM) | 0.4 mm |
| STUSB4500 | QFN-24 | 0.5 mm |
| PAC1954 ×3 | VQFN-16 | 0.5 mm |
| TPS62933 ×2 | SOT-583 | 0.5 mm |
| USB2514B, FT2232H, CP2102N, IP101GRI | QFN | 0.4–0.5 mm |
| 74LVC1G gates | SC-70 | 0.65 mm |
| ESD7351 (m1421 RF ESD) | SOD-523 | only made in this size |
| ESP32-C5-WROOM-1, ADSBee m1421, MAX-M10S | modules with bottom/edge pads | reflow recommended |

(Open question Q24 on ADSB_Test: full PCBA, or partial PCBA plus hand assembly.)
