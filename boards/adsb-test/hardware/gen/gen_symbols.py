#!/usr/bin/env python3
"""Project symbols for parts that have none in the KiCad 10 library.

Run from the repo root: python boards/adsb-test/hardware/gen/gen_symbols.py
then: kicad-cli sym upgrade --force boards/adsb-test/hardware/kicad/lib/ADSB_Test.kicad_sym
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from kicad_sym_make import add_box_symbol  # noqa: E402

LIB = ROOT / "boards/adsb-test/hardware/kicad/lib/ADSB_Test.kicad_sym"

# Diodes AP3032 WLED boost (SOT-23-6), as U12 on the Waveshare reference board. Pins from the
# AP3032 datasheet and the reference schematic: 1 SW, 2 GND, 3 FB, 4 EN, 5 OV, 6 IN.
add_box_symbol(LIB, "AP3032", "U", "AP3032",
               left=[("6", "IN", "power_in"), ("4", "EN", "input"), ("2", "GND", "power_in")],
               right=[("1", "SW", "output"), ("5", "OV", "input"), ("3", "FB", "input")],
               footprint="Package_TO_SOT_SMD:SOT-23-6_Handsoldering",
               datasheet="https://www.diodes.com/assets/Datasheets/AP3032.pdf",
               description="AP3032 LED driver boost, 1 A switch, OVP, PWM/analog dimming via FB, SOT-23-6",
               keywords="LED backlight boost")
print("wrote AP3032 into", LIB.name)
