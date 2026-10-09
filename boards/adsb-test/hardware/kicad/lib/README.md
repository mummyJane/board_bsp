# ADSB_Test project libraries

Referenced from the project via `${KIPRJMOD}/lib/...` (see `../sym-lib-table`, `../fp-lib-table`).

| Item | Library | Source |
|------|---------|--------|
| `PantsForBirds_ADSBee_m1421` symbol | ADSB_Test.kicad_sym | ADSBee 1421 carrier design (Rev A) |
| `MiniCircuits_SCN-2-11` symbol | ADSB_Test.kicad_sym | ADSBee 1421 carrier design (Rev A) |
| `PantsForBirds_ADSBee_m1421_Module` footprint | ADSB_Test.pretty | ADSBee 1421 carrier design: extracted from the PCB, flipped to the front side, orientation 0 |
| `MiniCircuits_SCN` footprint | ADSB_Test.pretty | ADSBee 1421 carrier design |

## Attribution and licence

The ADSBee items above come from the ADSBee 1421 carrier board by
**Pants for Birds LLC** (John McNelly), published at
<https://pantsforbirds.com/the-worlds-smallest-dual-band-ads-b-receiver-module/>
(`adsbee_1421-A.zip`). The ADSBee hardware is published as open source under
**GPL-3.0**, so these files remain under GPL-3.0, not the repository's MIT
licence.

Notes:
- The 3D STEP models embedded in the original board were not carried over.
- Check the footprint against the m1421 datasheet/drawing before ordering PCBs.
  It is the carrier's footprint, so it is the best available reference.
