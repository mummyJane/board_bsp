# ADSB_Test project libraries

Referenced from the project via `${KIPRJMOD}/lib/...` (see `../sym-lib-table`, `../fp-lib-table`).

| Item | Library | Source |
|------|---------|--------|
| `PantsForBirds_ADSBee_m1421` symbol | ADSB_Test.kicad_sym | PantsForBirds/kicad-libs `lib_sch/Custom_Module.kicad_sym`. **Changed:** SYNC (pin 28) electrical type output → **input**, matching the firmware docs. Footprint and datasheet fields re-pointed |
| `MiniCircuits_SCN-2-11` symbol | ADSB_Test.kicad_sym | PantsForBirds/kicad-libs `lib_sch/Custom_RF_SplitterCombiner.kicad_sym` |
| `PantsForBirds_ADSBee_m1421_Module` footprint | ADSB_Test.pretty | PantsForBirds/kicad-libs `lib_fp/Custom_Module.pretty`, unchanged (3D models embedded). Pads checked identical to the ADSBee 1421 carrier PCB |
| `MiniCircuits_SCN` footprint | ADSB_Test.pretty | PantsForBirds/kicad-libs `lib_fp/Custom_RF_SplitterCombiner.pretty`, unchanged |

## Licence

These parts come from <https://github.com/PantsForBirds/kicad-libs>, © 2024
John McNelly, **MIT licence**. The licence is copied in
[`LICENSE-PantsForBirds-kicad-libs.txt`](LICENSE-PantsForBirds-kicad-libs.txt).

The ADSBee m1421 firmware and module schematic are GPL-3.0. None of that is
copied into this repository.
