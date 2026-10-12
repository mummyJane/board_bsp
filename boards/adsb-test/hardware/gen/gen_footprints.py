#!/usr/bin/env python3
"""Create the hand-solder footprint variants used by ADSB_Test Rev A (all hand-assembled).

Run from the repo root: python boards/adsb-test/hardware/gen/gen_footprints.py
Writes <name>_HandSolder.kicad_mod into hardware/kicad/lib/ADSB_Test.pretty.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from kicad_fp_handsolder import make_handsolder  # noqa: E402

KIFP = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
LIB = ROOT / "boards/adsb-test/hardware/kicad/lib/ADSB_Test.pretty"

jobs = [
    # ADSBee m1421: bottom (LGA-style) pads 1.2 x 0.8 mm end 0.4 mm inside the 14.5 mm body.
    # +1.5 mm brings ~1.1 mm of each pad out past the body for the iron. Plated holes in the two
    # MP ground/thermal pads let them be soldered from the back.
    dict(src=LIB / "PantsForBirds_ADSBee_m1421_Module.kicad_mod", name="PantsForBirds_ADSBee_m1421_Module_HandSolder",
         extend=1.5, only=[str(i) for i in range(1, 37)],
         holes={"MP": [(-1.643744, -5.162307, 0.8),
                       (-1.393744, 3.037693, 0.8), (1.106256, 3.037693, 0.8),
                       (-1.393744, 5.037693, 0.8), (1.106256, 5.037693, 0.8)]},
         note="Holes in MP pads: solder from the back; slightly worse RF ground than filled vias"),
    # STUSB4500 QFN-24 4x4 mm, EP 2.7 mm: longer pads + 1.0 mm hole in the EP (pad 25)
    dict(src=KIFP / "Package_DFN_QFN.pretty/QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm.kicad_mod",
         name="QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_HandSolder", extend=0.5, holes={"25": [(0, 0, 1.0)]}),
    # PAC1954 VQFN-16 3x3 mm: EP is not connected inside, so no hole; longer pads only
    dict(src=KIFP / "Package_DFN_QFN.pretty/VQFN-16-1EP_3x3mm_P0.5mm_EP1.1x1.1mm.kicad_mod",
         name="VQFN-16-1EP_3x3mm_P0.5mm_EP1.1x1.1mm_HandSolder", extend=0.5),
    # TPS62933 SOT-583: short leads, longer pads help
    dict(src=KIFP / "Package_TO_SOT_SMD.pretty/SOT-583-8.kicad_mod", name="SOT-583-8_HandSolder", extend=0.4),
]

for j in jobs:
    n = make_handsolder(j["src"], LIB / f"{j['name']}.kicad_mod", j["name"], extend=j["extend"],
                        holes=j.get("holes"), only_pads=j.get("only"), descr_note=j.get("note", ""))
    print(f"{j['name']}: {n} pads lengthened")
