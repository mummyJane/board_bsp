# Generated schematic sheets

Some ADSB_Test sheets are generated from Python with
[`tools/kicad_sch_gen.py`](../../../../tools/kicad_sch_gen.py).

How it works:
- Symbols are copied from the KiCad 10 libraries and the project library and
  placed on the sheet.
- Every pin gets a short wire stub ending in a net label, power symbol or
  no-connect flag.
- Connectivity is by net name. **Global labels** are cross-sheet nets and
  **local labels** are sheet-only nets. The result is a normal KiCad
  schematic: ERC checks it and it can be tidied by hand.

| Sheet | Script | Status |
|-------|--------|--------|
| M1421 (page 14) | [gen_m1421.py](gen_m1421.py) | Generated (incl. optional RF can SH1401) |
| Power Input, Charger Battery, Power Rails, Power Monitor (pages 2–5) | [gen_power.py](gen_power.py) | Generated |
| MCU Module (page 6), RTC (page 7) | [gen_mcu.py](gen_mcu.py) | Generated (OSPTEK ESP32-P4C5 Core + optional DS3231M) |
| OSPTEK ESP32-P4C5 Core symbol + `_HandSolder` footprint (library) | [gen_osptek_p4c5.py](gen_osptek_p4c5.py) | Generated from OSPTEK's pin table and dimension drawing |
| Ethernet, User USB-C, Dev USB Hub, USB Host, GPS, Display Touch, Storage Misc, Test Debug, Dev UARTs, Dev m1421 Programmer (pages 8-13, 15-18) | [gen_periph.py](gen_periph.py) | Generated |
| AP3032 symbol, STUSB4500QTR copy with VSYS at the bottom (library) | [gen_symbols.py](gen_symbols.py) | Generated (uses `tools/kicad_sym_make.py`) |
| Net classes + pair rules (`ADSB_Test.kicad_pro`, `ADSB_Test.kicad_dru`) | [gen_netclasses.py](gen_netclasses.py) | Generated |
| PCB placement (`ADSB_Test.kicad_pcb`, A2 page, board centred): outline, corner holes, panel-cable slots, edge connectors, big parts, and every other part from the per-page `PLACE` arrays at the top of the script (uncommented = placed, commented = parked beside the board). One coordinate rule everywhere: `(x, y, rot)` = footprint origin in mm from the board's top-right corner as seen in KiCad's normal view (x to the left, y down), rot as KiCad shows it | [gen_pcb.py](gen_pcb.py) (KiCad's Python, no arguments: `& "C:\Program Files\KiCad\10.0\bin\python.exe" boards\adsb-test\hardware\gen\gen_pcb.py`) | Generated; overwrites the board but KEEPS routing (tracks, vias, hand-drawn zones copied over by net name; `--keep-locked` keeps only items locked in KiCad, `--clear-routing` drops them). Ground plane (In2), ground fills (B/In1/F) and ground vias are regenerated each run ([copper.py](copper.py)). After moving parts in KiCad, save and run [dump_placement.py](dump_placement.py) `--write` first so the moves go into `PLACE` |
| Placement numbers from the saved PCB | [dump_placement.py](dump_placement.py) (KiCad's Python; `--write` edits gen_pcb.py in place: changed numbers in PLACE/BIG/EDGE_*, comments out parts moved off the board, uncomments parts moved onto it; `--rebuild` rewrites the PLACE block after parts are added to the schematic; no option = print) | Tool |
| `_HandSolder` copies of vendor footprints, 4-pad Kelvin 1206 shunt footprint (library) | [gen_footprints.py](gen_footprints.py) | Generated (upgrade new footprints with `kicad-cli fp upgrade` in a temp folder; re-running rewrites the others) |

Whole-project ERC: **0 violations** (all 16 sheets generated, every cross-sheet net has both ends). 480 parts, 481 nets, no duplicate references; power symbols are numbered page x 1000 per sheet. Footprints are checked on every run (`MISSING FOOTPRINTS:` is printed if a name doesn't exist).

## Regenerate a sheet

```powershell
python boards\adsb-test\hardware\gen\gen_m1421.py
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch upgrade boards\adsb-test\hardware\kicad\m1421.kicad_sch
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch erc --severity-all boards\adsb-test\hardware\kicad\ADSB_Test.kicad_sch
```

**Regenerating overwrites the sheet.** Once a sheet has been tidied or edited
by hand in KiCad, stop regenerating it: mark it "frozen" in the table above and
edit it in KiCad from then on.

## Conventions

- Reference designators: the sheet's page number × 100 (M1421 = page 14 →
  U1401, R1401, …).
- Net names: `P4_*` = driven by the P4, `DEV_*` = from the Dev-port domain,
  `M1421_*` = the m1421 side, rails like `3V3_M1421` are global labels.
- `PWR_FLAG`s mark rails fed through passive parts (shunts, inductors) so ERC
  knows they're driven.
- If no footprint is given, the library symbol's default footprint is used.

## Routing

Layers (all parts on B.Cu): **B.Cu** parts + critical routing, **In2.Cu** solid ground (layer type *power*: the
reference plane right under the component side, never routed), **In1.Cu** power + slow signals, **F.Cu** slow
signals. Ground fill on B/In1/F, a via beside every small ground pad. Net classes (`gen_netclasses.py`):
`PWR_HI` 0.8 mm (charger, VSYS, 5V, 3V3_BUCK, switch nodes), `PWR` 0.3 mm, `GND` (fills only, never routed).

1. Route by hand and **lock** (select, `L`): RF_50R feeds (B.Cu only, no vias), USB / DSI / Ethernet pairs
   (diff-pair router, `6`), the PWR_HI nets with pours, crystal nets.
2. Freerouting (KiCad plugin): ignore net classes `GND` and `PWR_HI`; it sees In2 as a plane and does not route on it.
3. Import, run DRC. Rebuilding with gen_pcb.py keeps all of it (`--keep-locked` to throw away the autorouted part
   and keep the hand routes).
